"""The names lock (docs/EXAM_FORMAT.md §4.4).

Once a paper has been issued, the names its answers are stored under are
a contract: a student's saved work, the marking record and the graded
paper all quote them. The lock records, the first time a paper is issued,
every name with its kind, marks and printed label, and the text of every
option and match item; later readings are checked against it.

    from dewmark.lock import check, record
    result = check(paper, lock)       # messages, and the stored names
    record(lock, paper, "2026-10-20 Group A", "2026-10-13")

The lock lives beside the exam file as `names.lock.json`, one file for
the folder, with an entry for each paper by its code. After a paper is
locked:

- renumbering, removing, retyping or re-marking a locked part or box is
  refused, unless the paper's `version` setting changes;
- changing an option's text, or the number of gaps in a box, is refused;
- fixing a box's caption keeps the name its answers are stored under, and
  says so;
- moving whole questions without renumbering them is allowed, with a
  warning; adding a part or a box is always allowed.

A new `version` is checked against nothing: it is a new paper, and when it
is issued the lock records it beside the old one, whose sittings keep
their own names.
"""

import json
import os
import re
from collections import Counter

from . import READER_VERSION
from .messages import Messages

LOCK_FORMAT = "dewmark-names/1"
LOCK_FILE = "names.lock.json"
OPTION_KINDS = ("choice", "match", "order")
SLOT_KINDS = ("boxes", "blanks", "table")


# --- what the lock records ------------------------------------------------

def _marks(value):
    if value is None:
        return None
    return int(value) if float(value).is_integer() else value


def _text(value):
    return re.sub(r"\s+", " ", value or "").strip()


def snapshot(paper, file_name=""):
    """What the lock records about one version of a paper."""
    units = {}
    for name, unit in paper["units"].items():
        units[name] = {"label": unit["label"], "title": unit["title"],
                       "level": unit["level"], "parent": unit["parent"],
                       "marks": _marks(unit["marks"]), "parts": bool(unit["children"])}
    boxes = {}
    for name, box in paper["boxes"].items():
        boxes[name] = {"kind": box["kind"], "unit": box["unit"], "label": box["label"],
                       "stem": box["stem"], "caption": box["caption"], **_inner(box)}
    return {"reader": READER_VERSION, "format": paper["settings"].get("dewmark", ""),
            "file": file_name, "issued": [], "units": units, "boxes": boxes}


def empty_lock():
    return {"format": LOCK_FORMAT, "papers": {}}


def load(path):
    """Read a lock file. Returns (lock, message about why it can't be read)."""
    try:
        with open(path, encoding="utf-8") as handle:
            lock = json.load(handle)
    except (OSError, ValueError) as error:
        return None, f"{os.path.basename(path)} can't be read ({error})."
    if not isinstance(lock, dict) or lock.get("format") != LOCK_FORMAT:
        return None, (f"{os.path.basename(path)} is not a names lock this version of "
                      f"dewmark reads (it expects \"format\": \"{LOCK_FORMAT}\").")
    return lock, None


def dump(lock, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(lock, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def record(lock, paper, sitting, on, file_name=""):
    """Record that this version of the paper was issued for `sitting` on the
    date `on`. The first issue of a version records every name; a later
    issue of the same version adds only parts and boxes that are new, so a
    name, once locked, keeps what it was locked with. Call it only once
    `check()` finds no problems."""
    settings = paper["settings"]
    entry = lock["papers"].setdefault(settings["code"], {"versions": {}})
    version = settings.get("version", "1")
    now = snapshot(paper, file_name)
    locked = entry["versions"].get(version)
    if locked is None:
        locked = entry["versions"][version] = now
    else:
        stored = check(paper, lock, file_name)["stored"]
        for name, unit in now["units"].items():
            locked["units"].setdefault(name, unit)
        for name, box in now["boxes"].items():
            if stored.get(name, name) not in locked["boxes"]:
                locked["boxes"][name] = box
        locked["file"] = file_name or locked.get("file", "")
    if not any(s["sitting"] == sitting for s in locked["issued"]):
        locked["issued"].append({"sitting": sitting, "on": on})
    return lock


# --- checking a paper against the lock ------------------------------------

def check(paper, lock, file_name=""):
    """Check a paper against its lock.

    Returns a dict: "status", one line for a summary; "messages"; and
    "stored", mapping a box's name in the file to the name its answers are
    stored under, where a caption fix has changed it.
    """
    messages = Messages()
    settings = paper["settings"]
    lines = paper.get("setting_lines", {})
    code = settings.get("code", "")
    version = settings.get("version", "1")
    result = {"status": "", "messages": messages, "stored": {}}
    entry = lock.get("papers", {}).get(code)
    if entry is None:
        result["status"] = "not yet issued"
        for other, other_entry in lock.get("papers", {}).items():
            if file_name and any(v.get("file") == file_name
                                 for v in other_entry["versions"].values()):
                messages.problem(
                    "code-changed-after-issue", lines.get("code", 1),
                    f"{file_name} was issued with the code \"{other}\", and its answers and "
                    f"marking records are stored under that code. The settings now say "
                    f"\"code: {code}\".",
                    "Put the code back. If this is a different paper, give it a file name "
                    "of its own.")
        return result
    locked = entry["versions"].get(version)
    if locked is None:
        earlier = ", ".join(entry["versions"])
        result["status"] = (f"version {version} not yet issued "
                            f"(issued before as version {earlier})")
        return result
    sittings = _sittings(locked["issued"])
    result["status"] = f"version {version}, issued for {sittings}"
    change = _change_version(version, lines)

    if locked.get("reader") != READER_VERSION:
        messages.warning(
            "lock-reader-changed", lines.get("version", 1),
            f"Version {version} of this paper was locked by reader {locked.get('reader')}; "
            f"this is reader {READER_VERSION}. Its names were checked against the lock.")

    units, boxes = paper["units"], paper["boxes"]
    lunits, lboxes = locked["units"], locked["boxes"]
    moved, shifted = _moved(lunits, units)
    for old, new in moved.items():
        messages.problem(
            "renumbered-after-sitting", units[new]["line"],
            f"This paper was issued for {sittings}, and the answers to "
            f"{_called(lunits[old])} are stored under that number. It is now numbered "
            f"{units[new]['label']}.",
            change, units[new]["label"])

    gone = set()
    for name, unit in lunits.items():
        if name in units or _within(name, shifted, lunits):
            continue
        gone.add(name)
        parent = unit["parent"]
        if parent and parent not in units and not _within(parent, shifted, lunits):
            continue          # reported once, at the question that went
        messages.problem(
            "locked-part-removed", units[parent]["line"] if parent in units else 1,
            f"This paper was issued for {sittings} with {_called(unit)} and answers to it "
            f"are stored under that number. It is no longer in the file.",
            change, unit["label"])

    for name, unit in lunits.items():
        if name in units and not _within(name, shifted, lunits) and not unit["parts"]:
            now = units[name]
            if _marks(now["marks"]) != unit["marks"]:
                messages.problem(
                    "locked-marks-changed", now["line"],
                    f"{unit['label']} was worth {unit['marks']:g} marks when this paper was "
                    f"issued for {sittings}; the file now gives it {now['marks']:g}.",
                    change, unit["label"])

    claimed = set()
    for name, lbox in lboxes.items():
        unit = lbox["unit"]
        if unit in gone or unit not in units or _within(unit, shifted, lunits):
            continue
        box = boxes.get(name)
        if box is None:
            box = _caption_fixed(name, lbox, paper, lboxes, claimed)
            if box is not None:
                claimed.add(box["name"])
                result["stored"][box["name"]] = name
                messages.warning(
                    "caption-changed", box["line"],
                    f"This box's caption was \"{lbox['caption']}\" when the paper was issued; "
                    f"it is now \"{box['caption']}\". Its answers stay stored as {name}.",
                    "", box["label"])
            else:
                messages.problem(
                    "locked-box-removed", units[unit]["line"],
                    f"This paper was issued for {sittings} with a ```{lbox['kind']} box "
                    f"labelled \"{lbox['label']}\", and answers are stored under {name}. The "
                    f"box is no longer in the file.",
                    change, units[unit]["label"])
                continue
        if box["kind"] != lbox["kind"]:
            messages.problem(
                "locked-kind-changed", box["line"],
                f"{lbox['label']}'s box was ```{lbox['kind']} when this paper was issued for "
                f"{sittings}; it is now ```{box['kind']}, so the answers stored for it no "
                f"longer fit.", change, box["label"])
            continue
        for what in _inner_changes(lbox, box):
            messages.problem("locked-options-changed" if lbox["kind"] in OPTION_KINDS
                             else "locked-inner-changed",
                             box["line"], what, change, box["label"])

    order = [n for n, u in lunits.items() if u["level"] == 2 and n in units]
    current = [n for n, u in units.items() if u["level"] == 2 and n in lunits]
    if order != current:
        messages.warning(
            "questions-moved", units[current[0]]["line"] if current else 1,
            f"The questions are in a different order from when this paper was issued for "
            f"{sittings}. Their numbers are the same, so their answers stay where they are.")
    return result


def _sittings(issued):
    if not issued:
        return "no sitting"
    first = f"\"{issued[0]['sitting']}\""
    more = len(issued) - 1
    return first + (f" and {more} more" if more else "")


def _change_version(version, lines):
    if lines.get("version"):
        nxt = str(int(version) + 1) if version.isdigit() else "a new value"
        new = f"change \"version: {version}\" to \"version: {nxt}\""
    else:
        new = "add \"version: 2\" to the settings"
    return (f"If that was a slip, put it back. If this is a new version of the paper, "
            f"{new}; the earlier sittings keep their own record.")


def _called(unit):
    return unit["label"] + (f", \"{unit['title']}\"," if unit["title"] else "")


def _within(name, names, lunits):
    """Whether a locked unit, or a question or part it sits in, is in `names`."""
    while name:
        if name in names:
            return True
        name = lunits.get(name, {}).get("parent")
    return False


def _norm(title):
    return _text(title).lower()


def _moved(lunits, units):
    """Locked units that now carry another number: found by title, or, for
    a part that is gone and has no title match, by its position.

    Returns (moved, shifted): `moved` is what to report, a part that moved
    with its question being reported once, at the question; `shifted` is
    every locked unit that moved, for the checks that follow to skip."""
    counts = Counter(_norm(u["title"]) for u in lunits.values() if u["title"])
    by_title = {}
    for name, unit in units.items():
        by_title.setdefault(_norm(unit["title"]), []).append(name)
    moved = {}
    for name, unit in lunits.items():
        title = _norm(unit["title"])
        if not title or counts[title] > 1:
            continue
        if name in units and _norm(units[name]["title"]) == title:
            continue
        found = [n for n in by_title.get(title, []) if n != name
                 and units[n]["level"] == unit["level"]]
        if len(found) == 1:
            new = found[0]
            if new not in lunits or _norm(lunits[new]["title"]) != title:
                moved[name] = new
    leaves = [n for n, u in lunits.items() if not u["parts"]]
    now = [n for n, u in units.items() if not u["children"]]
    taken = set(moved.values())
    for index, name in enumerate(leaves):
        if name in units or name in moved or index >= len(now):
            continue
        new = now[index]
        if new not in lunits and new not in taken:
            moved[name] = new
            taken.add(new)
    reported = {name: new for name, new in moved.items()
                if not (lunits[name]["parent"] in moved
                        and units[new]["parent"] == moved[lunits[name]["parent"]])}
    return reported, set(moved)


def _caption_fixed(name, lbox, paper, lboxes, claimed):
    """A box in the file that is the locked box with its caption changed:
    same number, kind and place among its part's boxes."""
    unit = paper["units"][lbox["unit"]]
    locked_siblings = [n for n, b in lboxes.items() if b["unit"] == lbox["unit"]]
    position = locked_siblings.index(name)
    if position >= len(unit["boxes"]):
        return None
    box = paper["boxes"][unit["boxes"][position]]
    if (box["name"] not in lboxes and box["name"] not in claimed
            and box["stem"] == lbox["stem"] and box["kind"] == lbox["kind"]):
        return box
    return None


def _inner_changes(lbox, box):
    """What changed inside a box whose answers are stored by letter, item
    number or position."""
    now = _inner(box)
    label = lbox["label"]
    changes = []
    if lbox["kind"] in OPTION_KINDS:
        old, new = lbox["options"], now["options"]
        for letter, text in old.items():
            if new.get(letter) == text:
                continue
            elsewhere = [k for k, v in new.items() if v == text and k != letter]
            if letter not in new:
                changed = "it is no longer there"
            else:
                changed = f"it now reads \"{new[letter]}\""
            if elsewhere:
                changed += f", and that text is now option {elsewhere[0]}"
            changes.append(
                f"Option {letter} of {label} read \"{text}\" when the paper was issued; "
                f"{changed}. Answers are stored as the letter, so a student who chose "
                f"{letter} would be marked against the new option.")
        added = [k for k in new if k not in old]
        if added:
            changes.append(f"{label} has an option it did not have when the paper was "
                           f"issued: {', '.join(added)}.")
        for number, text in lbox.get("items", {}).items():
            if now.get("items", {}).get(number) != text:
                changes.append(
                    f"Item {number} of {label} read \"{text}\" when the paper was issued; it "
                    f"is now \"{now.get('items', {}).get(number, '')}\". Matches are stored "
                    f"by item number.")
    elif lbox["kind"] in SLOT_KINDS:
        old, new = lbox["slots"], now["slots"]
        if len(old) != len(new):
            changes.append(
                f"{label} had {len(old)} places to answer when the paper was issued; it now "
                f"has {len(new)}. Answers are stored by position, so they would land in the "
                f"wrong places.")
        else:
            for place, (was, is_now) in enumerate(zip(old, new), 1):
                if was != is_now:
                    changes.append(
                        f"The choices at place {place} of {label} changed since the paper was "
                        f"issued, so a stored answer may be one the page no longer offers.")
    return changes


def _inner(box):
    """What the lock records inside a box: the text of each option and
    match item, and, for boxes answered in several places, each place."""
    inner = box["inner"]
    if box["kind"] in OPTION_KINDS:
        entry = {"options": {k: _text(v) for k, v in inner["options"].items()}}
        if box["kind"] == "match":
            entry["items"] = {k: _text(v) for k, v in inner["items"].items()}
        return entry
    if box["kind"] in SLOT_KINDS:
        return {"slots": [choices if choices else "typed" for _, choices in inner["slots"]]}
    return {}
