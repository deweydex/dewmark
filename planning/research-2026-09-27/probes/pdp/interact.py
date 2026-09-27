import os, sys, time, json
sys.argv=[sys.argv[0]]
exec(open('shoot.py').read().split('with sync_playwright()')[0])  # reuse handler/imports
from playwright.sync_api import sync_playwright
D="/tmp/claude-0/-home-user/9d1373ae-0961-5985-b2c8-adad08e8b8ed/scratchpad/pdp"
S=D+"/shots"
def setcode(pg, cid, code):
    pg.evaluate("([id,c]) => editors[id].setValue(c)", [cid, code])
def run(pg, cid, wait=20000):
    t=time.time()
    pg.evaluate("id => runCell(id)", cid)
    pg.wait_for_function("id => document.getElementById('run-'+id).textContent==='Run'", arg=cid, timeout=wait)
    return round(time.time()-t,1), pg.inner_text("#out-"+cid)
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=EXE, args=["--no-sandbox"])
    ctx=b.new_context(viewport={"width":1400,"height":900}, accept_downloads=True)
    ctx.route("**/*", handler)
    pg=ctx.new_page()
    errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append("console."+m.type+": "+m.text[:200]) if m.type in ("warning","error") else None)
    answers=iter(["17","abc"])
    def ondialog(d):
        print("  DIALOG", d.type, repr(d.message[:120]))
        if d.type=="prompt": d.accept(next(answers,"x"))
        else: d.accept()
    pg.on("dialog", ondialog)
    pg.goto(f"file://{D}/PDP_5N2927_Sample_Exam.html")
    pg.wait_for_function("document.getElementById('nc-py').textContent.includes('ready')", timeout=120000)
    pg.uncheck("#use-file"); pg.fill("#sname","Aoife Test"); pg.click("#btn-begin"); pg.wait_for_timeout(800)
    blocks=pg.evaluate("blocks.filter(b=>b.id).map(b=>[b.id,b.type,b.q,b.label])"); print("BLOCKS",blocks)
    code=[x[0] for x in blocks if x[1]=="code"]
    c1C=[x[0] for x in blocks if x[3]=="1C"][0]; c2A=[x[0] for x in blocks if x[3]=="2A"][0]; c3C=[x[0] for x in blocks if x[3]=="3C"][0]; c3A=[x[0] for x in blocks if x[3]=="3A"][0]
    # print + error hint
    setcode(pg,c1C,"a = 17\nprint(a)\nprint(undefined_name)\n")
    print("RUN nameerror", run(pg,c1C))
    pg.evaluate("id=>document.getElementById('cell-'+id).scrollIntoView()", c1C); pg.wait_for_timeout(300)
    pg.screenshot(path=S+"/Sample_Exam_4_error_hint.png")
    # input
    setcode(pg,c2A,"age_text = input('Enter your age: ')\nprint('You typed', age_text)\nage = int(input('Again: '))\n")
    print("RUN input", run(pg,c2A))
    pg.evaluate("id=>document.getElementById('cell-'+id).scrollIntoView()", c2A); pg.wait_for_timeout(300)
    pg.screenshot(path=S+"/Sample_Exam_5_input_echo.png")
    # timeout
    setcode(pg,c3C,"n = 0\nwhile True:\n    n += 1\n")
    print("RUN infinite", run(pg,c3C,40000))
    # infinite print loop -> output size and localStorage
    setcode(pg,c3A,"i = 0\nwhile True:\n    print('line', i)\n    i += 1\n")
    t,out=run(pg,c3A,60000); print("RUN print-loop", t, "chars", len(out), out[-300:])
    pg.wait_for_timeout(2500)
    print(" save-status:", pg.text_content("#save-status"))
    print(" localStorage size:", pg.evaluate("(localStorage.getItem(STORE_KEY)||'').length"))
    print(" stored outputs has c3A:", pg.evaluate("id=>{const s=JSON.parse(localStorage.getItem(STORE_KEY)); return !!(s.outputs&&s.outputs[id])}", c3A))
    # jedi
    pg.wait_for_function("jediState==='ready'", timeout=120000)
    cm=pg.locator(f"#cm-{c1C} .CodeMirror"); cm.click()
    pg.keyboard.press("Control+End"); pg.keyboard.type("\nprin"); pg.keyboard.press("Control+Space"); pg.wait_for_timeout(1500)
    print(" hints:", pg.evaluate("[...document.querySelectorAll('.CodeMirror-hint')].map(e=>e.innerText).slice(0,5)"))
    pg.keyboard.type("t("); pg.wait_for_timeout(800)
    pg.screenshot(path=S+"/Sample_Exam_6_jedi.png")
    print(" sigtip:", pg.inner_text(f"#sig-{c1C}") if pg.is_visible(f"#sig-{c1C}") else None)
    pg.keyboard.press("Escape")
    # drawers
    pg.click("#btn-settings"); pg.wait_for_timeout(500); pg.screenshot(path=S+"/Sample_Exam_7_settings.png")
    pg.click("#btn-ref"); pg.wait_for_timeout(500); pg.screenshot(path=S+"/Sample_Exam_8_reference.png")
    pg.click("#drawer-x"); pg.wait_for_timeout(300)
    # focusability of closed drawer
    print(" drawer focusables when closed:", pg.evaluate("[...document.querySelectorAll('#drawer select,#drawer input,#drawer button')].filter(e=>e.tabIndex>=0 && !e.closest('[hidden]')).length"), "inert?", pg.evaluate("document.getElementById('drawer').inert"))
    # theme dark + OpenDyslexic
    pg.evaluate("settings.theme='dark'; settings.font='dyslexic'; settings.ruler=true; applySettings()")
    pg.mouse.move(700,400); pg.wait_for_timeout(1500)
    pg.screenshot(path=S+"/Sample_Exam_9_dark_dyslexic_ruler.png")
    pg.evaluate("settings.theme='light'; settings.font='default'; settings.ruler=false; applySettings()")
    # end banner
    pg.evaluate("document.getElementById('end-banner').scrollIntoView()"); pg.wait_for_timeout(400)
    pg.screenshot(path=S+"/Sample_Exam_10_end_banner.png")
    # save json
    with pg.expect_download() as dl: pg.click("#btn-save")
    f=dl.value; f.save_as(D+"/saved_sample.json"); print(" saved:", f.suggested_filename)
    with pg.expect_download() as dl: pg.click("#btn-ipynb")
    f=dl.value; f.save_as(D+"/saved_sample.ipynb"); print(" ipynb:", f.suggested_filename)
    pg.evaluate("preparePrint()"); pg.emulate_media(media="print")
    pg.pdf(path=D+"/print_sample.pdf"); pg.emulate_media(media="screen")
    # reload -> resume box
    pg.reload(); pg.wait_for_timeout(2500)
    pg.screenshot(path=S+"/Sample_Exam_11_resume_box.png")
    print(" resume visible:", pg.is_visible("#resume-box"), pg.inner_text("#resume-box")[:150])
    print("ERRS", errs[:15])
    b.close()
