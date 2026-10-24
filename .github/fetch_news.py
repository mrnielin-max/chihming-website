#!/usr/bin/env python3
"""Fetch latest plastics industry news per language (vi/zh/en) from Google News RSS
   -> news.json. Images: decode Google News link -> article og:image -> download,
   center-crop 16:9, save into repo news-img/ (self-hosted, avoids hotlink/403 blocks).
   Prefers items WITH images: scans up to 20 candidates until 6 imaged items."""
import io
import json
import os
import re
import ssl
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from PIL import Image

try:
    from googlenewsdecoder import gnewsdecoder
    HAS_DECODER = True
except Exception:
    HAS_DECODER = False

IMG_DIR = "news-img"
WANT_PER_LANG = 6          # final items per language
CANDIDATES_PER_LANG = 20   # parse up to N candidates, resolve until WANT imaged
IMG_W, IMG_H, IMG_Q = 480, 270, 70  # 16:9 card thumb

# 精準關鍵字：避免「nhựa」單獨匹配到名人八卦（大亨綽號 Minh "Nhựa"）
# 中文 feed 必須用中文關鍵字（實測英文關鍵字在 zh feed 回傳 0 筆）
Q_EN = "plastics+polymer+market+OR+masterbatch+OR+polyethylene+OR+polypropylene+OR+CaCO3+filler"
Q_ZH = urllib.parse.quote("塑料 市场 OR 母粒 OR 聚乙烯 OR 聚丙烯 OR 石化 OR 塑化")
Q_VI = urllib.parse.quote('"ngành nhựa" OR "hạt nhựa" OR "nhựa tái chế" OR polymer OR polyethylene OR polypropylene OR "giá nhựa"')

FEEDS = {
    "vi": f"https://news.google.com/rss/search?q={Q_VI}&hl=vi&gl=VN&ceid=VN:vi",
    "zh": f"https://news.google.com/rss/search?q={Q_ZH}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "en": f"https://news.google.com/rss/search?q={Q_EN}&hl=en-US&gl=US&ceid=US:en",
}

# 八卦/娛樂標題黑名單（越南 feed 常見污染）
JUNK_WORDS = [
    "ái nữ", "bikini", "khoe bụng", "khoe dáng", "khoe thân", "showbiz", "hoa hậu",
    "người đẹp", "đám cưới", "mang thai", "bụng bầu", "diễn viên", "ca sĩ",
    "người mẫu", "hot girl", "hotgirl", "scandal", "sao việt", "đồ bơi",
    "女星", "網紅", "泳裝", "寫真", "藝人", "八卦", "孕肚",
]

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
CTX = ssl.create_default_context()


def fetch(url, timeout=45, max_bytes=None):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.read(max_bytes) if max_bytes else r.read()


def is_junk(title):
    t = title.lower()
    return any(w.lower() in t for w in JUNK_WORDS)


def norm_key(title):
    """Strip trailing ' - Source' and lowercase, for dedupe across sources."""
    m = re.match(r"^(.*?)\s+-\s+([^-]+)$", title)
    return (m.group(1) if m else title).strip().lower()[:60]


def get_og_image(article_url):
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
                if not u.startswith("http"):
                    u = urllib.parse.urljoin(article_url, u)
                if u.startswith("http"):
                    return u
    except Exception as e:
        print("   og fail:", article_url[:60], e)
    return ""


def save_thumb(img_url, dest_name):
    """Download og image, center-crop 16:9, resize, JPEG -> news-img/dest_name.
    Returns relative path on success, '' on any failure."""
    try:
        raw = fetch(img_url, timeout=12, max_bytes=3_000_000)
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        w, h = im.size
        if w < 200 or h < 100:
            return ""
        target = IMG_W / IMG_H
        if w / h > target:                       # too wide -> crop sides
            nw = int(h * target)
            im = im.crop(((w - nw) // 2, 0, (w + nw) // 2, h))
        elif w / h < target:                     # too tall -> crop top/bottom
            nh = int(w / target)
            im = im.crop((0, (h - nh) // 2, w, (h + nh) // 2))
        im = im.resize((IMG_W, IMG_H), Image.LANCZOS)
        os.makedirs(IMG_DIR, exist_ok=True)
        path = os.path.join(IMG_DIR, dest_name)
        im.save(path, "JPEG", quality=IMG_Q, optimize=True)
        return path
    except Exception as e:
        print("   img dl fail:", img_url[:60], e)
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
        if not title or not link or is_junk(title):
            continue
        key = norm_key(title)
        if key in seen:
            continue
        seen.add(key)
        try:
            ts = parsedate_to_datetime(pub).astimezone(timezone.utc).isoformat()
        except Exception:
            ts = ""
        items.append({"title": title, "link": link, "pubDate": ts})
    items.sort(key=lambda x: x["pubDate"], reverse=True)
    return items[:CANDIDATES_PER_LANG]


out = {"updated": datetime.now(timezone.utc).isoformat(), "items": {}}
referenced = set()

for lang, url in FEEDS.items():
    cands = parse_lang(url)
    print(f"{lang}: {len(cands)} candidates")
    with_img, without_img = [], []
    for i, it in enumerate(cands):
        if len(with_img) >= WANT_PER_LANG:
            break
        img = ""
        if HAS_DECODER:
            try:
                r = gnewsdecoder(it["link"], interval=2, timeout=8.0)
                if r.get("success") and r.get("decoded_url"):
                    og = get_og_image(r["decoded_url"])
                    if og:
                        img = save_thumb(og, f"{lang}{i}.jpg")
            except Exception as e:
                print("   decode fail:", e)
        if img:
            it["img"] = img
            referenced.add(img)
            with_img.append(it)
            print(f"  [{len(with_img)}] IMG | {it['title'][:55]}")
        else:
            it["img"] = ""
            without_img.append(it)
            print(f"  [ ] no-img | {it['title'][:55]}")
        time.sleep(0.2)
    final = with_img[:WANT_PER_LANG]
    if len(final) < WANT_PER_LANG:
        final += without_img[: WANT_PER_LANG - len(final)]
    out["items"][lang] = final
    print(f"{lang}: final {len(final)} items, {len(with_img)} with images")

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

# 清掉不再被引用的舊圖
if os.path.isdir(IMG_DIR):
    for fn in os.listdir(IMG_DIR):
        p = os.path.join(IMG_DIR, fn)
        if p not in referenced:
            os.remove(p)

print("done")
