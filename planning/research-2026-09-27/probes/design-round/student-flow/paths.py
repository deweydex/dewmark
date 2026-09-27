import asyncio
from playwright.async_api import async_playwright
URL="file:///home/user/dewmark/planning/mockups/student-start.html"
EXE="/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=EXE,args=["--no-sandbox"])
        pg=await (await b.new_context(viewport={"width":390,"height":844})).new_page()
        errs=[]; pg.on("pageerror",lambda e: errs.append(str(e)))
        await pg.goto(URL)
        await pg.click("#scen summary"); await pg.check("#scSaved"); await pg.check('input[name=load][value=fail]')
        await pg.fill("#fName","Aoife Byrne"); await pg.fill("#fNum","d0012345"); await pg.click("#toSettings")
        print("warn:", await pg.inner_text("#fNumWarn"))
        await pg.fill("#fNum","D00123456"); await pg.click("#toSettings")
        print("resume visible:", await pg.is_visible("#resume"), "| focused:", await pg.evaluate("document.activeElement.id"))
        await pg.click("#resumeGo"); await pg.wait_for_timeout(6500)
        print("status:", await pg.inner_text("#loadStatus")); print("failbox:", await pg.is_visible("#failBox"), "| begin:", await pg.inner_text("#beginBtn"))
        await pg.click("#beginBtn"); await pg.wait_for_timeout(300)
        print("time chip:", await pg.inner_text("#timeChip"), "| cell:", await pg.inner_text("#cellStatus"))
        await pg.evaluate("document.getElementById('scFull').click()"); await pg.wait_for_timeout(1000)
        print("save chip:", await pg.inner_text("#saveChip")); print("banner:", await pg.inner_text("#storeBannerText"))
        await pg.evaluate("document.getElementById('kindPractice').click()"); await pg.wait_for_timeout(200)
        print("badge:", await pg.inner_text("#topbar .badge"), "| time hidden:", await pg.is_hidden("#timeChip"))
        await pg.evaluate("document.querySelector('[data-jump=\"5\"]').click()")
        print("f3:", await pg.inner_text("#f3h"), "|", (await pg.inner_text("#f3text"))[:80])
        await pg.evaluate("document.querySelector('[data-open-settings]').click()")
        print("drawer open:", await pg.is_visible("#drawer"), "| main inert:", await pg.evaluate("document.querySelector('main').inert"))
        await pg.keyboard.press("Escape"); print("drawer after Esc:", await pg.is_visible("#drawer"))
        print("errors:", errs)
        await b.close()
asyncio.run(main())
