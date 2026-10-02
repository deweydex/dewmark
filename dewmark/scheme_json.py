"""The marker's half, written out as `dewmark-scheme/1` JSON
(docs/EXAM_FORMAT.md §4.6; planning/PROPOSAL.md §4, stage 6).

This is the file a teacher keeps and the workbench reads: everything that
sits below `# Marking scheme`, attached to the permanent names of the
paper it marks, with the names themselves (every part and box, its kind and
marks, and the text of each option) so a scheme moved or emailed without
its exam file can still be checked against the answers it will mark. It
holds the secrets of the paper, so it is never put in a folder students
receive; the secrecy checks of `dewmark/secrecy.py` exist to keep it so.

    from dewmark.reader import read
    from dewmark.scheme_json import scheme_json, dumps
    text = dumps(scheme_json(read(exam_text)))

The shape is a contract with the workbench: a field may be added to it, but
a field is not renamed or taken away without a new format number.
"""

import json
from types import SimpleNamespace

from . import READER_VERSION
from .lock import snapshot
from .scheme import _keyed_box, _unit_of

FORMAT = "dewmark-scheme/1"

# The settings a marker needs to know a paper by.
PAPER_SETTINGS = ("code", "version", "kind", "title", "module", "module code",
                  "session", "institution", "college", "outcomes", "weighting", "technique")


def _number(text):
    try:
        value = float(text)
    except (TypeError, ValueError):
        return text
    return int(value) if value.is_integer() else value


def _alternative(alt):
    """One accepted answer: text, or a number with the rule that compares it.
    Numbers are written as numbers; "0123" stays text and stays 0123."""
    if "text" in alt:
        return {"text": alt["text"]}
    out = {}
    if "number" in alt:
        out["number"] = alt["number"]
        out["written"] = alt.get("written", "")
        if "tolerance" in alt:
            out["tolerance"] = alt["tolerance"]
            out["percent"] = alt.get("percent", False)
    else:
        out["low"], out["high"] = alt["low"], alt["high"]
    if alt.get("unit"):
        out["unit"] = alt["unit"]
    for places in ("dp", "sf"):
        if places in alt:
            out[places] = alt[places]
    return out


def _entry(entry, paper):
    # scheme.py's rules for "which box does this key belong to" work on the
    # reader's own paper object; read() hands back a dict of the same parts.
    view = SimpleNamespace(units=paper["units"], boxes=paper["boxes"], settings=paper["settings"])
    unit = _unit_of(entry, view)
    box = _keyed_box(entry, view) if entry["key"] is not None else None
    key = None
    if entry["key"] is not None:
        key = [[_alternative(a) for a in slot] for slot in entry["key"]]
    return {
        "name": entry["name"],
        "label": entry["label"],
        "unit": unit["name"],
        "marks": _number(unit["marks"]),
        "draft": entry["draft"],
        "method": entry.get("method", "total"),
        "topic": entry["topic"],
        "outcomes": entry["outcomes"],
        "box": box["name"] if box else None,
        "key": key,
        "any_order": entry["any_order"],
        "model": entry["model"],
        "model_is_code": entry["model_is_code"],
        "tests": entry["tests"],
        "points": [{"marks": _number(p["marks"]), "text": p["text"]} for p in entry["points"]],
        "criteria": [{"name": c["name"], "marks": _number(c["marks"]),
                      "bands": [{"low": _number(b["low"]), "high": _number(b["high"]),
                                 "text": b["text"]} for b in c["bands"]]}
                     for c in entry["criteria"]],
        "guidance": entry["guidance"],
    }


def scheme_json(paper):
    """The scheme of a paper read by `dewmark.reader.read`, as plain data.
    The paper should have no problems; the scheme of one that has is not
    worth marking from."""
    settings = paper["settings"]
    names = snapshot(paper)
    entries = [_entry(e, paper) for e in paper["scheme"]["entries"].values()]
    return {
        "format": FORMAT,
        "reader": READER_VERSION,
        "paper": {key: settings[key] for key in PAPER_SETTINGS if key in settings},
        "total": _number(paper["total"]),
        "names": {"units": names["units"], "boxes": names["boxes"]},
        "entries": entries,
        "drafts": paper["scheme"]["drafts"],
    }


def dumps(scheme):
    """The JSON as it is saved: stable, so the same paper always gives the
    same file and a change to a scheme shows as a change in a diff."""
    return json.dumps(scheme, indent=2, ensure_ascii=False) + "\n"
