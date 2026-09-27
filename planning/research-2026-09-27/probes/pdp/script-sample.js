
"use strict";
// ═══════════════════════════════════════════════════════════════════════════
//  Programming and Design Principles: browser exam tool
//  The exam paper is the Markdown in #exam-src. Fence types:
//    ```python            code cell (body = starting code)
//    ```python setup      hidden code that runs once when Python is ready
//    ```answer LABEL      written answer box (body = starting text)
//    ```fields LABEL      one short answer box per line of the body
//    ```text / ```py      code shown to the student, not editable
// ═══════════════════════════════════════════════════════════════════════════

const SRC  = JSON.parse(document.getElementById("exam-src").textContent);
const META = parseFrontmatter(SRC);
const CONFIG = {
  kind:            META.kind || "exam",
  duration:        parseInt(META.duration_minutes || "120", 10),
  allowCompletion: META.allow_completion !== "false",
  showReference:   META.show_reference !== "false",
  referenceTheory: META.reference_theory === "true",
  timeLimit:       parseFloat(META.time_limit_seconds || "10"),
  errorHints:      META.error_hints !== "false",
};
const EXAM_ID      = META.exam_id || "exam";
const STORE_KEY    = "pdp-exam:" + EXAM_ID;
const SETTINGS_KEY = "pdp-exam-settings";

// ── Settings ──────────────────────────────────────────────────────────────
const DEFAULTS = { font:"default", size:17, lineHeight:1.6, spacing:"normal", width:"medium", theme:"light",
  ruler:false, codeFont:"courier", codeSize:15, codeTheme:"auto", wrap:true, closeBrackets:true,
  jedi:true, autoPopup:true, sigHints:true, timer:true, reduceMotion:false };
const FONTS = {
  default:'Georgia,"Times New Roman",serif',
  sans:'system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif',
  atkinson:'"Atkinson Hyperlegible",system-ui,sans-serif',
  lexend:'"Lexend",system-ui,sans-serif',
  dyslexic:'"OpenDyslexic","Comic Sans MS",sans-serif'
};
const CODE_FONTS = {
  courier:'"Courier New",monospace',
  system:'ui-monospace,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace',
  atkinson:'"Atkinson Hyperlegible Mono",ui-monospace,monospace'
};
const SPACING = { normal:["0em","0em"], wide:["0.035em","0.1em"], wider:["0.07em","0.2em"] };
const WIDTHS  = { narrow:"60ch", medium:"75ch", wide:"95ch", full:"none" };
let settings = loadSettings();

function loadSettings(){
  try { return Object.assign({}, DEFAULTS, JSON.parse(localStorage.getItem(SETTINGS_KEY) || "{}")); }
  catch(e){ return Object.assign({}, DEFAULTS); }
}
function storeSettings(){ try { localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings)); } catch(e){} }

function applySettings(){
  const r = document.documentElement, st = r.style;
  r.dataset.theme = settings.theme;
  st.setProperty("--read-font", FONTS[settings.font] || FONTS.default);
  st.setProperty("--fs", settings.size + "px");
  st.setProperty("--lh", settings.lineHeight);
  const sp = SPACING[settings.spacing] || SPACING.normal;
  st.setProperty("--ls", sp[0]); st.setProperty("--ws", sp[1]);
  st.setProperty("--measure", WIDTHS[settings.width] || WIDTHS.medium);
  st.setProperty("--code-font", CODE_FONTS[settings.codeFont] || CODE_FONTS.courier);
  st.setProperty("--code-fs", settings.codeSize + "px");
  r.classList.toggle("reduce-motion", settings.reduceMotion);
  document.getElementById("ruler").classList.toggle("on", settings.ruler);
  document.getElementById("timer-chip").style.display = settings.timer ? "" : "none";
  const jediOn = CONFIG.allowCompletion && settings.jedi;
  document.getElementById("sd-complete-row").style.display = jediOn ? "" : "none";
  for (const id in editors) {
    const cm = editors[id];
    cm.setOption("lineWrapping", settings.wrap);
    cm.setOption("theme", codeThemeName());
    cm.setOption("autoCloseBrackets", settings.closeBrackets);
  }
  if (jediOn && pyReady) ensureJedi();
  refreshLayout();
}
function codeThemeName(){
  if (settings.codeTheme === "light") return "default";
  if (settings.codeTheme === "dark") return "dracula";
  return (settings.theme === "dark" || settings.theme === "contrast") ? "dracula" : "default";
}
let layoutTimer = null;
function refreshLayout(){
  clearTimeout(layoutTimer);
  layoutTimer = setTimeout(() => {
    for (const id in editors) editors[id].refresh();
    document.querySelectorAll("textarea.ans").forEach(autogrow);
  }, 30);
}

function bindSettingsForm(){
  const bind = (id, key, kind, fmt) => {
    const el = document.getElementById(id), out = document.getElementById("v-" + id.slice(2));
    const show = () => { if (out) out.textContent = fmt ? fmt(settings[key]) : settings[key]; };
    if (kind === "check") el.checked = !!settings[key]; else el.value = settings[key];
    show();
    el.addEventListener(kind === "range" ? "input" : "change", () => {
      settings[key] = kind === "check" ? el.checked : kind === "range" ? parseFloat(el.value) : el.value;
      show(); storeSettings(); applySettings();
    });
  };
  bind("s-font","font"); bind("s-size","size","range",v=>v+"px"); bind("s-lh","lineHeight","range",v=>(+v).toFixed(1));
  bind("s-spacing","spacing"); bind("s-width","width"); bind("s-theme","theme"); bind("s-ruler","ruler","check");
  bind("s-cfont","codeFont"); bind("s-csize","codeSize","range",v=>v+"px"); bind("s-ctheme","codeTheme");
  bind("s-wrap","wrap","check"); bind("s-brackets","closeBrackets","check");
  bind("s-jedi","jedi","check"); bind("s-popup","autoPopup","check"); bind("s-sig","sigHints","check");
  bind("s-timer","timer","check"); bind("s-motion","reduceMotion","check");
  document.getElementById("s-reset").onclick = () => {
    settings = Object.assign({}, DEFAULTS); storeSettings(); bindSettingsForm(); applySettings(); toast("Settings reset");
  };
  if (!CONFIG.allowCompletion) {
    document.getElementById("grp-jedi").innerHTML =
      '<h3>Code suggestions</h3><p class="set-note">Code suggestions are switched off for this paper.</p>';
  }
}

// ── Drawer ────────────────────────────────────────────────────────────────
function openDrawer(which){
  const d = document.getElementById("drawer");
  const already = d.classList.contains("open") && d.dataset.pane === which;
  if (already) { closeDrawer(); return; }
  d.dataset.pane = which;
  document.getElementById("pane-settings").classList.toggle("on", which === "settings");
  document.getElementById("pane-ref").classList.toggle("on", which === "ref");
  document.getElementById("drawer-title").textContent = which === "settings" ? "Settings" : "Python reference";
  document.getElementById("btn-settings").setAttribute("aria-pressed", which === "settings");
  document.getElementById("btn-ref").setAttribute("aria-pressed", which === "ref");
  d.classList.add("open"); d.setAttribute("aria-hidden","false");
  document.body.classList.add("drawer-open"); refreshLayout();
  if (window.innerWidth < 1100) document.getElementById("scrim").classList.add("on");
  setTimeout(() => (which === "ref" ? document.getElementById("ref-q") : document.getElementById("s-font")).focus(), 60);
}
function closeDrawer(){
  const d = document.getElementById("drawer");
  d.classList.remove("open"); d.setAttribute("aria-hidden","true");
  document.body.classList.remove("drawer-open"); refreshLayout();
  document.getElementById("scrim").classList.remove("on");
  document.getElementById("btn-settings").setAttribute("aria-pressed","false");
  document.getElementById("btn-ref").setAttribute("aria-pressed","false");
}

// ── Python reference ──────────────────────────────────────────────────────
function prepareReference(){
  document.querySelectorAll("#ref-list pre.ref-code").forEach(pre => {
    const src = pre.textContent.replace(/^\n/, "").replace(/\s+$/, "");
    pre.classList.add("hl");
    pre.innerHTML = highlight(src, false);
    const wrap = document.createElement("div"); wrap.className = "ref-code-wrap";
    pre.replaceWith(wrap); wrap.appendChild(pre);
    const b = document.createElement("button"); b.className = "copy-btn"; b.textContent = "Copy";
    b.onclick = () => copyText(src, b);
    wrap.appendChild(b);
  });
  const q = document.getElementById("ref-q");
  q.addEventListener("input", () => {
    const term = q.value.trim().toLowerCase();
    let shown = 0;
    document.querySelectorAll("#ref-list details").forEach(d => {
      const hit = !term || d.textContent.toLowerCase().includes(term);
      d.hidden = !hit; if (hit) shown++;
      d.open = !!term && hit;
    });
    document.getElementById("ref-none").hidden = shown > 0;
  });
}
function copyText(text, btn){
  const done = () => { if (btn) { btn.textContent = "Copied"; setTimeout(() => btn.textContent = "Copy", 1400); } toast("Copied"); };
  if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done).catch(() => window.prompt("Copy this:", text));
  else window.prompt("Copy this:", text);
}

// ── Exam state ────────────────────────────────────────────────────────────
let blocks = [];            // parsed paper
let editors = {};           // id -> CodeMirror
let S = { name:"", startedAt:null, values:{}, outputs:{} };
let fileHandle = null, isRunning = false, dirty = false;
let pyodide = null, pyReady = false, kit = null;
let jediState = "off";      // off | loading | ready | error

// ── Startup ───────────────────────────────────────────────────────────────
window.addEventListener("DOMContentLoaded", () => {
  applySettings();
  bindSettingsForm();
  prepareReference();
  if (!CONFIG.showReference) document.getElementById("btn-ref").style.display = "none";
  if (!CONFIG.referenceTheory) document.querySelectorAll("#ref-list [data-theory]").forEach(d => d.remove());

  document.title = [META.title, META.module].filter(Boolean).join(": ");
  document.getElementById("nc-inst").textContent    = META.institution || "";
  document.getElementById("nc-college").textContent = META.college || "";
  document.getElementById("nc-module").textContent  = META.module || "";
  document.getElementById("nc-paper").textContent   = `${META.title || "Examination"}, ${formatDuration(CONFIG.duration)}`;

  const canFile = "showSaveFilePicker" in window;
  if (!canFile) document.getElementById("use-file-wrap").style.display = "none";
  document.getElementById("save-note").innerHTML = canFile
    ? "Your work is also saved in this browser every few seconds. Press <b>Save</b> in the toolbar at any time to write your file again."
    : "Your work is saved in this browser every few seconds. Press <b>Save</b> in the toolbar regularly to download a copy of your work as a file.";

  const saved = readStore();
  if (saved && saved.name) {
    document.getElementById("resume-box").hidden = false;
    document.getElementById("fresh-box").hidden = true;
    document.getElementById("resume-name").textContent = saved.name;
    document.getElementById("resume-time").textContent = saved.savedAt ? new Date(saved.savedAt).toLocaleString() : "earlier";
  }
  document.getElementById("btn-begin").onclick  = () => beginExam(false);
  document.getElementById("btn-resume").onclick = () => beginExam(true);
  document.getElementById("btn-fresh").onclick  = () => {
    if (!confirm("Start this paper again? The work saved in this browser for this paper will be cleared. Any .json file you saved stays on your computer.")) return;
    try { localStorage.removeItem(STORE_KEY); } catch(e){}
    document.getElementById("resume-box").hidden = true;
    document.getElementById("fresh-box").hidden = false;
    document.getElementById("sname").focus();
  };
  document.getElementById("sname").addEventListener("keydown", e => { if (e.key === "Enter") beginExam(false); });
  document.getElementById("nc-settings").onclick = () => openDrawer("settings");
  document.getElementById("nc-load").onclick = pickLoadFile;
  document.getElementById("sd-load").onclick = pickLoadFile;
  document.getElementById("file-in").addEventListener("change", onLoadFile);

  document.getElementById("btn-settings").onclick = () => openDrawer("settings");
  document.getElementById("btn-ref").onclick = () => openDrawer("ref");
  document.getElementById("drawer-x").onclick = closeDrawer;
  document.getElementById("scrim").onclick = () => { closeDrawer(); document.getElementById("side").classList.remove("open"); };
  document.getElementById("btn-save").onclick = saveNow;
  document.getElementById("btn-ipynb").onclick = exportIpynb;
  document.getElementById("btn-print").onclick = () => { preparePrint(); window.print(); };
  document.getElementById("menu-btn").onclick = () => {
    document.getElementById("side").classList.toggle("open");
    document.getElementById("scrim").classList.toggle("on", document.getElementById("side").classList.contains("open"));
  };
  document.addEventListener("keydown", e => {
    if (e.key === "Escape" && document.getElementById("drawer").classList.contains("open")) closeDrawer();
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s" && S.name) { e.preventDefault(); saveNow(); }
  });
  document.addEventListener("mousemove", e => {
    if (!settings.ruler) return;
    const r = document.getElementById("ruler");
    r.style.top = (e.clientY - r.offsetHeight / 2) + "px";
  });
  window.addEventListener("beforeprint", preparePrint);
  window.addEventListener("resize", refreshLayout);
  window.addEventListener("beforeunload", e => { if (S.name && dirty) { writeStore(); e.preventDefault(); e.returnValue = ""; } });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(refreshLayout);

  blocks = parseExam(SRC);
  initPython();
});

function formatDuration(min){
  if (min % 60 === 0) return `${min/60} hour${min === 60 ? "" : "s"}`;
  return `${min} minutes`;
}

// ── Python (Pyodide) ──────────────────────────────────────────────────────
const KIT_PY = String.raw`
"""Helpers for the exam tool. Students never import this module directly."""
import builtins, sys, time
import js

class InputCancelled(Exception):
    """Raised when the student closes the input box without typing anything."""

_deadline = [0.0]
_limit = [10.0]

def _tracer(frame, event, arg):
    # Called by Python on every line while student code runs.
    if time.monotonic() > _deadline[0]:
        raise TimeoutError(
            "Your code ran for more than %g seconds, so the exam tool stopped it. "
            "This usually means a loop never ends." % _limit[0])
    return _tracer

def arm(limit):
    _limit[0] = float(limit)
    _deadline[0] = time.monotonic() + float(limit)
    if limit > 0:
        sys.settrace(_tracer)

def disarm():
    sys.settrace(None)

def _exam_input(prompt=""):
    try:
        sys.stdout.flush()
    except Exception:
        pass
    text = str(prompt)
    started = time.monotonic()
    value = js.examAsk(text)
    _deadline[0] += time.monotonic() - started   # time spent typing does not count
    if value is None:
        raise InputCancelled("You closed the input box, so the program stopped.")
    value = str(value)
    js.examEchoInput(text, value)
    return value

def install():
    builtins.input = _exam_input
    builtins.InputCancelled = InputCancelled

def complete(code, line, col):
    import json, jedi, __main__
    try:
        comps = jedi.Interpreter(code, [__main__.__dict__]).complete(line, col)
    except Exception:
        return "[]"
    out = []
    for c in comps:
        if c.name.startswith("_exam") or c.name == "InputCancelled":
            continue
        out.append([c.name, c.type])
        if len(out) >= 80:
            break
    return json.dumps(out)

def signature(code, line, col):
    import json, jedi, __main__
    try:
        sigs = jedi.Interpreter(code, [__main__.__dict__]).get_signatures(line, col)
    except Exception:
        return ""
    if not sigs:
        return ""
    s = sigs[0]
    doc = ""
    try:
        lines = [l for l in s.docstring(raw=True).strip().splitlines() if l.strip()]
        doc = lines[0] if lines else ""
    except Exception:
        pass
    return json.dumps({"name": s.name, "params": [p.to_string() for p in s.params],
                       "index": s.index, "doc": doc[:160]})
`;

async function initPython(){
  setPy("loading", "Python is loading in the background. You can start reading while it loads.");
  try {
    pyodide = await loadPyodide({ indexURL: "https://cdn.jsdelivr.net/pyodide/v0.27.4/full/" });
    const dec = new TextDecoder();
    const writer = cls => ({ write: buf => { appendOut(dec.decode(buf, { stream:true }), cls); return buf.length; } });
    pyodide.setStdout(writer(""));
    pyodide.setStderr(writer("stderr"));
    pyodide.FS.writeFile("/lib/python3.12/site-packages/_examkit.py", KIT_PY);
    kit = pyodide.pyimport("_examkit");
    kit.install();
    pyReady = true;
    setPy("ready", "Python is ready.");
    document.querySelectorAll(".run-btn").forEach(b => { b.disabled = false; b.textContent = "Run"; });
    await runSetupBlocks();
    if (CONFIG.allowCompletion && settings.jedi) ensureJedi();
  } catch(e) {
    console.error(e);
    setPy("error", "Python could not load. Check your internet connection and refresh the page. Your saved work is kept.");
  }
}
function setPy(state, msg){
  const dotCls = "dot" + (state === "ready" ? " ok" : state === "error" ? " err" : "");
  document.getElementById("nc-dot").className = dotCls;
  document.getElementById("py-dot").className = dotCls;
  document.getElementById("nc-py").textContent = msg;
  document.getElementById("py-txt").textContent =
    state === "ready" ? (jediState === "loading" ? "Python ready, suggestions loading" : "Python ready")
    : state === "error" ? "Python failed to load" : "Python loading";
}
async function ensureJedi(){
  if (jediState !== "off" || !pyReady) return;
  jediState = "loading"; setPy("ready", "Python is ready.");
  try {
    await pyodide.loadPackage(["jedi"], { messageCallback: () => {} });
    kit.complete("pri", 1, 3);          // warm up so the first real request is quick
    jediState = "ready";
  } catch(e) { console.warn("Jedi failed", e); jediState = "error"; }
  setPy("ready", "Python is ready.");
}
async function runSetupBlocks(){
  for (const b of blocks) {
    if (b.type !== "setup") continue;
    try { await pyodide.runPythonAsync(b.content); } catch(e) { console.warn("Setup failed", e); }
  }
}

// Output routing: Python's print() lands in the current cell's output.
let curOut = null;
function appendOut(text, cls){
  if (!curOut) { if (text.trim()) console.log(text); return; }
  if (cls) { const s = document.createElement("span"); s.className = cls; s.textContent = text; curOut.appendChild(s); }
  else curOut.appendChild(document.createTextNode(text));
}
window.examAsk = function(promptText){
  let context = "";
  if (curOut) {
    const lines = curOut.textContent.split("\n").filter(l => l.trim());
    context = lines.slice(-4).join("\n");
  }
  const msg = (context ? context + "\n\n" : "") + (promptText || "Your program is waiting for you to type something:");
  const v = window.prompt(msg, "");
  return v === null ? null : v;
};
window.examEchoInput = function(promptText, value){
  if (!curOut) return;
  if (promptText) curOut.appendChild(document.createTextNode(promptText));
  const s = document.createElement("span"); s.className = "in-echo"; s.textContent = value;
  curOut.appendChild(s); curOut.appendChild(document.createTextNode("\n"));
};

// ── Running a cell ────────────────────────────────────────────────────────
const ERROR_HINTS = {
  SyntaxError: "Python could not read this line. Look for a missing colon, bracket or quotation mark on or just before the line shown.",
  IndentationError: "The lines inside an if, loop or function must be indented by the same amount. Four spaces is the usual choice.",
  TabError: "This cell mixes tabs and spaces. Use the Tab key in the editor, which always inserts four spaces.",
  NameError: "Python does not recognise a name. Check the spelling and capital letters, and check that you ran the cell that creates it.",
  TypeError: "An operation received the wrong type of value, for example a number added to a string. The functions int(), float() and str() convert between types.",
  ValueError: "The value had the right type but the wrong content, for example int(\"hello\").",
  IndexError: "You asked for a position that does not exist. The first position is 0 and the last is len(...) - 1.",
  ZeroDivisionError: "A number was divided by zero.",
  AttributeError: "This kind of value does not have that method or attribute. Check the spelling, and check the type with type(...).",
  KeyError: "The dictionary does not contain that key.",
  TimeoutError: "Look for a while loop whose condition never becomes False, or a loop that never reaches break.",
  RecursionError: "A function keeps calling itself without stopping."
};

async function runCell(id){
  if (isRunning) return;
  if (!pyReady) { toast("Python is still loading. Try again in a moment."); return; }
  const cm = editors[id]; if (!cm) return;
  isRunning = true;
  const code = cm.getValue();
  S.values[id] = code;
  const outEl = document.getElementById("out-" + id), btn = document.getElementById("run-" + id), stat = document.getElementById("stat-" + id);
  btn.disabled = true; btn.textContent = "Running";
  stat.textContent = ""; stat.className = "cell-stat";
  outEl.innerHTML = "";
  curOut = document.createElement("pre"); curOut.className = "stdout"; outEl.appendChild(curOut);
  await new Promise(r => setTimeout(r, 20));      // let the browser paint "Running"
  let hasError = false;
  kit.arm(CONFIG.timeLimit);
  try {
    await pyodide.runPythonAsync(code, { filename: "<your code>" });
  } catch(e) {
    hasError = true;
    kit.disarm();
    showError(outEl, String(e.message || e));
  } finally {
    kit.disarm();
    try { pyodide.runPython("import sys\nsys.stdout.flush()", { globals: pyodide.toPy({}) }); } catch(_){}
  }
  curOut = null;
  S.outputs[id] = { html: outEl.innerHTML, text: outEl.innerText, hasError, lastRun: new Date().toISOString() };
  stat.textContent = hasError ? "Error" : "Ran " + new Date().toLocaleTimeString([], { hour:"2-digit", minute:"2-digit" });
  stat.className = "cell-stat " + (hasError ? "err" : "ok");
  btn.disabled = false; btn.textContent = "Run";
  isRunning = false;
  markDirty(true);
}

function showError(outEl, msg){
  const lines = msg.replace(/\s+$/, "").split("\n");
  const kept = []; let keep = false, anyFrame = false;
  for (const line of lines) {
    if (line.startsWith("Traceback")) continue;
    if (/^\s{2}File "/.test(line)) { keep = line.includes('"<your code>"'); if (keep) { kept.push(line); anyFrame = true; } continue; }
    if (/^\s{4}/.test(line)) { if (keep) kept.push(line); continue; }
    keep = false; kept.push(line);
  }
  const clean = (anyFrame ? "Traceback (most recent call last):\n" : "") + kept.join("\n")
    .replace(/File "<your code>", line (\d+), in <module>/g, "Line $1 of your code")
    .replace(/File "<your code>", line (\d+), in (\w+)/g, "Line $1 of your code, inside the function $2")
    .replace(/File "<your code>", line (\d+)/g, "Line $1 of your code");
  const pre = document.createElement("pre"); pre.className = "cell-err"; pre.textContent = clean;
  outEl.appendChild(pre);
  const last = kept.filter(l => l.trim()).pop() || "";
  const m = last.match(/^(\w+)(:|$)/);
  if (CONFIG.errorHints && m && ERROR_HINTS[m[1]]) {
    const h = document.createElement("div"); h.className = "err-hint"; h.textContent = "Hint: " + ERROR_HINTS[m[1]];
    outEl.appendChild(h);
  }
}

// ── Code suggestions (Jedi) ───────────────────────────────────────────────
function jediHint(cm){
  if (jediState !== "ready" || isRunning) return null;
  const cur = cm.getCursor(), line = cm.getLine(cur.line);
  let start = cur.ch; while (start > 0 && /[\w]/.test(line[start - 1])) start--;
  const typed = line.slice(start, cur.ch);
  let list = [];
  try { list = JSON.parse(kit.complete(cm.getValue(), cur.line + 1, cur.ch)); } catch(e) { return null; }
  if (!typed.startsWith("_")) list = list.filter(([n]) => !n.startsWith("_"));
  if (!list.length || (list.length === 1 && list[0][0] === typed)) return null;   // nothing new to offer
  return {
    from: CodeMirror.Pos(cur.line, start), to: CodeMirror.Pos(cur.line, cur.ch),
    list: list.map(([name, type]) => ({ text: name, render: (el) => {
      el.innerHTML = `<span>${esc(name)}</span><span class="hint-type">${esc(type)}</span>`; } }))
  };
}
function jediEnabled(){ return CONFIG.allowCompletion && settings.jedi; }
function showHints(cm){
  if (!jediEnabled()) return;
  if (jediState !== "ready") { ensureJedi(); toast("Code suggestions are loading. Try again in a few seconds."); return; }
  cm.showHint({ hint: jediHint, completeSingle: false });
}
function wireSuggestions(cm, id){
  let popT = null, sigT = null;
  cm.on("inputRead", (cm, change) => {
    if (!jediEnabled() || !settings.autoPopup || jediState !== "ready") return;
    const ch = change.text.join("");
    clearTimeout(popT);
    if (!/^[\w.]$/.test(ch)) return;
    popT = setTimeout(() => {
      if (cm.state.completionActive) return;
      const cur = cm.getCursor(), line = cm.getLine(cur.line).slice(0, cur.ch);
      if (/#/.test(line) || /(["']).*$/.test(line.replace(/(["'])(?:(?!\1).)*\1/g, ""))) return;  // not in comments or strings
      const word = (line.match(/[\w]+$/) || [""])[0];
      if (line.endsWith(".") || word.length >= 2) cm.showHint({ hint: jediHint, completeSingle: false });
    }, 180);
  });
  const tip = document.getElementById("sig-" + id);
  cm.on("cursorActivity", () => {
    clearTimeout(sigT);
    if (!jediEnabled() || !settings.sigHints || jediState !== "ready") { tip.hidden = true; return; }
    sigT = setTimeout(() => {
      if (isRunning) return;
      const cur = cm.getCursor();
      let data = null;
      try { const s = kit.signature(cm.getValue(), cur.line + 1, cur.ch); data = s ? JSON.parse(s) : null; } catch(e) {}
      if (!data) { tip.hidden = true; return; }
      const ps = data.params.map((p, i) => i === data.index ? `<b>${esc(p)}</b>` : esc(p)).join(", ");
      tip.innerHTML = `${esc(data.name)}(${ps})` + (data.doc ? `<span class="sig-doc">${esc(data.doc)}</span>` : "");
      tip.hidden = false;
    }, 250);
  });
  cm.on("blur", () => setTimeout(() => { tip.hidden = true; }, 200));
}

// ── Paper parsing ─────────────────────────────────────────────────────────
function parseFrontmatter(text){
  const m = text.match(/^---\n([\s\S]*?)\n---\n/); if (!m) return {};
  const o = {};
  m[1].split("\n").forEach(line => { const i = line.indexOf(":"); if (i > 0) o[line.slice(0, i).trim()] = line.slice(i + 1).trim(); });
  return o;
}
function parseExam(text){
  const body = text.replace(/^---\n[\s\S]*?\n---\n/, "");
  const out = [], fence = /^```([^\n]*)\n([\s\S]*?)^```[ \t]*$/gm;
  let last = 0, heading = "", q = 0, n = 0, m;
  const scanProse = prose => {
    for (const h of prose.matchAll(/^(#{2,3})\s+(.+)$/gm)) {
      if (h[1] === "##") { const mm = h[2].match(/^Question\s+(\d+)/i); q = mm ? +mm[1] : 0; }
      heading = h[2].trim();
    }
  };
  while ((m = fence.exec(body)) !== null) {
    if (m.index > last) { const prose = body.slice(last, m.index); scanProse(prose); out.push({ type:"markdown", content:prose }); }
    const info = m[1].trim(), kind = info.split(/\s+/)[0], arg = info.slice(kind.length).trim();
    const src = m[2].replace(/\n$/, "");
    const shortHead = heading.replace(/\s*\(.*?\)\s*$/, "");
    if (kind === "python" && arg === "setup") out.push({ type:"setup", content:src });
    else if (kind === "python") out.push({ type:"code", id:"b" + (n++), q, label: arg || shortHead, content:src });
    else if (kind === "answer") out.push({ type:"answer", id:"b" + (n++), q, label: arg || shortHead, content:src });
    else if (kind === "fields") out.push({ type:"fields", id:"b" + (n++), q, label: arg || shortHead,
      labels: src.split("\n").map(s => s.trim()).filter(Boolean) });
    else out.push({ type:"display", lang: kind || "text", content:src });
    last = m.index + m[0].length;
  }
  if (last < body.length) { const prose = body.slice(last); scanProse(prose); out.push({ type:"markdown", content:prose }); }
  return out;
}

// Minimal Markdown: headings, bold, italics, inline code, lists, tables, quotes, rules.
function mdToHtml(md){
  const codes = [];
  let h = md.replace(/`([^`\n]+)`/g, (_, c) => { codes.push(esc(c)); return `\u0000${codes.length - 1}\u0000`; });
  h = h.replace(/^---$/gm, "<hr>");
  for (let i = 6; i >= 1; i--) h = h.replace(new RegExp(`^${"#".repeat(i)}\\s+(.+)$`, "gm"), `<h${i}>$1</h${i}>`);
  h = h.replace(/((?:^\|.+\|[ \t]*\n?)+)/gm, block => {
    const rows = block.trim().split("\n").filter(r => !/^\|[-| :]+\|\s*$/.test(r));
    return "<table>" + rows.map((r, i) => { const t = i === 0 ? "th" : "td";
      return "<tr>" + r.split("|").slice(1, -1).map(c => `<${t}>${c.trim()}</${t}>`).join("") + "</tr>"; }).join("") + "</table>\n\n";
  });
  h = h.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  h = h.replace(/(^|[^\w*])\*([^*\n]+)\*(?!\w)/g, "$1<em>$2</em>");
  h = h.replace(/((?:^> .*\n?)+)/gm, b => "<blockquote>" + b.trim().split("\n").map(l => l.replace(/^> ?/, "")).join("<br>") + "</blockquote>\n\n");
  h = h.replace(/((?:^[-*] .+\n?)+)/gm, b => "<ul>" + b.trim().split("\n").map(l => `<li>${l.replace(/^[-*] /, "")}</li>`).join("") + "</ul>\n\n");
  h = h.replace(/((?:^\d+\. .+\n?)+)/gm, b => "<ol>" + b.trim().split("\n").map(l => `<li>${l.replace(/^\d+\. /, "")}</li>`).join("") + "</ol>\n\n");
  h = h.split(/\n{2,}/).map(b => { b = b.trim(); if (!b || /^<(h\d|ul|ol|table|hr|blockquote)/.test(b)) return b;
    return `<p>${b.replace(/\n/g, "<br>")}</p>`; }).join("\n");
  return h.replace(/\u0000(\d+)\u0000/g, (_, i) => `<code>${codes[+i]}</code>`);
}
function highlight(code, numbered){
  const lines = [[]];
  CodeMirror.runMode(code, "python", (text, style) => {
    if (text === "\n") { lines.push([]); return; }
    const t = esc(text);
    lines[lines.length - 1].push(style ? `<span class="${style.split(" ").map(s => "cm-" + s).join(" ")}">${t}</span>` : t);
  });
  if (numbered) return lines.map(l => `<span class="pl">${l.join("") || " "}</span>`).join("");
  return lines.map(l => l.join("")).join("\n");
}

// ── Rendering ─────────────────────────────────────────────────────────────
function renderExam(){
  const sheet = document.getElementById("sheet");
  sheet.innerHTML = `<div id="print-head" class="print-only"></div>`;
  editors = {};
  let firstQ = true;
  for (const b of blocks) {
    if (b.type === "setup") continue;
    if (b.type === "markdown") {
      const d = document.createElement("div"); d.className = "md"; d.innerHTML = mdToHtml(b.content);
      d.querySelectorAll("h2").forEach(h => { if (/^Question\s+\d/i.test(h.textContent)) {
        h.id = "q-" + h.textContent.match(/\d+/)[0]; h.classList.add("q-head"); if (firstQ) { h.classList.add("first-q"); firstQ = false; } } });
      sheet.appendChild(d); continue;
    }
    if (b.type === "display") {
      const pre = document.createElement("pre"); pre.className = "display-code hl";
      pre.innerHTML = /^(py|python|text)$/.test(b.lang) ? highlight(b.content, true) : esc(b.content);
      sheet.appendChild(pre); continue;
    }
    const wrap = document.createElement("div"); wrap.className = "cell " + b.type + "-cell"; wrap.id = "cell-" + b.id;
    if (b.type === "code") {
      wrap.innerHTML = `
        <div class="cell-bar">
          <span class="cell-lbl">${esc(b.label || "Code")}</span>
          <span class="cell-stat" id="stat-${b.id}"></span>
          <span class="run-hint">Ctrl+Enter to run</span>
          <button class="mini-btn" data-reset="${b.id}" title="Put back the starting code">Reset</button>
          <button class="run-btn" id="run-${b.id}" ${pyReady ? "" : "disabled"}>${pyReady ? "Run" : "Loading"}</button>
        </div>
        <div id="cm-${b.id}"></div>
        <div class="sig-tip" id="sig-${b.id}" hidden></div>
        <pre class="print-code hl" id="pc-${b.id}"></pre>
        <div class="cell-out" id="out-${b.id}" aria-live="polite"></div>`;
      sheet.appendChild(wrap);
      const value = S.values[b.id] != null ? S.values[b.id] : b.content;
      const cm = CodeMirror(document.getElementById("cm-" + b.id), {
        value, mode:"python", theme: codeThemeName(), lineNumbers:true, indentUnit:4, tabSize:4, indentWithTabs:false,
        lineWrapping: settings.wrap, viewportMargin: Infinity, matchBrackets:true, autoCloseBrackets: settings.closeBrackets,
        extraKeys: {
          "Tab": cm => cm.somethingSelected() ? cm.execCommand("indentMore") : cm.execCommand("insertSoftTab"),
          "Shift-Tab": cm => cm.execCommand("indentLess"),
          "Ctrl-Enter": () => runCell(b.id), "Cmd-Enter": () => runCell(b.id),
          "Ctrl-Space": cm => showHints(cm), "Ctrl-/": "toggleComment", "Cmd-/": "toggleComment"
        }
      });
      cm.getWrapperElement().setAttribute("aria-label", "Code editor: " + (b.label || "code"));
      cm.on("change", () => { S.values[b.id] = cm.getValue(); markDirty(); });
      editors[b.id] = cm;
      wireSuggestions(cm, b.id);
      wrap.querySelector(".run-btn").onclick = () => runCell(b.id);
      wrap.querySelector("[data-reset]").onclick = () => {
        if (!confirm("Put back the starting code for this cell? Your code in this cell will be replaced.")) return;
        cm.setValue(b.content); document.getElementById("out-" + b.id).innerHTML = ""; delete S.outputs[b.id]; markDirty();
      };
      const o = S.outputs[b.id];
      if (o) { document.getElementById("out-" + b.id).innerHTML = o.html || "";
        const st = document.getElementById("stat-" + b.id); st.textContent = o.hasError ? "Error" : "Ran earlier"; st.className = "cell-stat " + (o.hasError ? "err" : "ok"); }
    } else if (b.type === "answer") {
      wrap.innerHTML = `
        <div class="cell-bar"><span class="cell-lbl">${esc(b.label || "Your answer")}</span><span class="wc" id="wc-${b.id}"></span></div>
        <textarea class="ans" id="ta-${b.id}" rows="3" placeholder="Type your answer here." aria-label="Answer ${esc(b.label || "")}"></textarea>
        <div class="print-text" id="pt-${b.id}"></div>`;
      sheet.appendChild(wrap);
      const ta = wrap.querySelector("textarea");
      ta.value = S.values[b.id] != null ? S.values[b.id] : b.content;
      const upd = () => { S.values[b.id] = ta.value; autogrow(ta); wordCount(b.id, ta.value.trim() === b.content.trim() ? "" : ta.value); };
      ta.addEventListener("input", () => { upd(); markDirty(); });
      upd();
    } else if (b.type === "fields") {
      const vals = Array.isArray(S.values[b.id]) ? S.values[b.id] : b.labels.map(() => "");
      wrap.innerHTML = `<div class="cell-bar"><span class="cell-lbl">${esc(b.label || "Your answers")}</span></div>` +
        b.labels.map((l, i) => `<div class="field-row"><label for="f-${b.id}-${i}">${mdInline(l)}</label>
          <div><textarea class="ans" id="f-${b.id}-${i}" rows="1"></textarea><div class="print-text" id="pf-${b.id}-${i}"></div></div></div>`).join("");
      sheet.appendChild(wrap);
      b.labels.forEach((l, i) => {
        const ta = document.getElementById(`f-${b.id}-${i}`);
        ta.value = vals[i] || "";
        ta.addEventListener("input", () => { const arr = b.labels.map((_, j) => document.getElementById(`f-${b.id}-${j}`).value);
          S.values[b.id] = arr; autogrow(ta); markDirty(); });
        autogrow(ta);
      });
    }
  }
  sheet.appendChild(endBanner());
  buildNav();
  refreshLayout();
}
function mdInline(s){ return mdToHtml(s).replace(/^<p>|<\/p>$/g, ""); }
function autogrow(ta){ if (!ta.offsetParent) return; ta.style.height = "auto"; ta.style.height = (ta.scrollHeight + 2) + "px"; }
function wordCount(id, text){
  const n = (text.trim().match(/\S+/g) || []).length;
  const el = document.getElementById("wc-" + id); if (el) el.textContent = n ? `${n} word${n === 1 ? "" : "s"}` : "";
}
function endBanner(){
  const d = document.createElement("div"); d.id = "end-banner";
  const real = CONFIG.kind === "exam";
  d.innerHTML = `
    <h2>End of ${real ? "examination" : "paper"}</h2>
    <p style="margin-bottom:16px">${real
      ? "You have reached the end of the exam. Before you finish, complete all three steps below."
      : "You have reached the end of this " + (CONFIG.kind === "sample" ? "sample" : "practice") + " paper. The three steps below are the steps you will follow in the real exam, so it is worth practising them now."}</p>
    <div class="steps">
      <div class="step"><span class="n">1</span><div><strong>Print a PDF for the assessor.</strong> Click <strong>Print / PDF</strong> in the toolbar. In the print window, set the destination to <em>Save as PDF</em> and save the file. The PDF shows all of your code, outputs and written answers in full.</div></div>
      <div class="step"><span class="n">2</span><div><strong>Save your submission file (.json).</strong> Click <strong>Save</strong> in the toolbar. The .json file holds all of your work, and this tool can open it again later.</div></div>
      <div class="step"><span class="n">3</span><div><strong>${real ? "Upload to Moodle and confirm with your invigilator." : "Keep your files."}</strong> ${real
        ? "Upload your .json file and your PDF to the exam submission link on Moodle. Then raise your hand so your invigilator can confirm your submission before you close your computer."
        : "Keep your PDF and .json file so you can review them with your lecturer. The <strong>Export .ipynb</strong> button also creates a Jupyter notebook version of your answers."}</div></div>
    </div>`;
  return d;
}

// ── Navigation and progress ───────────────────────────────────────────────
function questionList(){
  const qs = [];
  const re = /^##\s+Question\s+(\d+)\s*[:.]?\s*(.*?)\s*\((\d+)\s*marks?\)\s*$/gim;
  for (const m of SRC.matchAll(re)) qs.push({ num:+m[1], label:m[2].trim(), marks:+m[3] });
  return qs;
}
function attempted(b){
  const v = S.values[b.id];
  if (b.type === "fields") return Array.isArray(v) && v.some(x => x && x.trim());
  if (v == null) return false;
  return v.trim() !== "" && v.replace(/\s+/g, "") !== (b.content || "").replace(/\s+/g, "");
}
function buildNav(){
  const nav = document.getElementById("nav"); nav.innerHTML = "";
  questionList().forEach(q => {
    const mine = blocks.filter(b => b.q === q.num && b.id && !/optional/i.test(b.label || ""));
    const done = mine.filter(attempted).length;
    const a = document.createElement("a"); a.className = "nav-item"; a.href = "#q-" + q.num;
    a.innerHTML = `<span class="nav-num">${q.num}</span>
      <span class="nav-lbl">${esc(q.label)}<div class="nav-bar"><i style="width:${mine.length ? Math.round(100 * done / mine.length) : 0}%"></i></div></span>
      <span class="nav-meta">${q.marks} marks<br>${done}/${mine.length} started</span>`;
    a.onclick = e => { e.preventDefault(); const h = document.getElementById("q-" + q.num);
      if (h) scrollMainTo(h);
      document.getElementById("side").classList.remove("open"); document.getElementById("scrim").classList.remove("on"); };
    nav.appendChild(a);
  });
}

// ── Begin / resume ────────────────────────────────────────────────────────
async function beginExam(resume){
  if (resume) {
    const saved = readStore(); if (!saved) return beginExam(false);
    S = { name:saved.name, startedAt:saved.startedAt || Date.now(), values:saved.values || {}, outputs:saved.outputs || {} };
    await maybePickFile();
  } else {
    const name = document.getElementById("sname").value.trim();
    if (!name) { alert("Please enter your full name."); document.getElementById("sname").focus(); return; }
    S = { name, startedAt: Date.now(), values:{}, outputs:{} };
    await maybePickFile();
  }
  startApp();
}
async function maybePickFile(){
  const want = document.getElementById("use-file").checked;
  if (!want || !("showSaveFilePicker" in window)) return;
  try {
    fileHandle = await window.showSaveFilePicker({ suggestedName: fileName("json"),
      types: [{ description:"Exam work (.json)", accept:{ "application/json":[".json"] } }] });
  } catch(e) { fileHandle = null; }
}
function startApp(){
  closeDrawer();
  document.getElementById("name-screen").style.display = "none";
  document.getElementById("app").style.display = "flex";
  document.body.classList.add("in-app");
  document.getElementById("h-title").textContent = [META.module, META.title].filter(Boolean).join(": ");
  document.getElementById("h-student").textContent = S.name;
  document.getElementById("sd-name").textContent = S.name;
  renderExam();
  updateSaveInfo();
  writeStore();
  if (fileHandle) writeFile();
  setInterval(tickTimer, 1000); tickTimer();
  setInterval(() => { if (dirty) flushSaves(); }, 15000);
}
function tickTimer(){
  const el = document.getElementById("timer");
  const end = S.startedAt + CONFIG.duration * 60000, left = Math.round((end - Date.now()) / 1000);
  const f = s => { s = Math.abs(s); const h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60), x = s % 60;
    return (h ? h + ":" + String(m).padStart(2, "0") : m) + ":" + String(x).padStart(2, "0"); };
  el.textContent = left >= 0 ? f(left) + " left" : "Time is up (+" + f(left) + ")";
  el.className = left < 0 ? "over" : left < 600 ? "low" : "";
}

// ── Saving ────────────────────────────────────────────────────────────────
let saveT = null;
function markDirty(immediate){
  dirty = true; setSave("pending");
  clearTimeout(saveT);
  saveT = setTimeout(flushSaves, immediate ? 50 : 1500);
  clearTimeout(markDirty.navT); markDirty.navT = setTimeout(buildNav, 600);
}
async function flushSaves(){
  writeStore();
  if (fileHandle) await writeFile(); else setSave("browser");
  dirty = false;
}
function readStore(){ try { return JSON.parse(localStorage.getItem(STORE_KEY) || "null"); } catch(e){ return null; } }
function writeStore(){
  try { localStorage.setItem(STORE_KEY, JSON.stringify(Object.assign({ savedAt: Date.now() }, S))); }
  catch(e){ console.warn("Browser save failed", e); }
}
async function writeFile(){
  try { const w = await fileHandle.createWritable(); await w.write(JSON.stringify(buildJSON(), null, 2)); await w.close(); setSave("file"); }
  catch(e){ console.warn(e); setSave("error"); }
}
async function saveNow(){
  if (!S.name) return;
  writeStore();
  if (fileHandle) { await writeFile(); toast("Saved to " + (fileHandle.name || "your file")); }
  else { download(fileName("json"), JSON.stringify(buildJSON(), null, 2), "application/json"); setSave("download"); toast("Downloaded " + fileName("json")); }
  dirty = false;
}
function setSave(s){
  const el = document.getElementById("save-status");
  const t = new Date().toLocaleTimeString([], { hour:"2-digit", minute:"2-digit" });
  const map = { pending:["Saving",  "var(--muted)"], browser:["Saved in browser " + t, "var(--success)"],
    file:["Saved to file " + t, "var(--success)"], download:["Downloaded " + t, "var(--success)"], error:["File save failed", "var(--error)"] };
  const [txt, col] = map[s] || ["", ""]; el.textContent = txt; el.style.color = col;
}
function updateSaveInfo(){
  document.getElementById("sd-save-info").innerHTML = fileHandle
    ? `Your work saves automatically to <b>${esc(fileHandle.name || "your file")}</b> and to this browser.`
    : `Your work saves automatically to this browser. Press <b>Save</b> to download a .json copy as well.`;
}
function fileName(ext){
  const safe = (S.name || "student").replace(/[^a-z0-9]+/gi, "_").replace(/^_|_$/g, "").toLowerCase();
  return `${EXAM_ID}_${safe}_${new Date().toISOString().slice(0, 10)}.${ext}`;
}
function buildJSON(){
  const cells = blocks.filter(b => b.id).map(b => {
    const o = S.outputs[b.id] || {};
    const base = { id:b.id, type:b.type, question:b.q, label:b.label || "" };
    if (b.type === "code") return Object.assign(base, { student_code: S.values[b.id] != null ? S.values[b.id] : b.content,
      output_text:o.text || "", output_html:o.html || "", has_error:!!o.hasError, last_run:o.lastRun || null });
    if (b.type === "answer") return Object.assign(base, { answer_text: S.values[b.id] != null ? S.values[b.id] : b.content });
    return Object.assign(base, { fields: b.labels.map((l, i) => ({ label:l, answer:(S.values[b.id] || [])[i] || "" })) });
  });
  return { format:"pdp-exam/1", exam_id:EXAM_ID, exam_title:META.title || "", module:META.module || "", session:META.session || "",
    student_name:S.name, started_at: S.startedAt ? new Date(S.startedAt).toISOString() : null,
    exported_at:new Date().toISOString(), cells };
}
function download(name, text, type){
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = document.createElement("a"); a.href = url; a.download = name; document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

// Opening a saved .json file
function pickLoadFile(){ document.getElementById("file-in").value = ""; document.getElementById("file-in").click(); }
async function onLoadFile(e){
  const f = e.target.files[0]; if (!f) return;
  let data; try { data = JSON.parse(await f.text()); } catch(err){ alert("That file could not be read. Choose a .json file saved by this exam tool."); return; }
  if (!data || !Array.isArray(data.cells)) { alert("That file was not saved by this exam tool."); return; }
  if (data.exam_id && data.exam_id !== EXAM_ID &&
      !confirm(`That file belongs to a different paper (${data.exam_title || data.exam_id}). Open it in this paper anyway? Answers are matched by position, so some may land in the wrong place.`)) return;
  if (S.name && !confirm("Replace the work on screen with the work in this file?")) return;
  const values = {}, outputs = {};
  data.cells.forEach(c => {
    if (!c.id) return;
    if (c.type === "code") { values[c.id] = c.student_code || "";
      if (c.output_html || c.output_text) outputs[c.id] = { html:c.output_html || esc(c.output_text || ""), text:c.output_text || "", hasError:!!c.has_error, lastRun:c.last_run }; }
    else if (c.type === "answer") values[c.id] = c.answer_text || "";
    else if (c.type === "fields") values[c.id] = (c.fields || []).map(x => x.answer || "");
  });
  const started = data.started_at ? Date.parse(data.started_at) : Date.now();
  S = { name: data.student_name || S.name || "Student", startedAt: started, values, outputs };
  if (document.getElementById("app").style.display !== "flex") startApp();
  else { renderExam(); document.getElementById("h-student").textContent = S.name; document.getElementById("sd-name").textContent = S.name; }
  writeStore(); toast("Opened " + f.name);
}

// ── Jupyter export ────────────────────────────────────────────────────────
function exportIpynb(){
  const lines = s => { const a = String(s).split("\n"); return a.map((l, i) => i < a.length - 1 ? l + "\n" : l).filter((l, i, arr) => !(i === arr.length - 1 && l === "")); };
  const md = s => ({ cell_type:"markdown", metadata:{}, source: lines(s) });
  const quote = s => (s && s.trim()) ? s.split("\n").map(l => "> " + l).join("\n") : "> *(no answer)*";
  const cells = [md(`# ${META.module || ""}\n## ${META.title || ""}\n\n**Student:** ${S.name}  \n**Exported:** ${new Date().toLocaleString()}`)];
  for (const b of blocks) {
    if (b.type === "setup") continue;
    if (b.type === "markdown") { const t = b.content.trim(); if (t) cells.push(md(t)); }
    else if (b.type === "display") cells.push(md("```" + (b.lang === "text" ? "python" : b.lang) + "\n" + b.content + "\n```"));
    else if (b.type === "code") {
      const o = S.outputs[b.id];
      const outputs = o && o.text ? [{ output_type:"stream", name: o.hasError ? "stderr" : "stdout", text: lines(o.text) }] : [];
      cells.push({ cell_type:"code", execution_count:null, metadata:{ exam_label: b.label || "" },
        source: lines(S.values[b.id] != null ? S.values[b.id] : b.content), outputs });
    }
    else if (b.type === "answer") cells.push(md(`**Your answer: ${b.label || ""}**\n\n` + quote(S.values[b.id] != null ? S.values[b.id] : b.content)));
    else if (b.type === "fields") cells.push(md(`**Your answers: ${b.label || ""}**\n\n` +
      b.labels.map((l, i) => `- **${l}** ${(S.values[b.id] || [])[i] || "*(no answer)*"}`).join("\n")));
  }
  cells.forEach((c, i) => { c.id = "cell-" + String(i).padStart(3, "0"); });
  const nb = { cells, metadata:{ kernelspec:{ display_name:"Python 3", language:"python", name:"python3" },
    language_info:{ name:"python", version:"3.12" } }, nbformat:4, nbformat_minor:5 };
  download(fileName("ipynb"), JSON.stringify(nb, null, 1), "application/x-ipynb+json");
  toast("Downloaded " + fileName("ipynb"));
}

// ── Print ─────────────────────────────────────────────────────────────────
function scrollMainTo(el){
  const main = document.getElementById("main");
  const top = el.getBoundingClientRect().top - main.getBoundingClientRect().top + main.scrollTop - 12;
  main.scrollTo({ top, behavior: settings.reduceMotion ? "auto" : "smooth" });
}
function preparePrint(){
  for (const id in editors) if (editors[id].state.completionActive) editors[id].closeHint();
  for (const b of blocks) {
    if (!b.id) continue;
    if (b.type === "code") {
      const code = editors[b.id] ? editors[b.id].getValue() : (S.values[b.id] || b.content);
      document.getElementById("pc-" + b.id).innerHTML = highlight(code, true);
    } else if (b.type === "answer") {
      const v = S.values[b.id] != null ? S.values[b.id] : b.content, el = document.getElementById("pt-" + b.id);
      el.textContent = v.trim() ? v : "(no answer)"; el.classList.toggle("empty", !v.trim());
    } else if (b.type === "fields") {
      b.labels.forEach((l, i) => { const v = (S.values[b.id] || [])[i] || "", el = document.getElementById(`pf-${b.id}-${i}`);
        el.textContent = v.trim() ? v : "(no answer)"; el.classList.toggle("empty", !v.trim()); });
    }
  }
  const mins = S.startedAt ? Math.round((Date.now() - S.startedAt) / 60000) : 0;
  document.getElementById("print-head").innerHTML =
    `<b>${esc(S.name)}</b><br>${esc(META.module || "")}: ${esc(META.title || "")}${META.session ? " (" + esc(META.session) + ")" : ""}<br>` +
    `Printed ${esc(new Date().toLocaleString())}. Time since starting: ${mins} minutes.`;
}

// ── Utilities ─────────────────────────────────────────────────────────────
function toast(msg){ const t = document.getElementById("toast"); t.textContent = msg; t.classList.add("show");
  clearTimeout(toast.t); toast.t = setTimeout(() => t.classList.remove("show"), 1900); }
function esc(s){ return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"); }
