"""
Text generation for demo data.

Deliberately tiny and dependency-free: a demo dataset needs names and sentences
that look plausible in a list, not a natural-language generator. Everything is
driven by ``ctx.rng``, so a run with the same ``--seed`` produces the same text.

Localising the demo data means replacing these pools — nothing else reads them.
"""

from __future__ import annotations

from .context import SeedContext

FIRST_NAMES = [
    "Alex", "Maria", "John", "Olena", "David", "Sofia", "Michael", "Anna",
    "Daniel", "Julia", "Peter", "Nina", "Thomas", "Eva", "Lucas", "Clara",
    "Adam", "Iris", "Victor", "Lena",
]  # fmt: skip

LAST_NAMES = [
    "Smith", "Kovalenko", "Johnson", "Novak", "Brown", "Ivanov", "Miller",
    "Petrenko", "Wilson", "Horvath", "Taylor", "Melnyk", "Anderson", "Weber",
    "Clark", "Shevchenko",
]  # fmt: skip

NOUNS = [
    "workspace", "dashboard", "report", "invoice", "project", "signal",
    "channel", "release", "backlog", "pipeline", "handbook", "review",
]  # fmt: skip

ADJECTIVES = [
    "quiet", "shared", "internal", "weekly", "draft", "archived",
    "public", "pinned", "recent", "legacy",
]  # fmt: skip

VERBS = [
    "keeps track of", "collects", "summarises", "replaces", "documents",
    "measures", "explains", "connects",
]  # fmt: skip


def person(ctx: SeedContext) -> tuple[str, str]:
    """A (first name, last name) pair."""
    return ctx.pick(FIRST_NAMES), ctx.pick(LAST_NAMES)


def title(ctx: SeedContext) -> str:
    """A short human-looking title, e.g. "Shared release"."""
    return f"{ctx.pick(ADJECTIVES).capitalize()} {ctx.pick(NOUNS)}"


def sentence(ctx: SeedContext) -> str:
    """One sentence: "The shared release documents the weekly backlog."."""
    return (
        f"The {ctx.pick(ADJECTIVES)} {ctx.pick(NOUNS)} {ctx.pick(VERBS)} "
        f"the {ctx.pick(ADJECTIVES)} {ctx.pick(NOUNS)}."
    )


def paragraph(ctx: SeedContext, sentences: int = 3) -> str:
    return " ".join(sentence(ctx) for _ in range(sentences))
