#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""繪製簡化版地球標誌（純向量線條，無文字），供 16~64px 小尺寸 favicon 使用。
原因：原 logo.png 的「CHIH MING」文字縮到 32px 會糊成一團，無法辨識。"""
from PIL import Image, ImageDraw
import math


def draw_globe(size, green=(0, 133, 44), pad_ratio=0.16, lw_ratio=None):
    """在白底正方形畫布上繪製簡化地球：外圓 + 3 條經線 + 2 條緯線。"""
    S = size * 4                      # 4x 超取樣，縮圖後邊緣平滑
    img = Image.new("RGB", (S, S), (255, 255, 255))
    d = ImageDraw.Draw(img)

    pad = round(S * pad_ratio)
    box = [pad, pad, S - pad, S - pad]
    lw = lw_ratio or max(2, round(S * 0.038))

    cx, cy = S / 2, S / 2
    r = (box[2] - box[0]) / 2

    # 外圓
    d.ellipse(box, outline=green, width=lw)

    # 經線（垂直橢圓，寬度遞減）
    for f in (0.62, 0.32):
        rx = r * f
        d.ellipse([cx - rx, cy - r, cx + rx, cy + r], outline=green, width=lw)
    # 中央垂直線
    d.line([cx, cy - r, cx, cy + r], fill=green, width=lw)

    # 緯線（水平線，長度依圓弧收縮）
    for f in (0.42, 0.78):
        dy = r * f
        half = math.sqrt(max(r * r - dy * dy, 0)) * 0.995
        d.line([cx - half, cy - dy, cx + half, cy - dy], fill=green, width=lw)
        d.line([cx - half, cy + dy, cx + half, cy + dy], fill=green, width=lw)
    # 赤道
    d.line([cx - r, cy, cx + r, cy], fill=green, width=lw)

    return img.resize((size, size), Image.LANCZOS)


def draw_globe_simple(size, green=(0, 133, 44)):
    """16px 專用極簡版：只有外圓 + 一條經線 + 一條緯線（十字）。
    原因：完整經緯網格在 16px 下會糊成一團。"""
    S = size * 8                      # 8x 超取樣，極小尺寸才不會鋸齒
    img = Image.new("RGB", (S, S), (255, 255, 255))
    d = ImageDraw.Draw(img)
    pad = round(S * 0.04)
    box = [pad, pad, S - pad, S - pad]
    lw = max(2, round(S * 0.13))
    cx, cy = S / 2, S / 2
    r = (box[2] - box[0]) / 2

    d.ellipse(box, outline=green, width=lw)
    # 中央垂直經線 + 赤道
    d.line([cx, cy - r, cx, cy + r], fill=green, width=lw)
    d.line([cx - r, cy, cx + r, cy], fill=green, width=lw)
    # 兩條簡化緯線（加立體感但不至於糊）
    for f in (0.62,):
        dy = r * f
        half = math.sqrt(max(r * r - dy * dy, 0)) * 0.98
        d.line([cx - half, cy - dy, cx + half, cy - dy], fill=green, width=lw)
        d.line([cx - half, cy + dy, cx + half, cy + dy], fill=green, width=lw)
    return img.resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    ROOT = "/home/mrnie/chihming-website"
    out = []
    for s in (512, 192, 96, 64, 48, 32):
        # 大尺寸留白多些、線條細些；小尺寸留白少、線條粗，才不會糊
        pad = 0.16 if s >= 192 else (0.11 if s >= 64 else 0.07)
        lwr = 0.034 if s >= 192 else (0.055 if s >= 64 else 0.09)
        p = "%s/globe-%d.png" % (ROOT, s)
        draw_globe(s, pad_ratio=pad, lw_ratio=max(1, round(s * lwr * 4))).save(p, "PNG", optimize=True)
        out.append(p)

    # 16px 極簡版
    p = ROOT + "/globe-16.png"
    draw_globe_simple(16).save(p, "PNG", optimize=True)
    out.append(p)

    # favicon.ico 多尺寸（Pillow ICO：由單張大圖自動產生多尺寸，append_images 對 ICO 無效）
    p = ROOT + "/favicon.ico"
    base = draw_globe(512, pad_ratio=0.11, lw_ratio=max(1, round(512 * 0.055 * 4)))
    base.save(p, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    out.append(p)

    # apple-touch-icon 180x180（iOS 會自己加圓角，需較多留白）
    p = ROOT + "/apple-touch-icon.png"
    draw_globe(180, pad_ratio=0.18, lw_ratio=max(1, round(180 * 0.045 * 4))).save(p, "PNG", optimize=True)
    out.append(p)

    import os
    print("=== 已產生簡化地球 favicon ===")
    for f in out:
        print(" %-24s %s  %d KB" % (os.path.basename(f), Image.open(f).size, os.path.getsize(f) // 1024))
