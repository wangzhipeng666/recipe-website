#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成「手绘菜谱卡片」风格的菜谱图片（参考治愈系菜谱海报）：
奶油纸张底 + 手写字体标题 + 主食插画 + 食材准备 + 步骤 + 小贴士 + 拟人吉祥物 + 印章装饰。

主图插画复用 generate_anime_images.py 中的 SVG 绘制函数。
字体来自 scripts/fonts_local.css（站酷快乐体 + 马善政楷书，已本地化）。

用法：
    python3 scripts/generate_recipe_cards.py             # 全部生成并更新数据库
    python3 scripts/generate_recipe_cards.py --no-db     # 只出图到 scripts/cards_out/
    python3 scripts/generate_recipe_cards.py --only 麻婆豆腐
"""

import json
import shutil
import sqlite3
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_anime_images import DISHES, canvas, INK  # noqa: E402

PROJECT = Path(__file__).resolve().parent.parent
BACKEND = PROJECT / "backend"
UPLOADS = BACKEND / "uploads"
DB_PATH = BACKEND / "recipes.db"
HTML_DIR = PROJECT / "scripts" / "cards_html"
OUT_DIR = PROJECT / "scripts" / "cards_out"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

W, H = 1024, 768
PAPER = "#FAF2E0"
RED = "#C8452C"
YELLOW = "#F5C445"
GREEN = "#7BA05B"

# 数据库缺数据时的补充内容（仅用于卡片展示，不写回数据库）
FALLBACK = {
    "水煮菜": {
        "ingredients": ["时蔬/娃娃菜 1份", "水 适量", "盐 少许", "食用油 少许", "蒜 2瓣", "生抽 1勺"],
        "steps": ["蔬菜洗净沥干", "锅中水烧开，加少许盐和油", "下蔬菜烫1-2分钟至断生", "捞出装盘，配万能蘸水食用"],
    },
    "砂锅麻辣烫": {
        "ingredients": ["牛筋面 1份", "丸子 适量", "豆皮 适量", "海带 适量", "蘑菇 适量", "土豆 适量",
                        "菠菜 适量", "火锅底料 1块", "芝麻酱 2勺", "二八酱 2勺"],
    },
}

# ---------------------------------------------------------------- 小图标库

def _svg(inner: str, vb: str = "0 0 24 24") -> str:
    return f'<svg viewBox="{vb}" xmlns="http://www.w3.org/2000/svg">{inner}</svg>'


ING_ICONS: list[tuple[tuple[str, ...], str]] = [
    (("菜花", "花菜", "花椰菜"), _svg('<circle cx="9" cy="12" r="6.4" fill="#FFF6E1" stroke="#4A322A" stroke-width="1.6"/><circle cx="16" cy="9" r="5.6" fill="#FFF9EA" stroke="#4A322A" stroke-width="1.5"/><circle cx="15" cy="16" r="5.2" fill="#FFFDF4" stroke="#4A322A" stroke-width="1.5"/><circle cx="7" cy="9" r="2" fill="#D9A85C"/>')),
    (("五花肉", "肉馅", "猪肉", "肉末", "肥瘦"), _svg('<path d="M4 8c3-4 13-4 16 0 2 2.6 1 6-2 7.6-4 2-10 2-13-1C3.4 12.6 3 9.6 4 8Z" fill="#F2B8A0" stroke="#4A322A" stroke-width="1.6"/><path d="M6.5 9.5c3-2.4 9-2.4 11.6-.4" stroke="#FFF9F4" stroke-width="2.2" fill="none" stroke-linecap="round"/><path d="M7 13.5c3 1.6 8 1.6 10.4-.4" stroke="#E8927A" stroke-width="1.8" fill="none" stroke-linecap="round"/>')),
    (("米饭", "大米", "米粒"), _svg('<path d="M4 11h16l-2 8H6l-2-8Z" fill="#FFF7E8" stroke="#4A322A" stroke-width="1.6"/><ellipse cx="12" cy="11" rx="8" ry="3.4" fill="#FBE08A" stroke="#4A322A" stroke-width="1.4"/><circle cx="9" cy="10.6" r="1" fill="#E2A933"/><circle cx="14" cy="11.2" r="1" fill="#E2A933"/>')),
    (("胡萝卜", "萝卜"), _svg('<path d="M14.5 4.5c2.4 1 2.6 4 .6 6.2l-6.8 7.4c-1.8 2-4.8 1.2-4.2-1l4.6-9.4c1-2 3.6-4 5.8-3.2Z" fill="#E8763A" stroke="#4A322A" stroke-width="1.6"/><path d="M14.5 4.5l3.4-2.4M13 7.6l2.6-1" stroke="#7BA05B" stroke-width="2" stroke-linecap="round" fill="none"/>')),
    (("黄瓜",), _svg('<rect x="3" y="8.4" width="18" height="7.2" rx="3.6" fill="#7BA05B" stroke="#4A322A" stroke-width="1.6" transform="rotate(-18 12 12)"/><circle cx="9" cy="11.4" r="1.1" fill="#EAF4DE"/><circle cx="14.6" cy="10.4" r="1.1" fill="#EAF4DE"/>')),
    (("火腿", "香肠", "火腿肠"), _svg('<rect x="3" y="9" width="18" height="6.8" rx="3.4" fill="#F2A0A0" stroke="#4A322A" stroke-width="1.6"/><line x1="8" y1="9" x2="8" y2="15.8" stroke="#E2837B" stroke-width="1.4"/><line x1="13" y1="9" x2="13" y2="15.8" stroke="#E2837B" stroke-width="1.4"/>')),
    (("可乐",), _svg('<rect x="6" y="4" width="12" height="16" rx="3" fill="#D0392B" stroke="#4A322A" stroke-width="1.6"/><path d="M7 8h10" stroke="#fff" stroke-width="1.4" opacity=".7"/>')),
    (("豆腐",), _svg('<rect x="4" y="6" width="16" height="13" rx="3" fill="#FFF3D9" stroke="#4A322A" stroke-width="1.6"/><path d="M8 10h5" stroke="#E4CBA0" stroke-width="2" stroke-linecap="round"/>')),
    (("鸡翅", "公鸡", "鸡肉", "鸡胸"), _svg('<path d="M14 5c3.5 0 6 2.5 6 5.5S17.5 16 14 16H9c-2.2 0-4-1.6-4-3.7C5 9.6 7.5 5 14 5Z" fill="#C8873B" stroke="#4A322A" stroke-width="1.6"/><circle cx="5.6" cy="18" r="2" fill="#FDF3E3" stroke="#4A322A" stroke-width="1.4"/>')),
    (("肉馅", "猪肉", "肉末", "肥瘦"), _svg('<ellipse cx="12" cy="13" rx="8" ry="6" fill="#F2A9A0" stroke="#4A322A" stroke-width="1.6"/><circle cx="9" cy="12" r="1.3" fill="#E2837B"/><circle cx="14" cy="14" r="1.3" fill="#E2837B"/>')),
    (("蛋",), _svg('<ellipse cx="12" cy="12" rx="7.5" ry="9" fill="#FFE08A" stroke="#4A322A" stroke-width="1.6" transform="rotate(-14 12 12)"/><path d="M8.5 8.5q2-2 4-1" stroke="#FFF6D8" stroke-width="2" stroke-linecap="round" fill="none"/>')),
    (("香菇", "杏鲍菇", "菇"), _svg('<path d="M4 11c0-4 3.6-7 8-7s8 3 8 7c0 1.7-1.3 2.6-3 2.6H7c-1.7 0-3-.9-3-2.6Z" fill="#D9B26E" stroke="#4A322A" stroke-width="1.6"/><rect x="9.6" y="12.6" width="4.8" height="7" rx="2" fill="#F5E8CE" stroke="#4A322A" stroke-width="1.5"/>')),
    (("葱",), _svg('<circle cx="12" cy="12" r="8" fill="#8FCB6E" stroke="#4A322A" stroke-width="1.6"/><circle cx="12" cy="12" r="3.4" fill="#F2FFE3"/>')),
    (("韭菜", "香菜", "菠菜", "青菜", "时蔬", "蔬菜", "菜"), _svg('<path d="M12 21c-6-3-8-8-6-14 2 0 4 1 5 3 0-3 1-6 4-7 1 5 3 14-3 18Z" fill="#7BA05B" stroke="#4A322A" stroke-width="1.6"/>')),
    (("姜",), _svg('<path d="M6 15c-2-4 1-9 6-9 5 0 8 3 7 7-1 3-4 5-8 4l-3 3-2-2 2-3Z" fill="#EFD9A7" stroke="#4A322A" stroke-width="1.6"/>')),
    (("蒜",), _svg('<path d="M12 4c4 0 7 3 7 7 0 5-3 9-7 9s-7-4-7-9c0-4 3-7 7-7Z" fill="#FBF5E6" stroke="#4A322A" stroke-width="1.6"/><path d="M12 8v11" stroke="#D9CBB0" stroke-width="1.6"/>')),
    (("辣椒", "小米辣", "糊辣"), _svg('<path d="M17 4c1 4-1 12-6 15-3 1.7-6 .3-5.6-2C6 12 11 5 17 4Z" fill="#D14B33" stroke="#4A322A" stroke-width="1.6"/><path d="M17 4l2-1" stroke="#7BA05B" stroke-width="2.4" stroke-linecap="round"/>')),
    (("花椒", "胡椒", "孜然"), _svg('<circle cx="8" cy="10" r="3.4" fill="#96422B" stroke="#4A322A" stroke-width="1.4"/><circle cx="16" cy="8" r="2.6" fill="#96422B" stroke="#4A322A" stroke-width="1.4"/><circle cx="15" cy="16" r="3" fill="#B0553B" stroke="#4A322A" stroke-width="1.4"/>')),
    (("芝麻酱", "二八酱", "麻酱", "花生酱"), _svg('<path d="M4 11h16l-2 9H6l-2-9Z" fill="#E8CBA0" stroke="#4A322A" stroke-width="1.6"/><path d="M7 14c2-1.4 4 1.4 6 0s4 1.4 4 0" stroke="#B98F55" stroke-width="1.8" fill="none" stroke-linecap="round"/>')),
    (("豆瓣酱", "黄豆酱", "甜面酱", "火锅底料", "酱"), _svg('<path d="M6 8h12l1 11c0 1-1 2-2 2H7c-1 0-2-1-2-2L6 8Z" fill="#A0522D" stroke="#4A322A" stroke-width="1.6"/><rect x="7" y="4" width="10" height="4" rx="1.6" fill="#8B4513" stroke="#4A322A" stroke-width="1.5"/>')),
    (("生抽", "老抽", "酱油", "蚝油"), _svg('<rect x="8" y="6" width="8" height="14" rx="2.4" fill="#6B3A1F" stroke="#4A322A" stroke-width="1.6"/><rect x="10" y="2.6" width="4" height="4" rx="1.2" fill="#4A322A"/><rect x="9.6" y="9" width="2" height="7" rx="1" fill="#E8D4B8" opacity=".7"/>')),
    (("醋",), _svg('<rect x="8" y="7" width="8" height="14" rx="2.4" fill="#8A4A2B" stroke="#4A322A" stroke-width="1.6"/><rect x="10" y="3" width="4" height="4.6" rx="1.2" fill="#4A322A"/>')),
    (("料酒", "黄酒", "酒"), _svg('<rect x="9" y="8" width="6" height="13" rx="2" fill="#E8DFB0" stroke="#4A322A" stroke-width="1.6"/><rect x="10.6" y="3" width="2.8" height="5" fill="#4A322A"/>')),
    (("油",), _svg('<path d="M12 3c3 4.6 6 7.8 6 11a6 6 0 0 1-12 0c0-3.2 3-6.4 6-11Z" fill="#F2B84B" stroke="#4A322A" stroke-width="1.6"/><circle cx="10" cy="15" r="1.8" fill="#FFE9B0"/>')),
    (("盐", "糖", "味精", "鸡精"), _svg('<path d="M6 19c1-4 3-6 6-6s5 2 6 6H6Z" fill="#FFFFFF" stroke="#4A322A" stroke-width="1.6"/>')),
    (("芝麻", "花生碎", "花生"), _svg('<circle cx="8" cy="9" r="2.4" fill="#F5E5C0" stroke="#4A322A" stroke-width="1.3"/><circle cx="15" cy="12" r="2.4" fill="#F5E5C0" stroke="#4A322A" stroke-width="1.3"/><circle cx="10" cy="17" r="2.4" fill="#F5E5C0" stroke="#4A322A" stroke-width="1.3"/>')),
    (("面粉", "面", "淀粉"), _svg('<path d="M6 7h12l2 13H4L6 7Z" fill="#FFFDF6" stroke="#4A322A" stroke-width="1.6"/><path d="M8 12c2-1.6 4 1.6 6 0" stroke="#E4D9C2" stroke-width="1.8" fill="none" stroke-linecap="round"/>')),
    (("紫菜", "海带"), _svg('<path d="M5 6c2 2 4-2 7 0s5-2 7 0v12c-2 2-4-2-7 0s-5 2-7 0V6Z" fill="#3F6B4F" stroke="#4A322A" stroke-width="1.6"/>')),
    (("虾皮", "虾"), _svg('<path d="M4 12c4-5 12-5 16 0-4 5-12 5-16 0Z" fill="#F7B8A4" stroke="#4A322A" stroke-width="1.6"/><path d="M9 12h.01M13 12h.01" stroke="#4A322A" stroke-width="1.8" stroke-linecap="round"/>')),
    (("八角", "桂皮", "香叶", "白芷", "茴香"), _svg('<path d="M12 3l2 5 5 1-3.6 3.8L16 18l-4-2-4 2 .6-5.2L5 9l5-1 2-5Z" fill="#B0703A" stroke="#4A322A" stroke-width="1.5"/>')),
    (("丸",), _svg('<circle cx="12" cy="13" r="7.5" fill="#FFF7E8" stroke="#4A322A" stroke-width="1.6"/><path d="M9 10q3-2 6 0" stroke="#E8D9BC" stroke-width="1.8" fill="none" stroke-linecap="round"/>')),
    (("豆皮", "腐竹"), _svg('<rect x="5" y="6" width="14" height="12" rx="2" fill="#EFD9A7" stroke="#4A322A" stroke-width="1.6"/><path d="M8 9h8M8 13h8" stroke="#D9BE8C" stroke-width="1.5"/>')),
    (("土豆",), _svg('<ellipse cx="12" cy="12" rx="8" ry="6.4" fill="#E8C98F" stroke="#4A322A" stroke-width="1.6"/><circle cx="10" cy="11" r="1" fill="#C8A86B"/><circle cx="15" cy="14" r="1" fill="#C8A86B"/>')),
    (("番茄",), _svg('<circle cx="12" cy="14" r="7.5" fill="#E8563A" stroke="#4A322A" stroke-width="1.6"/><path d="M12 6l1.6-2M12 6l-1.6-2M12 6c-2-1-4-.4-4-.4S10 8 12 6c2 2 4-.4 4-.4S14 5 12 6Z" fill="#7BA05B" stroke="#4A322A" stroke-width="1.2"/>')),
]

ING_FALLBACK_ICON = _svg('<circle cx="12" cy="12" r="7.5" fill="#F2C98A" stroke="#4A322A" stroke-width="1.6"/>')


def ing_icon(text: str) -> str:
    for keys, svg in ING_ICONS:
        if any(k in text for k in keys):
            return svg
    return ING_FALLBACK_ICON


STEP_ICONS: list[tuple[tuple[str, ...], str]] = [
    (("切", "剁", "划花刀", "洗净", "擦干", "挤干", "撕", "掰"), _svg('<rect x="3" y="10" width="18" height="9" rx="2" fill="#E8C98F" stroke="#4A322A" stroke-width="1.6"/><path d="M6 7l9-3 2 4-9 3-2-4Z" fill="#B9C4CE" stroke="#4A322A" stroke-width="1.6"/>')),
    (("腌", "备用", "泡", "醒面", "揉", "解冻"), _svg('<path d="M5 8h14l-1.4 11a2 2 0 0 1-2 1.8H8.4a2 2 0 0 1-2-1.8L5 8Z" fill="#CFE3F0" stroke="#4A322A" stroke-width="1.6"/><path d="M5 8c1.4 2 3 0 4.4 1.6S12 12 13.6 10 16 8 19 8" stroke="#9FC2D8" stroke-width="1.5" fill="none"/>')),
    (("炒", "翻炒", "爆香", "炒香"), _svg('<path d="M3 10h15c2 0 3 1.4 3 3.2S19.6 17 17.4 17H8L3 10Z" fill="#5A6570" stroke="#4A322A" stroke-width="1.6"/><path d="M8 17l-2 3M13 17l-2 3" stroke="#4A322A" stroke-width="1.8" stroke-linecap="round"/><path d="M9 6c0-1.4 1.6-1.4 1.6-2.8M13.4 6c0-1.4 1.6-1.4 1.6-2.8" stroke="#E8763A" stroke-width="1.8" stroke-linecap="round" fill="none"/>')),
    (("煎", "炸", "烤", "空气炸", "收汁"), _svg('<rect x="3" y="9" width="18" height="7" rx="3.5" fill="#4A4441" stroke="#4A322A" stroke-width="1.6"/><path d="M7 20c1-1.6 2-1.6 2.6 0M12 20c1-1.6 2-1.6 2.6 0M17 20c1-1.6 2-1.6 2.6 0" stroke="#E8763A" stroke-width="1.8" stroke-linecap="round" fill="none"/><circle cx="9" cy="12.4" r="1.2" fill="#F2C94C"/><circle cx="14.6" cy="12.4" r="1.2" fill="#F2C94C"/>')),
    (("煮", "炖", "焖", "熬", "烧开", "汆", "焯", "烫", "蒸熟", "蒸"), _svg('<path d="M4 9h16v7a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3V9Z" fill="#D96C4F" stroke="#4A322A" stroke-width="1.6"/><rect x="3" y="7" width="18" height="3" rx="1.5" fill="#B9503A" stroke="#4A322A" stroke-width="1.6"/><path d="M8 3.4c0-1.2 1.4-1.2 1.4-2.4M12.6 3.4c0-1.2 1.4-1.2 1.4-2.4" stroke="#9AA5AE" stroke-width="1.8" stroke-linecap="round" fill="none"/>')),
    (("拌", "搅", "混合", "调", "勾芡", "倒入", "淋入", "加", "撒", "捞出", "盛出", "出锅", "放"), _svg('<path d="M14.6 3.6L8 14h5l-2.4 6.4L18 9h-5l1.6-5.4Z" fill="#F2C94C" stroke="#4A322A" stroke-width="1.6" stroke-linejoin="round"/>')),
]
STEP_FALLBACK_ICON = _svg('<circle cx="12" cy="12" r="8" fill="#F2C98A" stroke="#4A322A" stroke-width="1.6"/>')


def step_icon(text: str) -> str:
    for keys, svg in STEP_ICONS:
        if any(k in text for k in keys):
            return svg
    return STEP_FALLBACK_ICON


# ---------------------------------------------------------------- 吉祥物

def _face(cx: float, cy: float, s: float = 1.0, smile: bool = True) -> str:
    eye = 2.2 * s
    return (
        f'<circle cx="{cx - 9 * s}" cy="{cy}" r="{eye}" fill="{INK}"/>'
        f'<circle cx="{cx + 9 * s}" cy="{cy}" r="{eye}" fill="{INK}"/>'
        f'<circle cx="{cx - 9 * s - eye}" cy="{cy - eye - 1}" r="{1.4 * s}" fill="#fff" opacity=".9"/>'
        f'<circle cx="{cx + 9 * s - eye}" cy="{cy - eye - 1}" r="{1.4 * s}" fill="#fff" opacity=".9"/>'
        f'<circle cx="{cx - 15 * s}" cy="{cy + 7 * s}" r="{3.4 * s}" fill="#F2A9A0" opacity=".85"/>'
        f'<circle cx="{cx + 15 * s}" cy="{cy + 7 * s}" r="{3.4 * s}" fill="#F2A9A0" opacity=".85"/>'
        + (f'<path d="M {cx - 4 * s} {cy + 5 * s} q {4 * s} {3.4 * s} {8 * s} 0" fill="none" stroke="{INK}" stroke-width="{1.8 * s}" stroke-linecap="round"/>' if smile else "")
    )


def mascot(kind: str) -> str:
    s = 96
    o = f'stroke="{INK}" stroke-width="3" stroke-linejoin="round"'
    if kind == "tofu":
        body = (f'<rect x="18" y="26" width="60" height="48" rx="10" fill="#FFF6DE" {o}/>'
                f'<rect x="24" y="32" width="26" height="12" rx="6" fill="#FFE9B8"/>'
                + _face(48, 52))
    elif kind == "drumstick":
        body = (f'<path d="M62 16c14 4 20 16 16 27-4 11-16 16-27 14l-16 16-9-9 16-16c-3-12 4-24 20-32Z" fill="#C8873B" {o}/>'
                f'<path d="M40 26c6-5 14-6 20-3" stroke="#E8A85C" stroke-width="5" stroke-linecap="round" fill="none"/>'
                + _face(56, 36))
    elif kind == "egg":
        body = (f'<ellipse cx="48" cy="52" rx="26" ry="31" fill="#FFE08A" {o} transform="rotate(-10 48 52)"/>'
                f'<path d="M32 34q8-8 16-4" stroke="#FFF6D8" stroke-width="6" stroke-linecap="round" fill="none"/>'
                + _face(48, 54))
    elif kind == "mushroom":
        body = (f'<path d="M14 46c0-17 15-28 34-28s34 11 34 28c0 7-5.6 11-12.6 11H26.6C19.6 57 14 53 14 46Z" fill="#D9B26E" {o}/>'
                f'<circle cx="34" cy="38" r="5" fill="#C89B58"/><circle cx="58" cy="34" r="6.4" fill="#C89B58"/><circle cx="66" cy="46" r="4.4" fill="#C89B58"/>'
                f'<rect x="39" y="55" width="18" height="22" rx="8" fill="#F5E8CE" {o}/>'
                + _face(48, 64, 0.9))
    elif kind == "chili":
        body = (f'<path d="M70 14c6 20-4 52-30 64-13 6-24-1-22-11C21 46 44 20 70 14Z" fill="#D14B33" {o}/>'
                f'<path d="M70 14l9-6" stroke="#7BA05B" stroke-width="7" stroke-linecap="round"/>'
                + _face(48, 48))
    elif kind == "bokchoy":
        body = (f'<path d="M46 92c-26-13-34-34-26-58 8 0 15 4 19 11 0-11 4-22 15-26 4 19 12 58-8 73Z" fill="#7BA05B" {o}/>'
                f'<path d="M36 88c-10-8-13-22-9-34" stroke="#5E8A45" stroke-width="4" stroke-linecap="round" fill="none"/>'
                f'<path d="M32 78C24 70 22 58 26 48" stroke="#FFF7E0" stroke-width="9" stroke-linecap="round" fill="none"/>'
                + _face(48, 52))
    elif kind == "chicken":
        body = (f'<ellipse cx="48" cy="52" rx="30" ry="27" fill="#FFF9EC" {o}/>'
                f'<path d="M40 24c2-6 8-8 10-2s-4 6-4 6" fill="#E8563A" {o}/>'
                f'<path d="M74 34c6 0 9 4 8 8M82 46c-4-1-7 1-8 4" stroke="#F2A9A0" stroke-width="5" stroke-linecap="round" fill="none"/>'
                f'<path d="M30 62c-6 4-14 3-16-2 5-6 12-6 16-2Z" fill="#F2A9A0" {o}/>'
                + _face(48, 48))
    elif kind == "pocket":
        body = (f'<path d="M16 52c0-22 15-34 32-34s32 12 32 34c0 16-14 26-32 26S16 68 16 52Z" fill="#F2CE82" {o}/>'
                f'<path d="M24 40c8-10 18-14 28-13" stroke="#E0B264" stroke-width="6" stroke-linecap="round" fill="none"/>'
                f'<ellipse cx="34" cy="62" rx="6" ry="4.6" fill="#C08436"/><ellipse cx="60" cy="58" rx="5" ry="4" fill="#C08436"/>'
                + _face(48, 50))
    elif kind == "cauliflower":
        body = (f'<path d="M20 58c-8 0-12-8-8-14-6-4-4-14 3-16-1-9 8-14 15-10 4-7 16-7 20 0 7-4 16 1 15 10 7 2 9 12 3 16 4 6 0 14-8 14H20Z" '
                f'fill="#FFF9EA" {o}/>'
                f'<circle cx="30" cy="34" r="8" fill="#FFFDF4"/><circle cx="60" cy="28" r="9" fill="#FFFDF4"/>'
                f'<circle cx="52" cy="44" r="8" fill="#FFFDF4"/>'
                f'<circle cx="26" cy="28" r="2.6" fill="#D9A85C"/><circle cx="66" cy="40" r="2.4" fill="#C89355"/>'
                f'<path d="M38 82v8M56 82v8" stroke="#8A6A55" stroke-width="5" stroke-linecap="round"/>'
                f'<ellipse cx="48" cy="90" rx="24" ry="5" fill="#8A5A33" opacity=".18"/>'
                + _face(48, 44, 0.95))
    elif kind == "ricebowl":
        body = (f'<ellipse cx="48" cy="40" rx="34" ry="14" fill="#FBE08A" {o}/>'
                f'<path d="M22 38q4-8 12-6t14-8 14 8q8-2 12 6l-6 4q-16 6-40 0Z" fill="#F6D568" {o}/>'
                f'<circle cx="42" cy="32" r="2.6" fill="#E2A933"/><circle cx="56" cy="34" r="2.6" fill="#E2A933"/>'
                f'<path d="M14 44h68c0 20-14 32-34 32S14 64 14 44Z" fill="#C8493B" {o}/>'
                f'<ellipse cx="48" cy="44" rx="34" ry="10" fill="#E9E2D6" stroke="{INK}" stroke-width="3"/>'
                + _face(48, 62, 0.95))
    else:  # clay pot
        body = (f'<path d="M12 40h72c0 24-14 38-36 38S12 64 12 40Z" fill="#3A3430" {o}/>'
                f'<ellipse cx="48" cy="40" rx="36" ry="10" fill="#544D48" {o}/>'
                f'<path d="M10 44q-10 4 0 12M86 44q10 4 0 12" stroke="{INK}" stroke-width="9" stroke-linecap="round" fill="none"/>'
                + _face(48, 60, 0.95))
    return (f'<svg width="{s}" height="{s}" viewBox="0 0 96 96" xmlns="http://www.w3.org/2000/svg">'
            f'<ellipse cx="48" cy="88" rx="30" ry="6" fill="#8A5A33" opacity=".18"/>{body}</svg>')


MASCOTS = {
    "mapo": "tofu", "wings": "drumstick", "soup": "egg", "sauce": "mushroom",
    "skewer": "mushroom", "dip": "chili", "greens": "bokchoy", "chilioil": "chili",
    "chicken": "chicken", "pocket": "pocket", "mala": "claypot", "drypot": "cauliflower",
}

# ---------------------------------------------------------------- 装饰件

def heart(x, y, s, color="#E8763A", op=0.85):
    return (f'<div style="position:absolute;left:{x}px;top:{y}px;width:{s}px;height:{s}px;'
            f'opacity:{op};transform:rotate({(x * 7) % 40 - 20}deg)">'
            f'<svg viewBox="0 0 24 24" width="100%" height="100%"><path d="M12 21C5 15 2 11 2 7.3 2 4.4 4.4 2 7.3 2 9.2 2 11 3 12 4.6 13 3 14.8 2 16.7 2 19.6 2 22 4.4 22 7.3c0 3.7-3 7.7-10 13.7Z" fill="{color}"/></svg></div>')


def star4(x, y, s, color="#F2C94C", op=0.9):
    k = 0.22
    return (f'<div style="position:absolute;left:{x}px;top:{y}px;width:{s}px;height:{s}px;opacity:{op}">'
            f'<svg viewBox="-1.2 -1.2 2.4 2.4" width="100%" height="100%"><path d="M0 -1 Q {k} -{k} 1 0 Q {k} {k} 0 1 Q -{k} {k} -1 0 Q -{k} -{k} 0 -1 Z" fill="{color}"/></svg></div>')


# ---------------------------------------------------------------- HTML


def build_html(rid, name, key, category, difficulty, cook_time, ingredients, steps, tips,
               step_mode: str = "normal", ing_font: float = 14.0) -> str:
    hero_svg = canvas(key, DISHES[name][1]())
    seal_char = name[0]

    # 食材 chips：全部完整显示，不截断
    chips = []
    for it in ingredients:
        text = it.strip()
        chips.append(
            f'<div class="ing">{span_icon(ing_icon(text))}<span>{text}</span></div>'
        )

    # 步骤 rows：全文显示，仅按自适应模式调整字号/徽章
    MODES = {
        "normal": {"cls": "", "badge": 34},
        "many":   {"cls": "many", "badge": 30},
        "lots":   {"cls": "lots", "badge": 26},
        "tiny":   {"cls": "tiny", "badge": 24},
    }
    m = MODES[step_mode]
    steps_cls = "steps tight" if step_mode in ("lots", "tiny") else "steps"
    rows = []
    for i, st in enumerate(steps, 1):
        st = st.strip()
        rows.append(
            f'<div class="step {m["cls"]}">'
            f'<div class="badge" style="width:{m["badge"]}px;height:{m["badge"]}px;'
            f'font-size:{m["badge"] * 0.55}px">{i}</div>'
            f'{span_icon(step_icon(st))}'
            f'<span class="stxt">{st}</span></div>'
        )

    # 小贴士便签（放在左栏照片下方）
    tip_html = ""
    if tips:
        tip_html = (
            f'<div class="tipnote"><div class="tiphead">✦ 小贴士</div>'
            f'<div class="tipbody">{tips}</div></div>'
        )

    chips_html = "".join(chips)
    rows_html = "".join(rows)
    style_ing_font = f".ing span{{font-size:{ing_font}px}}"
    masc = mascot(MASCOTS[key])

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<link rel="stylesheet" href="../fonts_local.css">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ width:{W}px; height:{H}px; overflow:hidden;
    background:
      radial-gradient(circle at 18% 12%, rgba(255,255,255,.5) 0 26px, transparent 27px),
      radial-gradient(circle at 85% 85%, rgba(255,255,255,.4) 0 34px, transparent 35px),
      radial-gradient(rgba(210,190,150,.38) 1.2px, transparent 1.3px),
      radial-gradient(rgba(210,190,150,.28) 1.2px, transparent 1.3px),
      {PAPER};
    background-size: auto, auto, 26px 26px, 34px 34px, auto;
    background-position: 0 0, 0 0, 0 0, 13px 17px, 0 0; }}
  .card {{ position:relative; width:{W}px; height:{H}px; padding:22px 26px;
    font-family:"ZCOOL KuaiLe","Hiragino Sans GB",sans-serif; color:{INK};
    display:flex; flex-direction:column; }}
  .frame {{ position:absolute; inset:12px; border:2.5px dashed rgba(200,69,44,.42);
    border-radius:22px; pointer-events:none; }}
  .topzone {{ display:flex; gap:20px; align-items:stretch; }}
  .leftzone {{ flex:1; min-width:0; display:flex; flex-direction:column; gap:12px; }}
  .rightzone {{ width:312px; flex:none; display:flex; flex-direction:column; gap:14px;
    align-items:center; }}
  .head {{ display:flex; align-items:center; gap:16px; }}
  .titleblock {{ flex:1; min-width:0; }}
  h1 {{ font-size:54px; line-height:1.05; letter-spacing:3px; font-weight:400; }}
  .sub {{ display:flex; gap:10px; align-items:center; margin-top:8px; }}
  .chip {{ display:flex; align-items:center; gap:5px; padding:3px 12px; border-radius:999px;
    font-size:16px; border:2px solid rgba(74,50,42,.35); background:rgba(255,251,240,.8); }}
  .chip.hot {{ border-color:{RED}; color:{RED}; }}
  .hero {{ position:relative; width:312px; flex:none; }}
  .blob {{ position:absolute; inset:-15px; z-index:0; }}
  .blob i {{ position:absolute; border-radius:50%; filter:blur(15px); }}
  .heroframe {{ position:relative; z-index:1; background:#FFFBF0; border:3px solid {INK};
    border-radius:16px; padding:7px; box-shadow:3px 4px 0 rgba(74,50,42,.18);
    transform:rotate(.9deg); overflow:hidden; }}
  .heroframe svg {{ width:100%; height:auto; display:block; }}
  .tape {{ position:absolute; z-index:3; width:92px; height:24px; background:rgba(245,196,69,.72);
    border:1.5px dashed rgba(74,50,42,.4); top:-11px; left:20px; transform:rotate(-5deg); }}
  .seal {{ position:absolute; z-index:3; right:-12px; bottom:-12px; width:74px; height:74px;
    border-radius:13px; background:{RED}; color:#FFF6E8; display:flex; align-items:center;
    justify-content:center; font-size:40px; transform:rotate(-6deg);
    box-shadow:2px 3px 0 rgba(74,50,42,.25);
    outline:2px solid rgba(200,69,44,.35); outline-offset:3px; }}
  .tipnote {{ position:relative; z-index:1; width:100%; background:rgba(245,196,69,.32);
    border:2px dashed rgba(200,69,44,.5); border-radius:12px; padding:8px 12px 10px;
    transform:rotate(-.7deg); }}
  .tiphead {{ font-size:16px; color:{RED}; margin-bottom:2px; }}
  .tipbody {{ font-family:"Ma Shan Zheng","ZCOOL KuaiLe",serif; font-size:16px;
    line-height:1.36; color:#8A5A2B; }}
  .sec {{ background:rgba(255,251,240,.86); border:2.5px solid rgba(74,50,42,.85);
    border-radius:16px; padding:10px 14px 12px; position:relative; overflow:hidden;
    flex:none; }}
  .sec.stepsec {{ flex:1 1 0; min-height:0; display:flex; flex-direction:column;
    margin-top:12px; }}
  .sectitle {{ display:flex; align-items:center; gap:9px; font-size:24px; color:{RED};
    margin-bottom:8px; }}
  .sectitle .line {{ flex:1; height:3px; border-radius:2px;
    background:repeating-linear-gradient(90deg, rgba(200,69,44,.4) 0 12px, transparent 12px 18px); }}
  .ings {{ display:flex; flex-wrap:wrap; gap:6px 8px; }}
  .ing {{ display:flex; align-items:center; gap:5px; padding:3px 10px 3px 6px;
    background:#FFF; border:1.8px solid rgba(74,50,42,.8); border-radius:999px;
    font-size:14px; white-space:nowrap; }}
  .ing svg {{ width:20px; height:20px; flex:none; }}
  .ing span {{ min-width:0; }}
  .steps {{ display:flex; flex-direction:column; gap:7px; }}
  .step {{ display:flex; align-items:flex-start; gap:10px; min-height:0; }}
  .step svg {{ width:24px; height:24px; flex:none; margin-top:3px; }}
  .badge {{ flex:none; border-radius:50%; background:{YELLOW}; border:2.5px solid {INK};
    color:{INK}; display:flex; align-items:center; justify-content:center; font-size:18px; margin-top:2px; }}
  .stxt {{ font-size:15px; line-height:1.34; padding-top:4px; min-width:0; }}
  .step.many .stxt {{ font-size:14px; line-height:1.3; padding-top:3px; }}
  .step.lots .stxt {{ font-size:13px; line-height:1.26; padding-top:3px; }}
  .step.tiny .stxt {{ font-size:12px; line-height:1.22; padding-top:2px; }}
  .step.tiny svg {{ width:19px; height:19px; margin-top:2px; }}
  .step.tiny {{ gap:7px; }}
  .step.lots svg {{ width:21px; height:21px; margin-top:2px; }}
  .step.lots {{ gap:8px; }}
  .steps.tight {{ gap:5px; }}
  .stepsec .steps {{ flex:1; justify-content:space-between; }}
  {style_ing_font}
</style></head>
<body><div class="card">
  <div class="frame"></div>
  {heart(30, 122, 16)}{heart(981, 330, 13, "#E8763A", .7)}{heart(935, 742, 14, "#F2A9A0", .8)}
  {star4(34, 300, 14)}{star4(986, 560, 12)}{star4(300, 748, 11, "#E8763A", .75)}{star4(680, 26, 12)}
  <div class="topzone">
    <div class="leftzone">
      <div class="head">
        {masc}
        <div class="titleblock">
          <h1>{name}</h1>
          <div class="sub">
            <div class="chip hot">★ {difficulty or "简单"}</div>
            <div class="chip">⏱ {cook_time or "15分钟"}</div>
            <div class="chip" style="color:{GREEN}">{category}</div>
          </div>
        </div>
      </div>
      <div class="sec">
        <div class="sectitle">🧺 食材准备<div class="line"></div></div>
        <div class="ings">{chips_html}</div>
      </div>
    </div>
    <div class="rightzone">
      <div class="hero">
        <div class="blob">
          <i style="left:2%;top:14%;width:180px;height:115px;background:#F5C445;opacity:.5"></i>
          <i style="right:0%;bottom:16%;width:200px;height:130px;background:#F2A9A0;opacity:.42"></i>
          <i style="left:24%;top:60%;width:150px;height:95px;background:#9FC98A;opacity:.4"></i>
        </div>
        <div class="heroframe">{hero_svg}</div>
        <div class="tape"></div>
        <div class="seal">{seal_char}</div>
      </div>
      {tip_html}
    </div>
  </div>
  <div class="sec stepsec">
    <div class="sectitle">🍳 做法步骤<div class="line"></div></div>
    <div class="{steps_cls}">{rows_html}</div>
  </div>
</div></body></html>"""


def span_icon(svg: str) -> str:
    return svg


# 溢出实测：注入 JS 用 Chrome 实际渲染后测量各区块是否溢出
MEASURE_JS = """
<script>
function __measure() {
  const out = [];
  document.querySelectorAll('.sec').forEach((el, i) => {
    if (el.scrollHeight > el.clientHeight + 1) out.push('SEC' + i + ':V:' + (el.scrollHeight - el.clientHeight));
    if (el.scrollWidth > el.clientWidth + 1) out.push('SEC' + i + ':H:' + (el.scrollWidth - el.clientWidth));
  });
  document.querySelectorAll('.stxt, .ing span').forEach((el) => {
    if (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1)
      out.push('TXT:' + el.textContent.slice(0, 10));
  });
  document.querySelectorAll('.tipnote, .heroframe, .topzone').forEach((el) => {
    const r = el.getBoundingClientRect();
    if (r.bottom > 768 - 12) out.push('BOX:' + el.className.split(' ')[0] + ':B:' + r.bottom.toFixed(0));
    if (r.right > 1024 - 12) out.push('BOX:' + el.className.split(' ')[0] + ':R:' + r.right.toFixed(0));
  });
  const rep = document.createElement('pre');
  rep.id = 'ovreport';
  rep.textContent = out.length ? out.join('|') : 'CLEAN';
  rep.style.cssText = 'position:fixed;left:0;top:0;z-index:999;background:#fff;font-size:12px';
  document.body.appendChild(rep);
}
if (document.fonts && document.fonts.ready) {
  let done = false;
  document.fonts.ready.then(() => { if (!done) { done = true; __measure(); } });
  setTimeout(() => { if (!done) { done = true; __measure(); } }, 8000);
} else {
  window.addEventListener('load', () => setTimeout(__measure, 3000));
}
</script>
"""


def measure_overflow(html_path: Path) -> str:
    """返回 'CLEAN' 或溢出描述串。"""
    html = html_path.read_text(encoding="utf-8")
    tmp = html_path.with_name(html_path.stem + "_m.html")
    tmp.write_text(html.replace("</body>", MEASURE_JS + "</body>"), encoding="utf-8")
    try:
        import re as _re
        r = subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--dump-dom",
             "--virtual-time-budget=15000", tmp.resolve().as_uri()],
            capture_output=True, timeout=90, check=True,
        )
        dom = r.stdout.decode("utf-8", "ignore")
        m = _re.search(r'<pre id="ovreport"[^>]*>(.*?)</pre>', dom, _re.S)
        return m.group(1).strip() if m else "MEASURE-FAILED"
    finally:
        tmp.unlink(missing_ok=True)


# ---------------------------------------------------------------- 主流程


def html_to_png(html_path: Path, png_path: Path) -> None:
    cmd = [
        CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        f"--screenshot={png_path}", f"--window-size={W},{H}",
        "--force-device-scale-factor=2", "--virtual-time-budget=20000",
        html_path.resolve().as_uri(),
    ]
    subprocess.run(cmd, capture_output=True, timeout=120, check=True)
    if not png_path.exists():
        raise RuntimeError(f"Chrome 未生成 {png_path}")


def main() -> None:
    args = sys.argv[1:]
    no_db = "--no-db" in args
    only = args[args.index("--only") + 1:] if "--only" in args else None

    HTML_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cats = {r["id"]: r["name"] for r in conn.execute("SELECT id, name FROM categories")}
    rows = conn.execute(
        "SELECT id, name, category_id, ingredients, steps, difficulty, cook_time, tips "
        "FROM recipes ORDER BY id"
    ).fetchall()

    results = []
    for r in rows:
        name = r["name"]
        if only and name not in only:
            continue
        if name not in DISHES:
            print(f"!! 跳过（无插画函数）：{name}")
            continue
        key = DISHES[name][0]
        try:
            ingredients = json.loads(r["ingredients"] or "[]")
        except json.JSONDecodeError:
            ingredients = []
        try:
            steps = json.loads(r["steps"] or "[]")
        except json.JSONDecodeError:
            steps = []
        fb = FALLBACK.get(name, {})
        if not ingredients:
            ingredients = fb.get("ingredients", ["时令食材 适量"])
        if not steps:
            steps = fb.get("steps", ["用心制作即可"])

        html_path = HTML_DIR / f"{key}.html"
        png_path = OUT_DIR / f"{key}.png"
        # 自适应：normal -> many -> lots -> tiny（仅调字号排版，不截断文字）
        step_mode, ing_font = "normal", 14.0 if len(ingredients) <= 9 else 13.0
        for attempt in range(6):
            html = build_html(
                r["id"], name, key, cats.get(r["category_id"], "家常味"),
                r["difficulty"], r["cook_time"], ingredients, steps,
                (r["tips"] or "").strip(), step_mode, ing_font,
            )
            html_path.write_text(html, encoding="utf-8")
            report = measure_overflow(html_path)
            if report == "CLEAN":
                break
            if "SEC0" in report and ing_font > 11.5:
                ing_font -= 1.0  # 食材区溢出：缩小胶囊字号
            elif step_mode != "tiny":
                step_mode = {"normal": "many", "many": "lots", "lots": "tiny"}[step_mode]
            else:
                print(f"  !! {name} 即使 tiny 模式仍报溢出：{report}")
                break
        html_to_png(html_path, png_path)
        mode_tag = "" if step_mode == "normal" else f" [{step_mode}|{ing_font:g}]"
        print(f"  ✓ {name}{mode_tag} -> {png_path.name} ({png_path.stat().st_size // 1024} KB)")
        results.append((r["id"], name, png_path))

    if no_db:
        print(f"\n完成：{len(results)} 张卡片输出到 {OUT_DIR}（未改动数据库）")
        conn.close()
        return

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = DB_PATH.with_name(f"recipes.db.bak-cards-{stamp}")
    shutil.copy2(DB_PATH, backup)
    print(f"\n已备份数据库 -> {backup.name}")

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
    print(f"\n完成：{len(results)} 个菜谱已换上菜谱卡片插画")


if __name__ == "__main__":
    main()
