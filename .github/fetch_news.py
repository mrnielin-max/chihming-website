#!/usr/bin/env python3
"""Fetch latest plastics industry news per language (vi/zh/en) from Google News RSS -> news.json."""
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import urllib.parse

Q_EN = "plastics+polymer+market+OR+masterbatch+OR+polyethylene+OR+polypropylene+OR+CaCO3+filler"
# 中文 feed 必須用中文關鍵字（實測英文關鍵字在 zh feed 回傳 0 筆）
Q_ZH = urllib.parse.quote("塑料 市场 OR 母粒 OR 聚乙烯 OR 聚丙烯 OR 石化")
Q_VI = urllib.parse.quote("nhựa OR polymer OR polyethylene OR polypropylene OR hạt nhựa")

FEEDS = {
    "vi": f"https://news.google.com/rss/search?q={Q_VI}&hl=vi&gl=VN&ceid=VN:vi",
    "zh": f"https://news.google.com/rss/search?q={Q_ZH}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "en": f"https://news.google.com/rss/search?q={Q_EN}&hl=en-US&gl=US&ceid=US:en",
}

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read()

def parse_lang(url):
    items, seen = [], set()
    try:
        root = ET.fromstring(fetch(url))
    except Exception as e:
        print("feed error:", url[:70], e)
        return items
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
    return items[:6]

out = {"updated": datetime.now(timezone.utc).isoformat(), "items": {}}
for lang, url in FEEDS.items():
    out["items"][lang] = parse_lang(url)
    print(lang, len(out["items"][lang]), "items")

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("done")
