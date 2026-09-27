import os, sys, time, json
sys.argv=[sys.argv[0]]
exec(open('shoot.py').read().split('with sync_playwright()')[0])
from playwright.sync_api import sync_playwright
D="/tmp/claude-0/-home-user/9d1373ae-0961-5985-b2c8-adad08e8b8ed/scratchpad/pdp"
DLG=[]
def begin(b, fn="PDP_5N2927_Sample_Exam.html"):
    ctx=b.new_context(viewport={"width":1400,"height":900}); ctx.route("**/*", handler)
    pg=ctx.new_page(); logs=[]
    pg.on("console", lambda m: logs.append(m.type+": "+m.text[:160]) if m.type in ("warning","error") else None)
    pg.on("pageerror", lambda e: logs.append("PAGEERROR "+str(e)))
    pg.on("dialog", lambda d: (DLG.append(d.message), d.dismiss() if len(DLG)<5 else d.accept("21")))   # Cancel on every prompt
    pg.goto(f"file://{D}/{fn}")
    pg.wait_for_function("document.getElementById('nc-py').textContent.includes('ready')", timeout=120000)
    pg.uncheck("#use-file"); pg.fill("#sname","T"); pg.click("#btn-begin"); pg.wait_for_timeout(500)
    return ctx,pg,logs
def trial(b, label, code, wait=45000):
    ctx,pg,logs=begin(b)
    t=time.time()
    print(" starting", label, flush=True)
    pg.evaluate("c => { editors['b11'].setValue(c); setTimeout(()=>runCell('b11'),0); }", code)
    print(" dispatched", flush=True)
    try:
        pg.wait_for_function("document.getElementById('run-b11').textContent==='Run'", timeout=wait)
        out=pg.inner_text("#out-b11")
        print(" dialogs seen:", len(DLG)); print(label, "finished in", round(time.time()-t,1), "s ::", out[-260:].replace("\n"," / "))
    except Exception as e:
        print(" dialogs seen:", len(DLG)); print(label, "STILL RUNNING after", round(time.time()-t,1), "s (tab frozen)")
    extra = pg.evaluate("1+1") if False else None
    ctx.close()
    return logs
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=EXE, args=["--no-sandbox"])
    mode=os.environ.get("MODE","")
    if mode=="trace":
        trial(b,"[except Exception swallows TimeoutError]", "n = 0\nwhile True:\n    try:\n        n += 1\n    except Exception:\n        pass\n", 45000)
    if mode=="trace2":
        trial(b,"[TimeoutError raised inside a called function, caught by except Exception]", "def work():\n    total = 0\n    for i in range(1000):\n        total += i\n    return total\n\nwhile True:\n    try:\n        work()\n    except Exception:\n        pass\n", 45000)
    if mode=="control":
        trial(b,"[control: same loop, except ValueError]", "def work():\n    total = 0\n    for i in range(1000):\n        total += i\n    return total\n\nwhile True:\n    try:\n        work()\n    except ValueError:\n        pass\n", 45000)
    if mode=="cancel":
        trial(b,"[Cancel inside try/except loop]", "while True:\n    try:\n        age = int(input('Age? '))\n        break\n    except:\n        print('Not a whole number')\n", 20000)
    if mode=="clevel":
        trial(b,"[C-level long op]", "total = sum(range(10**9))\nprint(total)\n", 90000)
    if mode=="printloop":
        ctx,pg,logs=begin(b)
        t=time.time()
        pg.evaluate("editors['b9'].setValue(\"i = 0\\nwhile True:\\n    print('line', i)\\n    i += 1\\n\"); runCell('b9')")
        pg.wait_for_function("document.getElementById('run-b9').textContent==='Run'", timeout=120000)
        print("printloop done", round(time.time()-t,1))
        pg.wait_for_timeout(2000)
        print(" status after run:", pg.text_content("#save-status"), "| stored len:", pg.evaluate("(localStorage.getItem(STORE_KEY)||'').length"))
        # now a later edit in another answer box
        pg.evaluate("document.getElementById('ta-b10').scrollIntoView()")
        pg.fill("#ta-b10", "An infinite loop never stops.")
        pg.wait_for_timeout(2500)
        stored=pg.evaluate("JSON.parse(localStorage.getItem(STORE_KEY)||'{}')")
        print(" status after later edit:", pg.text_content("#save-status"), "| b10 in storage:", repr((stored.get('values') or {}).get('b10')))
        print(" logs:", [l for l in logs][:6])
        ctx.close()
    b.close()
