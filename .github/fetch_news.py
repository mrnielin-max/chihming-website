#!/usr/bin/env python3
"""Fetch latest plastics industry news from Google News RSS -> news.json (top 8)."""
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

FEEDS = [
    "https://news.google.com/rss/search?q=plastics+polymer+market+OR+polyethylene+OR+polypropylene&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=masterbatch+OR+CaCO3+filler+OR+plastic+resin+price&hl=en-US&gl=US&ceid=US:en",
]

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read()

items, seen = [], set()
for feed in FEEDS:
    try:
        root = ET.fromstring(fetch(feed))
    except Exception as e:
        print("feed error:", feed[:60], e)
        continue
    for it in root.findall(".//item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        pub = (it.findtext("pubDate") or "").strip()
        key = title.lower()[:60]
        if not title or not link or key in seen:
            continue
        seen.add(key)
        try:
            dt = parsedate_to_datetime(pub)
            ts = dt.astimezone(timezone.utc).isoformat()
        except Exception:
            ts = ""
        items.append({"title": title, "link": link, "pubDate": ts})

items.sort(key=lambda x: x["pubDate"], reverse=True)
out = {"updated": datetime.now(timezone.utc).isoformat(), "items": items[:8]}
with open("news.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("wrote", len(out["items"]), "items")
