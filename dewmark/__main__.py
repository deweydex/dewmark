"""python -m dewmark check EXAM_FILE [EXAM_FILE ...]
python -m dewmark lock EXAM_FILE --sitting "2026-10-20 Group A"

check reads each exam file in the format of docs/EXAM_FORMAT.md and prints
what it found and every problem and warning. If names.lock.json sits beside
a file, the file is also checked against the names it was issued with.
Exits 1 if any file has a problem.

lock records that a paper has been issued for a sitting, in
names.lock.json beside the file (§4.4). It refuses a paper with problems.
After that, check refuses a change that would strand stored answers,
unless the paper's version setting changes.
"""

import datetime
import os
import sys

from . import lock as names_lock
from .reader import read


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


def main(argv):
    if len(argv) >= 2 and argv[0] == "check":
        return check(argv[1:])
    if len(argv) == 4 and argv[0] == "lock" and argv[2] == "--sitting":
        return lock(argv[1], argv[3])
    print(__doc__.strip())
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
