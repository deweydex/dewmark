"""The closed lists: what may follow three backticks, and what each kind of
answer box holds (docs/EXAM_FORMAT.md §4.3, §4.8).

This is the first shape of the registry. Each answer kind names its
body grammar here: how the reader finds its inner parts (options, lines,
gaps) so the marking scheme can be checked against them. The page and
workbench halves of each kind arrive with the steps that render them;
an unknown kind is refused, so adding one never changes the format.
"""

import re

# Answer boxes: what the student fills in.
ANSWER_KINDS = (
    "answer", "maths", "python exec", "code", "essay", "boxes", "blanks",
    "table", "choice", "match", "order", "photo", "on-paper",
)

# Listings: things students read. A closed list of languages.
LISTING_LANGUAGES = ("python", "sql", "text", "pseudo", "output")

# Kinds whose key in the scheme is checked against the box's inner parts.
KEYED_KINDS = ("boxes", "blanks", "table", "choice", "match", "order")

NOTE_RE = re.compile(
    r"\s*\((not marked|choose\s+\d+|about\s+\d+\s+words|\d+\s+lines|"
    r"input:\s*[a-z ,]+|letters may repeat)\)\s*$", re.I)

# A gap: three or more underscores, or [a / b / c] (options with " / ").
TYPED_GAP_RE = re.compile(r"_{3,}")
CHOICE_GAP_RE = re.compile(r"\[([^\[\]]+?(?:\s/\s[^\[\]]+?)+)\]")
PROTECTED_RE = re.compile(r"`[^`]*`|\$[^$]*\$")

OPTION_RE = re.compile(r"^([A-Z])\.(?:\s+|$)")
ITEM_RE = re.compile(r"^(\d+)\.\s+")
BANK_RE = re.compile(r"^choose from\s*:\s*(.+)$", re.I)


def split_notes(rest):
    """Peel the notes off the end of a fence line's label."""
    notes = []
    while True:
        m = NOTE_RE.search(rest)
        if not m:
            return rest.strip(), notes
        notes.insert(0, re.sub(r"\s+", " ", m.group(1).lower()))
        rest = rest[:m.start()]


def gaps_in(text):
    """The gaps in a line of text, in order: ("typed", None) for ____,
    ("choose", [options]) for [a / b / c]. Gaps inside backticks or $…$
    are not gaps."""
    masked = PROTECTED_RE.sub(lambda m: " " * len(m.group(0)), text)
    found = []
    for m in TYPED_GAP_RE.finditer(masked):
        found.append((m.start(), ("typed", None)))
    for m in CHOICE_GAP_RE.finditer(masked):
        found.append((m.start(), ("choose", [o.strip() for o in m.group(1).split(" / ")])))
    return [g for _, g in sorted(found, key=lambda x: x[0])]


def inner_parts(kind, body):
    """What a box contains that the scheme can refer to.

    Returns a dict: "options" (letter -> text) for choice, match and order;
    "items" (number -> text) for match; "slots" (a list, one per thing to
    fill in) for boxes, blanks and table; "bank" for boxes with a
    Choose from: line.
    """
    lines = [l for l in body if l.strip()]
    parts = {"options": {}, "items": {}, "slots": [], "bank": None}
    if kind in ("choice", "match", "order"):
        current = None
        for line in body:
            m = OPTION_RE.match(line)
            if m:
                current = m.group(1)
                parts["options"][current] = line[m.end():].strip()
            elif kind == "match" and ITEM_RE.match(line):
                mm = ITEM_RE.match(line)
                parts["items"][mm.group(1)] = line[mm.end():].strip()
                current = None
            elif current and line.strip():
                parts["options"][current] += "\n" + line.strip()
    elif kind == "boxes":
        if lines and BANK_RE.match(lines[-1].strip()):
            parts["bank"] = [o.strip() for o in BANK_RE.match(lines[-1].strip()).group(1).split(" / ")]
            lines = lines[:-1]
        for line in lines:
            gaps = gaps_in(line)
            parts["slots"].extend(gaps or [("typed", None)])
    elif kind in ("blanks", "table"):
        for line in lines:
            parts["slots"].extend(gaps_in(line))
    return parts
