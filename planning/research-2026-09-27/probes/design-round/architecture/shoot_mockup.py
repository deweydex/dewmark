import json, sys
from playwright.sync_api import sync_playwright
URL = "file:///home/user/dewmark/planning/mockups/teacher-studio.html"
OUT = "/tmp/claude-0/-home-user/9d1373ae-0961-5985-b2c8-adad08e8b8ed/scratchpad/design-round/architecture/shots/"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--headless=new"])
    for scheme in ["light", "dark"]:
        for w, h in [(1440, 900), (1000, 800), (390, 844)]:
            ctx = b.new_context(viewport={"width": w, "height": h}, color_scheme=scheme, offline=True)
            reqs, errs = [], []
            ctx.on("request", lambda r: reqs.append(r.url) if not r.url.startswith(("file:", "data:", "blob:")) else None)
            pg = ctx.new_page()
            pg.on("console", lambda m: errs.append(m.text) if m.type in ("error", "warning") else None)
            pg.on("pageerror", lambda e: errs.append("PAGEERROR " + str(e)))
            pg.goto(URL); pg.wait_for_timeout(2200)
            res = {}
            for screen in ["home", "editor", "issue"]:
                pg.click(f'.mock nav button[data-go="{screen}"]'); pg.wait_for_timeout(700)
                sw = pg.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
                res[screen] = sw
                pg.screenshot(path=f"{OUT}{scheme}-{w}-{screen}.png", full_page=(screen != "editor" or w < 800))
            print(scheme, w, res, "reqs:", reqs, "errs:", errs[:3])
            ctx.close()
    b.close()
