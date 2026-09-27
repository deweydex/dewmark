import os, sys, time, json, hashlib, urllib.request, ssl
CACHE=os.path.join("/tmp/claude-0/-home-user/9d1373ae-0961-5985-b2c8-adad08e8b8ed/scratchpad/pdp","cdncache"); os.makedirs(CACHE,exist_ok=True)
SSLCTX=ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")
OPENER=urllib.request.build_opener(urllib.request.ProxyHandler({"https":os.environ["HTTPS_PROXY"]}), urllib.request.HTTPSHandler(context=SSLCTX))
SEEN=[]
def handler(route):
    url=route.request.url
    if not url.startswith("http"): return route.continue_()
    k=hashlib.sha1(url.encode()).hexdigest()
    fp=os.path.join(CACHE,k)
    try:
        if os.path.exists(fp):
            body=open(fp,"rb").read(); ct=open(fp+".ct").read()
        else:
            r=OPENER.open(url,timeout=60); body=r.read(); ct=r.headers.get("Content-Type","application/octet-stream")
            open(fp,"wb").write(body); open(fp+".ct","w").write(ct)
        SEEN.append((url,len(body)))
        route.fulfill(status=200, body=body, headers={"Content-Type":ct,"Access-Control-Allow-Origin":"*"})
    except Exception as e:
        print("ROUTE FAIL",url,e); route.abort()

from playwright.sync_api import sync_playwright
D="/tmp/claude-0/-home-user/9d1373ae-0961-5985-b2c8-adad08e8b8ed/scratchpad/pdp"
EXE="/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
pages=["Sample_Exam","Practice_Exam_1","Practice_Exam_2","Exam_2027"]
only=sys.argv[1:] or pages
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=EXE, args=["--no-sandbox"])
    for name in only:
        ctx=b.new_context(viewport={"width":1400,"height":900})
        ctx.route("**/*", handler)
        pg=ctx.new_page()
        logs=[]
        pg.on("console", lambda m: logs.append(f"{m.type}: {m.text}"))
        pg.on("pageerror", lambda e: logs.append(f"PAGEERROR: {e}"))
        fails=[]
        pg.on("requestfailed", lambda r: fails.append(r.url))
        t0=time.time()
        pg.goto(f"file://{D}/PDP_5N2927_{name}.html", wait_until="load", timeout=90000)
        print(name,"load",round(time.time()-t0,1),"s")
        pg.wait_for_timeout(1500)
        pg.screenshot(path=f"{D}/shots/{name}_1_name_screen.png")
        try:
            pg.wait_for_function("document.getElementById('nc-py').textContent.includes('ready') || document.getElementById('nc-py').textContent.includes('could not')", timeout=120000)
        except Exception as e: print("py wait fail", e)
        print(" py status:", pg.text_content("#nc-py"), round(time.time()-t0,1),"s")
        pg.screenshot(path=f"{D}/shots/{name}_2_name_screen_python_ready.png")
        pg.uncheck("#use-file")
        pg.fill("#sname","Test Student")
        pg.click("#btn-begin")
        pg.wait_for_timeout(1500)
        pg.screenshot(path=f"{D}/shots/{name}_3_main_view.png")
        print(" nav:", pg.inner_text("#nav").replace("\n"," | ")[:300])
        print(" cells:", pg.evaluate("document.querySelectorAll('.cell').length"), "code:", pg.evaluate("document.querySelectorAll('.code-cell').length"))
        print(" logs:", logs[:10]); print(" failed:", fails[:10])
        ctx.close()
    b.close()
    json.dump(SEEN, open(os.path.join(CACHE,"..","cdn_seen.json"),"w"), indent=1)
