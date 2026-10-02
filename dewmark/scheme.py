"""The marker's half: everything below `# Marking scheme`
(docs/EXAM_FORMAT.md §4.6, §4.7).

Entries are found by the number they mark. Inside an entry, each line is
one of: a key (`Answer:`, `Answers:`), a model answer, hidden tests, a
point to tick, a criterion with its bands, a Topic or Outcomes field, or
guidance for the marker. The marking method is read from which of these
appear. A key is text unless it carries a tolerance, a range or a
precision, so `0123` never silently equals `123`.
"""

import re

from .numbers import label_of, name_of, read_number, split_title

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
FENCE_RE = re.compile(r"^(`{3,}|~{3,})(.*)$")
POINT_RE = re.compile(r"^\s*[-*]\s+(\d+(?:\.5)?)\s*marks?\s*:\s*(.+)$", re.I)
CRITERION_RE = re.compile(r"^[-*]\s+\*\*(.+?)\*\*\s*\((\d+(?:\.5)?)\s*marks?\)\s*$", re.I)
BAND_RE = re.compile(r"^\s{2,}[-*]\s+(\d+(?:\.5)?)\s*(?:to|–|-)\s*(\d+(?:\.5)?)\s*:\s*(.+)$", re.I)
ANSWER_RE = re.compile(r"^answer\s*:\s*(.*)$", re.I)
ANSWERS_RE = re.compile(r"^answers\s*(\(any order\))?\s*:\s*(.*)$", re.I)
MODEL_RE = re.compile(r"^model answer\s*:\s*(.*)$", re.I)
FIELD_RE = re.compile(r"^(topic|outcomes)\s*:\s*(.*)$", re.I)
LIST_ITEM_RE = re.compile(r"^\s*(?:\d+[.)]|[-*])\s+(.*)$")
DRAFT_RE = re.compile(r"\s*\(draft\)\s*$", re.I)
MARKS_SUFFIX_RE = re.compile(r"\s*(?:\(\d+(?:\.5)?\s*marks?\)|\[\d+(?:\.5)?(?:\s*marks?)?\])\s*$", re.I)
LOOKS_LIKE_POINT_RE = re.compile(
    r"^(?:[-*]\s*)?(?:award\s+\d|\(\d+(?:\.5)?\)\s|\d+(?:\.5)?\s*m\b\s*:?)", re.I)
CURLY = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'"})

NUM = r"-?\d+(?:\.\d+)?"
TOLERANCE_RE = re.compile(
    rf"^(?P<value>{NUM})\s*(?P<unit1>[^±+()\d][^±()]*?)?\s*"
    rf"(?:(?:±|\+-)\s*(?P<tol>\d+(?:\.\d+)?)(?P<pct>\s*%)?)\s*"
    rf"(?P<unit2>[^()]*?)\s*(?:\((?P<prec>\d+)\s*(?P<pk>d\.p\.|s\.f\.)\))?\s*$", re.I)
RANGE_RE = re.compile(
    rf"^(?P<low>{NUM})\s+to\s+(?P<high>{NUM})\s*(?P<unit>[^()]*?)\s*"
    rf"(?:\((?P<prec>\d+)\s*(?P<pk>d\.p\.|s\.f\.)\))?\s*$", re.I)
PRECISION_RE = re.compile(
    rf"^(?P<value>{NUM})\s*(?P<unit>[^()]*?)\s*\((?P<prec>\d+)\s*(?P<pk>d\.p\.|s\.f\.)\)\s*$", re.I)
CHOICE_KEY_RE = re.compile(r"^(?P<letters>[A-Z](?:\s*,\s*[A-Z])*)\s*(?:\((?P<phrase>.+)\))?\s*$")
MATCH_PAIR_RE = re.compile(r"^(\d+)\s*[-:]?\s*([A-Z])$")


def read_key(text):
    """One key: its accepted alternatives, each text or a number rule."""
    text = text.translate(CURLY).strip()
    alternatives = [a.strip() for a in text.split(" / ")] if " / " in text else [text]
    return [_alternative(a) for a in alternatives if a]


def _alternative(text):
    unquoted = text[1:-1] if len(text) > 1 and text[0] == text[-1] == '"' else text
    m = TOLERANCE_RE.match(text)
    if m:
        unit = " ".join(u.strip() for u in (m.group("unit1"), m.group("unit2")) if u and u.strip())
        rule = {"number": float(m.group("value")), "written": m.group("value"),
                "tolerance": float(m.group("tol")), "percent": bool(m.group("pct")),
                "unit": unit}
        return _precision(rule, m)
    m = RANGE_RE.match(text)
    if m:
        rule = {"low": float(m.group("low")), "high": float(m.group("high")),
                "unit": m.group("unit").strip()}
        return _precision(rule, m)
    m = PRECISION_RE.match(text)
    if m:
        rule = {"number": float(m.group("value")), "written": m.group("value"),
                "unit": m.group("unit").strip()}
        return _precision(rule, m)
    return {"text": unquoted}


def _precision(rule, m):
    if m.group("prec"):
        kind = "dp" if m.group("pk").lower().startswith("d") else "sf"
        rule[kind] = int(m.group("prec"))
    return rule


def read_scheme(lines, paper, messages):
    entries = {}
    entry = None
    mode = None
    fence, fence_kind, fence_lines = None, "", []
    for number, line in lines:
        if fence:
            if line.strip() and set(line.strip()) == {fence[0]} and len(line.strip()) >= len(fence):
                if entry is not None:
                    if fence_kind == "tests":
                        entry["tests"].extend(l for l in fence_lines if l.strip())
                    else:
                        entry["model"] = (entry["model"] + "\n" if entry["model"] else "") + "\n".join(fence_lines)
                        entry["model_is_code"] = True
                fence = None
            else:
                fence_lines.append(line)
            continue
        f = FENCE_RE.match(line)
        if f:
            fence, fence_kind, fence_lines = f.group(1), f.group(2).strip().lower(), []
            continue
        heading = HEADING_RE.match(line)
        if heading:
            entry = _entry(number, heading.group(2).translate(CURLY), paper, messages, entries)
            mode = None
            continue
        if entry is None:
            continue
        stripped = line.strip()
        if not stripped:
            if mode == "model":
                mode = None
            continue
        m = ANSWER_RE.match(stripped)
        if m:
            if entry["key"] is not None:
                messages.problem(
                    "two-answer-lines", number,
                    f"{entry['label']} has two Answer: lines (lines {entry['key_line']} and {number}).",
                    "Put every accepted answer on one line, separated by \" / \".", entry["label"])
                continue
            entry["key"] = [read_key(m.group(1))]
            entry["key_line"] = number
            _check_key(entry, entry["key"][0], number, messages)
            mode = None
            continue
        m = ANSWERS_RE.match(stripped)
        if m:
            if entry["key"] is not None:
                messages.problem(
                    "two-answer-lines", number,
                    f"{entry['label']} has both Answer: and Answers: lines.",
                    "Keep one of them.", entry["label"])
                continue
            entry["key"], entry["key_line"] = [], number
            entry["any_order"] = bool(m.group(1))
            mode = "answers"
            continue
        m = MODEL_RE.match(stripped)
        if m:
            entry["model"] = m.group(1)
            mode = "model"
            continue
        m = FIELD_RE.match(stripped)
        if m:
            field, value = m.group(1).lower(), m.group(2).strip()
            if field == "outcomes":
                entry["outcomes"] = [o.strip() for o in value.split(",") if o.strip()]
                _check_outcomes(entry, number, paper.settings, messages)
            else:
                entry["topic"] = value
            mode = None
            continue
        m = CRITERION_RE.match(line)
        if m:
            entry["criteria"].append({"name": m.group(1), "marks": float(m.group(2)),
                                      "bands": [], "line": number})
            mode = "criteria"
            continue
        m = BAND_RE.match(line)
        if m and entry["criteria"]:
            entry["criteria"][-1]["bands"].append(
                {"low": float(m.group(1)), "high": float(m.group(2)), "text": m.group(3)})
            continue
        m = POINT_RE.match(line)
        if m:
            entry["points"].append({"marks": float(m.group(1)), "text": m.group(2), "line": number})
            mode = "points"
            continue
        if mode == "answers":
            item = LIST_ITEM_RE.match(line)
            if item:
                key = read_key(item.group(1))
                entry["key"].append(key)
                _check_key(entry, key, number, messages)
                continue
        if mode == "model":
            entry["model"] += "\n" + stripped
            continue
        if LOOKS_LIKE_POINT_RE.match(stripped):
            messages.warning(
                "guidance-looks-like-points", number,
                f"\"{stripped[:60]}\" is read as guidance, so the marker will type a number "
                "instead of ticking points.",
                "If it is a point, write it as \"- 2 marks: …\".", entry["label"])
        entry["guidance"].append(stripped)
    for entry in entries.values():
        _check_entry(entry, paper, messages)
    return {"entries": entries,
            "drafts": [name for name, e in entries.items() if e["draft"]]}


def _entry(number, text, paper, messages, entries):
    draft = bool(DRAFT_RE.search(text))
    text = DRAFT_RE.sub("", text)
    text = MARKS_SUFFIX_RE.sub("", text)
    numtext, caption = split_title(text)
    num, leftover = read_number(numtext)
    if num is None:
        messages.problem(
            "scheme-heading-no-number", number,
            f"This marking-scheme heading doesn't start with the number of the part it "
            f"marks: \"{text}\".",
            "Start it with the part's number, such as \"### 2(a)\".")
        return None
    caption = (leftover.strip() + " " + caption.strip()).strip()
    name = name_of(num, caption)
    if name not in paper.units and name not in paper.boxes:
        # "### 1B" names a part; "### 1B: answer" a labelled box in it.
        if name_of(num) in paper.units and caption:
            name, caption = name_of(num), ""
        else:
            messages.problem(
                "scheme-unknown-part", number,
                f"The marking scheme has an entry for {label_of(num)}"
                f"{(': ' + caption) if caption else ''}, but the paper has no such part.",
                "Check the number against the paper.", label_of(num))
            return None
    if name in entries:
        messages.problem(
            "scheme-repeated-entry", number,
            f"{label_of(num)} has two entries in the marking scheme (lines "
            f"{entries[name]['line']} and {number}).",
            "Merge them into one.", label_of(num))
        return None
    entry = {"name": name, "label": label_of(num), "caption": caption, "line": number,
             "draft": draft,
             "key": None, "key_line": None, "any_order": False, "model": "",
             "model_is_code": False, "tests": [], "points": [], "criteria": [],
             "guidance": [], "topic": "", "outcomes": []}
    entries[name] = entry
    return entry


def _check_key(entry, key, number, messages):
    for alternative in key:
        places = alternative.get("dp")
        written = alternative.get("written")
        if places is not None and written is not None:
            decimals = len(written.split(".")[1]) if "." in written else 0
            if decimals != places:
                messages.problem(
                    "key-precision", number,
                    f"The key asks for {places} decimal place{'s' if places != 1 else ''}, but "
                    f"{written} is written with {decimals}.",
                    f"Write it as {float(written):.{places}f}.", entry["label"])


def _check_outcomes(entry, number, settings, messages):
    declared = [o.strip() for o in settings.get("outcomes", "").split(",") if o.strip()]
    if not declared:
        return
    for outcome in entry["outcomes"]:
        if outcome not in declared:
            messages.problem(
                "outcome-unknown", number,
                f"Outcome {outcome} isn't in the paper's \"outcomes\" setting ({', '.join(declared)}).",
                "Add it to the setting, or correct the number.", entry["label"])


def _unit_of(entry, paper):
    if entry["name"] in paper.units:
        return paper.units[entry["name"]]
    return paper.units[paper.boxes[entry["name"]]["unit"]]


def _check_entry(entry, paper, messages):
    unit = _unit_of(entry, paper)
    marks = unit["marks"]
    if entry["points"] and entry["criteria"]:
        messages.problem(
            "mixed-methods", entry["line"],
            f"The marking for {entry['label']} mixes points to tick and a criteria grid.",
            "Use one or the other.", entry["label"])
    if entry["criteria"] and marks is not None:
        added = sum(c["marks"] for c in entry["criteria"])
        if added != marks:
            messages.problem(
                "criteria-sum", entry["line"],
                f"The criteria for {entry['label']} add up to {added:g}, but it is worth {marks:g}.",
                "Change a criterion's marks.", entry["label"])
        for criterion in entry["criteria"]:
            _check_bands(entry, criterion, messages)
    if entry["points"] and marks is not None and not unit["children"]:
        added = sum(p["marks"] for p in entry["points"])
        if added < marks:
            messages.problem(
                "points-short", entry["line"],
                f"The points for {entry['label']} add up to {added:g}, but it is worth {marks:g}, "
                "so a perfect answer could not reach full marks.",
                "Add points, or raise a point's marks.", entry["label"])
    entry["method"] = ("criteria" if entry["criteria"] else
                       "points" if entry["points"] else "total")
    if entry["key"] is not None:
        _check_key_against_box(entry, paper, messages)


def _check_bands(entry, criterion, messages):
    bands = sorted(criterion["bands"], key=lambda b: b["low"])
    fine = bool(bands) and bands[0]["low"] == 0 and bands[-1]["high"] == criterion["marks"]
    for lower, upper in zip(bands, bands[1:]):
        if upper["low"] <= lower["high"] or upper["low"] > lower["high"] + 1:
            fine = False
    if not fine:
        messages.problem(
            "criteria-bands", criterion["line"],
            f"The bands for \"{criterion['name']}\" should run from 0 to {criterion['marks']:g} "
            "with no gap or overlap.",
            "Check each band's range, such as \"- 13 to 15: …\".", entry["label"])


def _keyed_box(entry, paper):
    """The box a key belongs to: the entry's own box, or the one box in its
    part that takes a key, or the part's only box."""
    if entry["name"] in paper.boxes:
        return paper.boxes[entry["name"]]
    unit = paper.units[entry["name"]]
    boxes = [paper.boxes[b] for b in unit["boxes"] if not paper.boxes[b]["unmarked"]]
    keyed = [b for b in boxes if b["kind"] in ("boxes", "blanks", "table", "choice", "match", "order")]
    if len(keyed) == 1:
        return keyed[0]
    if len(boxes) == 1:
        return boxes[0]
    return None


def _check_key_against_box(entry, paper, messages):
    box = _keyed_box(entry, paper)
    line = entry["key_line"]
    if box is None:
        messages.problem(
            "key-which-box", line,
            f"{entry['label']} has more than one box, so dewmark can't tell which this key is for.",
            f"Put the key under the box's own label, such as \"### {entry['label']}: answer\".",
            entry["label"])
        return
    inner = box["inner"]
    keys = entry["key"]
    if box["kind"] == "choice":
        _check_choice(entry, box, keys, line, messages)
    elif box["kind"] == "match":
        text = keys[0][0].get("text", "") if keys and keys[0] else ""
        pairs = [p.strip() for p in text.split(",") if p.strip()]
        for pair in pairs:
            m = MATCH_PAIR_RE.match(pair)
            if not m or m.group(1) not in inner["items"] or m.group(2) not in inner["options"]:
                messages.problem(
                    "key-not-option", line,
                    f"\"{pair}\" in {entry['label']}'s key doesn't pair one of its numbered items "
                    "with one of its lettered options.",
                    "Write the key as \"Answer: 1 B, 2 A, 3 C\".", entry["label"])
    elif box["kind"] == "order":
        text = keys[0][0].get("text", "") if keys and keys[0] else ""
        letters = [l.strip() for l in text.split(",")]
        if sorted(letters) != sorted(inner["options"]):
            messages.problem(
                "key-not-option", line,
                f"{entry['label']}'s key should list every option once, in the right order.",
                "Write it as \"Answer: C, A, D, B\".", entry["label"])
    elif box["kind"] in ("boxes", "blanks", "table"):
        slots = inner["slots"]
        if len(keys) != len(slots):
            messages.problem(
                "answers-count", line,
                f"{entry['label']} has {len(slots)} "
                f"{'box' if len(slots) == 1 else 'boxes or gaps'} to fill, but the key gives "
                f"{len(keys)} answer{'s' if len(keys) != 1 else ''}.",
                "Give one answer per box or gap, in order, under \"Answers:\".", entry["label"])
            return
        for index, (slot, key) in enumerate(zip(slots, keys), 1):
            allowed = slot[1] or inner["bank"]
            if not allowed:
                continue
            # A student choosing from a list can only give one of its entries,
            # so at least one accepted answer must be among them. Extra
            # alternatives outside the list are harmless and left alone.
            lower = [a.lower() for a in allowed]
            texts = [a["text"] for a in key if "text" in a]
            if texts and not any(t.lower() in lower for t in texts):
                messages.problem(
                    "key-not-option", line,
                    f"Answer {index} for {entry['label']}, \"{' / '.join(texts)}\", isn't one "
                    "of the choices the student is given, so no student could give it.",
                    "Use one of the choices, spelled as it is in the list.", entry["label"])


def _check_choice(entry, box, keys, line, messages):
    options = box["inner"]["options"]
    text = keys[0][0].get("text", "") if keys and keys[0] else ""
    m = CHOICE_KEY_RE.match(text)
    if not m:
        messages.problem(
            "key-not-option", line,
            f"{entry['label']}'s key should be the letter of an option, such as \"Answer: B\", "
            f"not \"{text}\".",
            "Write the letter (or letters, separated by commas).", entry["label"])
        return
    letters = [l.strip() for l in m.group("letters").split(",")]
    for letter in letters:
        if letter not in options:
            messages.problem(
                "key-not-option", line,
                f"{entry['label']}'s key is {letter}, but the options are "
                + ", ".join(options) + ".",
                "Use one of the option letters.", entry["label"])
            return
    phrase = m.group("phrase")
    if phrase and len(letters) == 1 and phrase not in options[letters[0]]:
        holder = next((l for l, t in options.items() if phrase in t), None)
        messages.problem(
            "key-check-phrase", line,
            f"The key says {letters[0]} ({phrase}), but option {letters[0]} reads "
            f"\"{options[letters[0]][:60]}\"." + (f" Option {holder} contains \"{phrase}\"." if holder else ""),
            "Did the options move? Change the key's letter, or the options back.", entry["label"])
    notes = box["notes"]
    choose = next((int(n.split()[1]) for n in notes if n.startswith("choose")), 1)
    if len(letters) != choose:
        messages.problem(
            "key-not-option", line,
            f"{entry['label']}'s key gives {len(letters)} letter{'s' if len(letters) != 1 else ''}, "
            f"but the box asks the student to choose {choose}.",
            "Match the key to the box's (choose N) note.", entry["label"])
