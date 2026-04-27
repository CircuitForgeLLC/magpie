#!/usr/bin/env python3
"""
Reddit posting script using Playwright + stealth.

Migrated from claude-bridge/reddit-poster/post.py.
Uses system Google Chrome (non-headless via Xvfb) with anti-detection flags
to avoid Reddit's bot detection. Saves a cookie session after first login.

Usage:
    python -m app.services.reddit.post --login
    python -m app.services.reddit.post --sub selfhosted --title "..." --body "..."
    python -m app.services.reddit.post --sub selfhosted --title "..." --body-file draft.txt
    python -m app.services.reddit.post --delete <post_url>
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from playwright_stealth import Stealth

# Load .env from project root (magpie repo root, 3 levels up from this file)
_HERE = Path(__file__).parent
_PROJECT_ROOT = _HERE.parents[2]  # reddit/ → services/ → app/ → magpie/
load_dotenv(_PROJECT_ROOT / ".env")

REDDIT_USERNAME = os.getenv("REDDIT_USERNAME", "")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD", "")
CHROME_BIN = os.getenv("CHROME_BIN", "/usr/bin/google-chrome")

# Session file path from env (so the service layer can pass it via env var)
SESSION_FILE = Path(os.getenv(
    "REDDIT_SESSION_FILE",
    str(Path.home() / ".local" / "share" / "magpie" / "session.json"),
))

LOGIN_URL = "https://www.reddit.com/login"
SUBMIT_URL = "https://www.reddit.com/r/{sub}/submit?type=text"


def _make_browser(p):
    return p.chromium.launch(
        executable_path=CHROME_BIN,
        headless=False,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--window-size=1280,900",
        ],
    )


def _make_context(browser):
    return browser.new_context(
        user_agent=(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 900},
        locale="en-US",
        storage_state=str(SESSION_FILE) if SESSION_FILE.exists() else None,
    )


def _apply_stealth(page) -> None:
    Stealth().apply_stealth_sync(page)


def _login(page) -> None:
    print("Navigating to Reddit login...")
    page.goto(LOGIN_URL, wait_until="domcontentloaded")
    time.sleep(2)

    selectors_user = [
        "#login-username",
        'input[name="username"]',
        'input[id="loginUsername"]',
        'input[placeholder*="Username"]',
        'input[autocomplete="username"]',
    ]
    selectors_pass = [
        "#login-password",
        'input[name="password"]',
        'input[id="loginPassword"]',
        'input[placeholder*="Password"]',
        'input[autocomplete="current-password"]',
    ]

    def fill_first(selectors, value):
        for sel in selectors:
            try:
                el = page.locator(sel).first
                if el.count() and el.is_visible():
                    el.fill(value)
                    return sel
            except Exception:
                continue
        raise RuntimeError(f"Could not find input. Tried: {selectors}")

    usel = fill_first(selectors_user, REDDIT_USERNAME)
    print(f"  Filled username via {usel}")
    time.sleep(0.3)
    psel = fill_first(selectors_pass, REDDIT_PASSWORD)
    print(f"  Filled password via {psel}")
    time.sleep(0.3)
    page.keyboard.press("Enter")

    try:
        page.wait_for_url(lambda url: "login" not in url, timeout=20_000)
    except PlaywrightTimeout:
        raise RuntimeError("Login did not redirect — check credentials or CAPTCHA.")

    print(f"Logged in as u/{REDDIT_USERNAME}")


def do_login() -> None:
    if not REDDIT_USERNAME or not REDDIT_PASSWORD:
        sys.exit("Set REDDIT_USERNAME and REDDIT_PASSWORD in .env")
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = _make_browser(p)
        ctx = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
            locale="en-US",
        )
        page = ctx.new_page()
        _apply_stealth(page)
        _login(page)
        ctx.storage_state(path=str(SESSION_FILE))
        print(f"Session saved to {SESSION_FILE}")
        browser.close()


def _ensure_logged_in(page) -> None:
    page.goto("https://www.reddit.com", wait_until="domcontentloaded")
    time.sleep(2)
    if REDDIT_USERNAME.lower() not in page.content().lower():
        print("Session expired — re-logging in...")
        _login(page)


def post(sub: str, title: str, body: str, flair: str | None = None, yes: bool = False) -> str:
    """Submit a text post. Returns the posted URL."""
    if not REDDIT_USERNAME or not REDDIT_PASSWORD:
        sys.exit("Set REDDIT_USERNAME and REDDIT_PASSWORD in .env")

    print(f"\n{'='*60}")
    print(f"  Subreddit : r/{sub}")
    print(f"  Title     : {title}")
    print(f"  Body      :\n")
    for line in body.splitlines():
        print(f"    {line}")
    print(f"\n{'='*60}\n")

    if not yes:
        confirm = input("Post this? [y/N] ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return ""

    with sync_playwright() as p:
        browser = _make_browser(p)
        ctx = _make_context(browser)
        page = ctx.new_page()
        _apply_stealth(page)

        _ensure_logged_in(page)

        page.goto(SUBMIT_URL.format(sub=sub), wait_until="domcontentloaded")
        time.sleep(2)

        # Fill title
        try:
            title_el = page.locator('textarea[name="title"]').first
            title_el.wait_for(state="visible", timeout=10_000)
            title_el.fill(title)
        except Exception as exc:
            print(f"  Warning: title fill failed ({exc})")

        time.sleep(0.5)

        # Fill body — Reddit shows either a markdown textarea or a Lexical
        # rich-text contenteditable depending on user/sub settings.
        # Try markdown textarea first (visible in screenshot), fall back to Lexical.
        try:
            md_textarea = page.locator('textarea[placeholder="Body text*"]')
            if md_textarea.count() > 0:
                md_textarea.first.wait_for(state="visible", timeout=5_000)
                md_textarea.first.click()
                time.sleep(0.3)
                md_textarea.first.fill(body)
                print("  Body filled via markdown textarea")
            else:
                body_el = page.locator('div[contenteditable="true"]').first
                body_el.wait_for(state="visible", timeout=10_000)
                body_el.click()
                time.sleep(0.3)
                page.keyboard.type(body, delay=2)
                print("  Body filled via rich text editor")
        except Exception as exc:
            print(f"  Warning: body fill failed ({exc})")

        time.sleep(0.5)

        # Flair selection (faceplate-radio-input custom web component)
        if flair:
            try:
                page.locator('faceplate-radio-input').filter(has_text=flair).click()
                time.sleep(0.5)
                # "Add" button in flair dialog — coordinate-based (1280x900 viewport)
                page.mouse.click(877, 765)
                time.sleep(0.5)
            except Exception as exc:
                print(f"  Warning: flair selection failed ({exc})")

        # Submit — try multiple selector strategies; Reddit's form markup varies
        try:
            # Scroll to bottom so button is in viewport
            page.keyboard.press("End")
            time.sleep(0.3)
            for selector in [
                'button[type="submit"]',
                'button:has-text("Post")',
                '[slot="submit-button"] button',
                'button.bg-interactive-onbackground',
            ]:
                btn = page.locator(selector).last
                if btn.count() > 0:
                    btn.scroll_into_view_if_needed()
                    btn.wait_for(state="visible", timeout=5_000)
                    btn.click()
                    print(f"  Clicked submit via {selector!r}")
                    break
            else:
                print("  Warning: no submit button found with any selector")
        except Exception as exc:
            print(f"  Warning: submit button click failed ({exc})")

        time.sleep(2)

        # Rule-warning dialog — must use wait_for(state=), not is_visible()
        try:
            warning_btn = page.locator('button:has-text("Submit without editing")')
            warning_btn.wait_for(state="visible", timeout=3_000)
            warning_btn.click()
            print("  Acknowledged rule warning — submitted without editing")
            time.sleep(1)
        except PlaywrightTimeout:
            pass

        try:
            page.wait_for_url(lambda url: "/comments/" in url, timeout=20_000)
        except PlaywrightTimeout:
            pass

        final_url = page.url
        if "/submit" in final_url:
            screenshot_path = SESSION_FILE.parent / f"debug_{sub}_{int(time.time())}.png"
            page.screenshot(path=str(screenshot_path))
            raise RuntimeError(
                f"Post may have failed — still on submit URL: {final_url}\n"
                f"Screenshot saved to {screenshot_path}"
            )

        print(f"\nPosted: {final_url}")
        ctx.storage_state(path=str(SESSION_FILE))
        browser.close()
        return final_url


def delete_post(post_url: str) -> None:
    import json
    import re
    import httpx

    state = json.loads(SESSION_FILE.read_text())
    cookies = {c["name"]: c["value"] for c in state.get("cookies", [])}
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/124.0.0.0"}

    match = re.search(r"/comments/([a-z0-9]+)/", post_url)
    if not match:
        print(f"Could not extract post ID from URL: {post_url}")
        return
    post_id = match.group(1)

    me = httpx.get("https://www.reddit.com/api/me.json", cookies=cookies, headers=headers)
    modhash = me.json().get("data", {}).get("modhash", "")
    if not modhash:
        print("Could not get modhash — session may be expired. Run --login first.")
        return

    resp = httpx.post(
        "https://www.reddit.com/api/del",
        cookies=cookies,
        headers={**headers, "X-Modhash": modhash},
        data={"id": f"t3_{post_id}"},
    )
    if resp.status_code == 200:
        print(f"Deleted: {post_url}")
    else:
        print(f"Delete failed ({resp.status_code}): {resp.text[:200]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Post to Reddit via Playwright")
    parser.add_argument("--sub")
    parser.add_argument("--title")
    parser.add_argument("--body")
    parser.add_argument("--body-file")
    parser.add_argument("--flair")
    parser.add_argument("--login", action="store_true")
    parser.add_argument("--delete", metavar="POST_URL")
    parser.add_argument("--yes", "-y", action="store_true")
    args = parser.parse_args()

    if args.login:
        do_login()
        return

    if args.delete:
        delete_post(args.delete)
        return

    if not args.sub or not args.title:
        parser.error("--sub and --title are required")

    body = ""
    if args.body_file:
        body = Path(args.body_file).read_text()
    elif args.body:
        body = args.body
    else:
        print("Enter post body (Ctrl+D when done):")
        body = sys.stdin.read()

    post(args.sub, args.title, body.strip(), flair=args.flair, yes=args.yes)


if __name__ == "__main__":
    main()
