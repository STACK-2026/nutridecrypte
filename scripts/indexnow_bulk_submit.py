"""
indexnow_bulk_submit.py , notify IndexNow (Bing + Yandex) of all URLs in sitemap.

Run once right after a batch deploy to trigger immediate crawling on Bing and Yandex.
Bing Webmaster also relays these submissions to other IndexNow partners.

Usage:
    export BING_URL_SUBMISSION_KEY=<your-key>
    python3 indexnow_bulk_submit.py --sitemap https://nutridecrypte.com/sitemap-index.xml
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET

KEY = os.environ.get("BING_URL_SUBMISSION_KEY") or os.environ.get("INDEXNOW_KEY") or ""
HOST = "nutridecrypte.com"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"


def fetch_xml(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "nutridecrypte-indexnow/0.1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def extract_urls(xml_bytes: bytes) -> list[str]:
    root = ET.fromstring(xml_bytes)
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    urls: list[str] = []

    # sitemap index?
    for sm in root.findall(f"{ns}sitemap"):
        loc = sm.findtext(f"{ns}loc")
        if loc:
            urls.extend(extract_urls(fetch_xml(loc)))

    # direct urlset?
    for u in root.findall(f"{ns}url"):
        loc = u.findtext(f"{ns}loc")
        if loc:
            urls.append(loc)

    return urls


def submit_batch(urls: list[str]) -> None:
    if not KEY:
        print("FATAL: BING_URL_SUBMISSION_KEY missing", file=sys.stderr)
        sys.exit(1)

    # IndexNow accepts up to 10000 URLs per request
    for i in range(0, len(urls), 9000):
        batch = urls[i:i+9000]
        payload = {
            "host": HOST,
            "key": KEY,
            "keyLocation": KEY_LOCATION,
            "urlList": batch,
        }
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            "https://api.indexnow.org/indexnow",
            data=data,
            method="POST",
            headers={"Content-Type": "application/json", "User-Agent": "nutridecrypte-indexnow/0.1"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                print(f"  batch {i}-{i+len(batch)} submitted ({resp.status})")
        except urllib.error.HTTPError as e:
            print(f"  batch {i} failed: {e.code} {e.read().decode()[:200]}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sitemap", default="https://nutridecrypte.com/sitemap-index.xml")
    args = parser.parse_args()

    print(f"Fetching {args.sitemap} ...")
    xml_bytes = fetch_xml(args.sitemap)
    urls = extract_urls(xml_bytes)
    print(f"Found {len(urls)} URLs")
    if not urls:
        print("No URLs to submit")
        return 0

    submit_batch(urls)
    print("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
