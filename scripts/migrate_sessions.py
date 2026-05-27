#!/usr/bin/env python3
"""
One-time migration: moves the legacy session.json to the new sessions/ directory.
Safe to run multiple times (idempotent).

Usage:  conda run -n cf python scripts/migrate_sessions.py
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path


DATA_DIR = Path.home() / ".local" / "share" / "magpie"
OLD_SESSION = DATA_DIR / "session.json"
SESSIONS_DIR = DATA_DIR / "sessions"
NEW_SESSION = SESSIONS_DIR / "alan_reddit.json"


def main() -> None:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Sessions directory: {SESSIONS_DIR}")

    if NEW_SESSION.exists():
        print(f"  alan_reddit.json already exists — nothing to move")
    elif OLD_SESSION.exists():
        shutil.copy2(OLD_SESSION, NEW_SESSION)
        print(f"  Copied {OLD_SESSION} → {NEW_SESSION}")
        # Leave the original in place during rollout; remove manually once confirmed
        print(f"  NOTE: {OLD_SESSION} left in place. Remove manually after confirming.")
    else:
        print(f"  No session.json found at {OLD_SESSION} — may need to run ./manage.sh login")

    print("\nPlaceholder files created for future accounts (empty — fill in when ready):")
    placeholders = [
        "xander_reddit.json",
        "neon_reddit.json",
        "cf_reddit.json",
        "cf_bluesky.json",
        "cf_mastodon.json",
    ]
    for name in placeholders:
        path = SESSIONS_DIR / name
        if not path.exists():
            path.touch()
            print(f"  Created {path}")
        else:
            print(f"  {name} already exists — skipping")


if __name__ == "__main__":
    main()
