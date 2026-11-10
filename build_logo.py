#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""產生正方形品牌圖：logo-square.png (1024)、favicon 系列、og-image (1200x630)。
原因：Google 搜尋結果 LOGO 縮圖版位為 1:1，原 logo.png 是 400x234 (1.71:1)，
會被中央裁切導致「CHIH MING」顯示成「HIH MIN」。"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = "/home/mrnie/chihming-website"
SRC_LOGO = ROOT + "/logo.png"

F_CJK = "/mnt/c/Windows/Fonts/msjhbd.ttc"      # 微軟正黑體 Bold（繁中）
F_LAT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # 越南語聲調完整

# 從原圖取樣得到的品牌綠
GREEN = (0, 133, 44)
GREEN_DARK = (0, 100, 33)
RED = (190, 30, 45)
INK = (30, 40, 35)


def crop_content(im):
    """裁掉白邊，只留實際圖形。"""
    px = im.convert("RGBA").load()
    w, h = im.size
    xs, ys = [], []
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a > 10 and not (r > 245 and g > 245 and b > 245):
                xs.append(x); ys.append(y)
    if not xs:
        return im
    return im.crop((min(xs), min(ys), max(xs) + 1, max(ys) + 1))


def fit_width(im, target_w):
    w, h = im.size
    nh = round(h * target_w / w)
    return im.resize((target_w, nh), Image.LANCZOS)


def text_w(draw, txt, font):
    b = draw.textbbox((0, 0), txt, font=font)
    return b[2] - b[0], b[3] - b[1], b[0], b[1]


def paste_centered(canvas, img, cx, top):
    canvas.paste(img, (round(cx - img.size[0] / 2), round(top)),
                 img if img.mode == "RGBA" else None)


def build_square(size=1024, with_names=True):
    """正方形完整版：地球+CHIH MING（原圖）→ 中文名 → 越南語全名。"""
    canvas = Image.new("RGB", (size, size), (255, 255, 255))
    d = ImageDraw.Draw(canvas)

    globe = crop_content(Image.open(SRC_LOGO).convert("RGBA"))

    margin = round(size * 0.055)
    if with_names:
        # 版面：地球 48% / 中文名 / 越南語名
        gw = size - margin * 2
        globe_f = fit_width(globe, gw)
        top = round(size * 0.045)
        paste_centered(canvas, globe_f, size / 2, top)

        block_top = top + globe_f.size[1] + round(size * 0.035)
        block_h = size - block_top - margin

        # 中文名（較大）+ 越南語全名（較小），垂直平分剩餘空間
        f_cjk = ImageFont.truetype(F_CJK, round(block_h * 0.42))
        zh = "志明責任有限公司"
        wzh, hzh, oxz, oyz = text_w(d, zh, f_cjk)
        while wzh > size - margin * 2 and f_cjk.size > 20:
            f_cjk = ImageFont.truetype(F_CJK, f_cjk.size - 4)
            wzh, hzh, oxz, oyz = text_w(d, zh, f_cjk)
        y1 = block_top + round(block_h * 0.06)
        d.text(((size - wzh) / 2 - oxz, y1 - oyz), zh, font=f_cjk, fill=INK)

        # 越南語法定全名
        f_lat_sz = round(block_h * 0.245)
        f_lat = ImageFont.truetype(F_LAT, f_lat_sz)
        vi = "CÔNG TY TNHH CHIH MING"
        wv, hv, oxv, oyv = text_w(d, vi, f_lat)
        while wv > size - margin * 2 and f_lat.size > 16:
            f_lat = ImageFont.truetype(F_LAT, f_lat.size - 3)
            wv, hv, oxv, oyv = text_w(d, vi, f_lat)
        y2 = y1 + hzh + round(block_h * 0.16)
        d.text(((size - wv) / 2 - oxv, y2 - oyv), vi, font=f_lat, fill=GREEN)

        # 底部細綠線作視覺收尾
        lw = round(size * 0.30)
        ly = size - margin - round(size * 0.008)
        d.rounded_rectangle(
            [(size - lw) / 2, ly, (size + lw) / 2, ly + round(size * 0.012)],
            radius=round(size * 0.006), fill=GREEN)
    else:
        # 純圖形版（favicon 用）：地球置中，四周留安全邊距
        gw = round(size * 0.94)
        globe_f = fit_width(globe, gw)
        paste_centered(canvas, globe_f, size / 2, (size - globe_f.size[1]) / 2)

    return canvas


def build_favicon_icon(size):
    """favicon：只有地球圖形，1:1，白底，大字清晰。"""
    return build_square(size, with_names=False)


def build_og(w=1200, h=630):
    """og:image 1200x630（社群分享 / Google 富結果備援）。"""
    canvas = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(canvas)

    # 左側綠色色塊
    bar = round(w * 0.012)
    d.rectangle([0, 0, bar, h], fill=GREEN)

    globe = crop_content(Image.open(SRC_LOGO).convert("RGBA"))
    gh = round(h * 0.52)
    gw = round(globe.size[0] * gh / globe.size[1])
    globe_f = globe.resize((gw, gh), Image.LANCZOS)
    lx = round(w * 0.05)
    canvas.paste(globe_f, (lx, round(h * 0.10)),
                 globe_f if globe_f.mode == "RGBA" else None)

    # 右側文字
    tx = lx + gw + round(w * 0.045)
    f1 = ImageFont.truetype(F_CJK, round(h * 0.115))
    d.text((tx, round(h * 0.15)), "志明責任有限公司", font=f1, fill=INK)
    f2 = ImageFont.truetype(F_LAT, round(h * 0.082))
    d.text((tx, round(h * 0.315)), "CÔNG TY TNHH CHIH MING", font=f2, fill=GREEN)
    f3 = ImageFont.truetype(F_CJK, round(h * 0.062))
    d.text((tx, round(h * 0.475)),
           "越南 CaCO₃ 填充母粒製造商 · 北寧省桂武工業區", font=f3, fill=(90, 100, 95))
    f4 = ImageFont.truetype(F_LAT, round(h * 0.052))
    d.text((tx, round(h * 0.60)), "chihming.com.vn  ·  MST 2300324175",
           font=f4, fill=(130, 140, 135))

    # 底部綠線
    d.rectangle([tx, round(h * 0.78), tx + round(w * 0.30), round(h * 0.785)], fill=GREEN)
    return canvas


if __name__ == "__main__":
    out = []

    sq = build_square(1024)
    p = ROOT + "/logo-square.png"; sq.save(p, "PNG", optimize=True); out.append(p)

    # favicon 系列（1:1，純圖形，小尺寸也清楚）
    for s, name in [(512, "favicon-512.png"), (192, "favicon-192.png"),
                    (48, "favicon-48.png"), (32, "favicon-32.png")]:
        p = ROOT + "/" + name
        build_favicon_icon(s).save(p, "PNG", optimize=True)
        out.append(p)

    # .ico 多尺寸（瀏覽器書籤列用）
    p = ROOT + "/favicon.ico"
    build_favicon_icon(256).save(p, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    out.append(p)

    p = ROOT + "/og-image.png"
    build_og().save(p, "PNG", optimize=True); out.append(p)

    print("=== 已產生 ===")
    import os
    for f in out:
        im = Image.open(f)
        print(" %-22s %sx%s ratio=%.2f  %d KB" %
              (os.path.basename(f), im.size[0], im.size[1],
               im.size[0] / im.size[1], os.path.getsize(f) // 1024))
