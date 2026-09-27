import os, time
from playwright.sync_api import sync_playwright
D="/tmp/claude-0/-home-user/9d1373ae-0961-5985-b2c8-adad08e8b8ed/scratchpad/pdp"
EXE="/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=EXE, args=["--no-sandbox"])
    ctx=b.new_context(viewport={"width":1400,"height":900}, offline=True)
    pg=ctx.new_page()
    errs=[]
    pg.on("pageerror", lambda e: errs.append(str(e)))
    t0=time.time()
    pg.goto(f"file://{D}/PDP_5N2927_Sample_Exam.html", wait_until="load")
    print("load", round(time.time()-t0,2))
    pg.wait_for_timeout(3000)
    pg.screenshot(path=f"{D}/shots/offline_Sample_Exam_name_screen.png")
    print("title:", pg.title()); print("nc-module:", repr(pg.text_content("#nc-module"))); print("nc-py:", pg.text_content("#nc-py"))
    pg.fill("#sname","Test Student"); pg.click("#btn-begin"); pg.wait_for_timeout(1000)
    print("app display:", pg.evaluate("getComputedStyle(document.getElementById('app')).display"))
    print("errors:", errs)
    b.close()
