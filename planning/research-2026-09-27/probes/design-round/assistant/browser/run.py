import json, sys
from playwright.sync_api import sync_playwright
url = sys.argv[1]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--headless=new"])
    pg = b.new_page(); msgs = []
    pg.on("console", lambda m: msgs.append(m.text))
    pg.goto(url)
    pg.wait_for_function("window.RESULTS && window.RESULTS.done", timeout=120000)
    r = pg.evaluate("window.RESULTS"); print("browser", b.version)
    print(json.dumps(r, indent=1)); print("console:", [m[:200] for m in msgs])
    b.close()
