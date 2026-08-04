# Playbook: add a seeder

Demo data for your domain, so `make demo-up` shows a site with content in it.

## 1. Choose a demo marker

Everything the seeder creates must be findable by one query. Accounts use the
`@demo.local` email domain; content usually uses a `demo-` slug prefix or a
`source_id` prefix. Without a marker, `--fresh` cannot delete demo data without
risking real records — and it will be run against a database that has both.

## 2. Write `apps/myapp/seeding.py`

```python
from apps.core.seeding import SeedContext, register_seeder
from apps.core.seeding.context import DEMO_SLUG_PREFIX
from apps.core.seeding.text import paragraph, title

from .models import Article


def demo_articles_qs():
    return Article.objects.filter(slug__startswith=DEMO_SLUG_PREFIX)


def clear_demo_articles() -> int:
    return demo_articles_qs().delete()[0]


@register_seeder("articles", order=40, clear=clear_demo_articles)
def seed_articles(ctx: SeedContext) -> None:
    """Published articles by the demo users."""
    if demo_articles_qs().exists():
        ctx.log("  articles           skipped (already seeded)")
        return

    authors = ctx.require("users")          # provided by the accounts seeder

    articles = [
        Article(
            slug=f"{DEMO_SLUG_PREFIX}article-{index}",
            title=title(ctx),
            body=paragraph(ctx, sentences=6),
            author=ctx.pick(authors),
            published_at=ctx.past(days=120),
        )
        for index in range(ctx.count("articles"))
    ]

    Article.objects.bulk_create(articles, batch_size=500)
    ctx.record("articles", articles)
```

`seeding.py` is discovered automatically — there is nothing to register anywhere
else.

## 3. Pick an `order`

Lower runs first. A seeder that reads another domain's objects out of
`ctx.store` needs a higher number than the one that puts them there. Accounts is
`10`. Leave gaps.

`clear` functions run in **reverse** order, which is what keeps a `PROTECT`
relation from raising during `--fresh`.

## 4. Add counts to the profiles

In `apps/core/seeding/profiles.py`, add your key to `_BASE_COUNTS` at the volume
the `small` profile should have. Other profiles scale it. Put structural
constants (say, "images per article") in `_ABSOLUTE` so they do not scale.

Never hardcode a count in the seeder — `ctx.count("articles")` is what makes the
same code produce 8 rows for a smoke test and 800 for query profiling.

## 5. Rules that keep it fast and deterministic

- **All randomness through `ctx`** (`ctx.pick`, `ctx.sample`, `ctx.chance`,
  `ctx.past`, `ctx.future`). A run with the same `--seed` then produces the same
  data, which is what makes a screenshot comparison meaningful.
- **`bulk_create`, not a loop of `save()`.** Seeding is dominated by round trips.
- **Hash passwords once per run**, not per user — with the default hasher that is
  hundreds of milliseconds each.
- **`auto_now_add` ignores what you pass to `bulk_create`.** Use
  `apps.core.seeding.utils.backdate` to spread timestamps afterwards, or every
  row shares one and the feed looks fake.
- **Share objects through `ctx.put` / `ctx.require`**, never by importing another
  app's `seeding.py`. `ctx.require` fails with a message naming the missing key
  and pointing at `order`.

## 6. Verify

```bash
make demo-reseed PROFILE=tiny     # from scratch
make demo-seed                    # again — must be a no-op
make demo-clear                   # deletes demo rows only
make demo-seeders                 # your seeder is listed
```

CI runs exactly this sequence at the `medium` profile. It fails whenever the
schema moved and something was not updated — a forgotten migration, a renamed
field, a new NOT NULL without a default. It is the cheapest integration test in
the project, and it is free once your seeder is registered.
