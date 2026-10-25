#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""程序化检测卡片文字溢出：给 cards_html/*.html 注入检测 JS，
Chrome dump-dom 执行后提取每张卡片各元素的溢出报告。"""

import re
import subprocess
import sys
from pathlib import Path

HTML_DIR = Path(__file__).resolve().parent / "cards_html"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

CHECK_JS = """
<script>
function __measure() {
  const out = [];
  const card = document.querySelector('.card');
  const cr = card.getBoundingClientRect();
  out.push('CARD ' + cr.width.toFixed(0) + 'x' + cr.height.toFixed(0));
  document.querySelectorAll('.stxt').forEach((el, i) => {
    const r = el.getBoundingClientRect();
    const clippedX = el.scrollWidth > el.clientWidth + 1;
    const clippedY = el.scrollHeight > el.clientHeight + 1;
    if (clippedX || clippedY)
      out.push('STEP' + (i+1) + ' CLIPPED sw=' + el.scrollWidth + ' cw=' + el.clientWidth
               + ' sh=' + el.scrollHeight + ' ch=' + el.clientHeight
               + ' right=' + (r.right).toFixed(0) + ' text=' + el.textContent.slice(0, 14));
  });
  document.querySelectorAll('.ing').forEach((el, i) => {
    const r = el.getBoundingClientRect();
    const sec = el.closest('.sec').getBoundingClientRect();
    if (r.bottom > sec.bottom + 1 || r.right > sec.right + 1)
      out.push('ING' + i + ' OUT-OF-SEC bottom=' + r.bottom.toFixed(0) + '/' + sec.bottom.toFixed(0)
               + ' text=' + el.textContent.slice(0, 14));
    if (el.scrollWidth > el.clientWidth + 1)
      out.push('ING' + i + ' CLIPPED text=' + el.textContent.slice(0, 14));
  });
  document.querySelectorAll('.sec').forEach((el, i) => {
    if (el.scrollHeight > el.clientHeight + 1)
      out.push('SEC' + i + ' V-OVERFLOW sh=' + el.scrollHeight + ' ch=' + el.clientHeight);
    if (el.scrollWidth > el.clientWidth + 1)
      out.push('SEC' + i + ' H-OVERFLOW sw=' + el.scrollWidth + ' cw=' + el.clientWidth);
    const r = el.getBoundingClientRect();
    if (r.bottom > 768 - 12 || r.right > 1024 - 12)
      out.push('SEC' + i + ' BEYOND-CARD bottom=' + r.bottom.toFixed(0) + ' right=' + r.right.toFixed(0));
  });
  const tip = document.querySelector('.tipbody');
  if (tip) {
    const r = tip.getBoundingClientRect();
    if (r.bottom > 768 - 12) out.push('TIP BEYOND-CARD bottom=' + r.bottom.toFixed(0));
  }
  const rep = document.createElement('pre');
  rep.id = 'ovreport';
  rep.textContent = out.length ? out.join('\\n') : 'CLEAN';
  rep.style.cssText = 'position:fixed;left:0;top:0;z-index:999;background:#fff;color:#000;font-size:12px;white-space:pre;';
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


def check(html_path: Path) -> str:
    html = html_path.read_text(encoding="utf-8")
    patched = html.replace("</body>", CHECK_JS + "</body>")
    tmp = html_path.with_name(html_path.stem + "_check.html")
    tmp.write_text(patched, encoding="utf-8")
    try:
        r = subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--dump-dom",
             "--virtual-time-budget=15000", tmp.resolve().as_uri()],
            capture_output=True, timeout=90, check=True,
        )
        dom = r.stdout.decode("utf-8", "ignore")
        m = re.search(r'<pre id="ovreport"[^>]*>(.*?)</pre>', dom, re.S)
        return m.group(1).strip() if m else "REPORT-NOT-FOUND"
    finally:
        tmp.unlink(missing_ok=True)


def main() -> None:
    files = sorted(HTML_DIR.glob("*.html"))
    files = [f for f in files if not f.stem.endswith("_check")]
    bad = 0
    for f in files:
        report = check(f)
        lines = [l for l in report.splitlines() if l and not l.startswith("CARD ")]
        status = "CLEAN" if not lines else "ISSUES"
        print(f"== {f.stem}: {status}")
        if lines:
            bad += 1
            print("\n".join(lines))
    print(f"\n{'ALL CLEAN' if bad == 0 else f'{bad} FILES WITH ISSUES'}")


if __name__ == "__main__":
    main()
