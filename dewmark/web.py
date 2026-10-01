"""The browser's door into the reader and the paste route (the checker page,
planning/PROPOSAL.md §9 step 3).

The page runs this package inside Pyodide, so everything here takes text
and returns JSON text: no Python object crosses into JavaScript, and the
command line and the browser can be tested against each other by comparing
strings. It adds nothing of its own: each function calls the reader, the
package builder or the reply check and writes down what they return.

    from dewmark import web
    web.check_json(text)                      # what the reader found
    web.package_json(mode, text, about_json)  # what to give an assistant
    web.reply_json(mode, original, reply, about_json, accept_json)
    web.follow_up_json(messages_json)         # "Copy these problems"
"""

import json

from . import READER_VERSION
from .messages import Message
from .package import ABOUT_KEYS, MODES, build_package, follow_up
from .reader import read
from .reply import check_reply


def _dump(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def summary(paper):
    """What a teacher wants to know a paper holds, as numbers and names."""
    kinds = {}
    for box in paper["boxes"].values():
        kinds[box["kind"]] = kinds.get(box["kind"], 0) + 1
    return {
        "questions": sum(1 for u in paper["units"].values() if u["level"] == 2),
        "boxes": len(paper["boxes"]),
        "rough": sum(1 for b in paper["boxes"].values() if b["unmarked"]),
        "marks": paper["total"],
        "entries": len(paper["scheme"]["entries"]),
        "drafts": len(paper["scheme"]["drafts"]),
        "kinds": dict(sorted(kinds.items())),
        "title": paper["settings"].get("title", ""),
        "code": paper["settings"].get("code", ""),
        "kind": paper["settings"].get("kind", ""),
    }


def version():
    return READER_VERSION


def modes_json():
    return _dump([{"key": m.key, "label": m.label, "summary": m.summary, "words": m.words}
                  for m in MODES.values()] + [{"about": list(ABOUT_KEYS)}])


def check_json(text):
    paper = read(text)
    return _dump({"summary": summary(paper),
                  "messages": [m.as_dict() for m in paper["messages"]]})


def package_json(mode, text, about_json="{}"):
    made = build_package(mode, text, json.loads(about_json or "{}"))
    return _dump({"text": made["text"] if not made["problems"] else "",
                  "problems": made["problems"], "findings": made["findings"],
                  "left_out": made["left_out"], "mode": mode})


def reply_json(mode, original, reply, about_json="{}", accept_json="null"):
    result = check_reply(original, reply, mode, json.loads(about_json or "{}"),
                         json.loads(accept_json or "null"))
    return _dump({"ok": result["ok"], "messages": [m.as_dict() for m in result["messages"]],
                  "hunks": result["hunks"], "text": result["text"],
                  "notes": result["notes"], "kept": result["kept"]})


def follow_up_json(messages_json):
    messages = [Message(**m) for m in json.loads(messages_json)]
    return follow_up([m for m in messages if m.level == "problem"] or messages, "")
