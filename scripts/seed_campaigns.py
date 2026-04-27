#!/usr/bin/env python3
"""
Seed Magpie DB with campaigns migrated from the legacy claude-bridge/reddit-poster scripts.

Idempotent: checks by name before inserting, so safe to re-run.

Usage:
    conda run -n cf python scripts/seed_campaigns.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings
from app.db.store import Store


# ---------------------------------------------------------------------------
# Campaign data — migrated from claude-bridge/reddit-poster/campaigns/
# ---------------------------------------------------------------------------

CAMPAIGNS = [
    {
        "campaign": {
            "name": "ND/AuDHD — CircuitForge intro",
            "product": "circuitforge",
            "platform": "reddit",
            "cron_schedule": "0 16 * * 1",  # Monday 16:00 UTC
            "notes": "Executive-function framing. Covers Peregrine + Kiwi. r/ADHD and r/autism hard-banned; AuDHD OK.",
        },
        "subs": ["AuDHD"],
        "variants": [
            {
                "sub_pattern": "*",
                "title": "I built two tools specifically for the 'I know I need to do this but I cannot make myself start' problem",
                "body": """\
I'm AuDHD and I kept running into the same wall: tasks that are not hard, they are just opaque and unstructured enough that my brain refuses to start them.

Job applications are the worst example. There is no clear next step, every posting is different, the feedback loop is invisible, and the rejection is silent. I would spend three hours staring at a job listing and close the tab.

I built **[Peregrine](https://demo.circuitforge.tech/peregrine)** to handle the mechanical parts. It finds listings, scores them against your resume, rewrites your resume bullets to pass ATS filters for that specific posting, and drafts a cover letter. You review everything before it goes anywhere. You still make the decisions, it just removes the blank-page paralysis.

The same problem shows up in the kitchen. I have ingredients, I know I should cook something, and I open the fridge and close it twelve times. **[Kiwi](https://menagerie.circuitforge.tech/kiwi)** is a pantry tracker that suggests recipes from what you actually have, tracks shelf life so you do not have to remember, and includes a meal planner with prep day scheduling. No guilt-trip UX, no "you should be eating better" energy, just a calm list of options.

Both are self-hostable via Docker. Both are free tier first. Neither sends your data anywhere without explicit opt-in.

Peregrine: [Demo](https://demo.circuitforge.tech/peregrine) | [Repo](https://git.opensourcesolarpunk.com/Circuit-Forge/peregrine)

Kiwi: [Demo](https://menagerie.circuitforge.tech/kiwi) | [Repo](https://git.opensourcesolarpunk.com/Circuit-Forge/kiwi)

Happy to answer questions about either. I know these communities get a lot of "I built an app!" posts so I will keep it brief and let the tools speak for themselves.""",
                "flair": None,
                "notes": "Works for r/AuDHD. r/ADHD rejected this framing (Rule 8). Do not reuse on r/ADHD.",
            },
        ],
    },
    {
        "campaign": {
            "name": "Mission — Solarpunk / Opensource",
            "product": "circuitforge",
            "platform": "reddit",
            "cron_schedule": "0 16 * * 1",  # Monday 16:00 UTC (same window, different subs)
            "notes": "Privacy-first, anti-VC, open-core framing. Both subs need flair.",
        },
        "subs": ["solarpunk", "opensource"],
        "variants": [
            {
                "sub_pattern": "solarpunk",
                "title": "CircuitForge: open source pipelines for the tasks systems made hard on purpose",
                "body": """\
I have been building tools under the CircuitForge name for the past year and wanted to introduce what we are doing here.

The premise: there is a category of task that is not actually hard, but that systems have made deliberately opaque, time-consuming, and exhausting. Job applications designed to filter by endurance. Government forms written to confuse. Auction platforms that reward automation over buyers. Pantry management that requires a subscription to your own grocery data.

These systems disproportionately harm people who are already under-resourced: neurodivergent folks, people without lawyers, people who do not have three hours to spend on a benefits form.

CircuitForge builds deterministic automation pipelines for those tasks. An LLM might draft a cover letter or flag a sketchy listing. The pipeline handles the structured work. You review and approve everything. Nothing acts without you in the loop.

**Privacy first, self-hostable, open core.**

No VC money. No growth KPIs. No plan to sell user data. The free tier is real.

Open-core licensing: the shared infrastructure library and all discovery/scraping pipelines are MIT. The AI assist layers (cover letter generation, recipe engine) and the VRAM orchestration coordinator are BSL 1.1 — free for personal non-commercial self-hosting, commercial SaaS re-hosting requires a license, converts to MIT after four years. Everything is on Forgejo.

**What is live now:**

- **Peregrine** — job search pipeline, ATS resume rewriting, cover letter drafting ([demo](https://demo.circuitforge.tech/peregrine))
- **Kiwi** — pantry tracker, meal planning, leftover recipe suggestions ([demo](https://menagerie.circuitforge.tech/kiwi))
- **Snipe** — eBay listing trust scoring before you bid ([demo](https://menagerie.circuitforge.tech/snipe))

More in the pipeline for government forms, insurance disputes, and accommodation requests.

[circuitforge.tech](https://circuitforge.tech) | [Forgejo org](https://git.opensourcesolarpunk.com/Circuit-Forge)""",
                "flair": "Action / DIY / Activism",
                "notes": "r/solarpunk flair required. Coordinate-click the flair Add button (shadow DOM).",
            },
            {
                "sub_pattern": "opensource",
                "title": "CircuitForge: open source pipelines for the tasks systems made hard on purpose",
                "body": """\
I have been building tools under the CircuitForge name for the past year and wanted to introduce what we are doing here.

The premise: there is a category of task that is not actually hard, but that systems have made deliberately opaque, time-consuming, and exhausting. Job applications designed to filter by endurance. Government forms written to confuse. Auction platforms that reward automation over buyers. Pantry management that requires a subscription to your own grocery data.

These systems disproportionately harm people who are already under-resourced: neurodivergent folks, people without lawyers, people who do not have three hours to spend on a benefits form.

CircuitForge builds deterministic automation pipelines for those tasks. An LLM might draft a cover letter or flag a sketchy listing. The pipeline handles the structured work. You review and approve everything. Nothing acts without you in the loop.

**Privacy first, self-hostable, open core.**

No VC money. No growth KPIs. No plan to sell user data. The free tier is real.

Open-core licensing: the shared infrastructure library and all discovery/scraping pipelines are MIT. The AI assist layers (cover letter generation, recipe engine) and the VRAM orchestration coordinator are BSL 1.1 — free for personal non-commercial self-hosting, commercial SaaS re-hosting requires a license, converts to MIT after four years. Everything is on Forgejo.

**What is live now:**

- **Peregrine** — job search pipeline, ATS resume rewriting, cover letter drafting ([demo](https://demo.circuitforge.tech/peregrine))
- **Kiwi** — pantry tracker, meal planning, leftover recipe suggestions ([demo](https://menagerie.circuitforge.tech/kiwi))
- **Snipe** — eBay listing trust scoring before you bid ([demo](https://menagerie.circuitforge.tech/snipe))

More in the pipeline for government forms, insurance disputes, and accommodation requests.

[circuitforge.tech](https://circuitforge.tech) | [Forgejo org](https://git.opensourcesolarpunk.com/Circuit-Forge)""",
                "flair": "Promotional",
                "notes": "r/opensource shows rule-warning dialog after Post click. Use wait_for(visible) + submit without editing.",
            },
        ],
    },
    {
        "campaign": {
            "name": "Privacy Stack — privacytoolsIO",
            "product": "circuitforge",
            "platform": "reddit",
            "cron_schedule": "0 16 * * 3",  # Wednesday 16:00 UTC
            "notes": "Data-ownership framing. Resume data, pantry data, eBay behaviour — all local.",
        },
        "subs": ["privacytoolsIO"],
        "variants": [
            {
                "sub_pattern": "*",
                "title": "Self-hosted tools for the tasks that leak the most data: job search, pantry tracking, eBay buying",
                "body": """\
Job applications go to LinkedIn, Indeed, and a dozen ATS platforms. Every one of them builds a profile on you. Your resume, your salary expectations, your rejection rate.

Grocery and pantry apps want to know what you eat, how often, and what you run out of. That is valuable data. They charge you a subscription for the privilege of giving it to them.

eBay and similar platforms know every item you searched, every bid you considered, every seller you trusted.

I built three tools that handle these tasks locally, with no account required for self-hosting:

**Peregrine** | job search pipeline. Your resume, application history, cover letters, and career profile in one place you control, not scattered across LinkedIn, Indeed, Greenhouse, and every other ATS you have applied through. Runs on Ollama for fully local inference.

**Kiwi** | pantry tracker and meal planner. Barcode and receipt scanning, shelf life tracking, recipe suggestions from what you have. No subscription, no cloud sync, no food behaviour profile.

**Snipe** | eBay trust scorer. Scores listings for red flags before you bid. Runs fully local. Has an MCP server if you want to wire it into an AI assistant.

All three run via Docker. All three are free tier first. Local LLM or BYOK (bring your own API key).

[circuitforge.tech](https://circuitforge.tech) | [Forgejo org](https://git.opensourcesolarpunk.com/Circuit-Forge)""",
                "flair": None,
                "notes": "r/privacytoolsIO allows self-promotion with context. No flair required.",
            },
        ],
    },
    {
        "campaign": {
            "name": "Linux/Self-hosted Stack — linuxmasterrace",
            "product": "circuitforge",
            "platform": "reddit",
            "cron_schedule": "0 16 * * 4",  # Thursday 16:00 UTC
            "notes": "Docker + Ollama + open-core framing. Technical audience — include stack details.",
        },
        "subs": ["linuxmasterrace"],
        "variants": [
            {
                "sub_pattern": "*",
                "title": "Three self-hosted Docker tools for job searching, pantry tracking, and eBay trust scoring — all run on Ollama",
                "body": """\
I've been building a suite of tools that run locally via Docker and use Ollama for inference. No cloud required, no subscription, no data leaving your machine unless you choose it.

**Peregrine** | job search pipeline. Discovers listings, scores them against your resume, rewrites resume bullets for ATS filters, drafts cover letters. Your resume and application history stay in a local SQLite DB. Ollama-first, BYOK fallback.

**Kiwi** | pantry tracker and meal planner. Barcode and receipt scanning, shelf life tracking, recipe suggestions from what you actually have. Meal planner with prep day scheduling. Local by default, no food behaviour profile being built on you.

**Snipe** | eBay trust scorer. Scores listings for red flags before you bid. Fully local. Has an MCP server for wiring into AI assistants or automation pipelines.

Stack: FastAPI + Vue 3 + SQLite + Docker Compose. Ollama for local LLM. Playwright for scraping where APIs don't exist.

All three are open core: discovery and pipeline layers are MIT, AI assist features are BSL 1.1 (free for personal self-hosting).

[circuitforge.tech](https://circuitforge.tech) | [Forgejo](https://git.opensourcesolarpunk.com/Circuit-Forge)

Happy to answer questions about the stack or self-hosting setup.""",
                "flair": None,
                "notes": "r/linuxmasterrace allows self-promotion. No flair. Technical framing expected.",
            },
        ],
    },
    {
        "campaign": {
            "name": "Weekly Sprint Review — selfhosted",
            "product": "circuitforge",
            "platform": "reddit",
            "cron_schedule": None,  # Manual — content changes every week
            "notes": "Regenerated weekly. Use the sprint_review skill to draft content. Post manually or via trigger.",
        },
        "subs": ["selfhosted"],
        "variants": [],  # No static variant — content is generated fresh each sprint
    },
    {
        "campaign": {
            "name": "Peregrine Launch — Apr 21 2026 (one-shot)",
            "product": "peregrine",
            "platform": "reddit",
            "cron_schedule": None,  # One-shot, already fired
            "notes": "Archived one-shot campaign. selfhosted + audhd variants fired. adhd variant killed (Rule 8).",
        },
        "subs": ["selfhosted", "AuDHD"],
        "variants": [
            {
                "sub_pattern": "selfhosted",
                "title": "What shipped this week across my self-hosted AI stack: job search, pantry tracking, eBay sniping, and shared local inference infra",
                "body": """\
Weekly update on CircuitForge — a collection of self-hosted tools for tasks the system made hard on purpose. Everything runs locally by default, local LLM or BYOK (bring your own key).

---

**Peregrine (job search)**
- Resume library to profile sync: pick a resume, review a before/after diff, push to active profile
- References tracker with recommendation letter draft generation
- CI added via GitHub Actions

**Kiwi (pantry + recipes)**
- Secondary-use hints: the recipe engine now suggests dishes for near-expired ingredients.
- Hierarchical subcategory navigation
- "Can make now" pantry match toggle, complexity badges, Surprise Me picker
- Barcode miss fallback: tries Open Beauty Facts and Open Products Facts
- Meal planner slot editor, meal type picker, current-week auto-select

**Snipe (eBay trust scoring)**
- Search with AI: describe what you want, Snipe builds the eBay query using a local LLM
- Community blocklist opt-in for reported sellers
- Listing detail page: trust score ring, signal breakdown, seller history panel

**circuitforge-core (MIT)**
- Community signal module shipped

**Website**
- Self-hosted Plausible analytics
- PayPal added alongside Stripe

All repos: https://git.opensourcesolarpunk.com/Circuit-Forge
Live demos: https://menagerie.circuitforge.tech

What does your self-hosted productivity stack look like? Always curious what people are running.""",
                "flair": None,
                "notes": "Filed 2026-04-21. Sprint review format — regenerate each week.",
            },
            {
                "sub_pattern": "AuDHD",
                "title": "Job searching with AuDHD is a particular kind of nightmare. Built something for it.",
                "body": """\
The specific AuDHD job search loop, as I understand it from building this and watching people I care about go through it:

You need structure to function. But the ADHD part means the structure you build collapses the moment life gets noisy. So you're perpetually rebuilding from scratch. The job search version of this is brutal because the stakes are real, the timeline feels urgent, and every interaction costs masking energy you may not have to spare.

Meanwhile you're trying to track 30 applications, write responses that sound "appropriately enthusiastic but professional," remember what you told each recruiter two weeks ago, and somehow prepare for an interview with 48 hours notice — while also holding down your current job or managing everything else.

I built Peregrine as a pipeline that holds the structure so you don't have to maintain it yourself. You review and approve rather than building from zero every day.

**What it does:**
- Scrapes job boards automatically — everything in one place, no tab archaeology
- Scores listings against your resume so the list is already filtered
- Writes cover letters as a starting draft. One edit instead of starting from a blank page.
- Tracks every application: applied > phone screen > interview > offer > hired.
- Recruiter emails attach to the right job automatically
- When you move to phone screen, a company research brief generates automatically.
- References tracker: log your references and generate draft request emails when needed
- Recommendation letter drafts built in

Everything runs locally via Docker. Your resume and application data stay on your machine. Free tier with a local AI model or bring your own API key.

Demo: https://menagerie.circuitforge.tech/peregrine

What part of the process drains you most? I'm building specifically for this community and want to know where to focus.""",
                "flair": None,
                "notes": "Soft-launch post Apr 23 2026. Follow up with engagement if thread is active.",
            },
        ],
    },
]

# ---------------------------------------------------------------------------
# Sub rules — verified manually
# ---------------------------------------------------------------------------

SUB_RULES = [
    {"sub": "selfhosted",      "promo_allowed": True,  "flair_required": False, "rule_warning": False, "notes": "Promo OK with context. Engages well with self-hosted + local inference framing."},
    {"sub": "solarpunk",       "promo_allowed": True,  "flair_required": True,  "flair_to_use": "Action / DIY / Activism", "rule_warning": False, "notes": "Flair required. Use coordinate-click for Add button (shadow DOM)."},
    {"sub": "opensource",      "promo_allowed": True,  "flair_required": True,  "flair_to_use": "Promotional", "rule_warning": True,  "notes": "Rule-warning dialog appears after Post click. wait_for(visible) + Submit without editing."},
    {"sub": "AuDHD",           "promo_allowed": True,  "flair_required": False, "rule_warning": False, "notes": "No hard promo ban. Personally-relevant content qualifies."},
    {"sub": "privacytoolsIO",  "promo_allowed": True,  "flair_required": False, "rule_warning": False, "notes": "Self-promo OK with privacy context. No flair needed."},
    {"sub": "linuxmasterrace", "promo_allowed": True,  "flair_required": False, "rule_warning": False, "notes": "Technical framing expected. Docker/Ollama angle works well."},
    {"sub": "ADHD",            "promo_allowed": False, "flair_required": False, "rule_warning": False, "notes": "HARD BAN. Rule 8 explicitly prohibits 'I made this' posts. Do not post here."},
    {"sub": "autism",          "promo_allowed": False, "flair_required": False, "rule_warning": False, "notes": "HARD BAN. Rule 9 bans promotion/self-promotion. Do not post here."},
    {"sub": "mealprep",        "promo_allowed": False, "flair_required": False, "rule_warning": False, "notes": "HARD BAN. No promotional content allowed."},
    {"sub": "ZeroWaste",       "promo_allowed": False, "flair_required": False, "rule_warning": False, "notes": "HARD BAN. No promotional posts."},
    {"sub": "jobs",            "promo_allowed": False, "flair_required": False, "rule_warning": False, "notes": "HARD BAN. Job postings only, no tools/products."},
    {"sub": "eBay",            "promo_allowed": False, "flair_required": False, "rule_warning": False, "notes": "HARD BAN. No tool promotion."},
    {"sub": "Flipping",        "promo_allowed": False, "flair_required": False, "rule_warning": False, "notes": "Sunday-only community thread for sharing. Direct posts not allowed on other days."},
    {"sub": "cscareerquestions","promo_allowed": False, "flair_required": False, "rule_warning": False, "notes": "First-Sunday-of-month megathread only. Direct posts not allowed."},
]


# ---------------------------------------------------------------------------
# Seeder
# ---------------------------------------------------------------------------

def seed(store: Store) -> None:
    existing_names = {c["name"] for c in store.list_campaigns()}

    for entry in CAMPAIGNS:
        camp_data = entry["campaign"]
        name = camp_data["name"]

        if name in existing_names:
            print(f"  [skip] campaign already exists: {name!r}")
            continue

        camp = store.create_campaign(**camp_data)
        cid = camp["id"]
        print(f"  [+] campaign {cid}: {name!r}")

        for i, sub in enumerate(entry["subs"]):
            store.add_campaign_sub(cid, sub, sort_order=i)
            print(f"       sub: r/{sub}")

        for v in entry["variants"]:
            store.create_variant(campaign_id=cid, **v)
            print(f"       variant: {v['sub_pattern']!r}")

    # --- r/Flipping Sunday self-promo (Snipe) ---
    flipping_campaign = store.get_or_create_campaign(
        name="Snipe | Sunday self-promo — r/Flipping",
        product="snipe",
        platform="reddit",
        type="reddit_comment",
        cron_schedule="0 16 * * 0",  # every Sunday 16:00 UTC
    )
    flipping_status = "skip" if flipping_campaign["name"] in existing_names else "+"
    print(f"  [{flipping_status}] campaign {flipping_campaign['id']}: {flipping_campaign['name']!r}")
    store.upsert_campaign_sub(
        campaign_id=flipping_campaign["id"],
        sub="Flipping",
        sort_order=0,
        thread_title_pattern="Weekly Self-Promotion",
        occurrence="every",
    )
    print("       sub: r/Flipping (thread_title_pattern='Weekly Self-Promotion', occurrence='every')")
    store.upsert_variant(
        campaign_id=flipping_campaign["id"],
        sub_pattern="*",
        title="",
        body=(
            "Working on evaluating auction listings? I built **Snipe** — "
            "a trust-scoring tool for eBay and estate auction platforms. "
            "It checks seller history, flags marketing photos, and scores "
            "listings before you bid.\n\n"
            "Still in beta, free to try: https://circuitforge.tech\n\n"
            "Happy to answer questions about how it works."
        ),
    )
    print("       variant: '*'")

    # --- r/cscareerquestions first-Sunday megathread (Peregrine) ---
    cscq_campaign = store.get_or_create_campaign(
        name="Peregrine | First-Sunday megathread — r/cscareerquestions",
        product="peregrine",
        platform="reddit",
        type="reddit_comment",
        cron_schedule="0 16 * * 0",  # every Sunday 16:00 UTC; occurrence gates to first_sunday
    )
    cscq_status = "skip" if cscq_campaign["name"] in existing_names else "+"
    print(f"  [{cscq_status}] campaign {cscq_campaign['id']}: {cscq_campaign['name']!r}")
    store.upsert_campaign_sub(
        campaign_id=cscq_campaign["id"],
        sub="cscareerquestions",
        sort_order=0,
        thread_title_pattern="Monthly Resume",
        occurrence="first_sunday",
    )
    print("       sub: r/cscareerquestions (thread_title_pattern='Monthly Resume', occurrence='first_sunday')")
    store.upsert_variant(
        campaign_id=cscq_campaign["id"],
        sub_pattern="*",
        title="",
        body=(
            "I'm building **Peregrine** — a local-first job search assistant "
            "for neurodivergent and adaptive-needs folks. It helps with "
            "cover letters, interview prep, and tracking applications without "
            "your data leaving your machine.\n\n"
            "Free tier available: https://circuitforge.tech/peregrine\n\n"
            "Built by someone who's been through the grind — genuinely trying "
            "to make this less awful."
        ),
    )
    print("       variant: '*'")

    print()
    print("Seeding sub rules...")
    for rule in SUB_RULES:
        sub = rule["sub"]
        fields = {k: v for k, v in rule.items() if k != "sub"}
        store.upsert_sub_rules(sub=sub, last_checked="2026-04-21", **fields)
        allowed = "OK" if rule.get("promo_allowed") else "BANNED"
        print(f"  r/{sub}: {allowed}")


def main() -> None:
    settings = get_settings()
    store = Store(settings.db_path)
    store.run_migrations()
    print(f"DB: {settings.db_path}")
    print()
    seed(store)
    store.close()
    print()
    print("Done.")


if __name__ == "__main__":
    main()
