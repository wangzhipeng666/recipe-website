#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为菜谱网站生成动漫风格菜谱插画（一个菜谱一张图）。

流程：
1. 每道菜用 SVG 绘制统一风格的动漫美食插画（厚描边 + 赛璐璐上色 + 暖色背景）
2. 用本机 Chrome headless 把 SVG 渲染成 1024x768 PNG
3. PNG 存入 backend/uploads/，并把 recipes 表的 image_url / images 更新为新图

用法：
    python3 scripts/generate_anime_images.py            # 全部生成并更新数据库
    python3 scripts/generate_anime_images.py --no-db    # 只生成到 scripts/anime_out/，不改数据库
    python3 scripts/generate_anime_images.py --only 麻婆豆腐 可乐鸡翅
"""

import json
import shutil
import sqlite3
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
BACKEND = PROJECT / "backend"
UPLOADS = BACKEND / "uploads"
DB_PATH = BACKEND / "recipes.db"
SVG_DIR = PROJECT / "scripts" / "anime_svg"
OUT_DIR = PROJECT / "scripts" / "anime_out"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

W, H = 1024, 768
INK = "#4A322A"  # 统一描边色

# ---------------------------------------------------------------- 通用元素


def canvas(dish_id: str, body: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <radialGradient id="bg{dish_id}" cx="50%" cy="38%" r="80%">
    <stop offset="0%" stop-color="#FFF8E9"/>
    <stop offset="55%" stop-color="#FFEAC8"/>
    <stop offset="100%" stop-color="#FFDCA8"/>
  </radialGradient>
  <linearGradient id="wood{dish_id}" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#DCA768"/>
    <stop offset="100%" stop-color="#C58E4E"/>
  </linearGradient>
</defs>
<rect width="{W}" height="{H}" fill="url(#bg{dish_id})"/>
{bokeh()}
<rect x="-20" y="618" width="{W + 40}" height="{H - 598}" rx="26" fill="url(#wood{dish_id})" stroke="{INK}" stroke-width="5"/>
<line x1="120" y1="668" x2="920" y2="668" stroke="#B47E42" stroke-width="3" opacity="0.5"/>
<line x1="260" y1="708" x2="800" y2="708" stroke="#B47E42" stroke-width="3" opacity="0.35"/>
{body}
{corner_sparkles()}
</svg>"""


def bokeh() -> str:
    circles = [
        (90, 120, 46, 0.5), (930, 90, 34, 0.45), (860, 240, 22, 0.4),
        (150, 300, 18, 0.35), (760, 60, 16, 0.5), (60, 430, 26, 0.3),
        (980, 380, 30, 0.3), (250, 60, 20, 0.4),
    ]
    parts = [
        f'<circle cx="{x}" cy="{y}" r="{r}" fill="#FFFFFF" opacity="{o}"/>'
        for x, y, r, o in circles
    ]
    return "\n".join(parts)


def sparkle(x: float, y: float, s: float, color: str = "#FFC94D", opacity: float = 0.95) -> str:
    k = s * 0.22
    return (
        f'<path d="M {x} {y - s} Q {x + k} {y - k} {x + s} {y} Q {x + k} {y + k} '
        f'{x} {y + s} Q {x - k} {y + k} {x - s} {y} Q {x - k} {y - k} {x} {y - s} Z" '
        f'fill="{color}" opacity="{opacity}"/>'
    )


def corner_sparkles() -> str:
    out = [sparkle(120, 170, 26), sparkle(158, 128, 13), sparkle(900, 200, 22),
           sparkle(938, 162, 11), sparkle(830, 90, 12), sparkle(210, 480, 10)]
    return "\n".join(out)


def steam(x: float, y: float, h: float, s: float = 1.0, o: float = 0.72) -> str:
    """三缕蒸汽，底部在 (x, y)，向上 h 像素。"""
    w = 26 * s
    p1 = f"M {x} {y} c -{w} -{h * .18} {w} -{h * .32} 0 -{h * .5} c -{w} -{h * .18} {w} -{h * .32} 0 -{h * .9}"
    x2, y2 = x + 58 * s, y + 14 * s
    p2 = f"M {x2} {y2} c -{w} -{h * .18} {w} -{h * .32} 0 -{h * .5} c -{w} -{h * .18} {w} -{h * .32} 0 -{h * .9}"
    x3, y3 = x - 58 * s, y + 14 * s
    p3 = f"M {x3} {y3} c -{w} -{h * .18} {w} -{h * .32} 0 -{h * .5} c -{w} -{h * .18} {w} -{h * .32} 0 -{h * .9}"
    return "\n".join(
        f'<path d="{p}" fill="none" stroke="#FFFFFF" stroke-width="{11 * s}" '
        f'stroke-linecap="round" opacity="{o}"/>' for p in (p1, p2, p3)
    )


def shadow(cx: float, cy: float, rx: float, ry: float) -> str:
    return (f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="#8A5A33" opacity="0.3"/>')


def bowl(cx: float, cy: float, rx: float, ry: float, depth: float,
         body_color: str, rim_color: str = "#FFFFFF", foot: bool = True) -> str:
    """俯视 30° 的碗：开口椭圆 + 碗身。cy 为开口中心。返回 (外身, 开口遮盖顺序由调用方控制)。
    这里先画碗身，食物画在其上，再由调用方画开口前沿。"""
    body = (
        f'<path d="M {cx - rx} {cy} '
        f'C {cx - rx} {cy + depth * 0.72} {cx - rx * 0.62} {cy + depth} {cx} {cy + depth} '
        f'C {cx + rx * 0.62} {cy + depth} {cx + rx} {cy + depth * 0.72} {cx + rx} {cy} Z" '
        f'fill="{body_color}" stroke="{INK}" stroke-width="6"/>'
    )
    if foot:
        body += (
            f'<ellipse cx="{cx}" cy="{cy + depth + 10}" rx="{rx * 0.42}" ry="14" '
            f'fill="{body_color}" stroke="{INK}" stroke-width="5"/>'
        )
    body += (
        f'<path d="M {cx - rx * 0.86} {cy + depth * 0.52} '
        f'C {cx - rx * 0.7} {cy + depth * 0.2} {cx - rx * 0.7} {cy + depth * 0.2} {cx - rx * 0.6} {cy + depth * 0.18}" '
        f'fill="none" stroke="#FFFFFF" stroke-width="7" stroke-linecap="round" opacity="0.55"/>'
    )
    return body


def food_disc(cx: float, cy: float, rx: float, ry: float, fill: str, grad_id: str = None,
              c2: str = None) -> str:
    """碗口内的食物面。"""
    fill_attr = f'url(#{grad_id})' if grad_id else fill
    return (
        f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill_attr}" '
        f'stroke="{INK}" stroke-width="6"/>'
        if not grad_id else
        f'''<defs><radialGradient id="{grad_id}" cx="50%" cy="40%" r="70%">
        <stop offset="0%" stop-color="{fill}"/><stop offset="100%" stop-color="{c2}"/>
        </radialGradient></defs>
        <ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="url(#{grad_id})" stroke="{INK}" stroke-width="6"/>'''
    )


def rim_front(cx: float, cy: float, rx: float, ry: float, color: str = "#FFFFFF") -> str:
    """碗口前沿（食物画完后再描一次前缘，形成碗沿）。"""
    return (
        f'<path d="M {cx - rx} {cy} A {rx} {ry} 0 0 0 {cx + rx} {cy}" '
        f'fill="none" stroke="{color}" stroke-width="13"/> '
        f'<path d="M {cx - rx} {cy} A {rx} {ry} 0 0 0 {cx + rx} {cy}" '
        f'fill="none" stroke="{INK}" stroke-width="6"/>'
    )


def plate(cx: float, cy: float, rx: float, ry: float, color: str = "#FFFFFF") -> str:
    return (
        f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{color}" stroke="{INK}" stroke-width="6"/>'
        f'<ellipse cx="{cx}" cy="{cy - 4}" rx="{rx * 0.74}" ry="{ry * 0.66}" fill="none" '
        f'stroke="#E4D9CB" stroke-width="5"/>'
    )


def scallion_bits(cx, cy, pts, s=1.0):
    out = []
    for dx, dy in pts:
        out.append(
            f'<circle cx="{cx + dx}" cy="{cy + dy}" r="{7 * s}" fill="#6FBF5A" stroke="{INK}" stroke-width="2.5"/>'
            f'<circle cx="{cx + dx}" cy="{cy + dy}" r="{2.6 * s}" fill="#4E9640"/>'
        )
    return "".join(out)


def glossy_arc(cx, cy, rx, ry, o=0.5):
    return (
        f'<path d="M {cx - rx} {cy} A {rx} {ry} 0 0 1 {cx + rx} {cy - ry * 0.1}" '
        f'fill="none" stroke="#FFFFFF" stroke-width="8" stroke-linecap="round" opacity="{o}"/>'
    )


# ---------------------------------------------------------------- 菜品绘制

def d_mapo_tofu() -> str:
    cx, cy, rx, ry, dep = 512, 430, 252, 92, 130
    s = [shadow(cx, cy + dep + 8, rx * 0.9, 26)]
    s.append(bowl(cx, cy, rx, ry, dep, "#FDFBF6"))
    s.append(food_disc(cx, cy - 2, rx - 14, ry - 8, "#E05A2B", "grad_mapo", "#B03A16"))
    tofu = [(-150, -8, -8), (-88, 16, 6), (-30, -20, -5), (44, 10, 8), (110, -12, -7),
            (168, 14, 5), (-120, 34, 5), (20, 38, -4), (130, 38, 7), (-40, 4, 3)]
    for dx, dy, rot in tofu:
        x, y = cx + dx, cy + dy
        s.append(
            f'<g transform="rotate({rot} {x} {y})">'
            f'<rect x="{x - 30}" y="{y - 22}" width="60" height="44" rx="10" '
            f'fill="#FFF6DE" stroke="{INK}" stroke-width="4"/>'
            f'<rect x="{x - 18}" y="{y - 14}" width="24" height="12" rx="6" fill="#FFE9B8"/></g>'
        )
    s.append(scallion_bits(cx, cy - 4, [(-170, -26), (-60, -38), (10, -34), (90, -34), (185, -20), (-135, 4), (75, 30)], 0.9))
    for dx, dy in [(-195, 18), (0, -6), (150, 2), (-70, 42), (200, 40)]:
        s.append(
            f'<circle cx="{cx + dx}" cy="{cy + dy}" r="6" fill="#8C2B10" opacity="0.85"/>'
            f'<circle cx="{cx + dx - 2}" cy="{cy + dy - 2}" r="1.8" fill="#FFB25E"/>'
        )
    s.append(rim_front(cx, cy, rx, ry))
    s.append(glossy_arc(cx - 40, cy + dep * 0.62, 60, 14, 0.5))
    s.append(steam(cx, cy - ry - 26, 130, 1.0))
    return "\n".join(s)


def d_cola_wings() -> str:
    cx, cy = 512, 470
    s = [shadow(cx, cy + 30, 270, 30), plate(cx, cy, 285, 96)]

    def wing(x, y, rot, L=190):
        x0, x1, x2 = -L * 0.5, L * 0.5, L * 0.3
        return (
            f'<g transform="translate({x} {y}) rotate({rot})">'
            f'<path d="M {x0} 0 Q {x0 + L * 0.2} -46 0 -44 Q {L * 0.42} -40 {x1} -6 '
            f'Q {L * 0.54} 26 {x2} 30 Q {x0 + L * 0.3} 34 {x0 + L * 0.06} 16 Z" '
            f'fill="#9C5623" stroke="{INK}" stroke-width="5"/>'
            f'<path d="M {x0 + L * 0.16} -14 Q {x0 + L * 0.45} -34 {x2} -22" fill="none" '
            f'stroke="#C77F3B" stroke-width="9" stroke-linecap="round"/>'
            f'<path d="M {x0 + L * 0.22} 6 Q 0 -8 {x2} 6" fill="none" stroke="#E8A85C" '
            f'stroke-width="7" stroke-linecap="round" opacity="0.9"/>'
            f'<circle cx="{x0 + L * 0.02}" cy="4" r="11" fill="#FDF3E3" stroke="{INK}" stroke-width="4"/>'
            f'<circle cx="{x0 - L * 0.06}" cy="2" r="15" fill="#FDF3E3" stroke="{INK}" stroke-width="4"/></g>'
        )

    s.append(wing(cx - 120, cy - 20, -14))
    s.append(wing(cx + 10, cy - 34, 4))
    s.append(wing(cx + 130, cy - 6, 16))
    for dx, dy in [(-60, 26), (40, 30), (150, 40), (-160, 40), (90, 44)]:
        s.append(f'<ellipse cx="{cx + dx}" cy="{cy + dy}" rx="5" ry="3" fill="#FBE8C8" stroke="{INK}" stroke-width="1.5"/>')
    s.append(scallion_bits(cx, cy + 6, [(-20, 34), (110, 22), (-130, 22)], 0.75))
    s.append(steam(cx - 60, cy - 90, 100, 0.8, 0.5))
    return "\n".join(s)


def d_seaweed_soup() -> str:
    cx, cy, rx, ry, dep = 512, 420, 240, 88, 128
    s = [shadow(cx, cy + dep + 8, rx * 0.9, 26), bowl(cx, cy, rx, ry, dep, "#4E77B5")]
    s.append(food_disc(cx, cy - 2, rx - 14, ry - 8, "#F3CF6B", "grad_soup", "#E0AE45"))
    seaweeds = [(-160, -14, -12, 1.1), (-30, -30, 8, 0.9), (95, -18, -6, 1.2), (175, 8, 14, 0.8), (-90, 30, 5, 0.85)]
    for dx, dy, rot, sc in seaweeds:
        x, y = cx + dx, cy + dy
        s.append(
            f'<g transform="translate({x} {y}) rotate({rot}) scale({sc})">'
            f'<path d="M -42 6 Q -30 -22 -6 -14 Q 4 -30 22 -16 Q 44 -22 40 4 Q 50 16 28 20 Q 4 30 -18 22 Q -44 24 -42 6 Z" '
            f'fill="#3F6B4F" stroke="{INK}" stroke-width="4"/>'
            f'<path d="M -28 4 Q -6 -6 24 6" fill="none" stroke="#597F52" stroke-width="4" stroke-linecap="round"/></g>'
        )
    ribbons = [(-110, 18, -8), (10, 8, 10), (130, 30, -5)]
    for dx, dy, rot in ribbons:
        x, y = cx + dx, cy + dy
        s.append(
            f'<g transform="translate({x} {y}) rotate({rot})">'
            f'<path d="M -50 0 Q -30 -16 -6 -4 Q 20 8 50 -6" fill="none" stroke="#FFE08A" '
            f'stroke-width="14" stroke-linecap="round"/>'
            f'<path d="M -50 0 Q -30 -16 -6 -4 Q 20 8 50 -6" fill="none" stroke="{INK}" '
            f'stroke-width="3.5" stroke-linecap="round" opacity="0.55"/></g>'
        )
    for dx, dy in [(-190, -18), (60, -34), (185, -22)]:
        s.append(f'<circle cx="{cx + dx}" cy="{cy + dy}" r="4.5" fill="#FFFDF4"/>')
    s.append(rim_front(cx, cy, rx, ry, "#FFFFFF"))
    # 白瓷汤勺（平放在碗右侧桌面上）
    spoon_x, spoon_y = cx + rx + 108, cy + dep + 26
    s.append(shadow(spoon_x - 20, spoon_y + 26, 74, 13))
    s.append(
        f'<g transform="translate({spoon_x} {spoon_y}) rotate(6)">'
        f'<path d="M 44 4 Q 88 10 104 26" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
        f'<path d="M 44 4 Q 88 10 104 26" fill="none" stroke="#FDFBF6" stroke-width="11" stroke-linecap="round"/>'
        f'<ellipse cx="0" cy="0" rx="52" ry="34" fill="#FDFBF6" stroke="{INK}" stroke-width="5"/>'
        f'<ellipse cx="-2" cy="-2" rx="38" ry="22" fill="#F7EBD3" stroke="{INK}" stroke-width="3"/></g>'
    )
    s.append(steam(cx, cy - ry - 28, 120, 0.95))
    return "\n".join(s)


def d_mushroom_sauce() -> str:
    cx, cy, rx, ry, dep = 512, 445, 212, 78, 108
    s = [shadow(cx, cy + dep + 8, rx * 0.9, 24), bowl(cx, cy, rx, ry, dep, "#C8493B")]
    s.append(food_disc(cx, cy - 2, rx - 13, ry - 8, "#8A5426", "grad_sauce", "#6B3C17"))
    # 香菇片
    for dx, dy, rot in [(-120, -12, -10), (-20, 8, 14), (95, -14, -6), (150, 24, 8), (-70, 32, 4)]:
        x, y = cx + dx, cy + dy
        s.append(
            f'<g transform="translate({x} {y}) rotate({rot})">'
            f'<ellipse cx="0" cy="0" rx="34" ry="24" fill="#5C3A1E" stroke="{INK}" stroke-width="4"/>'
            f'<ellipse cx="0" cy="-3" rx="24" ry="12" fill="#7A502B"/>'
            f'<circle cx="-8" cy="-4" r="3.4" fill="#8F6237"/><circle cx="9" cy="-6" r="2.8" fill="#8F6237"/></g>'
        )
    # 肉末颗粒
    for dx, dy in [(-175, 10), (-95, -32), (-40, 32), (30, -34), (60, 22), (170, -6), (125, -36), (-150, 40)]:
        s.append(f'<circle cx="{cx + dx}" cy="{cy + dy}" r="5" fill="#4E2F14"/>')
    # 油光
    for dx, dy, r in [(-40, -12, 16), (110, 8, 12), (-135, 22, 10)]:
        s.append(
            f'<circle cx="{cx + dx}" cy="{cy + dy}" r="{r}" fill="#C98F4E" opacity="0.6"/>'
            f'<circle cx="{cx + dx - 3}" cy="{cy + dy - 3}" r="{r * 0.3}" fill="#FFE9C4" opacity="0.9"/>'
        )
    s.append(scallion_bits(cx, cy - 2, [(-10, -40), (80, 34), (-160, -14)], 0.8))
    s.append(rim_front(cx, cy, rx, ry, "#E9E2D6"))
    s.append(steam(cx - 30, cy - ry - 24, 95, 0.8, 0.55))
    return "\n".join(s)


def d_mushroom_skewers() -> str:
    cx, cy = 512, 440
    s = [shadow(cx, cy + 120, 250, 26), plate(cx, cy + 120, 250, 62)]

    def skewer(x, y, rot, n=5):
        parts = [f'<g transform="translate({x} {y}) rotate({rot})">']
        # 竹签压在食材下面
        parts.append(
            f'<line x1="-228" y1="0" x2="238" y2="0" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>'
            f'<line x1="-224" y1="0" x2="234" y2="0" stroke="#D9B26E" stroke-width="4" stroke-linecap="round"/>'
        )
        total = n
        for i in range(total):
            px = -180 + i * (360 // (total - 1))
            h = 52 if i % 2 == 0 else 60
            w = 66 if i % 2 == 0 else 58
            parts.append(
                f'<g transform="translate({px} 0) rotate({(i * 17) % 23 - 11})">'
                f'<rect x="{-w / 2}" y="{-h / 2}" width="{w}" height="{h}" rx="17" '
                f'fill="#F3E5C8" stroke="{INK}" stroke-width="5"/>'
                f'<rect x="{-w / 2 + 8}" y="{-h / 2 + 7}" width="{w * 0.5}" height="{h - 14}" rx="9" fill="#FAF1DD"/>'
                f'<path d="M {-w / 2 + 10} {-h / 2 + 12} q 12 8 4 18" fill="none" stroke="#B98F55" stroke-width="4" stroke-linecap="round"/>'
                f'<path d="M {w / 2 - 18} {h / 2 - 20} q 10 10 -2 16" fill="none" stroke="#8A5A2B" stroke-width="4.5" stroke-linecap="round"/>'
                f'</g>'
            )
        parts.append(
            f'<circle cx="-236" cy="0" r="7" fill="#D9B26E" stroke="{INK}" stroke-width="3"/>'
            f'<circle cx="246" cy="0" r="7" fill="#D9B26E" stroke="{INK}" stroke-width="3"/>'
        )
        parts.append("</g>")
        return "".join(parts)

    # 两串平放在盘中，前后错开
    s.append(f'<ellipse cx="{cx - 10}" cy="{cy + 92}" rx="220" ry="16" fill="#8A5A33" opacity="0.18"/>')
    s.append(skewer(cx - 16, cy + 88, -7))
    s.append(f'<ellipse cx="{cx + 6}" cy="{cy + 140}" rx="220" ry="16" fill="#8A5A33" opacity="0.18"/>')
    s.append(skewer(cx + 16, cy + 128, 5))
    # 辣椒粉与葱花
    for dx, dy in [(-150, 172), (-40, 184), (80, 178), (170, 166), (-100, 164)]:
        s.append(f'<circle cx="{cx + dx}" cy="{cy + dy}" r="4.5" fill="#D14B33" stroke="{INK}" stroke-width="1.5"/>')
    s.append(scallion_bits(cx, cy + 170, [(-195, 4), (30, 8), (145, -10)], 0.7))
    s.append(sparkle(cx + 300, cy - 130, 16, "#FFFFFF", 0.85))
    s.append(sparkle(cx - 310, cy - 90, 12, "#FFFFFF", 0.7))
    return "\n".join(s)


def d_dipping_sauce() -> str:
    cx, cy, rx, ry, dep = 512, 455, 176, 64, 84
    s = [shadow(cx, cy + dep + 8, rx * 0.95, 22), bowl(cx, cy, rx, ry, dep, "#FDFBF6")]
    s.append(food_disc(cx, cy - 2, rx - 12, ry - 8, "#C43E22", "grad_dip", "#96281B"))
    # 蒜片
    for dx, dy, rot in [(-85, -10, -14), (0, 12, 10), (85, -12, -6)]:
        x, y = cx + dx, cy + dy
        s.append(
            f'<g transform="translate({x} {y}) rotate({rot})">'
            f'<ellipse cx="0" cy="0" rx="22" ry="13" fill="#FBF3E4" stroke="{INK}" stroke-width="3.5"/>'
            f'<ellipse cx="0" cy="0" rx="13" ry="6" fill="#EFE2C8"/></g>'
        )
    # 辣椒碎
    for dx, dy in [(-130, 14), (-45, 34), (40, -32), (130, 16), (95, 36), (-15, -36)]:
        s.append(f'<circle cx="{cx + dx}" cy="{cy + dy}" r="4" fill="#7E1D0C"/>')
    s.append(scallion_bits(cx, cy, [(-60, -16), (55, 6), (-125, -20)], 0.72))
    # 香菜叶
    s.append(
        f'<g transform="translate({cx + 15} {cy - 20}) rotate(-18)">'
        f'<path d="M 0 18 Q -4 2 -14 -8 Q -2 -16 0 -24 Q 2 -16 14 -8 Q 4 2 0 18 Z" '
        f'fill="#3E8F4A" stroke="{INK}" stroke-width="3.5"/></g>'
    )
    s.append(rim_front(cx, cy, rx, ry))
    s.append(glossy_arc(cx - 30, cy + dep * 0.6, 46, 10, 0.5))
    # 一只小辣椒作装饰
    s.append(
        f'<g transform="translate({cx + rx + 70} {cy + 96}) rotate(24)">'
        f'<path d="M -55 -4 Q -20 -26 30 -18 Q 60 -12 70 6 Q 30 2 0 14 Q -30 24 -55 12 Z" '
        f'fill="#D14B33" stroke="{INK}" stroke-width="4.5"/>'
        f'<path d="M -55 -4 Q -62 -10 -58 -16" fill="none" stroke="#5C8A3C" stroke-width="6" stroke-linecap="round"/></g>'
    )
    return "\n".join(s)


def d_blanched_greens() -> str:
    cx, cy = 512, 455
    s = [shadow(cx, cy + 26, 268, 30), plate(cx, cy, 272, 92)]

    def bokchoy(x, y, rot, sc):
        g = [f'<g transform="translate({x} {y}) rotate({rot}) scale({sc})">']
        g.append(
            f'<path d="M -22 40 Q -30 8 -18 -14 L 18 -14 Q 30 8 22 40 Q 0 52 -22 40 Z" '
            f'fill="#F6F3DF" stroke="{INK}" stroke-width="4.5"/>'
            f'<path d="M -8 36 Q -10 8 -6 -12" fill="none" stroke="#D9D2B4" stroke-width="4"/>'
            f'<path d="M 8 36 Q 10 8 6 -12" fill="none" stroke="#D9D2B4" stroke-width="4"/>'
        )
        for lx, ly, lr in [(-38, -34, -24), (0, -52, 0), (38, -34, 24)]:
            g.append(
                f'<g transform="rotate({lr})"><path d="M 0 8 Q -34 -14 -22 -46 Q -6 -66 0 -74 Q 6 -66 22 -46 Q 34 -14 0 8 Z" '
                f'fill="#5FAF57" stroke="{INK}" stroke-width="4.5"/>'
                f'<path d="M 0 4 L 0 -58" stroke="#3F8A3F" stroke-width="4" stroke-linecap="round"/>'
                f'<path d="M 0 -20 L -16 -32 M 0 -34 L 15 -45" stroke="#3F8A3F" stroke-width="3" stroke-linecap="round"/></g>'
            )
        g.append("</g>")
        return "".join(g)

    s.append(bokchoy(cx - 150, cy - 6, -8, 0.95))
    s.append(bokchoy(cx + 5, cy - 20, 3, 1.05))
    s.append(bokchoy(cx + 150, cy - 4, 10, 0.92))
    s.append(bokchoy(cx - 70, cy + 28, -4, 0.8))
    s.append(bokchoy(cx + 85, cy + 30, 6, 0.8))
    # 生抽淋面
    s.append(
        f'<path d="M {cx - 170} {cy - 46} Q {cx - 60} {cy - 66} {cx + 40} {cy - 48} Q {cx + 140} {cy - 32} {cx + 190} {cy - 44}" '
        f'fill="none" stroke="#7A4A1D" stroke-width="6" stroke-linecap="round" opacity="0.75"/>'
    )
    for dx, dy in [(-120, -50), (30, -58), (130, -40)]:
        s.append(f'<circle cx="{cx + dx}" cy="{cy + dy}" r="3.6" fill="#FBF3E4"/>')
    s.append(sparkle(cx - 250, cy - 120, 14, "#FFFFFF", 0.8))
    s.append(sparkle(cx + 260, cy - 100, 11, "#FFFFFF", 0.7))
    return "\n".join(s)


def d_chili_oil() -> str:
    cx, cy = 512, 420
    jar_w, jar_h = 250, 300
    top, bot = cy - jar_h / 2, cy + jar_h / 2
    s = [shadow(cx, bot + 16, 170, 26)]
    # 玻璃罐身
    s.append(
        f'<path d="M {cx - 108} {top + 40} Q {cx - 125} {bot} {cx - 60} {bot + 8} '
        f'L {cx + 60} {bot + 8} Q {cx + 125} {bot} {cx + 108} {top + 40} Z" '
        f'fill="#F4D9C4" opacity="0.5" stroke="{INK}" stroke-width="6"/>'
    )
    # 辣椒油（约占 3/4）
    oil_top = top + 108
    s.append(
        f'<path d="M {cx - 106} {oil_top + 6} Q {cx - 118} {bot} {cx - 58} {bot + 4} '
        f'L {cx + 58} {bot + 4} Q {cx + 118} {bot} {cx + 106} {oil_top + 6} '
        f'Q {cx} {oil_top - 16} {cx - 106} {oil_top + 6} Z" '
        f'fill="#D2452A" stroke="{INK}" stroke-width="5"/>'
    )
    s.append(f'<ellipse cx="{cx}" cy="{oil_top}" rx="106" ry="17" fill="#E86A44" stroke="{INK}" stroke-width="4"/>')
    # 油里的辣椒碎
    for dx, dy in [(-70, 60), (-20, 110), (50, 70), (85, 150), (-60, 180), (10, 220), (60, 240), (-15, 150)]:
        s.append(
            f'<g transform="translate({cx + dx} {oil_top + dy}) rotate({(dx + dy) % 40 - 20})">'
            f'<ellipse cx="0" cy="0" rx="9" ry="5" fill="#96281B" stroke="#7A1F0E" stroke-width="2"/></g>'
        )
    # 木盖
    s.append(
        f'<rect x="{cx - 118}" y="{top - 26}" width="236" height="52" rx="16" '
        f'fill="#C58E4E" stroke="{INK}" stroke-width="6"/>'
        f'<circle cx="{cx}" cy="{top}" r="9" fill="#8A5A2B" stroke="{INK}" stroke-width="3"/>'
        f'<rect x="{cx - 76}" y="{top - 12}" width="152" height="24" rx="8" fill="#D9A765"/>'
    )
    # 罐身高光
    s.append(
        f'<path d="M {cx - 80} {oil_top + 26} Q {cx - 92} {top + 150} {cx - 76} {bot - 30}" '
        f'fill="none" stroke="#FFFFFF" stroke-width="12" stroke-linecap="round" opacity="0.75"/>'
    )
    # 旁边两根干辣椒
    s.append(
        f'<g transform="translate({cx - 210} {bot - 40}) rotate(-14)">'
        f'<path d="M -58 6 Q -20 -20 26 -14 Q 58 -8 68 8 Q 30 4 2 16 Q -28 26 -58 6 Z" '
        f'fill="#C8402A" stroke="{INK}" stroke-width="4.5"/></g>'
        f'<g transform="translate({cx + 205} {bot - 26}) rotate(12)">'
        f'<path d="M -60 8 Q -24 -16 20 -12 Q 54 -4 64 10 Q 28 8 0 18 Q -30 28 -60 8 Z" '
        f'fill="#D14B33" stroke="{INK}" stroke-width="4.5"/></g>'
    )
    s.append(sparkle(cx - 40, top - 90, 15, "#FFC94D"))
    s.append(sparkle(cx + 120, top - 60, 11, "#FFC94D"))
    return "\n".join(s)


def d_shandong_chicken() -> str:
    cx, cy = 512, 462
    s = [shadow(cx, cy + 28, 278, 30), plate(cx, cy, 292, 98)]
    chunks = [
        (-185, -18, -14, 1.05), (-95, -40, 8, 0.9), (-15, -22, -6, 1.1),
        (75, -42, 12, 0.85), (170, -16, -10, 1.0), (-140, 26, 6, 0.9),
        (-45, 20, -12, 1.0), (55, 24, 8, 0.95), (150, 30, -5, 0.85),
    ]
    for dx, dy, rot, sc in chunks:
        x, y = cx + dx, cy + dy
        s.append(
            f'<g transform="translate({x} {y}) rotate({rot}) scale({sc})">'
            f'<path d="M -44 -10 Q -40 -38 -8 -40 Q 36 -42 46 -8 Q 50 22 18 32 Q -26 38 -42 12 Q -50 -2 -44 -10 Z" '
            f'fill="#C8873B" stroke="{INK}" stroke-width="5"/>'
            f'<path d="M -30 -16 Q -6 -30 26 -18" fill="none" stroke="#E2A85C" stroke-width="8" stroke-linecap="round"/>'
            f'<path d="M -26 12 Q 4 24 34 8" fill="none" stroke="#8C5A22" stroke-width="7" stroke-linecap="round" opacity="0.8"/>'
            f'<circle cx="-20" cy="-4" r="4" fill="#8C5A22"/><circle cx="12" cy="-12" r="3.4" fill="#8C5A22"/></g>'
        )
    # 青红椒块
    for dx, dy, col in [(-70, -50, "#4E9A45"), (35, -52, "#D64541"), (125, -40, "#4E9A45"),
                        (-175, 6, "#D64541"), (95, 0, "#4E9A45"), (200, 8, "#D64541")]:
        x, y = cx + dx, cy + dy
        s.append(
            f'<g transform="translate({x} {y}) rotate({dx % 30 - 15})">'
            f'<rect x="-22" y="-20" width="44" height="40" rx="9" fill="{col}" stroke="{INK}" stroke-width="4.5"/>'
            f'<rect x="-12" y="-10" width="16" height="12" rx="4" fill="#FFFFFF" opacity="0.35"/></g>'
        )
    s.append(scallion_bits(cx, cy - 6, [(-230, -34), (10, -66), (225, -28)], 0.8))
    s.append(glossy_arc(cx - 20, cy - 62, 90, 16, 0.35))
    s.append(steam(cx + 40, cy - 96, 90, 0.75, 0.5))
    return "\n".join(s)


def d_chive_pockets() -> str:
    cx, cy = 512, 470
    s = [shadow(cx, cy + 30, 268, 30), plate(cx, cy, 272, 92)]

    def pocket(x, y, rot, sc, bite=False):
        g = [f'<g transform="translate({x} {y}) rotate({rot}) scale({sc})">']
        edge = "M -150 0 Q -140 -52 -95 -80 Q -30 -112 45 -100 Q 120 -86 150 -30 Q 130 40 60 74 Q -20 100 -90 66 Q -145 38 -150 0 Z"
        if bite:
            edge = "M -150 0 Q -140 -52 -95 -80 Q -30 -112 45 -100 Q 120 -86 150 -30 Q 140 -6 118 6 Q 96 -20 70 -10 Q 74 22 48 40 Q -20 92 -90 66 Q -145 38 -150 0 Z"
        g.append(f'<path d="{edge}" fill="#F2CE82" stroke="{INK}" stroke-width="6"/>')
        # 内圈烙痕
        g.append(
            f'<path d="M -122 -6 Q -104 -48 -60 -66 Q 0 -88 66 -72 Q 116 -58 126 -24" '
            f'fill="none" stroke="#E0B264" stroke-width="10" stroke-linecap="round" opacity="0.8"/>'
        )
        # 焦斑
        for bx, by, br in [(-90, -40, 13), (-10, -70, 11), (70, -52, 12), (110, -14, 10), (-60, 30, 11), (30, 46, 9), (-125, 14, 9)]:
            g.append(
                f'<ellipse cx="{bx}" cy="{by}" rx="{br}" ry="{br * 0.75}" fill="#C08436" opacity="0.85"/>'
                f'<ellipse cx="{bx - 2}" cy="{by - 2}" rx="{br * 0.4}" ry="{br * 0.3}" fill="#9A6526"/>'
            )
        # 压边花纹
        g.append(
            f'<path d="M -150 0 Q -145 38 -90 66 Q -20 100 60 74 Q 130 40 150 -30" '
            f'fill="none" stroke="{INK}" stroke-width="4" stroke-dasharray="2 16" stroke-linecap="round"/>'
        )
        g.append("</g>")
        return "".join(g)

    s.append(pocket(cx - 40, cy + 6, -6, 1.02, bite=True))
    s.append(pocket(cx + 90, cy - 40, 8, 0.86))
    # 露出的韭菜
    s.append(
        f'<g transform="translate({cx + 30} {cy - 4}) rotate(24)">'
        f'<path d="M 0 0 Q 10 -28 4 -52" fill="none" stroke="#5FAF57" stroke-width="7" stroke-linecap="round"/>'
        f'<path d="M 6 -6 Q 22 -26 34 -40" fill="none" stroke="#4E9640" stroke-width="6" stroke-linecap="round"/></g>'
    )
    # 小醋碟
    s.append(
        f'<g transform="translate({cx - 210} {cy + 46})">'
        f'<ellipse cx="0" cy="14" rx="58" ry="20" fill="#FDFBF6" stroke="{INK}" stroke-width="5"/>'
        f'<ellipse cx="0" cy="10" rx="44" ry="13" fill="#8A5A2B" stroke="{INK}" stroke-width="3.5"/></g>'
    )
    s.append(sparkle(cx + 240, cy - 130, 15, "#FFFFFF", 0.85))
    s.append(steam(cx - 60, cy - 120, 80, 0.7, 0.45))
    return "\n".join(s)


def d_malatang() -> str:
    cx, cy, rx, ry, dep = 512, 415, 262, 92, 122
    s = [shadow(cx, cy + dep + 12, rx * 0.95, 28)]
    # 砂锅身（黑色）
    s.append(
        f'<path d="M {cx - rx} {cy} C {cx - rx} {cy + dep * 0.7} {cx - rx * 0.6} {cy + dep} {cx} {cy + dep} '
        f'C {cx + rx * 0.6} {cy + dep} {cx + rx} {cy + dep * 0.7} {cx + rx} {cy} Z" '
        f'fill="#3A3430" stroke="{INK}" stroke-width="6"/>'
    )
    # 双耳
    for side in (-1, 1):
        ex = cx + side * (rx + 6)
        s.append(
            f'<path d="M {ex} {cy + 26} Q {cx + side * (rx + 58)} {cy + 10} {ex} {cy - 34}" '
            f'fill="none" stroke="{INK}" stroke-width="26" stroke-linecap="round"/>'
            f'<path d="M {ex} {cy + 26} Q {cx + side * (rx + 58)} {cy + 10} {ex} {cy - 34}" '
            f'fill="none" stroke="#4A4441" stroke-width="15" stroke-linecap="round"/>'
        )
    # 锅口
    s.append(
        f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="#544D48" stroke="{INK}" stroke-width="6"/>'
    )
    s.append(food_disc(cx, cy - 2, rx - 16, ry - 10, "#C63D22", "grad_mala", "#9E2E14"))
    # 火锅料：青菜
    for dx, dy, rot in [(-170, -22, -14), (150, -26, 12)]:
        x, y = cx + dx, cy + dy
        s.append(
            f'<g transform="translate({x} {y}) rotate({rot})">'
            f'<path d="M 0 10 Q -26 -8 -16 -34 Q -4 -48 0 -54 Q 4 -48 16 -34 Q 26 -8 0 10 Z" '
            f'fill="#5FAF57" stroke="{INK}" stroke-width="4"/></g>'
        )
    # 豆腐泡
    for dx, dy, rot, sc in [(-90, -34, -8, 1.0), (85, -40, 10, 0.9)]:
        x, y = cx + dx, cy + dy
        s.append(
            f'<g transform="translate({x} {y}) rotate({rot}) scale({sc})">'
            f'<path d="M -30 14 L -36 -10 L 0 -32 L 34 -8 L 26 16 Z" fill="#E8A33D" stroke="{INK}" stroke-width="4.5"/>'
            f'<path d="M -20 6 L -24 -8 L 0 -22 L 22 -6 L 16 8 Z" fill="#F4C478"/></g>'
        )
    # 鱼豆腐/年糕
    s.append(
        f'<g transform="translate({cx - 10} {cy + 16})">'
        f'<rect x="-38" y="-16" width="76" height="34" rx="10" fill="#F7E7C3" stroke="{INK}" stroke-width="4.5"/>'
        f'<circle cx="-12" cy="0" r="4" fill="#E0C68E"/><circle cx="10" cy="2" r="4" fill="#E0C68E"/></g>'
    )
    # 蘑菇
    s.append(
        f'<g transform="translate({cx + 175} {cy + 18}) rotate(12)">'
        f'<path d="M -32 6 Q -36 -26 0 -28 Q 34 -26 30 6 Q 0 16 -32 6 Z" fill="#D9B26E" stroke="{INK}" stroke-width="4.5"/>'
        f'<rect x="-9" y="4" width="18" height="20" rx="6" fill="#F0E0C0" stroke="{INK}" stroke-width="4"/></g>'
    )
    # 粉条
    s.append(
        f'<g transform="translate({cx - 120} {cy + 26})">'
        f'<path d="M -44 -8 Q -20 -22 4 -6 Q 28 10 48 -6" fill="none" stroke="#F5EBDC" stroke-width="10" stroke-linecap="round"/>'
        f'<path d="M -48 8 Q -22 -6 2 10 Q 26 24 44 8" fill="none" stroke="#EDE0CC" stroke-width="9" stroke-linecap="round"/></g>'
    )
    # 辣椒与花椒
    for dx, dy in [(-205, 16), (30, -52), (120, 44), (205, 6), (-50, 48)]:
        s.append(f'<circle cx="{cx + dx}" cy="{cy + dy}" r="5" fill="#7E1D0C"/>')
    s.append(rim_front(cx, cy, rx, ry, "#544D48"))
    s.append(steam(cx, cy - ry - 24, 150, 1.05))
    s.append(sparkle(cx - 290, cy - 130, 14, "#FFFFFF", 0.8))
    s.append(sparkle(cx + 300, cy - 100, 11, "#FFFFFF", 0.7))
    return "\n".join(s)


def d_dry_pot_cauliflower() -> str:
    cx, cy, rx, ry, dep = 512, 415, 258, 88, 98
    s = [shadow(cx, cy + dep + 12, rx * 0.95, 26)]
    # 黑色双耳干锅
    s.append(
        f'<path d="M {cx - rx} {cy} C {cx - rx} {cy + dep * 0.72} {cx - rx * 0.6} {cy + dep} {cx} {cy + dep} '
        f'C {cx + rx * 0.6} {cy + dep} {cx + rx} {cy + dep * 0.72} {cx + rx} {cy} Z" '
        f'fill="#3A3430" stroke="{INK}" stroke-width="6"/>'
    )
    for side in (-1, 1):
        ex = cx + side * (rx + 4)
        s.append(
            f'<path d="M {ex} {cy + 22} Q {cx + side * (rx + 54)} {cy + 6} {ex} {cy - 32}" '
            f'fill="none" stroke="{INK}" stroke-width="24" stroke-linecap="round"/>'
            f'<path d="M {ex} {cy + 22} Q {cx + side * (rx + 54)} {cy + 6} {ex} {cy - 32}" '
            f'fill="none" stroke="#4A4441" stroke-width="13" stroke-linecap="round"/>'
        )
    s.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="#544D48" stroke="{INK}" stroke-width="6"/>')

    # 锅底红油
    s.append(food_disc(cx, cy - 2, rx - 16, ry - 10, "#C24E2E", "grad_dpot", "#96281B"))

    # 菜花朵簇（云朵状：3-5 个重叠圆）
    florets = [
        (-152, -18, 1.15, -6), (-58, -40, 1.0, 5), (44, -30, 1.2, -4),
        (138, -14, 0.95, 7), (-104, 28, 0.9, 4), (66, 32, 1.0, -7), (162, 36, 0.8, 5), (-10, 8, 1.05, 3),
    ]
    for dx, dy, sc, rot in florets:
        x, y = cx + dx, cy + dy
        s.append(
            f'<g transform="translate({x} {y}) rotate({rot}) scale({sc})">'
            f'<circle cx="-22" cy="-6" r="20" fill="#FFF6E1" stroke="{INK}" stroke-width="4"/>'
            f'<circle cx="8" cy="-16" r="24" fill="#FFF9EA" stroke="{INK}" stroke-width="4"/>'
            f'<circle cx="26" cy="6" r="19" fill="#FFF6E1" stroke="{INK}" stroke-width="4"/>'
            f'<circle cx="-2" cy="12" r="18" fill="#FFFDf2" stroke="{INK}" stroke-width="4"/>'
            f'<circle cx="4" cy="-6" r="14" fill="#FFFDF4"/>'
            f'<circle cx="-26" cy="-10" r="3.4" fill="#D9A85C"/><circle cx="18" cy="10" r="3" fill="#C89355"/>'
            f'<path d="M -34 -14 q 6 8 14 4" fill="none" stroke="#C89355" stroke-width="3" stroke-linecap="round" opacity="0.8"/>'
            f'</g>'
        )
    # 五花肉片（粉白相间的波浪条）
    for dx, dy, rot in [(-190, 16, -14), (5, -55, 8), (120, -50, -6), (-90, -60, 10)]:
        x, y = cx + dx, cy + dy
        s.append(
            f'<g transform="translate({x} {y}) rotate({rot})">'
            f'<path d="M -34 -8 Q -20 -18 -4 -10 Q 14 -2 30 -10 Q 36 2 26 8 Q 8 14 -8 8 Q -26 14 -36 4 Z" '
            f'fill="#F2B8A0" stroke="{INK}" stroke-width="4"/>'
            f'<path d="M -30 -2 Q -10 -8 24 -3" fill="none" stroke="#FFF9F4" stroke-width="4.5" stroke-linecap="round"/>'
            f'<path d="M -24 5 Q 0 10 22 4" fill="none" stroke="#E8927A" stroke-width="3.5" stroke-linecap="round" opacity="0.8"/>'
            f'</g>'
        )
    # 干辣椒
    for dx, dy, rot in [(-215, -8, -18), (95, 12, 14), (200, -35, -8), (-135, -35, 10)]:
        x, y = cx + dx, cy + dy
        s.append(
            f'<g transform="translate({x} {y}) rotate({rot})">'
            f'<path d="M -26 -3 Q -10 -12 14 -8 Q 26 -5 30 3 Q 12 6 -4 6 Q -18 6 -26 -3 Z" '
            f'fill="#D14B33" stroke="{INK}" stroke-width="3.5"/></g>'
        )
    # 青蒜段
    for dx, dy, rot in [(-60, 22, 20), (160, 8, -16), (-175, -40, -10)]:
        x, y = cx + dx, cy + dy
        s.append(
            f'<g transform="translate({x} {y}) rotate({rot})">'
            f'<rect x="-16" y="-5" width="32" height="10" rx="5" fill="#7BA05B" stroke="{INK}" stroke-width="3.5"/>'
            f'<line x1="-5" y1="-5" x2="-5" y2="5" stroke="#5E8A45" stroke-width="2.5"/>'
            f'<line x1="6" y1="-5" x2="6" y2="5" stroke="#5E8A45" stroke-width="2.5"/></g>'
        )
    # 红油亮斑
    for dx, dy in [(-215, 30), (205, 22), (-40, 48)]:
        s.append(f'<circle cx="{cx + dx}" cy="{cy + dy}" r="7" fill="#E0684A" opacity="0.75"/>')
    s.append(rim_front(cx, cy, rx, ry, "#544D48"))
    s.append(steam(cx, cy - ry - 24, 130, 0.95))
    s.append(sparkle(cx - 285, cy - 120, 13, "#FFFFFF", 0.8))
    s.append(sparkle(cx + 300, cy - 90, 11, "#FFFFFF", 0.7))
    return "\n".join(s)


DISHES = {
    "麻婆豆腐": ("mapo", d_mapo_tofu),
    "可乐鸡翅": ("wings", d_cola_wings),
    "紫菜蛋花汤": ("soup", d_seaweed_soup),
    "香菇肉酱": ("sauce", d_mushroom_sauce),
    "杏鲍菇烤串": ("skewer", d_mushroom_skewers),
    "万能蘸水": ("dip", d_dipping_sauce),
    "水煮菜": ("greens", d_blanched_greens),
    "辣椒油": ("chilioil", d_chili_oil),
    "山东炒鸡": ("chicken", d_shandong_chicken),
    "韭菜盒子": ("pocket", d_chive_pockets),
    "砂锅麻辣烫": ("mala", d_malatang),
    "干锅菜花": ("drypot", d_dry_pot_cauliflower),
}

# ---------------------------------------------------------------- 主流程


def svg_to_png(svg_path: Path, png_path: Path) -> None:
    cmd = [
        CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        f"--screenshot={png_path}", f"--window-size={W},{H}",
        svg_path.resolve().as_uri(),
    ]
    subprocess.run(cmd, capture_output=True, timeout=60, check=True)
    if not png_path.exists():
        raise RuntimeError(f"Chrome 未生成 {png_path}")


def main() -> None:
    args = sys.argv[1:]
    no_db = "--no-db" in args
    if "--only" in args:
        only = args[args.index("--only") + 1:]
    else:
        only = None

    SVG_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 读取数据库中的菜谱
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id, name FROM recipes ORDER BY id").fetchall()
    targets = [(rid, name) for rid, name in rows if only is None or name in only]

    missing = [n for n in (only or []) if n not in DISHES]
    if missing:
        print(f"!! 未实现绘制的菜：{missing}")
        return

    results = []
    for rid, name in targets:
        key, fn = DISHES[name]
        svg_path = SVG_DIR / f"{key}.svg"
        png_path = OUT_DIR / f"{key}.png"
        svg_path.write_text(canvas(key, fn()), encoding="utf-8")
        svg_to_png(svg_path, png_path)
        print(f"  ✓ {name} -> {png_path.name} ({png_path.stat().st_size // 1024} KB)")
        results.append((rid, name, png_path))

    if no_db:
        print(f"\n完成：{len(results)} 张图输出到 {OUT_DIR}（未改动数据库）")
        conn.close()
        return

    # 备份数据库
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = DB_PATH.with_name(f"recipes.db.bak-anime-{stamp}")
    shutil.copy2(DB_PATH, backup)
    print(f"\n已备份数据库 -> {backup.name}")

    # 复制到 uploads 并更新数据库
    for rid, name, png_path in results:
        filename = f"{uuid.uuid4().hex}.png"
        shutil.copy2(png_path, UPLOADS / filename)
        url = f"/api/uploads/{filename}"
        conn.execute(
            "UPDATE recipes SET image_url = ?, images = ?, updated_at = ? WHERE id = ?",
            (url, json.dumps([url], ensure_ascii=False), datetime.now().isoformat(" "), rid),
        )
        print(f"  ✓ [{rid}] {name}: {url}")
    conn.commit()
    conn.close()
    print(f"\n完成：{len(results)} 个菜谱已换上动漫风插画")


if __name__ == "__main__":
    main()
