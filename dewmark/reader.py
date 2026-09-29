"""The reader for the exam format in docs/EXAM_FORMAT.md.

    from dewmark.reader import read
    paper = read(text)
    paper["messages"]          # every problem and warning, in order
    paper["boxes"]             # answer boxes by permanent name

`read()` never raises on a bad file: everything wrong comes back as a
message with a stable code (dewmark/messages.py). The layers are read in
order: settings (§4.9), the split into the paper, the reference cards and
the marking scheme (§4.1, §4.5), headings and marks (§4.2), fences and
names (§4.3, §4.4), the sums, then the marker's half (§4.6) and the
checks that need both halves.
"""

import difflib
import re

from . import READER_VERSION
from .kinds import (ANSWER_KINDS, KEYED_KINDS, LISTING_LANGUAGES, inner_parts,
                    split_notes)
from .messages import Messages
from .numbers import label_of, name_of, read_number, slug, split_title
from .scheme import POINT_RE, CRITERION_RE, read_scheme
from .settings import read_settings

FENCE_RE = re.compile(r"^(`{3,}|~{3,})(.*)$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
MARKS_RE = re.compile(
    r"\s*(?:\((\d+(?:\.5)?)\s*marks?\)|\[(\d+(?:\.5)?)(?:\s*marks?)?\])\s*$", re.I)
ANY_RE = re.compile(r"\bany\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\b", re.I)
WORDS = dict(one=1, two=2, three=3, four=4, five=5, six=6, seven=7, eight=8, nine=9, ten=10)
SCHEME_LINE_RE = re.compile(r"^#\s+mark(?:ing)?\s+scheme\s*:?\s*$", re.I)
REFERENCE_LINE_RE = re.compile(r"^#\s+reference\s*$", re.I)
LOOKALIKE_RE = re.compile(r"^(mark|marking|scheme|solutions?|answers?|answer key|key)\b", re.I)
LOOKS_NUMBERED_RE = re.compile(r"^(question\s+\d|\(?[a-h]\)\s|\d+\s*\(?[a-h]\)?\s*[:\s)])", re.I)
ABOVE_LINE_RE = re.compile(r"^\s*(model answer|answers?)(\s*\(any order\))?\s*:", re.I)
BOLD_MARKS_RE = re.compile(r"\(\d+(?:\.5)?\s*marks?\)\.?\*\*")
CURLY = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'"})


def _tidy(text):
    """Line endings, tabs and non-breaking spaces; curly quotes are tidied
    later, only where they would break a match (settings, headings, fence
    lines, scheme keys), so prose keeps its typography."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace(" ", " ")
    return text.replace("\t", "    ")


def _is_closing(line, opener):
    """A fence closes on a line of nothing but its own character, at least
    as many as opened it; so ```` can hold a ``` listing inside."""
    stripped = line.strip()
    return bool(stripped) and set(stripped) == {opener[0]} and len(stripped) >= len(opener)


def _marks_of(text):
    m = MARKS_RE.search(text)
    if not m:
        return None, text
    return float(m.group(1) or m.group(2)), text[:m.start()].rstrip()


def _any_of(text):
    m = ANY_RE.search(text)
    if not m:
        return None
    word = m.group(1).lower()
    return int(word) if word.isdigit() else WORDS[word]


def read(text):
    messages = Messages()
    lines = list(enumerate(_tidy(text).split("\n"), 1))
    settings, start = read_settings(
        [(n, l.translate(CURLY)) for n, l in lines[:_settings_end(lines)]], messages)
    # Curly quotes in headings and fence lines would stop a number or a
    # kind matching; prose keeps its typography.
    lines = [(n, l.translate(CURLY)) if l.startswith(("#", "```", "~~~")) else (n, l)
             for n, l in lines]
    paper_lines, reference_lines, scheme_lines, split_line = _split(lines[start:], messages)

    state = _Paper(settings, messages)
    state.read(paper_lines)
    state.sum_up()

    scheme = read_scheme(scheme_lines, state, messages)
    _both_halves(state, scheme, split_line, messages)

    return {
        "reader": READER_VERSION,
        "settings": {k: v for k, v in settings.items() if not k.startswith("_")},
        "setting_lines": settings.get("_lines", {}),
        "front": state.front,
        "sections": state.sections,
        "units": state.units,
        "boxes": state.boxes,
        "total": state.total,
        "reference": _cards(reference_lines),
        "scheme": scheme,
        "messages": messages,
    }


def _settings_end(lines):
    """Where the settings block ends, so only it has its quotes tidied."""
    if not lines or lines[0][1].strip() != "---":
        return 0
    for index in range(1, len(lines)):
        if lines[index][1].strip() == "---":
            return index + 1
    return len(lines)


def _split(lines, messages):
    """Split the body at # Reference and # Marking scheme, before anything
    else reads it, so the student page is built from the paper half alone."""
    halves = {"paper": [], "reference": [], "scheme": []}
    where, fence, split_line = "paper", None, None
    for number, line in lines:
        if fence:
            if _is_closing(line, fence):
                fence = None
        else:
            f = FENCE_RE.match(line)
            if f:
                fence = f.group(1)
            elif SCHEME_LINE_RE.match(line):
                where, split_line = "scheme", number
                continue
            elif REFERENCE_LINE_RE.match(line) and where == "paper":
                where = "reference"
                continue
            elif where != "scheme":
                h = HEADING_RE.match(line)
                if h and len(h.group(1)) == 1 and LOOKALIKE_RE.match(h.group(2)):
                    messages.problem(
                        "scheme-lookalike", number,
                        f"\"{line.strip()}\" looks like the start of the marking scheme, but "
                        "it isn't one, so everything below it would appear on the student's page.",
                        "Change the line to \"# Marking scheme\".")
        halves[where].append((number, line))
    return halves["paper"], halves["reference"], halves["scheme"], split_line


def _cards(lines):
    cards, current = [], None
    for number, line in lines:
        h = HEADING_RE.match(line)
        if h and len(h.group(1)) == 2:
            current = {"title": h.group(2), "line": number, "text": []}
            cards.append(current)
        elif current is not None:
            current["text"].append(line)
    for card in cards:
        card["text"] = "\n".join(card["text"]).strip()
    return cards


class _Paper:
    """The paper half, read line by line into sections, units (questions,
    parts and sub-parts with marks) and answer boxes."""

    def __init__(self, settings, messages):
        self.settings = settings
        self.messages = messages
        self.front = []
        self.sections = [{"title": "", "marks": None, "any": None, "questions": [], "line": 0}]
        self.units = {}
        self.boxes = {}
        self.order = []
        self.current = {2: None, 3: None, 4: None}
        self.question = None     # (section letter, number) for relative numbers
        self.part = None
        self.started = False
        self.total = 0

    # --- reading ------------------------------------------------------

    def read(self, lines):
        index = 0
        while index < len(lines):
            number, line = lines[index]
            fence = FENCE_RE.match(line)
            if fence:
                body, index = self._fence_body(lines, index, fence.group(1))
                self._fence(number, fence.group(2).strip(), body, fence.group(1))
                continue
            heading = HEADING_RE.match(line)
            if heading and len(heading.group(1)) <= 4:
                self._heading(number, len(heading.group(1)), heading.group(2))
            else:
                self._prose(number, line)
            index += 1

    def _fence_body(self, lines, index, opener):
        body = []
        index += 1
        while index < len(lines) and not _is_closing(lines[index][1], opener):
            body.append(lines[index][1])
            index += 1
        return body, index + 1

    def _heading(self, number, level, text):
        marks, core = _marks_of(text)
        if level == 1:
            if marks is None and not re.match(r"^section\b", core, re.I):
                if not LOOKALIKE_RE.match(core):
                    self.messages.problem(
                        "heading-not-section", number,
                        f"\"# {text}\" is a top-level heading, which starts a section, but it "
                        "isn't one. The paper's title comes from the settings.",
                        "Delete the line, or use ## for a heading such as \"## Instructions\".")
                return
            self.started = True
            section = {"title": core, "marks": marks, "any": _any_of(core),
                       "questions": [], "line": number}
            self.sections.append(section)
            self.current = {2: None, 3: None, 4: None}
            self.question = self.part = None
            return
        if marks is None:
            if LOOKS_NUMBERED_RE.match(core):
                self.messages.warning(
                    "heading-looks-numbered", number,
                    f"\"{text}\" looks like a question or part, but it gives no marks, so it "
                    "is read as an ordinary heading.",
                    "If it is a question or part, end it with its marks, such as (5 marks).")
            for deeper in range(level, 5):
                self.current[deeper] = None
            if level == 2:
                self.question = self.part = None
            if not self.started:
                self.front.append("#" * level + " " + text)
            return
        numtext, title = split_title(core)
        num, rest = read_number(numtext, self.question if level > 2 else None,
                                self.part if level > 3 else None)
        if num is None:
            self.messages.problem(
                "heading-marks-no-number", number,
                f"\"{text}\" has marks but no number, so its answers would have no "
                "permanent name.",
                "Start the heading with its number, such as \"### 2(a): …\".")
            return
        if not title and rest.strip():
            title = rest.strip()
        name = name_of(num)
        where = label_of(num) if level > 2 else f"Question {num[0].upper()}{num[1]}"
        if name in self.units:
            self.messages.problem(
                "duplicate-number", number,
                f"{label_of(num)} appears twice (lines {self.units[name]['line']} and {number}).",
                "Renumber one of them.", where)
        parent = None
        for up in range(level - 1, 1, -1):
            if self.current.get(up):
                parent = self.current[up]
                break
        if level == 2:
            self.started = True
            self.question, self.part = (num[0], num[1]), None
            self.sections[-1]["questions"].append(name)
        elif parent is None:
            self.messages.problem(
                "part-outside-question", number,
                f"{label_of(num)} is not inside a question.",
                "Put a ## Question heading above it.", where)
            return
        if level == 3:
            self.part = num[2]
        self.units[name] = {
            "name": name, "label": label_of(num), "printed": numtext.strip(),
            "title": title, "level": level, "marks": marks, "any": _any_of(core) if level < 4 else None,
            "parent": parent, "children": [], "boxes": [], "line": number,
        }
        self.order.append(name)
        if parent:
            self.units[parent]["children"].append(name)
        self.current[level] = name
        for deeper in range(level + 1, 5):
            self.current[deeper] = None

    def _prose(self, number, line):
        if not self.started:
            self.front.append(line)
        if BOLD_MARKS_RE.search(line):
            self.messages.warning(
                "marks-not-heading", number,
                "This line gives marks but isn't a heading, so the marks aren't counted.",
                "If it is a sub-part with its own marks, start the line with ####.")
        if ABOVE_LINE_RE.match(line) or POINT_RE.match(line) or CRITERION_RE.match(line):
            self.messages.problem(
                "scheme-above-line", number,
                f"\"{line.strip()[:60]}\" looks like marking-scheme text, but it is above "
                "# Marking scheme, so students would see it.",
                "Move it below # Marking scheme, under the part it marks.",
                self._where())

    def _where(self):
        for level in (4, 3, 2):
            if self.current.get(level):
                return self.units[self.current[level]]["label"]
        return ""

    def _fence(self, number, info, body, opener="```"):
        words = info.split()
        first = words[0].lower() if words else ""
        if not first:
            self.messages.problem(
                "fence-without-kind", number,
                "This fence has no word after its three backticks, so dewmark can't tell "
                "whether it is a listing or an answer box.",
                "Add a word: ```text for plain text, ```python for code, or an answer box "
                "such as ```answer.", self._where())
            return
        if first in LISTING_LANGUAGES:
            second = words[1].lower() if len(words) > 1 else ""
            if first == "python" and second == "exec":
                self._box(number, "python exec", info.split(None, 2)[2] if len(words) > 2 else "",
                          body, opener)
            elif first == "python" and second == "setup":
                pass
            return
        if first == "material":
            return
        if first == "tests":
            self.messages.problem(
                "scheme-above-line", number,
                "A ```tests fence holds hidden tests, but it is above # Marking scheme, so "
                "students would see it.",
                "Move it below # Marking scheme, under the part it tests.", self._where())
            return
        if first not in ANSWER_KINDS:
            choices = list(ANSWER_KINDS) + list(LISTING_LANGUAGES) + ["material", "python exec"]
            near = []
            if len(words) > 1 and words[1].lower() in ("exec", "setup"):
                near = difflib.get_close_matches(first + " " + words[1].lower(),
                                                 choices + ["python setup"], n=1, cutoff=0.6)
            near = near or difflib.get_close_matches(first, choices, n=1, cutoff=0.6)
            self.messages.problem(
                "unknown-kind", number,
                f"dewmark doesn't know a box called ```{first}.",
                f"Did you mean ```{near[0]}?" if near else
                "The kinds of box are listed in docs/EXAM_FORMAT.md §4.3.", self._where())
            return
        self._box(number, first, info[len(words[0]):].strip(), body, opener)

    def _box(self, number, kind, rest, body, opener="```"):
        label, notes = split_notes(rest)
        owner = None
        for level in (4, 3, 2):
            if self.current.get(level):
                owner = self.current[level]
                break
        if owner is None:
            self.messages.problem(
                "box-outside-question", number,
                f"The ```{kind} box on line {number} is not inside a question.",
                "Put it under a question's or part's heading.")
            return
        caption, num = "", None
        if label:
            numtext, _, caption = label.partition(":")
            num, leftover = read_number(numtext, self.question, self.part)
            if num is None:
                caption = label
            elif leftover.strip():
                caption = (leftover.strip() + " " + caption).strip()
            caption = caption.strip()
        unmarked = "not marked" in notes
        if num is not None:
            owner_unit = self.units[owner]
            ancestors, up = [], owner
            while up:
                ancestors.append(up)
                up = self.units[up]["parent"]
            target = name_of(num)
            if target not in ancestors and not target.startswith(owner):
                self.messages.problem(
                    "box-label-mismatch", number,
                    f"The box labelled \"{label}\" sits under {owner_unit['label']}.",
                    f"Label it with {owner_unit['label']}'s number, or move it.",
                    owner_unit["label"])
            stem = name_of(num)
        else:
            stem = owner
        # The stem is the number's name; a caption, if any, follows it.
        name = stem + ("." + slug(caption) if caption and slug(caption) else "")
        if name in self.boxes:
            self.messages.problem(
                "duplicate-name", number,
                f"Two answer boxes would both be stored as {name} (lines "
                f"{self.boxes[name]['line']} and {number}).",
                "Give them different labels, such as \"2(a): working\" and \"2(a): answer\".",
                self.units[owner]["label"])
        # Opened with three backticks, a box that holds a listing ends at the
        # listing's own closing line; its opening line is left in the body.
        if (kind in KEYED_KINDS and len(opener) == 3
                and any(FENCE_RE.match(l.strip()) and FENCE_RE.match(l.strip()).group(2).strip()
                        for l in body)):
            self.messages.problem(
                "fence-closed-early", number,
                f"The ```{kind} box that starts on line {number} holds a code listing, so the "
                "listing's closing backticks end the box early.",
                "Open the box with four backticks (````) and close it with four.",
                self.units[owner]["label"])
        for offset, line in enumerate(body, 1):
            if ABOVE_LINE_RE.match(line):
                self.messages.problem(
                    "scheme-above-line", number + offset,
                    f"\"{line.strip()[:60]}\" is inside an answer box, so students would see it.",
                    "Move it below # Marking scheme, under the part it marks.",
                    self.units[owner]["label"])
        self.boxes[name] = {
            "name": name, "stem": stem, "kind": kind, "unit": owner, "line": number,
            "label": label or self.units[owner]["label"], "caption": caption,
            "notes": notes, "unmarked": unmarked, "body": "\n".join(body),
            "inner": inner_parts(kind, body),
        }
        self.units[owner]["boxes"].append(name)

    # --- sums ----------------------------------------------------------

    def sum_up(self):
        """Parts add up to their question, questions to their section,
        sections to total marks. Each level is checked against its own
        heading, so one wrong part is reported once, not again at every
        level above it."""
        for box in self.boxes.values():
            unit = self.units[box["unit"]]
            if unit["children"] and not box["unmarked"]:
                self.messages.problem(
                    "box-outside-parts", box["line"],
                    f"The ```{box['kind']} box is in {unit['label']} but outside all of its "
                    "parts, so it has no marks.",
                    "Move it under a part's heading, or add (not marked) if it is rough work.",
                    unit["label"])
        for name in self.order:
            unit = self.units[name]
            if not unit["children"]:
                if not unit["boxes"]:
                    self.messages.warning(
                        "no-answer-box", unit["line"],
                        f"{unit['label']} has marks but no answer box.",
                        "Add a box under it, or ```on-paper if it is answered on paper.",
                        unit["label"])
                continue
            marks = [self.units[c]["marks"] for c in unit["children"]]
            added = self._choose(unit["any"], marks, unit["line"], unit["label"])
            if added is not None and added != unit["marks"]:
                shown = ", ".join(f"{self.units[c]['label']} is {self.units[c]['marks']:g}"
                                  for c in unit["children"])
                self.messages.problem(
                    "marks-sum", unit["line"],
                    f"{unit['label']}'s parts add up to {added:g} marks, but its heading says "
                    f"({unit['marks']:g} marks): {shown}.",
                    "Change one part's marks, or the heading.", unit["label"])
        total = 0
        for section in self.sections:
            if not section["questions"]:
                continue
            marks = [self.units[q]["marks"] for q in section["questions"]]
            where = section["title"] or "the paper"
            added = self._choose(section["any"], marks, section["line"], where)
            if added is None:
                continue
            if section["marks"] is not None and added != section["marks"]:
                self.messages.problem(
                    "marks-sum", section["line"],
                    f"The questions in \"{section['title']}\" add up to {added:g} marks, but its "
                    f"heading says ({section['marks']:g} marks).",
                    "Change a question's marks, or the heading.", where)
                added = section["marks"]
            total += added
        self.total = total
        stated = self.settings.get("total marks")
        if stated is not None:
            try:
                stated_value = float(stated)
            except ValueError:
                self.messages.problem(
                    "setting-value", self.settings.get("_lines", {}).get("total marks", 1),
                    f"\"total marks: {stated}\" must be a number.")
                return
            if stated_value != total:
                self.messages.problem(
                    "total-marks", self.settings.get("_lines", {}).get("total marks", 1),
                    f"The paper adds up to {total:g} marks, but \"total marks\" says {stated}.",
                    "Change \"total marks\", or a question's marks.")

    def _choose(self, any_n, marks, line, where):
        if not any_n:
            return sum(marks)
        if len(set(marks)) != 1:
            self.messages.problem(
                "any-unequal", line,
                f"\"{where}\" says any {any_n}, but its questions or parts are not all worth "
                "the same, so which ones count would change the total.",
                "Give them the same marks.", where)
            return None
        if len(marks) <= any_n:
            self.messages.problem(
                "any-too-few", line,
                f"\"{where}\" says any {any_n}, but offers only {len(marks)}.",
                "Add a question, or change the number.", where)
            return None
        return marks[0] * any_n


def _both_halves(paper, scheme, split_line, messages):
    """Checks that need the paper and the scheme together."""
    kind = paper.settings.get("kind")
    if split_line is None and kind == "exam":
        messages.problem(
            "no-scheme", 1,
            "This is an exam paper with no \"# Marking scheme\" line.",
            "Add one at the end, even if every entry is still (draft).")
    entries = scheme["entries"]
    for name in paper.order:
        unit = paper.units[name]
        if unit["children"]:
            continue
        if name not in entries and not any(b in entries for b in unit["boxes"]) and split_line:
            messages.warning(
                "no-scheme-entry", unit["line"],
                f"{unit['label']} has no entry in the marking scheme, so it will be marked "
                "out of its total with no guidance.",
                f"Add \"### {unit['label']}\" below # Marking scheme.", unit["label"])
    for name, box in paper.boxes.items():
        if box["unmarked"] or not box["body"].strip():
            continue
        entry = entries.get(name) or entries.get(box["unit"])
        if not entry or not entry.get("model"):
            continue
        ratio = difflib.SequenceMatcher(None, _flat(box["body"]), _flat(entry["model"])).ratio()
        if ratio >= 0.8:
            messages.problem(
                "starter-is-answer", box["line"],
                f"The text already in {box['label']}'s box is almost the same as its model answer.",
                "Delete the starter text, or change it to a prompt.", box["label"])


def _flat(text):
    return re.sub(r"\s+", " ", text).strip().lower()
