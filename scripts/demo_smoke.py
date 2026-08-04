#!/usr/bin/env python
"""
Smoke-walk the demo environment in a real browser.

What this catches that pytest does not: an empty render caused by a dead asset
bundle, JS errors in the console, broken Alpine initialisation, a 500 on a page
no test opens, and horizontal overflow on a phone-sized viewport. The Django test
client only ever sees HTML — here the page actually executes in Chromium.

Run: `make demo-smoke` (needs a seeded demo database — `make demo-setup`).

Screenshots land in `var/demo-smoke/`, which is where to look after a failure.
"""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SCREENSHOT_DIR = BASE_DIR / "var" / "demo-smoke"
SETTINGS = "config.settings.demo"

DEMO_PASSWORD = "demo12345"

# Console errors that are not a defect of the page: external demo media and the
# Vite dev server, which is not running in this environment.
IGNORED_CONSOLE_PATTERNS = (
    "favicon",
    "5173",
    "ERR_INTERNET_DISCONNECTED",
    "ERR_NAME_NOT_RESOLVED",
    "ERR_CONNECTION_REFUSED",
    "ERR_FAILED",
)

#: How long to wait for a page. The walk should either pass quickly or fail —
#: "hanging for a third minute" is not a result.
PAGE_TIMEOUT_MS = 15_000

#: Long enough for the staggered entry animations to finish before a screenshot.
ANIMATION_SETTLE_MS = 1_400

DESKTOP_VIEWPORT = {"width": 1280, "height": 900}

#: Widths every page must fit without horizontal scrolling. 360 is the narrowest
#: Android still in wide use, 390 is the iPhone baseline.
MOBILE_WIDTHS = (360, 390)


@dataclass
class PageCheck:
    """One check: a URL, text that must be on the page, and who to log in as."""

    name: str
    path: str
    expect_text: str = ""
    login_as: str = ""
    expect_status: int = 200


@dataclass
class Failure:
    check: str
    reason: str


@dataclass
class Report:
    failures: list[Failure] = field(default_factory=list)
    checked: int = 0

    def fail(self, check: str, reason: str) -> None:
        self.failures.append(Failure(check, reason))


CHECKS = [
    PageCheck("home", "/"),
    PageCheck("contact", "/contact/"),
    PageCheck("privacy", "/privacy/"),
    PageCheck("terms", "/terms/"),
    PageCheck("cookies", "/cookies/"),
    PageCheck("login", "/accounts/login/"),
    PageCheck("register", "/accounts/register/"),
    PageCheck("health", "/health/"),
    PageCheck("profile", "/accounts/profile/", login_as="user@demo.local"),
    PageCheck("admin", "/admin/", login_as="admin@demo.local"),
]


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for_server(base_url: str, process: subprocess.Popen, timeout: float = 40.0) -> None:
    import urllib.error
    import urllib.request

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"server died on startup (exit code {process.returncode})")
        try:
            urllib.request.urlopen(f"{base_url}/health/", timeout=2)
            return
        except urllib.error.HTTPError:
            return  # answered with anything at all — it is up
        except Exception:
            time.sleep(0.4)
    raise RuntimeError(f"server did not start within {timeout:.0f}s")


def log_in(page, base_url: str, email: str) -> None:
    page.goto(f"{base_url}/accounts/login/", wait_until="domcontentloaded")
    page.fill("input[name='username']", email)
    page.fill("input[name='password']", DEMO_PASSWORD)
    # Scope the button to the form holding the password field: layouts tend to
    # grow other hidden submit buttons (mobile menu, language switch), and a
    # global `button[type=submit]` selector grabs whichever comes first.
    page.locator("form:has(input[name='password']) button[type='submit']").first.click()
    page.wait_for_load_state("domcontentloaded")

    if "/accounts/login/" in page.url:
        raise RuntimeError(f"could not log in as {email}")


def find_chromium() -> str:
    """
    Use a Chromium that is already in the container, when there is one.

    Cloud sessions keep browsers under `PLAYWRIGHT_BROWSERS_PATH` at a build
    number that need not match the `playwright` package; the default launch then
    looks for a build that does not exist and suggests `playwright install`.
    An empty string means "default behaviour" (a developer's own machine).
    """
    explicit = os.environ.get("PLAYWRIGHT_CHROMIUM_PATH", "")
    if explicit:
        return explicit

    root = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", ""))
    if not root.is_dir():
        return ""
    candidates = sorted(root.glob("chromium*/chrome-linux/chrome"), reverse=True)
    return str(candidates[0]) if candidates else ""


def _attach(page, console_errors: list[str]) -> None:
    """
    Collect console errors and drop every request that leaves localhost.

    External hosts (fonts, CDNs, analytics) do not resolve in a sealed container
    and each one burns a timeout, turning a ten-page walk into several minutes of
    waiting. What is under test is this application, not somebody else's CDN.
    """
    page.set_default_timeout(PAGE_TIMEOUT_MS)
    page.set_default_navigation_timeout(PAGE_TIMEOUT_MS)
    page.on(
        "console",
        lambda message: console_errors.append(message.text) if message.type == "error" else None,
    )
    page.route(
        "**/*",
        lambda route: (
            route.continue_()
            if "127.0.0.1" in route.request.url or "localhost" in route.request.url
            else route.abort()
        ),
    )


def check_mobile_overflow(page, check: PageCheck, report: Report) -> None:
    """Fail when the page scrolls sideways at a phone width."""
    for width in MOBILE_WIDTHS:
        page.set_viewport_size({"width": width, "height": 800})
        overflow = page.evaluate(
            "() => ({scroll: document.documentElement.scrollWidth,"
            " client: document.documentElement.clientWidth})"
        )
        if overflow["scroll"] > overflow["client"]:
            page.screenshot(path=str(SCREENSHOT_DIR / f"{check.name}-{width}.png"), full_page=True)
            report.fail(
                check.name,
                f"horizontal overflow at {width}px: "
                f"scrollWidth {overflow['scroll']} > clientWidth {overflow['client']}",
            )
    page.set_viewport_size(DESKTOP_VIEWPORT)


def run_checks(base_url: str, checks: list[PageCheck], headed: bool) -> Report:
    from playwright.sync_api import sync_playwright

    report = Report()
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    launch_kwargs = {"headless": not headed}
    executable = find_chromium()
    if executable:
        launch_kwargs["executable_path"] = executable

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(**launch_kwargs)
        try:
            current_login = ""
            context = browser.new_context(viewport=DESKTOP_VIEWPORT)
            page = context.new_page()

            console_errors: list[str] = []
            _attach(page, console_errors)

            for check in checks:
                if check.login_as != current_login:
                    # Every change of user gets a fresh context, otherwise the
                    # previous session leaks and the wrong role is exercised.
                    context.close()
                    context = browser.new_context(viewport=DESKTOP_VIEWPORT)
                    page = context.new_page()
                    _attach(page, console_errors)
                    if check.login_as:
                        log_in(page, base_url, check.login_as)
                    current_login = check.login_as

                console_errors.clear()
                response = page.goto(f"{base_url}{check.path}", wait_until="load")
                report.checked += 1

                # Entry animations cascade for up to ~1.3s (DESIGN.md: 540ms per
                # item, 120ms apart). Screenshotting on `load` catches the later
                # cards mid-fade and makes every review look like a rendering bug.
                page.wait_for_timeout(ANIMATION_SETTLE_MS)

                page.screenshot(path=str(SCREENSHOT_DIR / f"{check.name}.png"), full_page=True)

                status = response.status if response else 0
                if status != check.expect_status:
                    report.fail(check.name, f"{check.path} → HTTP {status}")
                    continue

                if check.expect_text and check.expect_text not in page.content():
                    report.fail(check.name, f"page is missing the text {check.expect_text!r}")

                real_errors = [
                    error
                    for error in console_errors
                    if not any(pattern in error for pattern in IGNORED_CONSOLE_PATTERNS)
                ]
                if real_errors:
                    report.fail(check.name, f"console errors: {real_errors[:3]}")

                check_mobile_overflow(page, check, report)

            context.close()
        finally:
            browser.close()

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headed", action="store_true", help="show the browser")
    parser.add_argument(
        "--base-url",
        default="",
        help="check an already running server instead of starting one",
    )
    args = parser.parse_args()

    if args.base_url:
        report = run_checks(args.base_url.rstrip("/"), CHECKS, args.headed)
    else:
        port = free_port()
        base_url = f"http://127.0.0.1:{port}"
        env = {
            **os.environ,
            "DJANGO_SETTINGS_MODULE": SETTINGS,
            # The debug toolbar panel covers the content in screenshots.
            "DEMO_DEBUG_TOOLBAR": "False",
        }
        server = subprocess.Popen(
            [sys.executable, "manage.py", "runserver", f"127.0.0.1:{port}", "--noreload"],
            cwd=BASE_DIR,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            wait_for_server(base_url, server)
            report = run_checks(base_url, CHECKS, args.headed)
        finally:
            server.terminate()
            server.wait(timeout=10)

    for failure in report.failures:
        print(f"FAIL  {failure.check}: {failure.reason}")

    print(f"\nPages checked: {report.checked}, failures: {len(report.failures)}")
    print(f"Screenshots: {SCREENSHOT_DIR}")
    return 1 if report.failures else 0


if __name__ == "__main__":
    sys.exit(main())
