"""Daily Bing URL Submission for petfoodrate.com.

Submits up to the daily quota (currently 100 URLs/day, grows with site age).
Tracks already-submitted URLs in scripts/bing_submitted.json so we cycle
through the sitemap without re-submitting the same pages.

Env required:
  BING_URL_SUBMISSION_KEY  (shared STACK-2026 key)

Usage:
  python3 scripts/bing_submit.py              # submit daily quota
  python3 scripts/bing_submit.py --reset      # clear submission history (forces re-submit)
  python3 scripts/bing_submit.py --dry-run    # show what would be submitted
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

BING_KEY = os.environ.get("BING_URL_SUBMISSION_KEY", "").strip()
SITE_URL = "https://petfoodrate.com"
HEADERS = {
    "Content-Type": "application/json; charset=utf-8",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}

SCRIPT_DIR = Path(__file__).parent
STATE_FILE = SCRIPT_DIR / "bing_submitted.json"

HOT_PATHS = [
    "/", "/fr/",
    "/rankings/", "/fr/rankings/",
    "/methodology/", "/fr/methodology/",
    "/about/", "/fr/about/",
    "/encyclopedia/", "/fr/encyclopedia/",
    "/compare/", "/fr/compare/",
    "/best/", "/fr/best/",
    "/worst/", "/fr/worst/",
    "/brand/", "/fr/brand/",
    "/fr/divulgation-affiliation/",
    "/affiliate-disclosure/",
]


def get_quota():
    req = urllib.request.Request(
        f"https://ssl.bing.com/webmaster/api.svc/json/GetUrlSubmissionQuota?siteUrl={SITE_URL}&apikey={BING_KEY}",
        headers=HEADERS,
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}


def submit_batch(urls):
    body = json.dumps({"siteUrl": SITE_URL, "urlList": urls}).encode("utf-8")
    req = urllib.request.Request(
        f"https://ssl.bing.com/webmaster/api.svc/json/SubmitUrlBatch?apikey={BING_KEY}",
        data=body,
        headers=HEADERS,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")[:300]


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            return {"submitted": []}
    return {"submitted": []}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))


def fetch_sitemap():
    req = urllib.request.Request(f"{SITE_URL}/sitemap-0.xml", headers={"User-Agent": "Mozilla/5.0"})
    xml = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    return re.findall(r"<loc>(https://petfoodrate\.com[^<]+)</loc>", xml)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not BING_KEY:
        print("ERROR: BING_URL_SUBMISSION_KEY env var not set", file=sys.stderr)
        sys.exit(1)

    q = get_quota()
    print(f"Quota: {q}", file=sys.stderr)
    daily = 100
    if isinstance(q, dict) and "d" in q and q["d"]:
        daily = int(q["d"].get("DailyQuota", 100))
    if daily <= 0:
        print("Daily quota already used, skipping.", file=sys.stderr)
        return

    sitemap_urls = fetch_sitemap()
    print(f"Sitemap: {len(sitemap_urls)} URLs", file=sys.stderr)

    state = {"submitted": []} if args.reset else load_state()
    submitted = set(state.get("submitted", []))

    # Priority order: hot paths → FR product/alternatives/brand → other
    hot_urls = [f"{SITE_URL}{p}" for p in HOT_PATHS]
    fr_urls = [u for u in sitemap_urls if "/fr/" in u]
    other_urls = [u for u in sitemap_urls if u not in set(fr_urls) and u not in set(hot_urls)]
    ordered = hot_urls + fr_urls + other_urls

    pending = []
    seen = set()
    for u in ordered:
        if u in seen or u in submitted:
            continue
        seen.add(u)
        pending.append(u)
        if len(pending) >= daily:
            break

    if not pending:
        print("All URLs already submitted. Consider --reset if sitemap changed.", file=sys.stderr)
        return

    print(f"Will submit {len(pending)} URLs (daily quota={daily})", file=sys.stderr)

    if args.dry_run:
        for u in pending[:10]:
            print(f"  DRY  {u}", file=sys.stderr)
        if len(pending) > 10:
            print(f"  ... +{len(pending)-10} more", file=sys.stderr)
        return

    ok = 0
    for i in range(0, len(pending), 50):
        chunk = pending[i:i + 50]
        status, body = submit_batch(chunk)
        if status == 200 and '"d":null' in body:
            ok += len(chunk)
            submitted.update(chunk)
            print(f"  [{i+len(chunk)}/{len(pending)}] OK", file=sys.stderr)
        else:
            print(f"  [{i+len(chunk)}/{len(pending)}] FAIL status={status} {body[:200]}", file=sys.stderr)
            if status in (400, 401, 403):
                break
        time.sleep(1.5)

    state["submitted"] = sorted(submitted)
    save_state(state)
    print(f"Submitted today: {ok} URLs (total in state: {len(submitted)})", file=sys.stderr)


if __name__ == "__main__":
    main()
