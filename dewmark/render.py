"""Turning a paper read by `dewmark.reader` into the HTML of a page
(docs/EXAM_FORMAT.md §4.3; planning/PROPOSAL.md §9, step 4).

The reader keeps the paper's content in document order as blocks: sections
and parts as they are headed, the prose between them, listings, answer
boxes, shared material and hints. This module draws each as HTML for one of
three pages built from every file:

- **student**: the paper, with no hint and nothing from the marking scheme;
- **practice**: the same, with each hint drawn under its box;
- **answer-key**: the practice page with the marking scheme's key, model
  answer, points, criteria and tests drawn under each box, for the teacher.

A paper comes from a teacher, and from an assistant a teacher asked for help,
so what is in it is not trusted. Raw HTML in prose is shown as text, never
run; a link is shown as text with its address; a picture is embedded only if
it is a picture file inside the paper's own folder. A page carries a policy
that lets it connect to nothing (`dewmark/build.py`), and these rules are the
reason that policy is not the only guard.

This is the one module of the package that needs more than Python's standard
library (`markdown`, and `latex2mathml` to typeset $…$), so the checker page,
which runs the reader in a browser, does not carry it.
"""

import base64
import html
import re
from pathlib import Path

import markdown as markdown_lib

try:
    import latex2mathml.converter as mathml_converter
except ImportError:  # the build reports this when a paper needs it
    mathml_converter = None

from .kinds import gap_spans
from .messages import Messages

VARIANTS = ("student", "practice", "answer-key")

# Kinds the reader accepts that no page draws yet. A paper using one cannot
# be built, with a message saying so, rather than be drawn without it.
NOT_BUILT = {
    "match": "matching boxes, which come with the biology papers (step 8)",
    "order": "ordering boxes, which come with the biology papers (step 8)",
    "photo": "photographs of handwritten work (step 8)",
    "on-paper": "answers given on paper (step 8)",
}

PICTURE_TYPES = {"svg": "image/svg+xml", "png": "image/png", "jpg": "image/jpeg",
                 "jpeg": "image/jpeg", "gif": "image/gif", "webp": "image/webp"}
LOGO_LIMIT = 150 * 1024        # bytes: a logo is carried in every copy of the page
MATH_RE = re.compile(r"\$([^$\n]+)\$")
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]*)\)")
LINK_RE = re.compile(r'<a href="([^"]*)"[^>]*>(.*?)</a>', re.S)
IMG_TAG_RE = re.compile(r'<img [^>]*?alt="([^"]*)"[^>]*?src="([^"]*)"[^>]*?/?>|'
                        r'<img [^>]*?src="([^"]*)"[^>]*?alt="([^"]*)"[^>]*?/?>')


def esc(value):
    return html.escape(str(value), quote=True)


# --- prose -----------------------------------------------------------------------

def math_html(tex):
    """One $…$ expression, typeset as MathML, which every current browser
    draws itself. If the converter is missing or refuses the expression the
    text falls back to italics, and the build says so."""
    if mathml_converter is not None:
        try:
            return mathml_converter.convert(tex)
        except Exception:
            pass
    return f'<em class="dm-math">{esc(tex)}</em>'


def _picture(base_dir, path):
    """A picture file as a data address, so the page stays one file. Only a
    picture inside the paper's own folder is read: never an address on the
    internet, never a path that climbs out of the folder. Returns None if the
    path is not one of those."""
    if base_dir is None or not path or re.match(r"^[a-z][a-z0-9+.-]*:", path, re.I) \
            or path.startswith(("/", "\\")):
        return None
    root = Path(base_dir).resolve()
    target = (root / path).resolve()
    kind = PICTURE_TYPES.get(target.suffix.lower().lstrip("."))
    if kind is None or not target.is_file() or root not in target.parents:
        return None
    return f"data:{kind};base64,{base64.b64encode(target.read_bytes()).decode('ascii')}"


def logo_problem(settings, base_dir):
    """Why the `logo` setting cannot go into a page, in words, or None."""
    path = settings.get("logo")
    if not path:
        return None
    data = _picture(base_dir, path)
    if data is None:
        return ("unavailable", f"The logo \"{path}\" can't be put in the page: it must be a "
                f"{', '.join(sorted(PICTURE_TYPES))} file in the paper's own folder.")
    size = len(base64.b64decode(data.partition(",")[2]))
    if size > LOGO_LIMIT:
        return ("too-big", f"The logo \"{path}\" is {size // 1024} KB, and a logo may be at "
                f"most {LOGO_LIMIT // 1024} KB, because every copy of the paper carries it.")
    return None


def render_markdown(text, base_dir=None, holes=None):
    """Prose as HTML, with $…$ typeset and nothing in it trusted.

    `holes` maps a marker string already placed in `text` to the HTML to put
    there afterwards (the gaps of a sentence, which the Markdown step must
    not touch)."""
    stash = []

    def lift(match):
        stash.append(match.group(1))
        return f"\x00MATH{len(stash) - 1}\x00"

    md = markdown_lib.Markdown(extensions=["tables", "fenced_code"])
    md.preprocessors.deregister("html_block")     # raw HTML is text, not markup
    md.inlinePatterns.deregister("html")
    out = md.convert(MATH_RE.sub(lift, text))
    for index, tex in enumerate(stash):
        out = out.replace(f"\x00MATH{index}\x00", math_html(tex))

    def link(match):
        address, words = html.unescape(match.group(1)), match.group(2)
        if re.match(r"^https?://", address, re.I):
            return f'{words} <span class="dm-url">({esc(address)})</span>'
        return words

    out = LINK_RE.sub(link, out)

    def picture(match):
        alt, src = (match.group(1), match.group(2)) if match.group(1) is not None \
            else (match.group(4), match.group(3))
        data = _picture(base_dir, html.unescape(src))
        if data is None:
            return f'<span class="dm-missing">[picture not available: {alt}]</span>'
        return f'<img alt="{alt}" src="{data}">'

    out = IMG_TAG_RE.sub(picture, out)
    for marker, replacement in (holes or {}).items():
        out = out.replace(marker, replacement)
    return out


# --- what cannot be drawn ---------------------------------------------------------

def check_buildable(paper, base_dir):
    """Everything that stops a page being built from this paper, as messages
    with codes: a kind no page draws yet, and a picture that is undescribed,
    on the internet, outside the paper's folder, missing, or not a picture."""
    messages = Messages()
    for box in paper["boxes"].values():
        if box["kind"] in NOT_BUILT:
            messages.problem(
                "kind-not-built", box["line"],
                f"The ```{box['kind']} box in {box['label']} can't be built into a page yet: "
                f"pages don't draw {NOT_BUILT[box['kind']]}.",
                "Use another kind of box for now, or ```answer.", box["label"])
    sources = []
    for block in paper["blocks"]:
        if block["type"] == "text":
            sources.append((block["line"], "\n".join(block["lines"])))
        elif block["type"] in ("material", "hint"):
            sources.append((block["line"], block["body"]))
    sources += [(box["line"], box["body"]) for box in paper["boxes"].values()]
    for line, text in sources:
        for alt, path in IMAGE_RE.findall(text):
            if not alt.strip():
                messages.problem(
                    "picture-undescribed", line,
                    f"The picture {path or '(no file)'} has no description, so a student who "
                    "can't see it would have nothing to read in its place.",
                    "Write what it shows between the square brackets: ![what it shows](file).")
            if _picture(base_dir, path) is None:
                messages.problem(
                    "picture-unavailable", line,
                    f"The picture \"{path}\" can't be put in the page: it must be a "
                    f"{', '.join(sorted(PICTURE_TYPES))} file in the paper's own folder.",
                    "Put the file beside the exam file, or in a folder inside it, and use "
                    "its relative name.")
    found = logo_problem(paper["settings"], base_dir)
    if found:
        code, what = found
        messages.problem(
            f"logo-{code}", paper["setting_lines"].get("logo", 1), what,
            "Put a smaller picture beside the exam file, or take the logo line out." if code == "too-big"
            else "Put the file beside the exam file, or in a folder inside it, and use its relative name.")
    if mathml_converter is None and any(MATH_RE.search(t) for _, t in sources):
        messages.problem(
            "maths-not-installed", 1,
            "The paper has maths between dollar signs, but the typesetting program "
            "latex2mathml is not installed.", "pip install -r requirements.txt")
    return messages


# --- answer boxes -----------------------------------------------------------------

def _rows(box, marks):
    for note in box["notes"]:
        found = re.match(r"(\d+) lines", note)
        if found:
            return max(2, int(found.group(1)))
    if marks is None or marks <= 2:
        return 3
    return 6 if marks <= 5 else 10


def _note(box, pattern):
    for note in box["notes"]:
        found = re.match(pattern, note)
        if found:
            return int(found.group(1))
    return None


def _gap_html(gap, index, label):
    kind, choices = gap
    if kind == "typed":
        return (f'<input class="dm-gap" type="text" data-slot="{index}" '
                f'autocomplete="off" aria-label="{esc(label)}">')
    options = "".join(f'<option value="{esc(c)}">{esc(c)}</option>' for c in choices)
    return (f'<select class="dm-gap" data-slot="{index}" aria-label="{esc(label)}">'
            f'<option value=""></option>{options}</select>')


def _with_gaps(text, start, bank=None):
    """A line of text with its gaps replaced by markers, and the HTML to put
    at each marker, numbering the gaps from `start`. A bank turns every typed
    gap into a drop-down of the bank. Returns (text, holes, next number)."""
    holes, out, last, index = {}, [], 0, start
    for first, end, gap in gap_spans(text):
        out.append(text[last:first])
        marker = f"\x00GAP{index}\x00"
        shown = ("choose", bank) if bank and gap[0] == "typed" else gap
        holes[marker] = _gap_html(shown, index, f"answer {index}")
        out.append(marker)
        last, index = end, index + 1
    out.append(text[last:])
    return "".join(out), holes, index


def _choice(box, base_dir):
    options = box["inner"]["options"]
    several = (_note(box, r"choose\s+(\d+)") or 1) > 1
    control = "checkbox" if several else "radio"
    rows = []
    for letter, text in options.items():
        rows.append(
            f'<label class="dm-option"><input type="{control}" name="{esc(box["name"])}" '
            f'value="{esc(letter)}"><span class="dm-letter">{esc(letter)}</span>'
            f'<span class="dm-option-text">{render_markdown(text, base_dir)}</span></label>')
    return '<div class="dm-options">' + "".join(rows) + "</div>"


def _boxes(box, base_dir):
    lines = [l for l in box["body"].split("\n") if l.strip()]
    bank = box["inner"]["bank"]
    if bank:
        lines = lines[:-1]
    rows, index = [], 1
    for line in lines:
        text, holes, after = _with_gaps(line, index, bank)
        if after == index:                        # a line with no gap is one box to fill
            holes["\x00ROW\x00"] = (_gap_html(("choose", bank), index, line) if bank else
                                    _gap_html(("typed", None), index, line))
            text, after = text + " \x00ROW\x00", index + 1
        rows.append('<div class="dm-boxline">' + render_markdown(text, base_dir, holes) + "</div>")
        index = after
    return '<div class="dm-boxes">' + "".join(rows) + "</div>"


def _blanks(box, base_dir):
    rows, index = [], 1
    for line in [l for l in box["body"].split("\n") if l.strip()]:
        text, holes, index = _with_gaps(line, index)
        rows.append(render_markdown(text, base_dir, holes))
    return '<div class="dm-blanks">' + "".join(rows) + "</div>"


def _table(box, base_dir):
    holes, index, lines = {}, 1, []
    for line in box["body"].split("\n"):
        text, more, index = _with_gaps(line, index)
        holes.update(more)
        lines.append(text)
    out = render_markdown("\n".join(lines), base_dir, holes)
    # Say which row and column each box is in, for a reader who hears the page.
    rows = out.split("<tr>")
    for r, row in enumerate(rows[1:], 1):
        cells = row.split("<td")
        for c, cell in enumerate(cells[1:], 1):
            cells[c] = re.sub(r'aria-label="answer (\d+)"',
                              lambda m: f'aria-label="answer {m.group(1)}, row {r - 1}, '
                                        f'column {c}"', cell)
        rows[r] = "<td".join(cells)
    return '<div class="dm-table-wrap">' + "<tr>".join(rows) + "</div>"


def render_box(box, paper, base_dir):
    """One answer box as HTML. The page finds it by data-answer and its kind
    by data-kind, and every control inside it by a class or a number."""
    kind, name = box["kind"], box["name"]
    marks = paper["units"][box["unit"]]["marks"]
    label = ""
    if box["caption"]:
        label = f'<p class="dm-small-label">{esc(box["caption"])}</p>'
    if box["unmarked"]:
        label += '<p class="dm-small-label">Not marked</p>'
    starter = esc(box["body"].rstrip())
    if kind in ("answer", "maths"):
        what = "your working" if kind == "maths" else "your answer"
        inner = (f'<textarea class="dm-writing" rows="{_rows(box, marks)}" '
                 f'aria-label="{esc(box["caption"] or what)}">{starter}</textarea>')
    elif kind == "essay":
        words = _note(box, r"about\s+(\d+)\s+words")
        guide = f'<p class="dm-small-label">About {words} words</p>' if words else ""
        inner = (guide + f'<textarea class="dm-writing dm-essay" rows="24" '
                 f'aria-label="your essay">{starter}</textarea>'
                 '<p class="dm-word-count" aria-live="polite">0 words</p>')
    elif kind in ("code", "python exec"):
        bar = '<div class="dm-code-bar"><span class="dm-code-lang">Python</span></div>' \
            if kind == "python exec" else ""
        inner = (bar + f'<textarea class="dm-code" spellcheck="false" '
                 f'rows="{max(6, box["body"].count(chr(10)) + 3)}" '
                 f'aria-label="{esc(box["caption"] or "your code")}">{starter}</textarea>')
    elif kind == "choice":
        inner = _choice(box, base_dir)
    elif kind == "boxes":
        inner = _boxes(box, base_dir)
    elif kind == "blanks":
        inner = _blanks(box, base_dir)
    elif kind == "table":
        inner = _table(box, base_dir)
    else:
        raise ValueError(f"no page draws a ```{kind} box; check_buildable should have refused")
    return (f'<div class="dm-answer" data-answer="{esc(name)}" data-kind="{esc(kind)}" '
            f'data-marked="{"no" if box["unmarked"] else "yes"}">{label}{inner}</div>')


# --- the answer key ---------------------------------------------------------------

def _alternative_text(alt):
    if "text" in alt:
        return alt["text"]
    unit = f" {alt['unit']}" if alt.get("unit") else ""
    places = f" ({alt['dp']} d.p.)" if "dp" in alt else f" ({alt['sf']} s.f.)" if "sf" in alt else ""
    if "number" in alt:
        if "tolerance" in alt:
            return f"{alt['written']}{unit} ± {alt['tolerance']:g}{'%' if alt.get('percent') else ''}{places}"
        return f"{alt['written']}{unit}{places}"
    return f"{alt['low']:g} to {alt['high']:g}{unit}{places}"


def render_key(entry):
    """The marking scheme's entry for a box or part, drawn for the teacher."""
    parts = ['<div class="dm-model">']
    if entry["draft"]:
        parts.append('<p class="dm-draft">Draft: not yet approved by the teacher</p>')
    if entry["key"]:
        slots = [" / ".join(esc(_alternative_text(a)) for a in slot) for slot in entry["key"]]
        parts.append('<p class="dm-model-label">Key</p>' + (
            f'<p class="dm-model-text">{slots[0]}</p>' if len(slots) == 1 else
            "<ol>" + "".join(f"<li>{s}</li>" for s in slots) + "</ol>")
            + ('<p class="dm-small-label">Any order</p>' if entry["any_order"] else ""))
    if entry["model"]:
        shown = (f'<pre class="dm-model-code">{esc(entry["model"])}</pre>' if entry["model_is_code"]
                 else f'<p class="dm-model-text">{esc(entry["model"])}</p>')
        parts.append('<p class="dm-model-label">Model answer</p>' + shown)
    if entry["points"]:
        parts.append('<p class="dm-model-label">Points to tick</p><ul>' + "".join(
            f"<li>{p['marks']:g}: {esc(p['text'])}</li>" for p in entry["points"]) + "</ul>")
    for criterion in entry["criteria"]:
        parts.append(f'<p class="dm-model-label">{esc(criterion["name"])} '
                     f'({criterion["marks"]:g} marks)</p><ul>' + "".join(
                         f"<li>{b['low']:g} to {b['high']:g}: {esc(b['text'])}</li>"
                         for b in criterion["bands"]) + "</ul>")
    if entry["tests"]:
        parts.append('<p class="dm-model-label">Hidden tests</p><pre class="dm-model-code">'
                     + esc("\n".join(entry["tests"])) + "</pre>")
    if entry["guidance"]:
        parts.append('<p class="dm-model-label">For the marker</p><ul>' + "".join(
            f"<li>{esc(g)}</li>" for g in entry["guidance"]) + "</ul>")
    if entry["topic"] or entry["outcomes"]:
        parts.append('<p class="dm-small-label">' + esc(" · ".join(filter(None, [
            f"Topic: {entry['topic']}" if entry["topic"] else "",
            f"Outcomes: {', '.join(entry['outcomes'])}" if entry["outcomes"] else ""]))) + "</p>")
    if len(parts) == 1:                  # nothing to say: no empty box
        return ""
    parts.append("</div>")
    return "".join(parts)


# --- the paper --------------------------------------------------------------------

def _marks_chip(marks):
    return f'<span class="dm-marks">({marks:g} mark{"" if marks == 1 else "s"})</span>'


def _unit_title(unit):
    if unit["level"] == 2:
        head = f"Question {unit['label']}"
    elif unit["level"] == 3:
        head = unit["label"]
    else:
        head = re.findall(r"\([^)]*\)", unit["label"])[-1]
    return esc(head + (f": {unit['title']}" if unit["title"] else ""))


def _listing(block):
    lines = block["body"].split("\n")
    code = "".join(f'<span class="dm-line">{esc(line) or " "}</span>' for line in lines)
    return f'<pre class="dm-listing" data-lang="{esc(block["lang"])}"><code>{code}</code></pre>'


def render_front(paper, base_dir):
    """The instructions to candidates: the prose and headings before the
    first section or question."""
    return "".join(render_markdown("\n".join(b["lines"]), base_dir)
                   for b in paper["blocks"] if b["type"] == "text" and b["front"])


def render_paper(paper, variant, base_dir):
    """The body of the paper: its sections, questions, parts, prose, listings
    and answer boxes in the order they were written. The student page has no
    hint and no key; the practice page has hints; the answer key has both."""
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {', '.join(VARIANTS)}")
    entries = paper["scheme"]["entries"]
    out, stack = [], []         # stack: the unit levels open now

    def close(to=0):
        while len(stack) > to:
            stack.pop()
            out.append("</div>")

    section_open = False
    pending = None              # a unit whose own entry is drawn when it closes

    def settle():
        nonlocal pending
        if pending and variant == "answer-key":
            out.append(render_key(entries[pending]))
        pending = None

    for block in paper["blocks"]:
        kind = block["type"]
        if kind == "text":
            if not block["front"]:
                out.append(render_markdown("\n".join(block["lines"]), base_dir))
        elif kind == "section":
            settle(); close()
            if section_open:
                out.append("</section>")
            section_open = True
            marks = _marks_chip(block["marks"]) if block["marks"] is not None else ""
            out.append(f'<section class="dm-section"><h2 class="dm-section-title">'
                       f'{esc(block["title"])} {marks}</h2>')
        elif kind == "unit":
            settle()
            unit = paper["units"][block["name"]]
            close(unit["level"] - 2)
            tag = {2: "h3", 3: "h4", 4: "h5"}[unit["level"]]
            cls = {2: "dm-question", 3: "dm-part", 4: "dm-subpart"}[unit["level"]]
            extra = f' data-question="{esc(unit["name"])}"' if unit["level"] == 2 else ""
            out.append(f'<div class="{cls}" id="{esc(unit["name"])}"{extra}>'
                       f'<{tag} class="{cls}-title">{_unit_title(unit)} '
                       f'{_marks_chip(unit["marks"])}</{tag}>')
            stack.append(unit["level"])
            pending = unit["name"] if unit["name"] in entries else None
        elif kind == "listing":
            out.append(_listing(block))
        elif kind == "material":
            label = f'<figcaption>{esc(block["label"])}</figcaption>' if block["label"] else ""
            out.append(f'<figure class="dm-material">{label}'
                       f'{render_markdown(block["body"], base_dir)}</figure>')
        elif kind == "box":
            box = paper["boxes"][block["name"]]
            out.append(render_box(box, paper, base_dir))
            if variant == "answer-key" and block["name"] in entries:
                out.append(render_key(entries[block["name"]]))
                if pending == block["name"]:     # a box named as its part has its entry now
                    pending = None
        elif kind == "hint" and variant != "student":
            out.append('<details class="dm-hint"><summary>Hint</summary>'
                       f'{render_markdown(block["body"], base_dir)}</details>')
    settle(); close()
    if section_open:
        out.append("</section>")
    return "".join(out)
