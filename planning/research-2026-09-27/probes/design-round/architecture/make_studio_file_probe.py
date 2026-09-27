"""Write studio-file-probe/: a studio-like page that carries the builder and one sample, and loads Pyodide
plus the three builder wheels from a sibling python/payload.js. Run it with onefile-probe/run_offline.py."""
import base64, json, pathlib
PY = pathlib.Path("../../engine-probe/pyodide"); W = pathlib.Path("studio-probe/wheels")
b = lambda p: base64.b64encode(p.read_bytes()).decode()
pathlib.Path("studio-file-probe/python").mkdir(parents=True, exist_ok=True)
payload = {n: b(PY / n) for n in ["pyodide.js", "pyodide.asm.js", "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json"]}
payload.update({w.name: b(w) for w in W.glob("*.whl")})
pathlib.Path("studio-file-probe/python/payload.js").write_text("window.DEWMARK_PY = " + json.dumps(payload) + ";\n")
work = {p: b(pathlib.Path("studio-probe") / p) for p in ["builder/build_exam.py", "builder/assets/exam-page.css",
        "builder/assets/exam-page.js", "samples/sample-mixed-paper.exam.md"]}
work.update({str(x.relative_to("studio-probe")): b(x) for x in pathlib.Path("studio-probe/samples/pictures").glob("*")})
page = pathlib.Path("studio-file-probe/studio.html").read_text() if pathlib.Path("studio-file-probe/studio.html").exists() else None
print("payload and work written;", "studio.html kept" if page else "studio.html missing: regenerate from the design-round notes")
