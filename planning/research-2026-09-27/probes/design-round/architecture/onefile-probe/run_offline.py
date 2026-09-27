import json, sys
from playwright.sync_api import sync_playwright
url = sys.argv[1]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--headless=new"])
    ctx = b.new_context(offline=True)
    reqs = []
    ctx.on("request", lambda r: reqs.append(r.url[:80]) if not r.url.startswith(("file:", "data:", "blob:")) else None)
    pg = ctx.new_page()
    msgs = []
    pg.on("console", lambda m: msgs.append(m.text[:200]))
    pg.goto(url)
    try:
        pg.wait_for_function("window.RESULTS && window.RESULTS.done", timeout=120000)
    except Exception as e:
        print("TIMEOUT", str(e)[:100])
    print(json.dumps(pg.evaluate("window.RESULTS"), indent=1)[:3000])
    print("non-local requests attempted:", reqs)
    print("console:", msgs[-6:])
    b.close()
