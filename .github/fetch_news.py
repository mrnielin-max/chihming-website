#!/usr/bin/env python3
"""Fetch latest plastics industry news per language (vi/zh/en) from Google News RSS
   -> news.json, each item with an og:image thumbnail (via googlenewsdecoder + page scrape)."""
import json
import re
import ssl
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

try:
    from googlenewsdecoder import gnewsdecoder
    HAS_DECODER = True
except Exception:
    HAS_DECODER = False

Q_EN = "plastics+polymer+market+OR+masterbatch+OR+polyethylene+OR+polypropylene+OR+CaCO3+filler"
# 中文 feed 必須用中文關鍵字（實測英文關鍵字在 zh feed 回傳 0 筆）
Q_ZH = urllib.parse.quote("塑料 市场 OR 母粒 OR 聚乙烯 OR 聚丙烯 OR 石化")
Q_VI = urllib.parse.quote("nhựa OR polymer OR polyethylene OR polypropylene OR hạt nhựa")

FEEDS = {
    "vi": f"https://news.google.com/rss/search?q={Q_VI}&hl=vi&gl=VN&ceid=VN:vi",
    "zh": f"https://news.google.com/rss/search?q={Q_ZH}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "en": f"https://news.google.com/rss/search?q={Q_EN}&hl=en-US&gl=US&ceid=US:en",
}

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
CTX = ssl.create_default_context()


def fetch(url, timeout=45, max_bytes=None):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.read(max_bytes) if max_bytes else r.read()


def get_og_image(article_url):
    """Read og:image / twitter:image / image_src from an article page."""
    try:
        html = fetch(article_url, timeout=10, max_bytes=250000).decode("utf-8", "ignore")
        for pat in (
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image',
            r'<meta[^>]+(?:name|property)=["\']twitter:image["\'][^>]+content=["\']([^"\']+)',
            r'<link[^>]+rel=["\']image_src["\'][^>]+href=["\']([^"\']+)',
        ):
            m = re.search(pat, html, re.I)
            if m:
                u = m.group(1).strip().replace("&amp;", "&")
                if u.startswith("//"):
                    u = "https:" + u
                if u.startswith("http"):
                    return u
    except Exception as e:
        print("   og:image fail:", article_url[:60], e)
    return ""


def resolve_image(glink):
    """Google News redirect -> real article URL -> og:image. Never raises."""
    if not HAS_DECODER:
        return ""
    try:
        r = gnewsdecoder(glink, interval=2, timeout=8.0)
        if r.get("success") and r.get("decoded_url"):
            return get_og_image(r["decoded_url"])
    except Exception as e:
        print("   decode fail:", e)
    return ""


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
    items = parse_lang(url)
    print(f"{lang}: {len(items)} items, fetching images...")
    for i, it in enumerate(items):
        img = resolve_image(it["link"])
        it["img"] = img
        print(f"  [{i+1}] {'IMG' if img else 'no-img'} | {it['title'][:55]}")
        time.sleep(0.3)
    out["items"][lang] = items

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("done")
