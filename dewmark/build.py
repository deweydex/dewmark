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
"""

import html
import json
from pathlib import Path

from .reader import read
from .render import VARIANTS, check_buildable, render_front, render_paper
from .scheme_json import dumps, scheme_json
from .secrecy import find_leaks, mutation_test, scheme_strings

ASSETS = Path(__file__).resolve().parent.parent / "assets"

# What a built page may do: run its own script and style, show pictures it
# carries, and nothing else. It connects to nothing, so a student's answers,
# and anything a paper's wording might try, have nowhere to go.
POLICY = ("default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
          "img-src data:; form-action 'none'; base-uri 'none'")

KIND_LABELS = {"exam": "Examination", "practice": "Practice paper", "sample": "Sample paper"}
BANDS = {"student": None, "practice": "Practice version",
         "answer-key": "Answer key: not for students"}
DETAILS = ("full name", "student number")


class BuildError(Exception):
    """A build that cannot go ahead. `messages` says why, in plain words."""

    def __init__(self, messages):
        self.messages = [str(m) for m in messages]
        super().__init__("\n".join(self.messages))


def esc(value):
    return html.escape(str(value), quote=True)


def page_model(paper, variant):
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
                     "marks": paper["total"]},
            "sections": sections, "questions": questions}


def _band(paper, variant):
    settings = paper["settings"]
    kind = BANDS[variant] or KIND_LABELS.get(settings.get("kind"), "Paper")
    meta = [settings.get(k) for k in ("module", "session", "institution")]
    meta = " · ".join(esc(m) for m in meta if m)
    facts = []
    if settings.get("time allowed"):
        facts.append("Time allowed: " + esc(settings["time allowed"]))
    facts.append(f"Total marks: {paper['total']:g}")
    return (f'<header class="dm-band dm-band-{variant}"><p class="dm-band-kind">{esc(kind)}</p>'
            f'<h1 class="dm-band-title">{esc(settings.get("title", ""))}</h1>'
            f'<p class="dm-band-meta">{meta + " · " if meta else ""}{" · ".join(facts)}</p></header>')


def build_page(paper, variant, base_dir):
    """One complete page as text: styles, start screen, paper, finish screen,
    data block and behaviour, all in one file."""
    settings = paper["settings"]
    css = (ASSETS / "page.css").read_text(encoding="utf-8")
    js = (ASSETS / "page.js").read_text(encoding="utf-8")
    model = json.dumps(page_model(paper, variant)).replace("<", "\\u003c")
    instructions = render_front(paper, base_dir) or "<p>Read each question carefully.</p>"
    details = "".join(
        f'<label class="dm-detail">{esc(d.capitalize())} '
        f'<input type="text" data-detail="{esc(d)}" autocomplete="off"></label>' for d in DETAILS)
    hand_in = esc(settings.get("hand in", ""))
    title = esc(settings.get("title", ""))
    return f"""<!doctype html>
<html lang="en-IE">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="Content-Security-Policy" content="{POLICY}">
<title>{title}</title>
<style>{css}</style>
</head>
<body data-variant="{variant}">
{_band(paper, variant)}

<div id="dm-start" class="dm-card">
  <div class="dm-instructions">{instructions}</div>
  <div class="dm-details">{details}</div>
  <p class="dm-save-note">When you press Begin, you will be asked where to keep your
  answer file. The paper then saves itself there, and in this browser, as you work.
  Nothing leaves this computer.</p>
  <button type="button" id="dm-begin" class="dm-primary">Begin</button>
  <button type="button" id="dm-load-file" class="dm-secondary">Load a saved answer file…</button>
</div>

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

<div id="dm-finish-screen" class="dm-card" hidden>
  <h2>Check before you hand in</h2>
  <div id="dm-finish-report"></div>
  <p>{hand_in or "Save your answer file, and hand it in as your teacher has said."}</p>
  <button type="button" id="dm-submit" class="dm-primary">Save my answer file</button>
  <button type="button" id="dm-save-readable" class="dm-secondary">Save a readable copy</button>
  <button type="button" id="dm-keep-working" class="dm-secondary">Keep working</button>
</div>

<script type="application/json" id="dewmark-page-model">{model}</script>
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
    pages = {variant: build_page(paper, variant, base_dir) for variant in VARIANTS}

    def builder(variant):
        return lambda changed: build_page(read(changed), variant, base_dir)

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
