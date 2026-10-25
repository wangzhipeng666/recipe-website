#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 Google Fonts 下载站酷快乐体 + 马善政楷书，改写为本地 @font-face CSS。"""

import re
import urllib.request
from pathlib import Path

FONTS_DIR = Path(__file__).resolve().parent / "fonts"
CSS_URL = (
    "https://fonts.googleapis.com/css2"
    "?family=Ma+Shan+Zheng&family=ZCOOL+KuaiLe&display=swap"
)
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


def main() -> None:
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(CSS_URL, headers={"User-Agent": UA})
    css = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    urls = sorted(set(re.findall(r"url\((https://[^)]+)\)", css)))
    print(f"css2 返回 {len(urls)} 个字体分片，开始下载…")
    for i, u in enumerate(urls):
        name = u.rsplit("/", 1)[-1]
        # 加序号前缀避免不同 family 的同名分片冲突
        local = f"{i:03d}-{name}"
        dest = FONTS_DIR / local
        if not dest.exists():
            r = urllib.request.Request(u, headers={"User-Agent": UA})
            dest.write_bytes(urllib.request.urlopen(r, timeout=30).read())
        css = css.replace(u, f"fonts/{local}")
    (FONTS_DIR.parent / "fonts_local.css").write_text(css, encoding="utf-8")
    print(f"完成：{len(urls)} 个文件 -> {FONTS_DIR}，CSS -> scripts/fonts_local.css")


if __name__ == "__main__":
    main()
