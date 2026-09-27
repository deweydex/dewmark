# What dewlab has built since PR #181 that dewmark should reuse

Scope: dewlab moved from #181 (2026-09-12, dewmark's last commit, `87e465f6`) to #414 (`a6d2c6d4`, 2026-09-27). That is 248 commits, 8 of which touched the engine or widget files. Both repos were read-only for this work. Every probe ran in `/tmp/claude-0/-home-user/9d1373ae-0961-5985-b2c8-adad08e8b8ed/scratchpad/engine-probe/` against headless Chromium 141 and a local copy of Pyodide 0.28.3.

## 0. Headline findings

1. **dewlab's Python engine can't run from a `file://` exam as written.** It is an ES-module Worker (`new Worker(new URL("./pyodide-worker.js", import.meta.url), {type:"module"})`, `assets/pyodide-engine.js:110`). From `file://`, Chromium throws `SecurityError … cannot be accessed from origin 'null'` (verified). dewlab's own downloaded copy of a tutorial falls back to main-thread Pyodide with no Stop button (DECISIONS_LOG 7.77).
2. **dewlab has no `input()` and no timeout.** 7.240 says: "A cell cannot wait for typing, so the page says so and writes the typing down." grep finds no `setStdin`, no `Atomics`, no watchdog. The hand-built PDP exams already do better on both counts: `builtins.input` is backed by `window.prompt()`, and a `sys.settrace` deadline gives a 10 s limit.
3. **Verified: an offline-safe engine can have `input()` and Stop together.**
   - A blob-URL *classic* Worker starts from `file://`.
   - Pyodide 0.28.3's `pyodide.ffi.run_sync` (JSPI) lets `input()` await a `postMessage` reply from the page. The Worker returned `49` for `int(input())*int(input())`.
   - `worker.terminate()` stops `while True: pass`. A warm restart took about 1.6 s.
   - When the page is served over http with COOP/COEP headers, the SharedArrayBuffer interrupt also works and the interpreter survives (`KeyboardInterrupt`, then `'alive after interrupt'`).
4. **Pinned versions:**
   - Pyodide **0.28.3** (Python 3.13; numpy 2.2.5, pandas 2.3.1, matplotlib 3.8.4). dewmark and the PDP exams are on **0.27.4**.
   - CodeMirror 6 (`@codemirror/view` 6.36.8 and others). The PDP exams use CodeMirror **5.65.16** from cdnjs.
   - KaTeX **0.16.22**; @fontsource Lexend and OpenDyslexic **5.3.0**; coi-serviceworker **0.1.7**; esbuild **0.25.5**.
5. **The sibling-repo precedent is "port in shape, not code; no twinned files; record the dewlab commit".** That is dewstack's rule, and the repo was later partly absorbed back into dewlab. The engine proper is small (1,152 lines) but changes often. The right mechanism for an exam that must work offline is a pinned, hash-stamped copy inlined into each built exam, never a live link.

---

## 1. Baseline: what dewmark and the hand-built exams do today

**dewmark (`/home/user/dewlab/dewmark/`):**
- `assets/exam-page.js:715` loads `https://cdn.jsdelivr.net/pyodide/v0.27.4/full/`, overridable with `window.DEWMARK_PYTHON_BASE`, on the main thread.
- Packages come through `micropip.install(...)` (`:756`), which needs the network. dewlab uses `loadPackage` from the Pyodide lockfile instead.
- Students type into a plain `<textarea class="dm-code">`. There is no Stop button; OPEN_QUESTIONS Q8 accepts "close the page and reopen".
- There is no `input()`, no dark mode and no font choice (no `data-theme` or `prefers-color-scheme` in `exam-page.css`).
- Maths is rendered at build time by `latex2mathml` (`build_exam.py:33`).
- `docs/DEVELOPMENT.md:10` says "dewmark … deliberately shares no code, styles, or build machinery with [dewlab]". That makes the lift into a separate repo clean.
- CI lives in dewlab's `.github/workflows/tests.yml:103` (the `dewmark:` job) and has to move with it.

**PDP 5N2927 hand-built exams (structure only; read from the Sample exam):**
- Main-thread Pyodide 0.27.4 from jsdelivr.
- CodeMirror 5.65.16 plus hint, matchbrackets, closebrackets and comment add-ons, all from cdnjs.
- Atkinson Hyperlegible and Lexend from Google Fonts; OpenDyslexic from `cdn.jsdelivr.net/npm/@fontsource/opendyslexic@5`.
- A `KIT_PY` module (sketched below): `_tracer` with `sys.settrace` gives the 10 s deadline, and `_exam_input` calls `js.examAsk`, which calls `window.prompt()`. Time spent typing is added back to the deadline.
- Jedi `complete()` for Ctrl+Space.
- Saving goes to a File System Access `fileHandle.createWritable()`, with a JSON download as fallback, plus localStorage every few seconds. There is a `beforeprint` handler and a reading ruler.
- **Every one of those CDN loads fails in an offline room.** The exam only works where the browser cache is already warm.

```python
# KIT_PY (from the Sample exam), the shape only:
def arm(limit): _deadline[0] = time.monotonic() + limit; sys.settrace(_tracer)
def _exam_input(prompt=""): value = js.examAsk(text)   # window.prompt()
```

---

## 2. The Python engine: `assets/pyodide-engine.js` (720 lines, 23.7 KB) and `assets/pyodide-worker.js` (432 lines, 14.5 KB)

### API surface (`pyodide-engine.js` exports)

| Group | Exports |
|---|---|
| Setup | `configure({getOutputEl, onStatus, packages, dataBase, rerunCell, isBusy})` (`:48`), `applyOutputEvent`, `clearOutput` |
| Lifecycle | `ensureBooted()` (`:454`), `restart()` (`:464`), `engineMode()` → `"worker"` or `"main-thread"`, `canStop()` (`:503`, true only on the Worker path with a real interrupt buffer), `requestInterrupt` |
| Running | `runCell(cellId, code, label)` (`:542`), `resetPageState()`, `sliderStripFor`, `clearWidgets` |
| Editor help | `hoverDoc`, `signatureHelp`, `jediCompletions`, `pageNamesCompletion`, `describeGlobals` |
| Files (Notebook only) | `mountNative`, `mountIdbfs`, `syncFs`, `unmount`, `listDir`, `readFile`, `writeFile`, `deleteFile`, `mkdir`, `addImportPath`, `setWorkingDirectory`, `changedImportedModules`, `reloadModules` |

The Worker protocol is `{type, id, …}` in and `{type:"response", id, result|error}` out. There are also one-way `status`, `output` and `jedi-ready` pushes. Message types, from `pyodide-worker.js:354-420`:

- `boot`, `set-interrupt-buffer`, `run-cell`, `compare`, `reset-page-state`, `load-toolkit`
- `hover-doc`, `signature-help`, `page-names`, `jedi-complete`, `describe-globals`, `query-rows`, `widget-changed`
- `fs-*` and `add-import-path`

### How Pyodide is loaded

- **CDN by default, pinned, overridable with one global** (DECISIONS_LOG 0.17): `globalThis.DEWLAB_PYODIDE_BASE || "https://cdn.jsdelivr.net/pyodide/v0.28.3/full/"`.
- The version string is repeated in five places:
  - `assets/tutorial-runtime.js:11` (`PYODIDE_VERSION`)
  - `assets/pyodide-engine.js:315`
  - `build.py:5933` (`PYODIDE_CLASSIC`, used by downloaded copies)
  - `compose/dewmini.js:9`
  - `dev/fetch_pyodide.py:33`
- **Self-hosting:** `dev/fetch_pyodide.py` downloads the release tarball and keeps the core files plus the wheels that `resolve()` walks from `pyodide-lock.json`.
  - `BASELINE = ["numpy","pandas","matplotlib","jedi","pyodide-http","sqlite3"]` comes to about 30–32 MB.
  - Output goes to `dev/pyodide/` or `assets/vendor/pyodide/`; both are gitignored.
  - dewstack already adapted this script as `tools/fetch_pyodide.py --packages sqlite3` (about 13 MB).
  - **Measured core with no packages: 12.3 MB** (`pyodide.asm.wasm` 8.6 MB, `python_stdlib.zip` 2.4 MB, `pyodide.asm.js` 1.07 MB, plus `pyodide.js`/`.mjs`/lock). An exam that needs only plain Python costs 12 MB, not 30.
- Packages load with `pyodide.loadPackage(msg.packages)` (`pyodide-worker.js:237`), never micropip. The default is `["numpy","pandas","matplotlib","sqlite3"]` (engine `:5`).
- `pyodide-http` is also loaded and `patch_all()`ed (`:239-245`), so `urllib`/`requests` go through the browser (7.100). **An exam engine should drop this.** It is a network door, and 7.100 notes that a hung request can't be stopped.

### Stop (interrupt), cross-origin isolation and timeouts

- Stop: `interruptBuffer = new SharedArrayBuffer(4)`, posted as `set-interrupt-buffer`, then `pyodide.setInterruptBuffer(...)`. Writing `2` (SIGINT) stops the run (engine `:145-153`). This is only set when `globalThis.crossOriginIsolated`.
- On GitHub Pages, isolation comes from `assets/vendor/coi-serviceworker.js` (v0.1.7, 4.7 KB). `build.py:7666` copies it to the site root. The first visit needs one reload before the headers apply (7.77).
- **Service workers can't register on `file://`.** `standalone_html()` strips the shim (`build.py:6029`).
- **Timeouts: none.** A tight loop runs until Stop, or forever on the main-thread path.
- **`input()`: none.** Widgets (`text_input`, `dropdown`, `slider`) work in the Worker through `widget-changed` messages (#274, `f07b4c36`). `button()` raises in the Worker (7.77, 7.264).

### Coupling to dewlab

- **ES module imports:**
  - `pyodide-engine.js` imports `./module-watch.js` (63 lines) and `./cell-widgets.js` (140 lines).
  - The worker imports `./module-watch.js`.
  - The full set of files needed to run the engine is `DEWMINI_ASSET_FILES` (`build.py:6344`): engine, worker, module-watch, cell-widgets, `tutorial_tools.py`.
- **`tutorial_tools.py` is fetched by URL** in the worker (`fetch(msg.toolsSourceUrl)`, `pyodide-worker.js:249`). That fails from a blob Worker on `file://`. dewlab's downloaded copy sidesteps it by inlining the source into the manifest (`manifest["toolsSource"]`, `build.py:6040`).
- **The worker calls `tools.run_cell_report(cellId, emit, code, expect, label)`, `tools._page_globals`, `tools._load_toolkit`, `tools._set_widget_value` and more.** It is bound to `tutorial_tools.py`'s internals, not to plain Pyodide.
- **`__name__` is seeded as `"__dewlab__"`** (`RESEED_GLOBALS_SOURCE`). Per 7.240, `if __name__ == "__main__": main()` therefore silently does nothing. That is fatal for a programming exam where students are taught that guard. dewmark must run student code as `__main__`.
- Dependence on `build.py`: nothing at runtime. `build.py` only pins the classic-script URL and injects `DEWLAB_PYODIDE_BASE` into the Notebook download (`build.py:6429`).

### Probe results (scratchpad `probe.html`, `probe2.html`; Chromium 141, Pyodide 0.28.3)

| Context | `crossOriginIsolated` / SAB | Module Worker | Blob classic Worker | `input()` via JSPI `run_sync` | Stop |
|---|---|---|---|---|---|
| `file://` page | false / undefined | SecurityError | works (boot 1.7 s from local server) | **works** on main thread (`"Hello Ada"`) and in the Worker via postMessage (`"49"`) | `worker.terminate()`: works, restart about 1.6 s, state lost |
| `http://127.0.0.1` with COOP/COEP sent **by the server** (no service worker) | true / function | (not tested; would work) | works | works | interrupt buffer: `KeyboardInterrupt`, state kept |

Other probe results:

- **`sys.settrace` timeout costs about 2.6×** on a tight loop (300 ms without tracing, 772 ms with).
- **All `file://` pages share one localStorage** in Chromium (`origin: "file://"`; a value written by `a/p.html` was read by `b/p.html`).

Caveats:

- JSPI (`WebAssembly.Suspending`) is on by default in Chrome and Edge from 137. **Firefox and Safari were not verified.** Keep `window.prompt()` as the fallback, the way the PDP exams do it.
- A blob Worker still needs Pyodide from somewhere it can `importScripts` and `fetch`:
  - a CDN (warm cache),
  - a room server with CORS, or
  - Pyodide inlined into the page (12 MB core, which would need a blob or `data:` loader; not probed).

**Takeaway for dewmark:** don't copy `pyodide-worker.js`. Port it in shape into a small exam engine with three modes:

- **(a)** Offline `file://`: blob classic Worker, JSPI `input()`, terminate-and-reboot Stop, plus an optional settrace time limit.
- **(b)** Room server: `serve.py` sends COOP/COEP headers itself, so the interrupt buffer works with no service worker and no reload.
- **(c)** Main-thread fallback: `window.prompt()` input and settrace timeout, as in the PDP exams.

Keep dewlab's request/response protocol, the `canStop()`-reports-reality rule (7.77) and `restart()`-rejects-pending-promises (7.97).

---

## 3. `assets/tutorial_tools.py` (2,297 lines, 96 KB)

Public `__all__`: `text_input`, `dropdown`, `slider`, `button`, `image_input`, `show`, `show_table`, `load_csv`, `load_text`, `run_query`. The module says of itself: "Nothing about this is assessment-shaped: no scoring, no submission, no record kept anywhere, and no verdict."

Worth taking for dewmark:

- **The output renderer.** `run_cell` (`:765`) streams stdout in order and renders DataFrames (`_table_html`), figures (`_figure_html`, transparent, recoloured for the theme), animations and tracebacks trimmed to the student's frames (`_format_exception`, `_is_user_frame`). Printed text is always `textContent` (0.15). `KeyboardInterrupt` shows as "Stopped." It has two sinks: `_DomSink` for main thread and `_MessageSink` for the Worker.
- **`compare(solution, inputs_json, tests)` (`:1037`)** runs the student's code and a model solution in *copies* of the namespace against a list of expressions. It returns JSON rows `{input, yours, solution, differ}` and swallows printed output and figures. This is almost exactly the primitive the marking workbench needs for "run the student's function against the marking scheme's cases, beside the model answer". dewlab deliberately never gives a verdict; the workbench would.
- `holds(expression)` and `_report()` evaluate an author's `expect:` against the namespace and fail quietly. That makes an "evidence of reaching X" flag for marking.

Beware (dewstack found the same, `staging/dewstack-import/planning/NEXT_STEPS.md:637-660`):

- `run_query()` and `_run_sql_cell()` need a live `_CellContext` (`_require_cell()`).
- Table rendering needs pandas.

Port single functions, not the module.

---

## 4. `assets/vendor/` and `vendor-src/`

The build is `vendor-src/build-vendor.mjs` (184 lines, esbuild 0.25.5). The rule, from `vendor-src/package.json` and DECISIONS_LOG 0.19: exact pins, a committed `package-lock.json`, and committed output so neither CI nor authors need Node. CI job `standalone-bundle-is-current` (`tests.yml:131`) rebuilds with `npm ci && npm run build` and fails on any diff.

| File | Size | Pin | What it would give dewmark | Verdict |
|---|---|---|---|---|
| `codemirror.bundle.js` | 619 KB, ESM | `@codemirror/view` 6.36.8, `state` 6.5.2, `commands` 6.8.1, `language` 6.11.0, `autocomplete` 6.18.6, `search` 6.5.11, `lang-python` 6.2.1, plus lang-sql/html/css/javascript and `theme-one-dark` 6.1.2 | CodeMirror 6 in place of textarea or CM5-from-cdnjs. See the notes below the table. | **Reuse the entry, rebuild an exam-specific IIFE.** Drop html/css/js/sql if unused; add an off switch for completion. |
| `katex.bundle.js`, `katex.min.css`, `fonts/KaTeX_*` | 272 KB + 23 KB + 296 KB of woff2 (20 files) | katex 0.16.22 | `renderMath(el, tex, displayMode)`; `output:"html"` only, so no MathML for screen readers | **Keep latex2mathml for the paper** (no runtime, prints cleanly, native MathML reads aloud). Take KaTeX only if students *type* maths and need a live preview, and then use `output:"htmlAndMathml"`. |
| `accessible-fonts.css`, `fonts/lexend-*`, `fonts/opendyslexic-*` | Lexend 400/700 = 29 KB; OpenDyslexic 400/700 roman and italic = 464 KB | @fontsource/lexend 5.3.0, @fontsource/opendyslexic 5.3.0 (SIL OFL) | Self-hosted accessible fonts. The PDP exams currently pull these from Google Fonts and jsdelivr, which break offline. | **Reuse directly.** Inlined as base64 they are about 660 KB. Consider making OpenDyslexic an opt-in build flag. |
| `coi-serviceworker.js` | 4.7 KB | coi-serviceworker 0.1.7 | Isolation on hosts that can't set headers | Only for a hosted exam. On `file://` it does nothing; a room server should send the headers itself. |
| `standalone.bundle.js` | 1.0 MB, IIFE | built from `assets/tutorial-runtime.js` | Nothing directly (it is the tutorial runtime) | **Reuse the technique:** ESM source, esbuild `format:"iife"`, inlined, with a CI staleness check. |
| `milkdown.bundle.js` / `.css` | 2.9 MB / 73 KB | @milkdown/crepe 7.21.3 | A WYSIWYG markdown editor (dewlab's authoring editor) | Not for the exam page. At most, for a future teacher-side exam editor. |

Notes on the CodeMirror bundle:

- `createCodeEditor(parent, doc, {dark, onChange, completeNames, getDoc, getSignature, getJediCompletions, language, lineNumbersVisible, indentWidth})` returns `{view, getValue, setValue, focus, destroy}`.
- It also exports `setEditorTheme`, `setLineNumbers`, `setIndentWidth` and `createReadOnlyCode` (`vendor-src/codemirror-entry.js:310-417`).
- Jedi-first completion has a 400 ms patience limit.
- The bundle **always** enables `autocompletion()` plus local and global completion; there is no switch for a "no suggestions" exam.

---

## 5. How dewlab's downloaded copy of a tutorial works offline (`build.py:5991-6106`)

`standalone_html()` turns a built page into one file. Every step goes through `replace_once()`, which fails the build if the needle is missing (5.13):

- It inlines `tutorial-style.css`.
- It inlines KaTeX CSS with only the woff2 fonts it names, as base64 (`inline_katex_css`), and does the same for `accessible-fonts.css` (`inline_accessible_fonts_css`).
- It swaps the module runtime for `PYODIDE_CLASSIC` plus the inline IIFE bundle.
- It strips `coi-serviceworker`, search and cross-file navigation.
- It puts the `tutorial_tools.py` source and the datasets into the JSON manifest (`manifest.standalone = true`).

The runtime then chooses `bootMainThread()` with no Stop (7.77).

**It deliberately does not inline Pyodide** (4.2: "one file that still needs the internet once"). The one-line failure message is `bootMainThread`, `tutorial-runtime.js:3684`.

The **Notebook download** (`write_dewmini_bundle()`, 7.92) is a folder containing:

- `serve.py`, a stdlib `http.server` on 127.0.0.1:8756, `build.py:6308`
- the vendored `assets/vendor/pyodide/`
- `coi-serviceworker.js`

7.95 verified it with every non-loopback request aborted ("zero blocked requests, a cell printing `42` with the network off"). 7.92 also recorded a real failure: an ES-module app opened from `file://` just comes up blank. `index.html` now checks `location.protocol` and explains what to do.

For dewmark this gives two room recipes, already proven in dewlab:

1. a single file plus a warm CDN cache, and
2. a folder plus `serve.py` plus vendored Pyodide.

Add COOP/COEP headers to `serve.py` (a two-line handler subclass, verified) and recipe 2 gets a real Stop without the service-worker reload.

---

## 6. The Settings panel and reading options (`assets/shell.html:297-446`, `tutorial-runtime.js:40-58, 1880-1990`, `tutorial-style.css:1-165`)

- **State:** `TEXTURE_DEFAULTS = {theme:"system", font:"serif", size:18, width:34, link:"#d4692a", contrast:"normal", buttons:"both", motion:"normal", codeLineHeight:1.5, indent:4, linenumbers:"on"}`. It is stored as one JSON value under the localStorage key `dewlab:texture`, and a blocked `setItem` is tolerated.
- **Apply:** `applyTexture()` sets attributes on `<html>`: `data-theme`, `data-font` (`sans|mono|lexend|opendyslexic`), `data-contrast="high"`, `data-button-labels`, `data-motion="reduced"`. It also sets custom properties `--dl-font-size`, `--dl-line-width`, `--dl-code-line-height` and `--dl-link`.
- **CSS:** each option is a separate rule block (`:root[data-font="lexend"]` and so on).
  - High contrast covers both light and dark (7.123, 7.124).
  - The link colour is not written inline under high contrast, to keep AA contrast.
  - `@media print` appears in three blocks.
- **Markup:** segmented controls are `role="radiogroup"` with roving focus (`syncSegRoving`, 7.130), and there is a settings search over `data-keywords`.
- **Accessible fonts:** Lexend replaced Atkinson Hyperlegible on Josh's call (7.127). The PDP exams still load Atkinson from Google Fonts. The two should be brought into line.

For dewmark:

- **Reuse the tokens, the attribute scheme and the `applyTexture()` shape, not the corner-dock markup.** A "settings first" start screen (name, font, size, theme, contrast, and a Python loading bar) can drive the same attributes.
- Because every `file://` page shares one localStorage (verified), a reading preference stored under a shared key such as `dewmark:texture` carries from one exam to the next on a machine. That is a bonus.
- **The same sharing means saved answers must be keyed by exam id and sitting**, and the resume screen must confirm the student's name before restoring. Otherwise the next student on the same PC sees the last one's work.

---

## 7. The question fence (DECISIONS_LOG 7.179, 7.182, 7.188)

The design note `planning/QUESTION_BLOCKS.md` (commit `562dcc8f`) was deleted after the feature shipped, under the 7.188 rule. dewlab took dewmark's *vocabulary* but not its *grammar*:

- It kept the spelled-out `type:` names (`multiple-choice`, `fill-in-the-blank`), `correct:` as a 1-based position, and `{word}` / `{a|b|c}` gaps with the first item correct.
- It chose markdown after a flat `key: value` header over YAML throughout, so that prompts and options stay prose for the plain-language tools.
- **Options are shuffled at runtime** (`shuffle()`, `buildQuestions()`, `tutorial-runtime.js:2220, 2409`). dewmark never shuffles, because marking needs "option 3" to mean the same thing each time.
- **Correctness sits in the DOM** (`data-correct="true"`, `data-expected`). The decision says this is "right for a self-check, wrong for anything that has to keep its answer from a reader who opens the page's source."

For dewmark: keep the shared vocabulary as a stated cross-repo contract. Consider moving dewmark's exam file to the same header-plus-markdown form, so a teacher who knows one can read the other. **Never copy the runtime**, because it puts the answer key in the page source.

---

## 8. `compose/`: the Notebook and Workspace (`docs/DEWMINI.md`, `compose/dewmini-fs.js` 244 lines)

- **Persistence choices** (`dewmini-fs.js:130-150`):
  1. A real folder through `showDirectoryPicker()`. The handle is saved in IndexedDB (`dewmini-fs`/`kv`) and re-granted with `requestPermission` inside a click.
  2. OPFS, mounted as a named subfolder (`OPFS_SUBDIR = "dewmini"`) so two tools on one origin can't clobber each other.
  3. IDBFS.

  All three mount at `/mnt/dewmini` and become Python's working directory. This is directly relevant to "save the submission to the USB stick or a network share as you go". The PDP exams already use `createWritable()`. dewmini's handle-in-IndexedDB pattern adds reconnection after a reload. It is Chrome and Edge only; keep download as the fallback.
- **Formats:**
  - `.ipynb` export with outputs (`downloadAsIpynb`, `tutorial-runtime.js:3447`, nbformat 4.5).
  - `.py` with `# %%` markers.
  - A self-running `.html` single file.

  An `.ipynb` view of a code answer would let an assessor open a submission in Jupyter.
- **Storage quota (7.133):** a single `localStorage.setItem` holding base64 figures can blow the roughly 5 MB quota, and every autosave then fails silently. The fix is to retry with large outputs blanked. dewmark's continuous save needs the same guard: store code and outputs separately, and never let a figure crowd out answer text.

---

## 9. `assets/term-definitions.js` (238 lines)

Shows a glossary definition on hover, but only on italics the author marked as the term (7.273, after prose-linking was withdrawn in 7.94). The setting is `dewlab:definitions`. **Not for an exam page**, because it is help. At most it is a pattern for a formula-sheet or allowed-reference lookup.

---

## 10. DECISIONS_LOG digest: the entries that bear on dewmark

| Entry | Decision | Relevance |
|---|---|---|
| 0.16 | A page with no cells never loads Pyodide | Only exams with code questions pay for Python |
| 0.17 / 0.20 | CDN by default through one overridable constant; Pyodide 0.28.3 (30 MB self-hosted) | Upgrade dewmark from 0.27.4; one pin, not five |
| 0.18 / 0.19 | CodeMirror and KaTeX vendored; build script separate; output committed | The model for dewmark's vendor folder |
| 1.8 | KaTeX in the browser, so the build has no Node step | dewmark's latex2mathml is the pure-Python equivalent; keep it |
| 2.1–2.4 | Silent autosave, visible restore; orphaned saves reported; export and import replace | Maps onto exam resume and "load my saved file" |
| 4.1–4.3, 5.13 | One source, two outputs; the export needs the internet once; the IIFE bundle has a CI staleness check; substitutions fail loudly | The exact recipe for a built exam file |
| 7.21 / 7.22 | Saves keyed by module and slug; a loaded file is checked before it overwrites | Key by exam id, sitting and student; refuse a mismatched submission |
| 7.33 | Downloaded copies drop the version list | An exam file should carry no links it can't honour offline |
| 7.77 / 7.89 / 7.97 | Worker migration; interrupt buffer plus coi-serviceworker; restart must reject pending promises | Protocol and pitfalls to port |
| 7.92 / 7.95 | Offline Notebook plus `serve.py`; `file://` ES modules fail blank; zero-network proven | The room-server recipe |
| 7.100 | `pyodide-http` patch; a hung request can't be stopped | Drop it for exams |
| 7.123 / 7.127 / 7.130 | High contrast; Lexend and OpenDyslexic; accessible radiogroups | The reading-settings kit |
| 7.133 | Figures can blow the localStorage quota | Guard the exam's autosave |
| 7.179 / 7.188 | Question fence; answers in the DOM; design note deleted | Shared vocabulary, never shared runtime |
| 7.240 | No `input()` in cells; `__name__` is `"__dewlab__"` | dewmark must implement `input()` and run code as `__main__` |

---

## 11. How to share across repos

**The precedent** (`staging/dewstack-import/README.md`, `planning/CONSOLIDATION_PLAN.md` §6 and §8 Q9, `NEXT_STEPS.md` step 7):

- dewstack took "dewlab's design, not its code".
- The shell, tokens, Settings panel and search were "carried over as files".
- The engine was "ported in shape", because copying `pyodide-engine.js` would bring in "dead code paths" (Jedi, the FS layer). "Port in shape stays the only rule between the repositories, no twinned files", and "the ledger notes the dewlab commit each copy was taken from so a later sync is possible."
- A banner on each ported file names its twin (DECISIONS_LOG 7.134).
- The outcome: dewstack's content was later copied back into dewlab (`staging/dewstack-import/`, pinned at dewstack `892e8780`, 7.141).

| Option | Offline exam room | Cost | Verdict |
|---|---|---|---|
| **Copy + sync script + version stamp** | Best: the files are inlined into each built exam at build time | Manual sync; drift unless checked | **Recommended** |
| Git submodule | Fine once checked out | GitHub "Download ZIP" leaves submodules out, so a teacher's download is broken; adds about 38 MB of dewlab history; tied to dewlab's layout | No |
| Publish as npm, served by jsdelivr `@x.y.z` | Needs the network, unless vendored anyway | A publish pipeline for dewlab (`vendor-src` is `"private": true`) | Later, if a third consumer appears |
| Load from `deweydex.github.io/dewlab/assets/...` | **Fails offline**; URLs are cache-busted by `?v=` hash (`build.py:5401`), not versioned | Breaks whenever dewlab pushes; there were 8 engine commits in 15 days | Never, for exams |

How the recommended copy would work:

- A `vendor/dewlab/` folder in the dewmark repo, plus `vendor/dewlab/SOURCE.json` recording:
  - the dewlab commit SHA,
  - the file list with a sha256 for each file,
  - the Pyodide version.
- A `tools/sync_from_dewlab.py` that fetches those paths at a SHA.
- A CI check that fails if a vendored file's hash differs from the stamp, catching hand edits.
- Ported-in-shape files (the exam engine) carry a banner naming the dewlab file and commit they came from.

Exact files to vendor as-is:

- `assets/vendor/accessible-fonts.css`
- `assets/vendor/fonts/lexend-latin-{400,700}.woff2`
- `assets/vendor/fonts/opendyslexic-latin-{400,700}{,-italic}.woff2`
- `vendor-src/codemirror-entry.js` and `vendor-src/katex-entry.js`: sources, rebuilt as IIFE with dewmark's own `package.json` pinning the same versions
- `dev/fetch_pyodide.py`
- The token and attribute sections of `assets/tutorial-style.css`, lines 1–165

Files to port in shape:

- `pyodide-engine.js` and `pyodide-worker.js` become an exam engine with blob Worker, JSPI stdin, terminate Stop, a settrace timeout and a `__main__` namespace.
- From `tutorial_tools.py`, only the output renderer and `compare()`.
- `serve.py`, with COOP/COEP headers added.

---

## What this means for dewmark

- **Engine:** build a small exam engine ported in shape from dewlab. On `file://`, a blob classic Worker with JSPI-backed `input()` (an on-page input line, not `window.prompt()`) and Stop by terminate-and-reboot (about 1.6 s warm). Served locally with COOP/COEP, a true interrupt with state kept. Fallback is main thread plus `prompt()` plus settrace. Upgrade to Pyodide 0.28.3, `loadPackage` only, no micropip, no `pyodide-http`, code runs as `__main__`. All verified in Chromium 141; Firefox and Safari JSPI still to test.
- **Offline for real:** vendor and inline CodeMirror 6 (an exam-specific IIFE with a no-completion option), Lexend and OpenDyslexic, and optionally KaTeX. Keep latex2mathml for the paper. Ship dewlab's two room recipes as dewmark's checklist: warm cache, or folder + `serve.py` + trimmed Pyodide (12 MB core, about 30 MB with numpy/pandas/matplotlib).
- **Settings-first start screen:** reuse dewlab's `TEXTURE_DEFAULTS` attribute and token scheme under a `dewmark:texture` key. Show Python loading progress there. Key saved work by exam, sitting and student, because every `file://` page shares one localStorage.
- **Marking workbench:** port `tutorial_tools.compare()` to run a submission against the scheme's cases beside the model answer. Use dewmini's File System Access pattern (handle in IndexedDB, reconnect) for live save-to-folder.
- **Repo move:** take `dewmark/` out of dewlab, along with its CI job (`tests.yml:103`). Adopt "copy + `SOURCE.json` stamp + CI hash check" for everything taken from dewlab. Record the dewlab SHA (`a6d2c6d4` today), and treat the question-type vocabulary shared with dewlab's `question` fence as a documented cross-repo contract.

Probe files: `/tmp/claude-0/-home-user/9d1373ae-0961-5985-b2c8-adad08e8b8ed/scratchpad/engine-probe/probe.html`, `probe2.html`, `serve_probe.py`, `run_probe.py`, `run_ls.py`.