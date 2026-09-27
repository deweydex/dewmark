from playwright.sync_api import sync_playwright
URL = "file:///home/user/dewmark/planning/mockups/teacher-studio.html"
JS = """() => {
  document.body.style.overflowX = 'visible';
  const W = document.documentElement.clientWidth, out = [];
  for (const el of document.querySelectorAll('body *')) {
    if (el.closest('[hidden]')) continue;
    const r = el.getBoundingClientRect();
    if (r.width === 0) continue;
    let p = el.parentElement, clipped = false;
    while (p && p !== document.body) { const o = getComputedStyle(p).overflowX; if (o === 'auto' || o === 'scroll' || o === 'hidden') { clipped = true; break; } p = p.parentElement; }
    if (!clipped && (r.right > W + 1 || r.left < -1)) out.push(el.tagName + '.' + el.className + ' ' + Math.round(r.left) + '-' + Math.round(r.right));
  }
  return [document.documentElement.scrollWidth, W, out.slice(0, 8)];
}"""
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--headless=new"])
    for w in [320, 390, 768, 1000]:
        pg = b.new_page(viewport={"width": w, "height": 800})
        pg.goto(URL); pg.wait_for_timeout(600)
        for screen in ["home", "editor", "issue"]:
            pg.click(f'.mock nav button[data-go="{screen}"]'); pg.wait_for_timeout(500)
            if screen == "editor" and w < 820:
                for pane in ["outline", "source", "preview"]:
                    pg.click(f'.tabs [data-pane="{pane}"]'); pg.wait_for_timeout(200)
                    print(w, screen, pane, pg.evaluate(JS))
            else:
                print(w, screen, pg.evaluate(JS))
        # drawers open on home
        pg.click('.mock nav button[data-go="home"]'); pg.click('[data-drawer="new"]'); pg.wait_for_timeout(200)
        print(w, "home+new", pg.evaluate(JS))
        pg.click('[data-drawer="convert"]'); pg.wait_for_timeout(200)
        print(w, "home+convert", pg.evaluate(JS))
        pg.close()
    b.close()
