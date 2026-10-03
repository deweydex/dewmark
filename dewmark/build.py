"""Building the pages of a paper in the new format
(docs/EXAM_FORMAT.md; planning/PROPOSAL.md §9, step 4).

    python -m dewmark build FILE -o DIR

One exam file gives three pages (a student page, a practice page, an answer
key) and the marking scheme as JSON. Nothing reaches a student except through
this module, which is why the checks are here: a paper with problems, one that
uses a kind no page draws yet, or one whose pages let the marking scheme or a
hint through to the student's page, is refused, and no file is written.

The paper's own layers (the split at `# Marking scheme`, the refusals) are the
reader's. The last two layers of the format's four are run here, on the pages
this module has just made (dewmark/secrecy.py): a search of each page for the
scheme's strings, and the mutation test, which builds the page again with the
scheme and the hints made nonsense and demands the same bytes.

A page opens on two screens before the paper (decision 25): *Start*, with the
student's details, their reading settings and what the paper needs, and
*Before you begin*, with the instructions, where the answer file goes and
Begin. The reading settings are described once, in READING, and drawn twice
(on the first screen and in the Aa drawer that every screen has), so the page
and its drawer cannot disagree about what a setting is.
"""

import base64
import hashlib
import html
import json
from pathlib import Path

from .package import split_halves
from .reader import read
from .receipt import fingerprint
from .render import (IMAGE_RE, VARIANTS, _picture, check_buildable, picture_file, render_front,
                     render_paper)
from .scheme_json import dumps, scheme_json
from .secrecy import find_leaks, mutation_test, scheme_strings, without_hints

ASSETS = Path(__file__).resolve().parent.parent / "assets"

# The page's behaviour, in the order it is joined into one script: the answer
# kinds, saving and finishing; the reading settings; the PDF writer; the finish
# sheet's saving; then the screens before the paper, which also start the page.
SCRIPTS = ("page.js", "page-reading.js", "page-pdf.js", "page-finish.js", "page-start.js")

# What a built page may do: run its own script and style, show pictures it
# carries, use the fonts it carries, and nothing else. It connects to nothing,
# so a student's answers, and anything a paper's wording might try, have
# nowhere to go.
POLICY = ("default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
          "img-src data:; font-src data:; form-action 'none'; base-uri 'none'")

KIND_LABELS = {"exam": "Examination", "practice": "Practice paper", "sample": "Sample paper"}
BANDS = {"student": None, "practice": "Practice version",
         "answer-key": "Answer key: not for students"}
DETAILS = ("full name", "student number")

# The reading fonts, carried in every page so that a student's choice never
# depends on the computer. The files are copies from dewlab (assets/vendor/SOURCE.json).
# The fonts a PDF is set in (assets/vendor/pdf-fonts/, made by dev/make_pdf_fonts.py),
# carried as the TrueType files they are and written into each PDF the page makes.
PDF_FONTS = {"sans": "DejaVuSans-subset.ttf", "mono": "DejaVuSansMono-subset.ttf"}

FONTS = (("Lexend", 400, "lexend-latin-400.woff2"), ("Lexend", 700, "lexend-latin-700.woff2"),
         ("OpenDyslexic", 400, "opendyslexic-latin-400.woff2"),
         ("OpenDyslexic", 700, "opendyslexic-latin-700.woff2"))

# The reading settings: what each is, what it may be, and what it is to begin
# with. The page checks a stored setting against this, so a setting left by an
# older page, or edited by hand, can never put the page in a state it cannot
# draw. `where` says which controls show it: "key" on the first screen, "more"
# under More settings; both are in the drawer.
READING = {
    "font": {"options": ["serif", "sans", "lexend", "dyslexic"], "default": "serif", "where": "key"},
    "size": {"min": 14, "max": 32, "step": 1, "default": 18, "where": "key"},
    "scheme": {"options": ["", "light", "cream", "blue", "dark", "contrast"], "default": "", "where": "key"},
    "ruler": {"default": False, "where": "key"},
    "lineHeight": {"min": 1.3, "max": 2.4, "step": 0.1, "default": 1.6, "where": "more"},
    "spacing": {"options": ["normal", "wide", "wider"], "default": "normal", "where": "more"},
    "width": {"options": ["56ch", "68ch", "84ch", "100%"], "default": "68ch", "where": "more"},
    "motion": {"default": False, "where": "more"},
    "codeSize": {"min": 12, "max": 28, "step": 1, "default": 16, "where": "more"},
    "codeScheme": {"options": ["auto", "light", "dark"], "default": "auto", "where": "more"},
    "wrap": {"default": False, "where": "more"},
}


class BuildError(Exception):
    """A build that cannot go ahead. `messages` says why, in plain words."""

    def __init__(self, messages):
        self.messages = [str(m) for m in messages]
        super().__init__("\n".join(self.messages))


def esc(value):
    return html.escape(str(value), quote=True)


def paper_fingerprint(text, paper, base_dir):
    """The paper's fingerprint (dewmark/receipt.py): its text as students are
    given it, and a checksum of every picture it carries, the logo included.
    Nothing from the marking scheme or a hint goes into it, so it is the same
    for every page built from one paper and does not change when a key does."""
    head, _ = split_halves(text, reference=False)
    paths = {path for _, path in IMAGE_RE.findall(without_hints(head))}
    if paper["settings"].get("logo"):
        paths.add(paper["settings"]["logo"])
    pictures = []
    for path in paths:
        found = picture_file(base_dir, path)
        if found:
            pictures.append((path, hashlib.sha256(found[1]).hexdigest()))
    return fingerprint(text, pictures)


def page_model(paper, variant, code=""):
    """What the page's own behaviour needs: names, kinds, marks, and the shape
    of the paper. It holds nothing of the marking scheme or the hints, and the
    leak checks run over it with the rest of the page."""
    units, boxes = paper["units"], paper["boxes"]

    def leaves(name):
        unit = units[name]
        if not unit["children"]:
            return [name]
        return [leaf for child in unit["children"] for leaf in leaves(child)]

    questions, sections = {}, []
    for index, section in enumerate(paper["sections"]):
        if not section["questions"]:
            continue
        for name in section["questions"]:
            unit = units[name]
            questions[name] = {
                "label": unit["label"], "title": unit["title"], "marks": unit["marks"],
                "parts": [{"name": leaf, "label": units[leaf]["label"],
                           "marks": units[leaf]["marks"],
                           "boxes": [b for b in units[leaf]["boxes"] if not boxes[b]["unmarked"]]}
                          for leaf in leaves(name)],
            }
        sections.append({"index": index, "title": section["title"], "any": section["any"],
                         "questions": list(section["questions"])})
    settings = paper["settings"]
    return {"format": "dewmark-page/1", "variant": variant,
            "exam": {"code": settings["code"], "version": settings.get("version", "1"),
                     "title": settings.get("title", ""), "kind": settings.get("kind", ""),
                     "marks": paper["total"], "fingerprint": code,
                     "institution": settings.get("institution", ""),
                     "college": settings.get("college", ""), "module": settings.get("module", ""),
                     "moduleCode": settings.get("module code", ""),
                     "session": settings.get("session", "")},
            "reading": READING,
            "sections": sections, "questions": questions}


# --- the band -----------------------------------------------------------------------

def _band(paper, variant, base_dir):
    """The fixed band at the top of every screen: what kind of page this is,
    in words a glance across a room can read (decision 12), then the paper's
    own details from its settings. No college colour, by decision."""
    settings = paper["settings"]
    kind = BANDS[variant] or KIND_LABELS.get(settings.get("kind"), "Paper")
    names = [settings.get(k) for k in ("institution", "college")]
    organisation = " · ".join(esc(n) for n in names if n)
    module, code = settings.get("module"), settings.get("module code")
    module_text = (esc(module) + (f" ({esc(code)})" if code else "")) if module else esc(code or "")
    facts = [module_text, esc(settings.get("session", ""))]
    if settings.get("time allowed"):
        facts.append("Time allowed: " + esc(settings["time allowed"]))
    facts.append(f"Total marks: {paper['total']:g}")
    logo = _picture(base_dir, settings["logo"]) if settings.get("logo") else None
    mark = ""
    if logo:
        name = next((n for n in names if n), "")
        mark = f'<img class="dm-band-logo" alt="{esc(name + " logo" if name else "Logo")}" src="{logo}">'
    return (f'<header class="dm-band dm-band-{variant}">{mark}<div class="dm-band-text">'
            f'<p class="dm-band-kind">{esc(kind)}</p>'
            f'<h1 class="dm-band-title">{esc(settings.get("title", ""))}</h1>'
            + (f'<p class="dm-band-org">{organisation}</p>' if organisation else "")
            + f'<p class="dm-band-meta">{" · ".join(f for f in facts if f)}</p></div></header>')


# --- what the paper needs -----------------------------------------------------------

def needs(paper, variant):
    """The list on the first screen: what this paper needs, made from what the
    paper declares, so a teacher never writes a loading screen. Each item names
    the check the page runs for it (assets/page-start.js, CHECKS). The answer
    key saves nothing, so it lists nothing about saving."""
    settings = paper["settings"]
    items = [("paper", "The paper: questions and figures", "Inside this page", "inside"),
             ("fonts", "Reading fonts", "Inside this page", "inside")]
    sets_up = any(block["type"] == "setup" for block in paper["blocks"])
    if sets_up or any(box["kind"] == "python exec" for box in paper["boxes"].values()):
        where = "From the internet" if settings.get("python from") == "internet" else "From this file"
        items.append(("python", "Python", where, "python"))
        packages = [p.strip() for p in settings.get("python packages", "").split(",") if p.strip()]
        if packages:
            items.append(("packages", "Packages: " + ", ".join(packages), where, "python"))
        if sets_up:
            items.append(("setup", "Set-up code", "Runs by itself when Python is ready", "python"))
    if variant != "answer-key":
        items += [("storage", "Saving in this browser", "Tested when this page opened", "storage"),
                  ("file", "Saving into a folder you choose", "Your browser decides how", "file")]
    return items


def _checklist(paper, variant):
    rows = "".join(
        f'<li data-need="{esc(key)}" data-check="{esc(check)}" data-state="checking">'
        f'<span class="dm-ci" aria-hidden="true"></span>'
        f'<div><span class="dm-cn">{esc(label)}</span><span class="dm-cs">{esc(detail)}</span></div>'
        f'<span class="dm-cw">Checking</span></li>'
        for key, label, detail, check in needs(paper, variant))
    return f'<ul id="dm-checklist" class="dm-checklist">{rows}</ul>'


# --- reading settings ---------------------------------------------------------------

FONT_NAMES = {"serif": "Standard", "sans": "Plain", "lexend": "Lexend", "dyslexic": "OpenDyslexic"}
SCHEME_NAMES = {"": "Match my computer", "light": "Light", "cream": "Cream paper",
                "blue": "Blue tint", "dark": "Dark", "contrast": "High contrast"}
SPACING_NAMES = {"normal": "Normal", "wide": "Wide", "wider": "Wider"}
WIDTH_NAMES = {"56ch": "Narrow", "68ch": "Medium", "84ch": "Wide", "100%": "Full width"}
CODE_NAMES = {"auto": "Standard", "light": "Light", "dark": "Dark"}


def _choices(prefix, key, legend, names, sample=None):
    """A row of radio buttons for one setting. The group's name carries the
    prefix, because the same setting is drawn twice and a radio group is
    shared by every radio of one name."""
    options = "".join(
        f'<label><input type="radio" name="{prefix}-{key}" value="{esc(value)}" data-setting="{key}">'
        + (f'<span class="{sample(value)}" aria-hidden="true"></span>' if sample else "")
        + f'<span>{esc(label)}</span></label>' for value, label in names.items())
    return f'<fieldset><legend>{esc(legend)}</legend><div class="dm-choices">{options}</div></fieldset>'


def _slider(prefix, key, label, unit_label):
    spec = READING[key]
    more, less = (f"Larger {unit_label}", f"Smaller {unit_label}")
    return (f'<div class="dm-set"><span class="dm-set-label" id="{prefix}-{key}-l">{esc(label)}</span>'
            f'<div class="dm-stepper">'
            f'<button type="button" class="dm-stepbtn" data-step="{key}" data-d="-1" aria-label="{less}">−</button>'
            f'<input type="range" data-setting="{key}" min="{spec["min"]}" max="{spec["max"]}" '
            f'step="{spec["step"]}" aria-labelledby="{prefix}-{key}-l">'
            f'<button type="button" class="dm-stepbtn" data-step="{key}" data-d="1" aria-label="{more}">+</button>'
            f'<output data-out="{key}" aria-hidden="true"></output></div></div>')


def _toggle(key, title, note=""):
    small = f"<small>{esc(note)}</small>" if note else ""
    return (f'<label class="dm-toggle"><input type="checkbox" data-setting="{key}">'
            f'<span><b>{esc(title)}</b>{small}</span></label>')


def reading_controls(prefix, which):
    """The controls for the settings in `which` ("key", "more" or "all")."""
    def wanted(key):
        return which == "all" or READING[key]["where"] == which

    out = []
    if wanted("font"):
        out.append(_choices(prefix, "font", "Font", FONT_NAMES, lambda v: f"dm-sample dm-f-{v}"))
    if wanted("size"):
        out.append(_slider(prefix, "size", "Text size", "text"))
    if wanted("scheme"):
        out.append(_choices(prefix, "scheme", "Colours", SCHEME_NAMES,
                            lambda v: f"dm-sw dm-sw-{v or 'match'}"))
    if wanted("ruler"):
        out.append(_toggle("ruler", "Reading ruler",
                           "A band that follows your pointer, and the line you are typing on."))
    if wanted("lineHeight"):
        out.append(_slider(prefix, "lineHeight", "Line spacing", "spacing"))
    if wanted("spacing"):
        out.append(_choices(prefix, "spacing", "Space between letters and words", SPACING_NAMES))
    if wanted("width"):
        out.append(_choices(prefix, "width", "Line length", WIDTH_NAMES))
    if wanted("motion"):
        out.append(_toggle("motion", "Reduce motion",
                           "Stops things sliding. This is on by itself if your computer asks for it."))
    if wanted("codeSize"):
        out.append(_slider(prefix, "codeSize", "Code text size", "code"))
    if wanted("codeScheme"):
        out.append(_choices(prefix, "codeScheme", "Code colours", CODE_NAMES))
    if wanted("wrap"):
        out.append(_toggle("wrap", "Wrap long lines of code"))
    return "".join(out)


PREVIEW = (
    '<div class="dm-preview" aria-label="Preview of your reading settings">'
    '<h4>Question 1(a) <span class="dm-marks">(2 marks)</span></h4>'
    '<p>A list keeps its values in order. Read the code, then write what it prints.</p>'
    '<p><code>print(len(["a", "b"]))</code></p></div>')


def _drawer():
    return (
        '<div id="dm-scrim" hidden></div>'
        '<div id="dm-drawer" role="dialog" aria-modal="true" aria-labelledby="dm-drawer-h" hidden>'
        '<div class="dm-drawer-head"><h2 id="dm-drawer-h">Reading settings</h2>'
        '<button type="button" class="dm-secondary" id="dm-drawer-close">Close</button></div>'
        '<div class="dm-settings">' + PREVIEW + reading_controls("drawer", "all")
        + '<p class="dm-kept" data-kept hidden>These settings are kept on this computer. If someone '
          'else used it before you, check them, or choose Use standard settings.</p>'
          '<button type="button" class="dm-secondary" data-reset>Use standard settings</button>'
          '</div></div>')


# --- the screens before the paper ---------------------------------------------------

def _start_screen(paper, variant):
    settings = paper["settings"]
    example = settings.get("number example")
    number_hint = ("As on your student card" + (f", for example {esc(example)}" if example else "") + ".")
    checklist = _checklist(paper, variant)
    return f"""<section id="dm-start" class="dm-screen" aria-labelledby="dm-start-h">
  <p class="dm-steps">Step 1 of 2</p>
  <h2 id="dm-start-h" tabindex="-1">Start</h2>
  <p class="dm-lede">Type your details and choose how the page looks. Then press Next.</p>
  <div class="dm-grid">
    <form id="dm-details" novalidate>
      <div class="dm-card">
        <h3>Your details</h3>
        <div class="dm-field">
          <label for="dm-name">Full name</label>
          <span class="dm-hint-text" id="dm-name-hint">As it appears on your college record.</span>
          <input type="text" id="dm-name" data-detail="full name" autocomplete="off" spellcheck="false"
                 aria-describedby="dm-name-hint dm-name-err">
          <p class="dm-error" id="dm-name-err" role="alert" hidden></p>
        </div>
        <div class="dm-field">
          <label for="dm-number">Student number</label>
          <span class="dm-hint-text" id="dm-number-hint">{number_hint}</span>
          <input type="text" id="dm-number" data-detail="student number" autocomplete="off"
                 spellcheck="false" autocapitalize="characters"
                 aria-describedby="dm-number-hint dm-number-err">
          <p class="dm-error" id="dm-number-err" role="alert" hidden></p>
        </div>
        <div id="dm-restore" class="dm-restore-note" hidden>
          <h3 id="dm-restore-h">Welcome back</h3>
          <p id="dm-restore-text"></p>
          <div class="dm-actions">
            <button type="button" class="dm-primary" id="dm-continue">Continue my work</button>
            <button type="button" class="dm-secondary" id="dm-again">Start again</button>
            <button type="button" class="dm-secondary" id="dm-not-me">This is not my number</button>
          </div>
          <p class="dm-error" id="dm-restore-err" role="alert" hidden></p>
          <p id="dm-again-text" class="dm-note" hidden>Your earlier work is not deleted. It is kept aside on
            this computer. Press Next, then Begin, to start again.</p>
        </div>
        <p class="dm-hint-text" id="dm-file-msg" role="status"></p>
      </div>
      <div class="dm-card dm-settings">
        <h3>Reading settings</h3>
        {PREVIEW}
        {reading_controls("start", "key")}
        <details class="dm-more"><summary>More settings</summary><div>{reading_controls("start", "more")}</div></details>
        <p class="dm-kept" data-kept hidden>These settings are kept on this computer. If someone else used
          it before you, check them, or choose Use standard settings.</p>
        <button type="button" class="dm-secondary" data-reset>Use standard settings</button>
      </div>
      <div class="dm-actions">
        <button type="submit" class="dm-primary dm-big" id="dm-next">Next</button>
        <button type="button" class="dm-secondary" id="dm-load-file">I have an answer file</button>
      </div>
    </form>
    <aside class="dm-card" aria-labelledby="dm-needs-h">
      <h3 id="dm-needs-h">What this paper needs</h3>
      {checklist}
      <p id="dm-load-status" class="dm-ready-line" role="status" aria-live="polite"></p>
    </aside>
  </div>
</section>"""


def _before_screen(paper, variant, base_dir, code):
    settings = paper["settings"]
    instructions = render_front(paper, base_dir) or "<p>Read each question carefully.</p>"
    if variant == "answer-key":
        where = "<p>The answer key saves nothing, and has no answer file.</p>"
    else:
        where = ('<p id="dm-file-text">Choose a folder for your files, for example a folder on a USB stick. '
                 'The page saves your answer file into it as you work, and puts your PDF there when you '
                 'finish. Nothing leaves this computer.</p>'
                 '<button type="button" class="dm-secondary" id="dm-choose-folder">Choose a folder…</button>'
                 '<p class="dm-hint-text" id="dm-file-status" role="status"></p>')
    time = (f'<div class="dm-card"><h3>Time</h3><p>Time allowed: {esc(settings["time allowed"])}.</p></div>'
            if settings.get("time allowed") else "")
    go = ("Press Begin when your invigilator tells you to start." if variant == "student"
          else "Press Begin when you are ready.")
    return f"""<section id="dm-before" class="dm-screen" aria-labelledby="dm-before-h" hidden>
  <p class="dm-steps">Step 2 of 2</p>
  <h2 id="dm-before-h" tabindex="-1">Before you begin</h2>
  <p id="dm-resume-line" class="dm-note" role="status" hidden></p>
  <div class="dm-card"><div class="dm-instructions">{instructions}</div></div>
  <div class="dm-card"><h3>Your files</h3>{where}</div>
  {time}
  <p id="dm-ready-line" class="dm-ready-line" role="status"></p>
  <p class="dm-hint-text">Paper ID {esc(code)}. Your invigilator may ask you to read it out.</p>
  <div class="dm-actions">
    <button type="button" class="dm-secondary" id="dm-back">Back</button>
    <button type="button" class="dm-primary dm-big" id="dm-begin">Begin</button>
  </div>
  <p class="dm-hint-text">{go}</p>
</section>"""


def pdf_fonts_json():
    """The PDF fonts as one JSON object of base64 text, for the page's data block."""
    carried = {name: base64.b64encode((ASSETS / "vendor" / "pdf-fonts" / file).read_bytes()).decode("ascii")
               for name, file in PDF_FONTS.items()}
    return json.dumps(carried)


def fonts_css():
    """The reading fonts as @font-face rules, each file carried as a data address."""
    rules = []
    for family, weight, name in FONTS:
        data = base64.b64encode((ASSETS / "vendor" / "fonts" / name).read_bytes()).decode("ascii")
        rules.append(f"@font-face{{font-family:'{family}';font-style:normal;font-weight:{weight};"
                     f"font-display:swap;src:url(data:font/woff2;base64,{data}) format('woff2')}}")
    return "".join(rules)


def build_page(paper, variant, base_dir, code=""):
    """One complete page as text: styles, screens, paper, finish screen, data
    block and behaviour, all in one file. `code` is the paper's fingerprint."""
    settings = paper["settings"]
    css = (ASSETS / "page.css").read_text(encoding="utf-8")
    js = "\n".join((ASSETS / name).read_text(encoding="utf-8") for name in SCRIPTS)
    model = json.dumps(page_model(paper, variant, code)).replace("<", "\\u003c")
    hand_in = esc(settings.get("hand in", ""))
    title = esc(settings.get("title", ""))
    return f"""<!doctype html>
<html lang="en-IE">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="Content-Security-Policy" content="{POLICY}">
<title>{title}</title>
<style id="dm-fonts">{fonts_css()}</style>
<style id="dm-style">{css}</style>
</head>
<body data-variant="{variant}">
<button type="button" id="dm-aa" aria-haspopup="dialog" aria-label="Reading settings">Aa</button>
{_drawer()}
<div id="dm-ruler" aria-hidden="true"></div>
{_band(paper, variant, base_dir)}

{_start_screen(paper, variant)}

{_before_screen(paper, variant, base_dir, code)}

<div id="dm-app" hidden>
  <div id="dm-topbar">
    <span id="dm-top-title">{title}</span>
    <span id="dm-top-student"></span>
    <span id="dm-save-browser" class="dm-save-pill" title="saved in this browser">Browser —</span>
    <span id="dm-save-file" class="dm-save-pill" title="saved to your answer file">File —</span>
    <button type="button" id="dm-download" class="dm-secondary">Save a copy</button>
    <button type="button" id="dm-finish" class="dm-primary">Finish…</button>
  </div>
  <div id="dm-body">
    <nav id="dm-panel" aria-label="questions"><div id="dm-panel-questions"></div></nav>
    <main id="dm-paper">{render_paper(paper, variant, base_dir)}</main>
  </div>
</div>

<section id="dm-finish-screen" class="dm-screen" aria-labelledby="dm-finish-h" hidden>
  <h2 id="dm-finish-h" tabindex="-1">Finish</h2>
  <p class="dm-lede">Three steps. Nothing ends until you choose, and you can go back to the paper at any time.</p>
  <p id="dm-changed" class="dm-note" role="status" hidden>You changed your answers after you saved.
    Save your files again before you hand in.</p>
  <ol class="dm-finish-steps">
    <li class="dm-card">
      <h3>1. Check your answers</h3>
      <div id="dm-finish-report"></div>
    </li>
    <li class="dm-card">
      <h3>2. Save your answer file and your PDF</h3>
      <p>One press saves both. The page checks what it saved and gives you a receipt.</p>
      <div class="dm-actions">
        <button type="button" id="dm-submit" class="dm-primary">Save my answer file and PDF</button>
        <button type="button" id="dm-save-readable" class="dm-secondary">Save a readable copy</button>
        <button type="button" id="dm-print" class="dm-secondary">Print or save as PDF</button>
      </div>
      <p id="dm-saved" class="dm-restore-note" role="status" hidden></p>
      <p id="dm-problem" class="dm-problem" role="alert" hidden></p>
      <div class="dm-actions"><button type="button" id="dm-rechoose" class="dm-secondary" hidden>Choose the folder again</button></div>
      <p id="dm-pdf-note" class="dm-note" role="status" hidden></p>
      <div id="dm-again-row" class="dm-actions" hidden>
        <span class="dm-hint-text">If a file did not arrive:</span>
        <button type="button" id="dm-again-file" class="dm-secondary">Save the answer file again</button>
        <button type="button" id="dm-again-pdf" class="dm-secondary">Save the PDF again</button>
      </div>
    </li>
    <li class="dm-card">
      <h3>3. Hand it in</h3>
      <p>{hand_in or "Hand in your files as your teacher has said."}</p>
    </li>
  </ol>
  <section id="dm-confirm" class="dm-card dm-confirm" aria-labelledby="dm-confirm-h" hidden>
    <h3 id="dm-confirm-h">For your invigilator</h3>
    <dl class="dm-facts">
      <div><dt>Name</dt><dd id="dm-c-name"></dd></div>
      <div><dt>Student number</dt><dd id="dm-c-number"></dd></div>
      <div><dt>Paper</dt><dd id="dm-c-paper"></dd></div>
      <div><dt>Paper ID</dt><dd id="dm-c-id"></dd></div>
      <div><dt>Answers</dt><dd id="dm-c-answers"></dd></div>
      <div><dt>Saved</dt><dd id="dm-c-saved"></dd></div>
      <div><dt>Receipt</dt><dd id="dm-c-receipt"></dd></div>
      <div><dt>Files</dt><dd id="dm-c-files"></dd></div>
    </dl>
  </section>
  <div class="dm-actions"><button type="button" id="dm-keep-working" class="dm-secondary">Keep working</button></div>
</section>

<script type="application/json" id="dewmark-page-model">{model}</script>
<script type="application/json" id="dewmark-pdf-fonts">{pdf_fonts_json()}</script>
<script>{js}</script>
</body>
</html>
"""


def build_pages(text, base_dir):
    """The pages of a paper, and its marking scheme, as {file name: text}.
    Raises BuildError, with every reason, if the paper cannot be built or a
    page lets the marking scheme or a hint through."""
    base_dir = Path(base_dir)
    paper = read(text)
    if paper["messages"].problems:
        raise BuildError(paper["messages"].problems)
    problems = check_buildable(paper, base_dir)
    if problems:
        raise BuildError(problems)
    code = paper_fingerprint(text, paper, base_dir)
    pages = {variant: build_page(paper, variant, base_dir, code) for variant in VARIANTS}

    def builder(variant):
        def build_again(changed):
            again = read(changed)
            return build_page(again, variant, base_dir, paper_fingerprint(changed, again, base_dir))
        return build_again

    leaks = []
    for variant, strings in (("student", scheme_strings(text, student=True)),
                             ("practice", scheme_strings(text))):
        for leak in find_leaks(pages[variant], strings):
            leaks.append(f"{leak['kind']} text from {leak['where']} is in the {variant} page "
                         f"({leak['found as']}): \"{leak['text'][:60]}\"")
        result = mutation_test(text, builder(variant), hints=variant == "student")
        if not result["ok"]:
            leaks.append(f"the {variant} page changed when the marking scheme"
                         + (" and hints" if variant == "student" else "") + " did"
                         + (": " + ", ".join(result["culprits"]) if result["culprits"] else "")
                         + f" ({result['reason']})")
    if leaks:
        raise BuildError(["The paper was not built, because a page it would make gives away "
                          "what students must not see:"] + leaks)
    code = paper["settings"]["code"]
    files = {f"{code}.{variant}.html": pages[variant] for variant in VARIANTS}
    files[f"dewmark_{code}_marking_scheme.json"] = dumps(scheme_json(paper))
    return files


def build(path, out_dir=None):
    """Build the file at `path`. With `out_dir` the files are written there,
    all or none; without it the paper is only checked. Returns the file names."""
    path = Path(path)
    files = build_pages(path.read_text(encoding="utf-8"), path.parent)
    if out_dir is not None:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        for name, text in files.items():
            (out / name).write_text(text, encoding="utf-8")
    return list(files)
