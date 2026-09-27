"""Build one HTML file that carries Pyodide's core (and the sqlite3 wheel)
inside itself, boots it in a blob-URL classic Worker, and runs Python with
no network and no sibling files. Question being tested: can a Python exam
be ONE file that works from file:// with the network off?"""
import base64, json, pathlib, sys

HERE = pathlib.Path(__file__).parent
PY = HERE.parent.parent.parent / "engine-probe" / "pyodide"
with_sqlite = "--no-sqlite" not in sys.argv

def b64(p):
    return base64.b64encode(p.read_bytes()).decode()

blobs = {
    "pyodide.js": b64(PY / "pyodide.js"),
    "pyodide.asm.js": b64(PY / "pyodide.asm.js"),
    "pyodide.asm.wasm": b64(PY / "pyodide.asm.wasm"),
    "python_stdlib.zip": b64(PY / "python_stdlib.zip"),
    "pyodide-lock.json": b64(PY / "pyodide-lock.json"),
}
if with_sqlite:
    w = HERE / "sqlite3-1.0.0-cp313-cp313-pyodide_2025_0_wasm32.whl"
    blobs[w.name] = b64(w)

tags = "\n".join(
    f'<script type="application/octet-stream" data-name="{name}">{data}</script>'
    for name, data in blobs.items())

WORKER = r"""
const BASE = "https://pyodide.invalid/";
let files = null;
const realFetch = self.fetch.bind(self);
self.fetch = (url, opts) => {
  const u = String(url);
  if (u.startsWith(BASE)) {
    const name = u.slice(BASE.length).split("?")[0];
    const buf = files[name];
    if (!buf) return Promise.resolve(new Response("missing " + name, {status: 404}));
    const type = name.endsWith(".wasm") ? "application/wasm" : "application/octet-stream";
    return Promise.resolve(new Response(buf, {headers: {"Content-Type": type}}));
  }
  return realFetch(url, opts);
};
self.onmessage = async (e) => {
  const t0 = performance.now();
  try {
    files = e.data.files;
    const dec = new TextDecoder();
    importScripts(URL.createObjectURL(new Blob([files["pyodide.js"]], {type: "text/javascript"})));
    importScripts(URL.createObjectURL(new Blob([files["pyodide.asm.js"]], {type: "text/javascript"})));
    const py = await loadPyodide({indexURL: BASE, lockFileContents: dec.decode(files["pyodide-lock.json"]),
                                  stdLibURL: BASE + "python_stdlib.zip", packageBaseUrl: BASE});
    const tBoot = performance.now();
    let sqliteOut = null;
    if (files["sqlite3-1.0.0-cp313-cp313-pyodide_2025_0_wasm32.whl"]) {
      await py.loadPackage("sqlite3");
      sqliteOut = py.runPython("import sqlite3; c=sqlite3.connect(':memory:'); c.execute('create table t(x)'); c.executemany('insert into t values (?)', [(i,) for i in range(5)]); str(c.execute('select sum(x) from t').fetchone()[0])");
    }
    const out = py.runPython("import sys; f'{sys.version.split()[0]} {sum(range(10))}'");
    postMessage({ok: true, out, sqliteOut, bootMs: tBoot - t0, totalMs: performance.now() - t0});
  } catch (err) {
    postMessage({ok: false, error: String(err && err.stack || err)});
  }
};
"""

PAGE = f"""<!doctype html>
<meta charset="utf-8">
<title>one-file Pyodide probe</title>
<p id="status">starting</p>
{tags}
<script id="worker-src" type="text/plain">{WORKER}</script>
<script>
window.RESULTS = {{done: false}};
(async () => {{
  const t0 = performance.now();
  const files = {{}};
  for (const el of document.querySelectorAll('script[data-name]')) {{
    const r = await fetch("data:application/octet-stream;base64," + el.textContent);
    files[el.dataset.name] = await r.arrayBuffer();
  }}
  const tDecode = performance.now();
  const src = document.getElementById("worker-src").textContent;
  const worker = new Worker(URL.createObjectURL(new Blob([src], {{type: "text/javascript"}})));
  worker.onmessage = (e) => {{
    window.RESULTS = Object.assign({{done: true, decodeMs: tDecode - t0, pageToReadyMs: performance.now() - t0,
      protocol: location.protocol}}, e.data);
    document.getElementById("status").textContent = JSON.stringify(window.RESULTS);
  }};
  worker.onerror = (e) => {{ window.RESULTS = {{done: true, error: "worker error: " + e.message}}; }};
  worker.postMessage({{files}}, Object.values(files));
}})();
</script>
"""

out = HERE / ("onefile.html" if with_sqlite else "onefile-core.html")
out.write_text(PAGE)
print(out, round(out.stat().st_size / 1e6, 2), "MB")
