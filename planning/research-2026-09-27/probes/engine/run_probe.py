import json, os, sys
from playwright.sync_api import sync_playwright
url = sys.argv[1]
proxy = os.environ.get("HTTPS_PROXY")
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
                          proxy=None,
                          args=["--headless=new"])
    pg = b.new_page()
    msgs=[]
    pg.on("console", lambda m: msgs.append(m.text))
    pg.goto(url)
    try:
        pg.wait_for_function("window.RESULTS && window.RESULTS.done", timeout=150000)
    except Exception as e:
        print("TIMEOUT", str(e)[:100])
    print(json.dumps(pg.evaluate("window.RESULTS"), indent=1))
    print("console:", msgs[-5:])
    b.close()
