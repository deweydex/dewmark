import sys
from playwright.sync_api import sync_playwright
url = sys.argv[1]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--headless=new"])
    pg = b.new_page(); msgs = []
    pg.on("console", lambda m: msgs.append(m.text))
    pg.goto(url)
    pg.wait_for_selector("#out", timeout=120000, state="attached")
    print(pg.text_content("#out")); print("console:", [m[:220] for m in msgs])
    b.close()
