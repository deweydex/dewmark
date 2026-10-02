"""Keeping the marking scheme off the student page: the last two of the four
layers (docs/EXAM_FORMAT.md §4.5).

Layers 1 and 2, in the reader, keep a teacher's slip from putting the scheme
on the page: the file is split at `# Marking scheme` before anything is
rendered, and anything shaped like scheme text above the line is refused.
These two guard the renderer, which is code and can be wrong, and neither
needs to know how a page is made: each takes a function `build(text)` that
turns an exam file into the student's page.

**The search (layer 3)** looks for every string of the scheme in the whole
built page, its embedded data included. The old builder searched only the text
a student could see, and so would never have found a key put into a script for
the page to use. A string is looked for as it is, escaped for HTML, and
escaped for JSON, since a page carries its data in any of these.

**The mutation test (layer 4)** needs no list of strings. It replaces what the
scheme says with nonsense (and each key of a choice, match, order or drop-down
box with a different valid one), builds the page again, and demands the page
be byte for byte what it was. A renderer that lets the key through in any
form, however short or hidden or encoded, changes the page, and the test
says which part of the scheme it came from.

    leaks = find_leaks(page, scheme_strings(text))
    result = mutation_test(text, build)
"""

import html
import json
import re
from types import SimpleNamespace

from .package import split_halves
from .reader import HEADING_RE, _tidy, read
from .scheme import CHOICE_KEY_RE, MATCH_PAIR_RE, _keyed_box

MIN_SEARCH = 8      # a shorter string would match innocent text
LONG = 40           # a longer one is also looked for in pieces, since a page
PIECE = 30          # may show only the start or the end of it
CURLY = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'"})


def _norm(text):
    """Capitals, curly quotes and runs of white space do not hide a string."""
    return re.sub(r"\s+", " ", text.translate(CURLY).lower()).strip()


# --- layer 3: the search -------------------------------------------------------

def scheme_strings(text):
    """Every piece of the marking scheme a page could give away, as a list of
    {"text", "where", "kind", "searchable", "looking for"}. The pieces are
    what a renderer would print: keys, model answers, tests, points,
    criteria, bands and the
    marker's guidance, a line at a time, and any text below the dividing
    line that is not in an entry. A string that also appears in the paper
    students are given, or is shorter than MIN_SEARCH, is listed but not
    searchable: finding it would prove nothing. "looking for" is what the
    search takes from it, normalised."""
    paper = read(text)
    head, rest = split_halves(text, reference=False)
    visible = _norm(head)
    found = []

    def add(piece, where, kind):
        piece = piece.strip()
        if not piece:
            return
        n = _norm(piece)
        # What is looked for: the whole string, and for a long one its start and
        # its end, each only if the paper does not already show it (a point may
        # open with the question's own words).
        looking = [n] + ([n[:PIECE], n[-PIECE:]] if len(n) > LONG else [])
        looking = [x for x in looking if len(x) >= MIN_SEARCH and x not in visible]
        found.append({"text": piece, "where": where, "kind": kind,
                      "searchable": bool(looking), "looking for": looking})

    for entry in paper["scheme"]["entries"].values():
        where = entry["label"]
        for slot in entry["key"] or []:
            for alternative in slot:
                add(str(alternative.get("text") or alternative.get("written") or ""), where, "key")
        for line in entry["model"].split("\n"):
            add(line, where, "model answer")
        for line in entry["tests"]:
            add(line, where, "test")
        for point in entry["points"]:
            add(point["text"], where, "point")
        for criterion in entry["criteria"]:
            add(criterion["name"], where, "criterion")
            for band in criterion["bands"]:
                add(band["text"], where, "band")
        for line in entry["guidance"]:
            add(line, where, "guidance")
    lines = rest.split("\n")[1:]
    for line in lines:
        if HEADING_RE.match(line):
            break
        add(line, "the marking scheme", "scheme text")
    return found


def _forms(n):
    """A string as a page might carry it."""
    yield n, "as it is"
    yield html.escape(n), "HTML-escaped"
    yield html.escape(n, quote=False), "HTML-escaped"
    for ascii_only in (True, False):
        encoded = json.dumps(n, ensure_ascii=ascii_only)[1:-1]
        yield encoded, "JSON-escaped"
        yield (encoded.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"),
               "JSON-escaped")


def find_leaks(page, strings):
    """Search the whole of a built page, data and scripts included, for the
    searchable strings of the scheme. Returns {"text", "where", "kind",
    "found as"} for each one found."""
    raw, unescaped = _norm(page), _norm(html.unescape(page))
    leaks = []
    for item in strings:
        if not item["searchable"]:
            continue
        for piece in item["looking for"]:
            hit = next((how for form, how in _forms(piece) if form in raw), None)
            if hit is None and piece in unescaped:       # escaped some other way for HTML
                hit = "HTML-escaped"
            if hit:
                leaks.append({"text": item["text"], "where": item["where"],
                              "kind": item["kind"], "found as": hit})
                break
    return leaks


# --- layer 4: the mutation test ---------------------------------------------------

def _view(paper):
    # scheme.py's rule for "which box does this key belong to" works on the
    # reader's own paper object; read() hands back a dict of the same parts.
    return SimpleNamespace(units=paper["units"], boxes=paper["boxes"], settings=paper["settings"])


def _alternative_text(alternative):
    return str(alternative.get("text") or alternative.get("written") or "")


def _next(options, letter):
    return options[(options.index(letter) + 1) % len(options)]


def _varied_key(entry, box, make):
    """A key of the same shape with different answers, still valid for its
    box: another option for a choice, match or order box, another entry of a
    list for a drop-down, nonsense for anything a student writes."""
    texts = [[_alternative_text(a) for a in slot] for slot in entry["key"]]
    kind, inner = (box["kind"], box["inner"]) if box else (None, None)
    first = texts[0][0] if texts and texts[0] else ""
    options = list(inner["options"]) if inner else []
    if kind == "choice" and len(options) > 1:
        m = CHOICE_KEY_RE.match(first)
        if m:
            letters = [l.strip() for l in m.group("letters").split(",")]
            return [[", ".join(_next(options, l) for l in letters)]]
    if kind == "match" and len(options) > 1:
        pairs = [MATCH_PAIR_RE.match(p.strip()) for p in first.split(",") if p.strip()]
        if pairs and all(pairs):
            return [[", ".join(f"{m.group(1)} {_next(options, m.group(2))}" for m in pairs)]]
    if kind == "order" and len(options) > 1:
        letters = [l.strip() for l in first.split(",")]
        if len(letters) > 1:
            return [[", ".join(letters[1:] + letters[:1])]]
    if kind in ("boxes", "blanks", "table") and inner:
        varied = []
        for slot, key in zip(inner["slots"], texts):
            allowed = slot[1] or inner["bank"]
            if allowed and len(allowed) > 1:
                current = next((i for i, a in enumerate(allowed)
                                if any(a.lower() == t.lower() for t in key)), -1)
                varied.append([allowed[(current + 1) % len(allowed)]])
            else:
                varied.append([make("key")])
        if len(varied) == len(texts):
            return varied
    return [[make("key")] for _ in texts]


def _entry_lines(entry, paper, make):
    """One entry of the scheme written again with nonsense in the place of
    everything it says, and its structure, its marks and its outcomes kept."""
    heading = "### " + entry["label"]
    if entry["caption"]:
        heading += ": " + entry["caption"]
    lines = [heading + (" (draft)" if entry["draft"] else ""), ""]
    if entry["topic"]:
        lines.append("Topic: " + make("topic"))
    if entry["outcomes"]:
        lines.append("Outcomes: " + ", ".join(entry["outcomes"]))
    if entry["key"] is not None:
        box = _keyed_box(entry, _view(paper))
        key = _varied_key(entry, box, make)
        if len(key) == 1 and not entry["any_order"]:
            lines.append("Answer: " + " / ".join(key[0]))
        else:
            lines.append("Answers (any order):" if entry["any_order"] else "Answers:")
            lines += [f"{n}. " + " / ".join(slot) for n, slot in enumerate(key, 1)]
    if entry["model"]:
        if entry["model_is_code"]:
            lines += ["```python", "# " + make("model"), "```"]
        else:
            lines.append("Model answer: " + make("model"))
    if entry["tests"]:
        lines += ["```tests"] + ["# " + make("test") for _ in entry["tests"]] + ["```"]
    for point in entry["points"]:
        lines.append(f"- {point['marks']:g} marks: " + make("point"))
    for criterion in entry["criteria"]:
        lines.append(f"- **{make('criterion')}** ({criterion['marks']:g} marks)")
        for band in criterion["bands"]:
            lines.append(f"  - {band['low']:g} to {band['high']:g}: " + make("band"))
    for _ in entry["guidance"]:
        lines.append(make("guidance"))
    return lines + [""]


def mutate(text, only=None):
    """The exam file with its marking scheme said again in nonsense. The
    paper half is not touched, and the scheme keeps its entries, marks and
    structure, so the mutated file reads as the original does. With `only`
    (a set of entry names) the other entries are kept as they were written.
    Returns (text, the number of entries made nonsense)."""
    text = _tidy(text)
    paper = read(text)
    lines = text.split("\n")
    head, rest = split_halves(text, reference=False)
    entries = list(paper["scheme"]["entries"].values())
    if not rest.strip() or not entries:
        return text, 0
    counter = iter(range(1, 10 ** 6))

    def make(kind):
        return f"zqx{next(counter):04d}vjk"

    first = len(head.split("\n"))              # index of the "# Marking scheme" line
    out = head.split("\n") + [lines[first], ""]
    starts = [e["line"] - 1 for e in entries] + [len(lines)]
    changed = 0
    for entry, start, stop in zip(entries, starts, starts[1:]):
        if only is None or entry["name"] in only:
            out += _entry_lines(entry, paper, make)
            changed += 1
        else:
            out += lines[start:stop]
    if only is not None and starts[0] > first + 1:       # text before the first entry
        out[first + 2:first + 2] = lines[first + 1:starts[0]]
    return "\n".join(out).rstrip("\n") + "\n", changed


def mutation_test(text, build):
    """Build the student page from the exam file and from the file with its
    marking scheme replaced by nonsense, and compare. `build(text)` is the
    renderer, returning the page. Returns {"ok", "reason", "culprits"}: the
    page must not change, and if it does, `culprits` names the entries of
    the scheme it changed with."""
    original = read(text)
    if original["messages"].problems:
        return {"ok": False, "reason": "the paper has problems, so it cannot be built",
                "culprits": []}
    mutated, changed = mutate(text)
    if not changed:
        return {"ok": True, "reason": "the paper has no marking scheme entries to change",
                "culprits": []}
    after = read(mutated)
    if after["messages"].problems or list(after["boxes"]) != list(original["boxes"]):
        return {"ok": False, "culprits": [], "reason":
                "the nonsense version of the scheme does not read as the paper does ("
                + "; ".join(m.what for m in after["messages"].problems[:3]) + ")"}
    page = build(text)
    if build(mutated) == page:
        return {"ok": True, "reason": "", "culprits": []}
    culprits = []
    for entry in original["scheme"]["entries"].values():
        one, _ = mutate(text, only={entry["name"]})
        if build(one) != page:
            culprits.append(entry["label"])
    return {"ok": False, "culprits": culprits,
            "reason": "the student page changed when the marking scheme did"
                      + ("" if culprits else ", but not for any one entry alone")}
