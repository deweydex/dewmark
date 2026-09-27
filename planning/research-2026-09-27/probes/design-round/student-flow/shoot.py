import asyncio, sys
from playwright.async_api import async_playwright
URL = "file:///home/user/dewmark/planning/mockups/student-start.html"
EXE = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=EXE, args=["--no-sandbox"])
        results = []
        for (w,h,scheme,tag) in [(1280,900,"light","desk-light"),(390,844,"dark","phone-dark")]:
            ctx = await b.new_context(viewport={"width":w,"height":h}, color_scheme=scheme, device_scale_factor=1)
            pg = await ctx.new_page()
            errs=[]; reqs=[]
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.on("console", lambda m: errs.append("console:"+m.type+":"+m.text) if m.type in ("error","warning") else None)
            pg.on("request", lambda r: reqs.append(r.url) if not r.url.startswith("file:") and not r.url.startswith("data:") else None)
            await pg.goto(URL)
            await pg.fill("#fName","Aoife Byrne"); await pg.fill("#fNum","D00123456")
            await pg.screenshot(path=f"{tag}-1.png", full_page=True)
            await pg.click("#toSettings")
            if tag=="phone-dark":
                await pg.check('input[name=font][value=dyslexic]'); 
                await pg.fill("#sSize","20"); await pg.dispatch_event("#sSize","input")
            await pg.screenshot(path=f"{tag}-2.png", full_page=True)
            await pg.click('#s2 [data-go="3"]')
            await pg.wait_for_timeout(4000)
            await pg.click("#chooseFile"); await pg.wait_for_timeout(900)
            await pg.screenshot(path=f"{tag}-3.png", full_page=True)
            await pg.wait_for_timeout(14000)
            await pg.click("#beginBtn"); await pg.wait_for_timeout(1500)
            await pg.click("#runBtn"); await pg.wait_for_timeout(600)
            await pg.fill("#stdinBox","3"); await pg.press("#stdinBox","Enter"); await pg.wait_for_timeout(700)
            await pg.screenshot(path=f"{tag}-4.png", full_page=False)
            sw = await pg.evaluate("[document.documentElement.scrollWidth, window.innerWidth]")
            results.append((tag,"paper scrollWidth",sw))
            await pg.click('#topbar [data-go="5"]'); await pg.wait_for_timeout(300)
            await pg.click("#saveFileBtn"); await pg.wait_for_timeout(1200)
            await pg.screenshot(path=f"{tag}-5.png", full_page=True)
            for n in (1,2,3,5):
                pass
            sws = await pg.evaluate("""(()=>{const out={};for(const n of [1,2,3,4,5]){for(let i=1;i<=5;i++)document.getElementById('s'+i).hidden=i!==n;out[n]=document.documentElement.scrollWidth;}return out;})()""")
            results.append((tag,"scrollWidth per screen",sws, "inner", w))
            results.append((tag,"errors",errs)); results.append((tag,"external requests",reqs))
            await ctx.close()
        await b.close()
        for r in results: print(r)
asyncio.run(main())
