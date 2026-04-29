#!/usr/bin/env python3
"""Ping IndexNow with all URLs from sitemap.xml.

Usage (env vars required):
  SITE_URL=https://example.com
  INDEXNOW_KEY=your-key-value

Reads SITE_URL/sitemap.xml (or sitemap-index.xml), extracts all URLs,
and POSTs them to https://api.indexnow.org/indexnow in batches of 10k.
"""
import os
import sys
import json
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET

SITE_URL = os.environ.get("SITE_URL", "").rstrip("/")
KEY = os.environ.get("INDEXNOW_KEY", "")

if not SITE_URL or not KEY:
    print("ERROR: SITE_URL and INDEXNOW_KEY env vars required", file=sys.stderr)
    sys.exit(1)


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "IndexNowPinger/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def parse_sitemap(xml_bytes: bytes):
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    root = ET.fromstring(xml_bytes)
    tag = root.tag.lower()
    urls = []
    if tag.endswith("sitemapindex"):
        for sm in root.findall("sm:sitemap", ns):
            loc = sm.find("sm:loc", ns)
            if loc is not None and loc.text:
                urls.extend(parse_sitemap(fetch(loc.text.strip())))
    else:
        for u in root.findall("sm:url", ns):
            loc = u.find("sm:loc", ns)
            if loc is not None and loc.text:
                urls.append(loc.text.strip())
    return urls


def ping(url_list):
    payload = {
        "host": SITE_URL.replace("https://", "").replace("http://", "").rstrip("/"),
        "key": KEY,
        "keyLocation": f"{SITE_URL}/{KEY}.txt",
        "urlList": url_list,
    }
    req = urllib.request.Request(
        "https://api.indexnow.org/indexnow",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "IndexNowPinger/1.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def main():
    candidates = [
        f"{SITE_URL}/sitemap-index.xml",
        f"{SITE_URL}/sitemap.xml",
    ]
    urls = []
    for s in candidates:
        try:
            urls = parse_sitemap(fetch(s))
            print(f"Parsed {len(urls)} URLs from {s}")
            break
        except Exception as e:
            print(f"  Skip {s}: {e}")
    if not urls:
        print("ERROR: no sitemap found", file=sys.stderr)
        sys.exit(1)
    # Batch by 10000 (IndexNow limit)
    BATCH = 10000
    for i in range(0, len(urls), BATCH):
        chunk = urls[i : i + BATCH]
        status = ping(chunk)
        print(f"IndexNow batch {i}-{i + len(chunk)}: HTTP {status}")
    # Also ping sitemap to Google + Bing
    for name, url in [
        ("Google", f"https://www.google.com/ping?sitemap={SITE_URL}/sitemap-index.xml"),
        ("Bing", f"https://www.bing.com/ping?sitemap={SITE_URL}/sitemap-index.xml"),
    ]:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "IndexNowPinger/1.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                print(f"Sitemap ping {name}: HTTP {r.status}")
        except Exception as e:
            print(f"Sitemap ping {name} failed: {e}")


if __name__ == "__main__":
    main()
