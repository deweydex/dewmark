"""python -m dewmark check EXAM_FILE [EXAM_FILE ...]

Reads each exam file in the format of docs/EXAM_FORMAT.md and prints what
it found and every problem and warning. Exits 1 if any file has a problem.
"""

import sys

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


def main(argv):
    if len(argv) < 2 or argv[0] != "check":
        print(__doc__.strip())
        return 2
    failed = False
    for path in argv[1:]:
        with open(path, encoding="utf-8") as handle:
            paper = read(handle.read())
        print(f"{path}: {summary(paper)}")
        for message in paper["messages"]:
            print("  " + str(message).replace("\n", "\n  "))
        failed = failed or bool(paper["messages"].problems)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
