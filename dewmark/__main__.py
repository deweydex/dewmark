"""python -m dewmark check EXAM_FILE [EXAM_FILE ...]
python -m dewmark lock EXAM_FILE --sitting "2026-10-20 Group A"
python -m dewmark build EXAM_FILE [-o DIR]
python -m dewmark scheme EXAM_FILE [-o OUT]
python -m dewmark receipt ANSWER_FILE [ANSWER_FILE ...]
python -m dewmark fingerprint EXAM_FILE
python -m dewmark package MODE FILE [--set "key: value" ...] [-o OUT]
python -m dewmark reply MODE ORIGINAL REPLY [--set "key: value" ...] [-o OUT]

check reads each exam file in the format of docs/EXAM_FORMAT.md and prints
what it found and every problem and warning. If names.lock.json sits beside
a file, the file is also checked against the names it was issued with.
Exits 1 if any file has a problem.

lock records that a paper has been issued for a sitting, in
names.lock.json beside the file (§4.4). It refuses a paper with problems.
After that, check refuses a change that would strand stored answers,
unless the paper's version setting changes.

build makes the pages of a paper: a student page, a practice page and an answer
key, and the marking scheme as JSON, into DIR. It refuses a paper with problems,
a paper that uses a kind of box no page draws yet, and any page that would give
away the scheme or a hint (§4.5); and with no -o it only checks. It needs the
`markdown` and `latex2mathml` packages (requirements.txt).

receipt checks each answer file a student handed in: it works out the receipt
(dewmark/receipt.py) from the file and says whether it is the one the page
wrote into it. A file that was changed after it was saved does not match. It
exits 1 if any file does not.

fingerprint prints the paper's ID, the code students see as "Paper ID" and the
code in every answer file made from the paper. It needs the `markdown` and
`latex2mathml` packages, since it reads the pictures the paper carries.

scheme writes the marking scheme of a paper as dewmark-scheme/1 JSON, the
file the marking workbench reads (§4.6). It holds the paper's secrets: keep
it with the teacher's files, never in a folder students receive. It refuses
a paper with problems.

package makes the text to give an assistant (the paste route, §4.10): MODE
is copy, tidy, plain, udl or invite. copy reads a Word paper and needs its
details, as --set "code: my-paper" and so on; the others read an exam file
and leave its marking scheme out.

reply checks what the assistant returned against the paper it was given,
refuses a change to anything but wording, lists each change of wording,
and with -o writes the file with every change made.
"""

import datetime
import json
import os
import sys

from . import lock as names_lock
from .package import ABOUT_KEYS, MODES, build_package
from .reader import read
from .receipt import receipt as receipt_of
from .reply import check_reply
from .scheme_json import dumps, scheme_json


def summary(paper):
    boxes = paper["boxes"].values()
    rough = sum(1 for b in boxes if b["unmarked"])
    kinds = {}
    for box in boxes:
        kinds[box["kind"]] = kinds.get(box["kind"], 0) + 1
    questions = sum(1 for u in paper["units"].values() if u["level"] == 2)
    return (f"{questions} questions, {len(paper['boxes'])} answer boxes"
            f"{f' ({rough} not marked)' if rough else ''}, {paper['total']:g} marks; "
            f"{len(paper['scheme']['entries'])} scheme entries, "
            f"{len(paper['scheme']['drafts'])} draft; kinds: "
            + ", ".join(f"{k} {n}" for k, n in sorted(kinds.items())))


def read_with_lock(path):
    """Read a file and check it against the lock beside it, if there is one.
    Returns (paper, lock or None, lock path, status line or None)."""
    with open(path, encoding="utf-8") as handle:
        paper = read(handle.read())
    lock_path = os.path.join(os.path.dirname(os.path.abspath(path)), names_lock.LOCK_FILE)
    if not os.path.exists(lock_path):
        return paper, None, lock_path, None
    lock, why = names_lock.load(lock_path)
    if lock is None:
        paper["messages"].problem("lock-unreadable", 1, why,
                                  "Restore the file from a backup, or ask for help.")
        return paper, None, lock_path, None
    result = names_lock.check(paper, lock, os.path.basename(path))
    paper["messages"].extend(result["messages"])
    paper["stored"] = result["stored"]
    return paper, lock, lock_path, result["status"]


def check(paths):
    failed = False
    for path in paths:
        paper, _, _, status = read_with_lock(path)
        print(f"{path}: {summary(paper)}")
        if status:
            print(f"  names: {status}")
        for message in paper["messages"]:
            print("  " + str(message).replace("\n", "\n  "))
        failed = failed or bool(paper["messages"].problems)
    return 1 if failed else 0


def lock(path, sitting, on=None):
    paper, found, lock_path, _ = read_with_lock(path)
    if paper["messages"].problems:
        print(f"{path}: not locked, because the paper has problems:")
        for message in paper["messages"].problems:
            print("  " + str(message).replace("\n", "\n  "))
        return 1
    found = found or names_lock.empty_lock()
    on = on or datetime.date.today().isoformat()
    names_lock.record(found, paper, sitting, on, os.path.basename(path))
    names_lock.dump(found, lock_path)
    version = paper["settings"].get("version", "1")
    drafts = paper["scheme"]["drafts"]
    print(f"{path}: version {version} locked for \"{sitting}\" in {lock_path}: "
          f"{len(paper['boxes'])} answer boxes.")
    if drafts:
        print(f"  The scheme still has {len(drafts)} (draft) entries; the names are "
              "locked, the scheme is not.")
    return 0


def _options(argv):
    """Split `--set "key: value"` and `-o OUT` from the other arguments."""
    rest, about, out, index = [], {}, None, 0
    while index < len(argv):
        if argv[index] == "--set" and index + 1 < len(argv):
            key, _, value = argv[index + 1].partition(":")
            about[key.strip()] = value.strip()
            index += 2
        elif argv[index] == "-o" and index + 1 < len(argv):
            out = argv[index + 1]
            index += 2
        else:
            rest.append(argv[index])
            index += 1
    return rest, about, out


def _read_text(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def build(argv):
    from .build import BuildError, build as build_files    # needs markdown: only when asked
    rest, _, out = _options(argv)
    if len(rest) != 1:
        print("build needs an exam file.")
        return 2
    paper, _, _, _ = read_with_lock(rest[0])
    try:
        if paper["messages"].problems:
            raise BuildError(paper["messages"].problems)
        names = build_files(rest[0], out)
    except BuildError as error:
        print(f"{rest[0]}: not built.")
        for message in error.messages:
            print("  " + message.replace("\n", "\n  "))
        return 1
    print(f"{rest[0]}: " + (f"built {len(names)} files into {out}." if out else
                            "builds cleanly; no files written (give -o DIR to write them)."))
    for name in names:
        print("  " + name)
    return 0


def receipts(paths):
    """Check the receipt in each answer file against the file."""
    failed = False
    for path in paths:
        try:
            record = json.loads(_read_text(path))
        except (OSError, ValueError) as error:
            print(f"{path}: cannot be read as an answer file ({error}).")
            failed = True
            continue
        if not isinstance(record, dict) or record.get("format") != "dewmark-answers/1":
            print(f"{path}: not a dewmark answer file (its format is not dewmark-answers/1).")
            failed = True
            continue
        written = record.get("receipt")
        found = receipt_of(record)
        student = record.get("student") or {}
        who = f"{student.get('full name', '?')}, {student.get('student number', '?')}"
        if not written:
            print(f"{path}: {who}: no receipt. The student did not save at the finish sheet "
                  f"(the receipt would be {found}).")
            failed = True
        elif written == found:
            count = len(record.get("answers") or {})
            print(f"{path}: {who}: receipt {found} matches. "
                  f"{count} answer{'' if count == 1 else 's'}; paper ID "
                  f"{(record.get('exam') or {}).get('fingerprint', '?')}.")
        else:
            print(f"{path}: {who}: receipt {written} does not match the file, which works out "
                  f"to {found}. The file was changed after it was saved.")
            failed = True
    return 1 if failed else 0


def fingerprint_of(path):
    from .build import paper_fingerprint            # needs markdown: only when asked
    text = _read_text(path)
    print(paper_fingerprint(text, read(text), os.path.dirname(os.path.abspath(path))))
    return 0


def scheme(argv):
    rest, _, out = _options(argv)
    if len(rest) != 1:
        print("scheme needs an exam file.")
        return 2
    paper = read(_read_text(rest[0]))
    if paper["messages"].problems:
        print(f"{rest[0]}: no scheme written, because the paper has problems:")
        for message in paper["messages"].problems:
            print("  " + str(message).replace("\n", "\n  "))
        return 1
    text = dumps(scheme_json(paper))
    if out:
        with open(out, "w", encoding="utf-8") as handle:
            handle.write(text)
        print(f"{out}: {len(paper['scheme']['entries'])} entries, "
              f"{len(paper['scheme']['drafts'])} still draft. Keep it away from students.")
    else:
        print(text, end="")
    return 0


def package(argv):
    rest, about, out = _options(argv)
    if len(rest) != 2 or rest[0] not in MODES:
        print("package needs a mode (" + ", ".join(MODES) + ") and a file.")
        return 2
    made = build_package(rest[0], _read_text(rest[1]), about)
    for problem in made["problems"]:
        print("  " + problem)
    if made["problems"]:
        print("  (for copy, give each with --set: " + ", ".join(ABOUT_KEYS) + ")")
        return 1
    for finding in made["findings"]:
        print(f"  Check line {finding['line']}: {finding['what']} ({finding['excerpt']}). "
              "Is it student information?")
    if out:
        with open(out, "w", encoding="utf-8") as handle:
            handle.write(made["text"])
        print(f"{out}: {len(made['text'].splitlines())} lines for the \"{rest[0]}\" mode.")
    else:
        print(made["text"])
    return 0


def reply(argv):
    rest, about, out = _options(argv)
    if len(rest) != 3 or rest[0] not in MODES:
        print("reply needs a mode (" + ", ".join(MODES) + "), the paper and the reply.")
        return 2
    result = check_reply(_read_text(rest[1]), _read_text(rest[2]), rest[0], about)
    for message in result["messages"]:
        print("  " + str(message).replace("\n", "\n  "))
    for hunk in result["hunks"]:
        print(f"  Change at line {hunk['line']}" + (f" ({hunk['where']})" if hunk["where"] else ""))
        print("".join(f"    - {l}\n" for l in hunk["before"]) +
              "".join(f"    + {l}\n" for l in hunk["after"]), end="")
    if result["kept"] is not None:
        print(f"  The reply keeps {result['kept']:.0%} of your words, in order.")
    if result["notes"]:
        print("  The assistant's notes:\n    " + result["notes"].replace("\n", "\n    "))
    print("  " + ("Accepted." if result["ok"] else "Refused: nothing was written."))
    if result["ok"] and out:
        with open(out, "w", encoding="utf-8") as handle:
            handle.write(result["text"])
        print(f"  {out}: written with {len(result['hunks'])} change(s) made.")
    return 0 if result["ok"] else 1


def main(argv):
    if len(argv) >= 2 and argv[0] == "check":
        return check(argv[1:])
    if len(argv) == 4 and argv[0] == "lock" and argv[2] == "--sitting":
        return lock(argv[1], argv[3])
    if argv and argv[0] == "build":
        return build(argv[1:])
    if argv and argv[0] == "scheme":
        return scheme(argv[1:])
    if len(argv) >= 2 and argv[0] == "receipt":
        return receipts(argv[1:])
    if len(argv) == 2 and argv[0] == "fingerprint":
        return fingerprint_of(argv[1])
    if argv and argv[0] == "package":
        return package(argv[1:])
    if argv and argv[0] == "reply":
        return reply(argv[1:])
    print(__doc__.strip())
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
