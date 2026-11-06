#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build /zh/ and /en/ static language pages from index.html + I18N dict (EuroPlas-style multilingual URLs)."""
import json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "index.html")
I18N_JSON = "/tmp/i18n.json"

from bs4 import BeautifulSoup

def load_i18n():
    if not os.path.exists(I18N_JSON):
        # extract via node
        subprocess.run(["node", "-e", """
const fs=require('fs');
const html=fs.readFileSync('%s','utf8');
const m=html.match(/const I18N = \\{[\\s\\S]*?\\n\\};/);
eval(m[0].replace('const I18N','globalThis.I18N'));
fs.writeFileSync('%s', JSON.stringify(I18N));
""" % (SRC, I18N_JSON)], check=True)
    return json.load(open(I18N_JSON, encoding="utf-8"))

META = {
    "zh": {
        "lang_attr": "zh-Hant",
        "path": "/zh/",
        "url": "https://chihming.com.vn/zh/",
        "locale": "zh_TW",
        "description": "志明有限公司（CHIH MING，越南稅號 MST 2300324175）– 越南 CaCO₃ 碳酸鈣填充母粒（Filler Masterbatch）直接製造商，工廠位於北寧省桂武工業區（KCN Quế Võ）， compound 複合粒與塑料助劑，全球出口，24 小時內報價。",
        "og_title": "志明有限公司 CHIH MING – 越南 CaCO₃ 填充母粒製造商（北寧）",
        "og_desc": "越南工廠直供 CaCO₃ 填充母粒，位於北寧省桂武工業區。從原料到成品全程品管，全球出口。",
        "tw_title": "CHIH MING 志明有限公司 – CaCO₃ 填充母粒製造商",
        "tw_desc": "越南直營工廠，北寧省桂武工業區。填充母粒、複合粒與塑料助劑，全球出口。",
        "keywords": "志明有限公司, CHIH MING, 填充母粒, 碳酸钙填充母粒, CaCO3 填充母粒, 越南填充母粒制造商, 北宁 塑料厂, filler masterbatch 越南, 塑料添加剂",
    },
    "en": {
        "lang_attr": "en",
        "path": "/en/",
        "url": "https://chihming.com.vn/en/",
        "locale": "en_US",
        "description": "CHIH MING Co., Ltd. (Cong Ty TNHH CHIH MING, Tax ID 2300324175) – direct CaCO₃ filler masterbatch manufacturer in Que Vo Industrial Park, Bac Ninh, Vietnam. Compounds & plastic additives, global export, quotes within 24 hours.",
        "og_title": "CHIH MING Co., Ltd. – CaCO₃ Filler Masterbatch Manufacturer in Bac Ninh, Vietnam",
        "og_desc": "Direct CaCO₃ filler masterbatch factory in Que Vo IP, Bac Ninh. Quality controlled from raw material to finished pellets. Global export.",
        "tw_title": "CHIH MING – CaCO₃ Filler Masterbatch Manufacturer in Vietnam",
        "tw_desc": "Direct factory in Que Vo IP, Bac Ninh, Vietnam. Filler masterbatch, compounds & plastic additives. Global export.",
        "keywords": "CHIH MING, Cong Ty TNHH CHIH MING, filler masterbatch, CaCO3 filler masterbatch, calcium carbonate masterbatch, plastic filler masterbatch manufacturer Vietnam, Bac Ninh plastic factory, plastic additives, compound pellets",
    },
}

HREFLANG = """  <link rel="alternate" hreflang="vi" href="https://chihming.com.vn/">
  <link rel="alternate" hreflang="zh-Hant" href="https://chihming.com.vn/zh/">
  <link rel="alternate" hreflang="en" href="https://chihming.com.vn/en/">
  <link rel="alternate" hreflang="x-default" href="https://chihming.com.vn/">
"""

def set_meta(soup, prop_or_name, key, value):
    tag = soup.find("meta", attrs={prop_or_name: key})
    if tag:
        tag["content"] = value

def bake(lang, i18n):
    dict_ = i18n[lang]
    m = META[lang]
    html = open(SRC, encoding="utf-8").read()
    soup = BeautifulSoup(html, "html.parser")

    # html lang
    soup.find("html")["lang"] = m["lang_attr"]
    # title
    soup.find("title").string = dict_["page_title"]
    # metas
    set_meta(soup, "name", "description", m["description"])
    set_meta(soup, "name", "keywords", m["keywords"])
    set_meta(soup, "property", "og:locale", m["locale"])
    for alt in soup.find_all("meta", attrs={"property": "og:locale:alternate"}):
        alt.decompose()
    set_meta(soup, "property", "og:url", m["url"])
    set_meta(soup, "property", "og:title", m["og_title"])
    set_meta(soup, "property", "og:description", m["og_desc"])
    set_meta(soup, "name", "twitter:title", m["tw_title"])
    set_meta(soup, "name", "twitter:description", m["tw_desc"])
    # canonical
    can = soup.find("link", rel="canonical")
    if can: can["href"] = m["url"]
    # hreflang block after canonical (root already patched by patch_root; skip if present)
    if can and 'hreflang=' not in html:
        href_soup = BeautifulSoup(HREFLANG, "html.parser")
        for t in reversed([x for x in href_soup.contents if getattr(x, "name", None)]):
            can.insert_after(t)

    # bake all data-i18n content
    for el in soup.find_all(attrs={"data-i18n": True}):
        k = el["data-i18n"]
        if k in dict_:
            el.clear()
            for child in BeautifulSoup(dict_[k], "html.parser").contents[:]:
                el.append(child)
    for el in soup.find_all(attrs={"data-i18n-ph": True}):
        k = el["data-i18n-ph"]
        if k in dict_:
            el["placeholder"] = dict_[k]

    out = str(soup)

    # ── JS adjustments (string-level, on serialized output) ──
    # 1. lang buttons: <button class="lang-btn" data-lang="X"> → <a href="..."> links
    out = out.replace(
        '<button class="lang-btn" data-lang="vi">VI</button>',
        '<a class="lang-btn" href="/">VI</a>')
    out = out.replace(
        '<button class="lang-btn" data-lang="zh">中文</button>',
        '<a class="lang-btn" href="/zh/">中文</a>')
    out = out.replace(
        '<button class="lang-btn" data-lang="en">EN</button>',
        '<a class="lang-btn" href="/en/">EN</a>')
    # mark active lang
    active = {"zh": "中文", "en": "EN"}[lang]
    href = m["path"]
    out = out.replace(
        '<a class="lang-btn" href="%s">%s</a>' % (href, active),
        '<a class="lang-btn active" href="%s">%s</a>' % (href, active))

    # 2. remove JS button click binding + auto-detect IIFE, force page lang
    out = re.sub(
        r"document\.querySelectorAll\('\.lang-btn'\)\.forEach\(btn => \{\s*btn\.addEventListener\('click', \(\) => applyLang\(btn\.getAttribute\('data-lang'\)\)\);\s*\}\);",
        "", out)
    out = re.sub(
        r"/\* 初次載入：SEO 爬蟲一律使用原始越南語 HTML.*?\n\(function \(\) \{.*?\}\)\(\);",
        "window.__cmLang = '%s';\ntry { applyLang('%s'); } catch(e) {}" % (lang, lang),
        out, flags=re.S)

    # 3. news.json → absolute
    out = out.replace('fetch("news.json?t="', 'fetch("/news.json?t="')

    d = os.path.join(ROOT, lang)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
        f.write(out)
    print("built /%s/index.html (%d bytes)" % (lang, len(out.encode("utf-8"))))

def patch_root():
    html = open(SRC, encoding="utf-8").read()
    # hreflang after canonical (idempotent)
    if 'hreflang="zh-Hant"' not in html:
        html = html.replace(
            '<link rel="canonical" href="https://chihming.com.vn/">',
            '<link rel="canonical" href="https://chihming.com.vn/">\n' + HREFLANG.rstrip("\n"))
    # lang buttons → links
    html = html.replace('<button class="lang-btn" data-lang="vi">VI</button>',
                        '<a class="lang-btn active" href="/">VI</a>')
    html = html.replace('<button class="lang-btn" data-lang="zh">中文</button>',
                        '<a class="lang-btn" href="/zh/">中文</a>')
    html = html.replace('<button class="lang-btn" data-lang="en">EN</button>',
                        '<a class="lang-btn" href="/en/">EN</a>')
    # remove button click JS binding
    html = re.sub(
        r"document\.querySelectorAll\('\.lang-btn'\)\.forEach\(btn => \{\s*btn\.addEventListener\('click', \(\) => applyLang\(btn\.getAttribute\('data-lang'\)\)\);\s*\}\);",
        "", html)
    # root auto-detect: humans with non-vi preference get redirected to their language URL (bots stay vi)
    html = html.replace(
        """  let lang = null;
  try { lang = localStorage.getItem('cm_lang'); } catch (e) {}
  if (!lang) {
    const bl = (navigator.language || 'vi').toLowerCase();
    lang = bl.startsWith('zh') ? 'zh' : (bl.startsWith('en') ? 'en' : 'vi');
  }
  if (lang !== 'vi') applyLang(lang); else applyLang('vi');""",
        """  let lang = null;
  try { lang = localStorage.getItem('cm_lang'); } catch (e) {}
  if (!lang) {
    const bl = (navigator.language || 'vi').toLowerCase();
    lang = bl.startsWith('zh') ? 'zh' : (bl.startsWith('en') ? 'en' : 'vi');
  }
  if (lang === 'zh') { location.replace('/zh/'); return; }
  if (lang === 'en') { location.replace('/en/'); return; }
  applyLang('vi');""")
    html = html.replace('fetch("news.json?t="', 'fetch("/news.json?t="')
    with open(SRC, "w", encoding="utf-8") as f:
        f.write(html)
    print("patched root index.html")

if __name__ == "__main__":
    i18n = load_i18n()
    patch_root()
    for lang in ("zh", "en"):
        bake(lang, i18n)
