import json
from playwright.sync_api import sync_playwright
import os
d=os.getcwd()
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
    ctx = b.new_context()
    for u in [f"file://{d}/a/p.html", f"file://{d}/b/p.html"]:
        pg = ctx.new_page(); pg.goto(u); print(u.split('/')[-2], pg.evaluate("window.RESULTS"))
    b.close()
