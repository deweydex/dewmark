"""Tests for the names lock (dewmark/lock.py, docs/EXAM_FORMAT.md §4.4).

Each test issues a small paper, changes it the way a teacher might after
students have sat it, and checks what the lock says. A change that would
strand stored answers is refused unless `version` changes; a caption fix,
a question moved without renumbering and a new box are allowed.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from dewmark import READER_VERSION  # noqa: E402
from dewmark.__main__ import main  # noqa: E402
from dewmark.lock import check, empty_lock, record, snapshot  # noqa: E402
from dewmark.reader import read  # noqa: E402

PAPER = """\
---
dewmark: 1
code: lock-test
kind: practice
total marks: 30
time allowed: 1 hour
{extra}---

## Question 1: Measuring (10 marks)

### 1(a): Height (4 marks)

```answer 1(a): working
```

```answer 1(a): result
```

### 1(b): Units (6 marks)

```choice
A. metres
B. seconds
C. kilograms
```

## Question 2: Loops (10 marks)

### 2(a): Counting (5 marks)

```python exec 2(a): your function
```

### 2(b): Tracing (5 marks)

```blanks
The loop runs ____ times and prints ____.
```

## Question 3: Lists (10 marks)

```answer
```
"""


def issue(text=PAPER, sitting="2026-10-20 Group A", **fields):
    paper = read(text.format(extra="".join(f"{k}: {v}\n" for k, v in fields.items())))
    assert not paper["messages"].problems, paper["messages"]
    return record(empty_lock(), paper, sitting, "2026-10-13", "lock-test.exam.md")


def after(lock, text, **fields):
    paper = read(text.format(extra="".join(f"{k}: {v}\n" for k, v in fields.items())))
    return check(paper, lock, "lock-test.exam.md")


def codes(result, level="problem"):
    return [m.code for m in result["messages"] if m.level == level]


# --- what is recorded ------------------------------------------------------

def test_the_lock_records_every_name_with_its_kind_marks_label_and_options():
    lock = issue()
    version = lock["papers"]["lock-test"]["versions"]["1"]
    assert list(version["boxes"]) == ["q1a.working", "q1a.result", "q1b",
                                      "q2a.your-function", "q2b", "q3"]
    assert version["boxes"]["q1b"]["options"] == {"A": "metres", "B": "seconds",
                                                  "C": "kilograms"}
    assert version["boxes"]["q2b"]["slots"] == ["typed", "typed"]
    assert version["units"]["q1a"]["marks"] == 4
    assert version["units"]["q1a"]["label"] == "1(a)"
    assert version["reader"] == READER_VERSION
    assert version["issued"] == [{"sitting": "2026-10-20 Group A", "on": "2026-10-13"}]


def test_the_lock_is_plain_json():
    json.dumps(issue())


def test_an_unchanged_paper_passes():
    result = after(issue(), PAPER)
    assert result["messages"] == []
    assert result["status"] == "version 1, issued for \"2026-10-20 Group A\""


def test_a_paper_never_issued_passes():
    result = after(empty_lock(), PAPER)
    assert result["messages"] == [] and result["status"] == "not yet issued"


# --- refused after issue -----------------------------------------------------

def test_a_part_renumbered_after_a_sitting_is_refused():
    # A new 2(b) is written in, and the old 2(b) becomes 2(c).
    text = PAPER.replace("## Question 2: Loops (10 marks)", "## Question 2: Loops (15 marks)")
    text = text.replace("### 2(b): Tracing (5 marks)",
                        "### 2(b): Naming (5 marks)\n\n```answer\n```\n\n"
                        "### 2(c): Tracing (5 marks)").replace("total marks: 30", "total marks: 35")
    result = after(issue(), text)
    assert codes(result) == ["renumbered-after-sitting"]
    message = result["messages"][0]
    assert "2(b)" in message.what and "2(c)" in message.what and message.where == "2(c)"
    assert "version: 2" in message.fix


def test_a_renumbered_question_is_reported_once_not_once_per_part():
    text = PAPER.replace("## Question 2: Loops", "## Question 4: Loops")
    for part in ("a", "b"):
        text = text.replace(f"### 2({part})", f"### 4({part})").replace(
            f"python exec 2({part})", f"python exec 4({part})")
    result = after(issue(), text)
    assert codes(result) == ["renumbered-after-sitting"]
    assert "answers to 2, \"Loops\", are stored" in result["messages"][0].what
    assert result["messages"][0].where == "4"


def test_a_part_renumbered_and_retitled_is_still_caught_by_its_place():
    text = PAPER.replace("### 2(b): Tracing", "### 2(c): Tracing the loop")
    result = after(issue(), text)
    assert codes(result) == ["renumbered-after-sitting"]


def test_a_part_removed_after_a_sitting_is_refused():
    text = PAPER.replace("### 2(b): Tracing (5 marks)\n\n```blanks\n"
                         "The loop runs ____ times and prints ____.\n```\n", "")
    text = text.replace("Loops (10 marks)", "Loops (5 marks)").replace(
        "total marks: 30", "total marks: 25")
    result = after(issue(), text)
    assert codes(result) == ["locked-part-removed"]
    assert result["messages"][0].where == "2(b)"


def test_a_whole_question_removed_is_reported_once():
    text = PAPER[:PAPER.index("## Question 2")] + PAPER[PAPER.index("## Question 3"):]
    result = after(issue(), text.replace("total marks: 30", "total marks: 20"))
    assert codes(result) == ["locked-part-removed"]
    assert result["messages"][0].where == "2"


def test_re_marking_a_part_is_refused():
    text = PAPER.replace("### 1(a): Height (4 marks)", "### 1(a): Height (5 marks)")
    text = text.replace("### 1(b): Units (6 marks)", "### 1(b): Units (5 marks)")
    result = after(issue(), text)
    assert codes(result) == ["locked-marks-changed", "locked-marks-changed"]
    assert "4 marks" in result["messages"][0].what


def test_retyping_a_box_is_refused():
    text = PAPER.replace("```answer 1(a): result", "```maths 1(a): result")
    result = after(issue(), text)
    assert codes(result) == ["locked-kind-changed"]


def test_removing_a_box_is_refused():
    text = PAPER.replace("```answer 1(a): working\n```\n\n", "")
    result = after(issue(), text)
    assert codes(result) == ["locked-box-removed"]


def test_swapping_options_is_refused_and_says_where_the_text_went():
    text = PAPER.replace("A. metres\nB. seconds", "A. seconds\nB. metres")
    result = after(issue(), text)
    assert codes(result) == ["locked-options-changed", "locked-options-changed"]
    assert "now option B" in result["messages"][0].what


def test_changing_the_number_of_gaps_is_refused():
    text = PAPER.replace("prints ____.", "prints ____ and ends on ____.")
    result = after(issue(), text)
    assert codes(result) == ["locked-inner-changed"]


def test_changing_the_code_of_an_issued_file_is_refused():
    text = PAPER.replace("code: lock-test", "code: lock-test-2")
    result = after(issue(), text)
    assert codes(result) == ["code-changed-after-issue"]


# --- allowed after issue -----------------------------------------------------

def test_a_caption_fix_keeps_the_stored_name_and_says_so():
    lock = issue(PAPER.replace("your function", "your fucntion"))
    result = after(lock, PAPER)
    assert codes(result) == [] and codes(result, "warning") == ["caption-changed"]
    assert result["stored"] == {"q2a.your-function": "q2a.your-fucntion"}


def test_moving_questions_without_renumbering_warns():
    one = PAPER[PAPER.index("## Question 1"):PAPER.index("## Question 2")]
    text = PAPER.replace(one, "") + "\n" + one
    result = after(issue(), text)
    assert codes(result) == [] and codes(result, "warning") == ["questions-moved"]


def test_adding_a_box_is_allowed():
    text = PAPER.replace("```answer\n```\n", "```answer\n```\n\n```answer 3: rough work "
                         "(not marked)\n```\n")
    result = after(issue(), text)
    assert result["messages"] == []


def test_a_new_version_is_checked_against_nothing():
    text = PAPER.replace("### 1(a): Height (4 marks)", "### 1(a): Height (5 marks)")
    text = text.replace("### 1(b): Units (6 marks)", "### 1(b): Units (5 marks)")
    result = after(issue(), text, version=2)
    assert result["messages"] == []
    assert result["status"].startswith("version 2 not yet issued")


def test_a_second_sitting_is_added_and_new_boxes_are_locked_with_it():
    lock = issue()
    text = PAPER.replace("```answer\n```\n", "```answer\n```\n\n```answer 3: notes "
                         "(not marked)\n```\n")
    paper = read(text.format(extra=""))
    record(lock, paper, "2026-10-21 Group B", "2026-10-14", "lock-test.exam.md")
    version = lock["papers"]["lock-test"]["versions"]["1"]
    assert [s["sitting"] for s in version["issued"]] == ["2026-10-20 Group A",
                                                         "2026-10-21 Group B"]
    assert "q3.notes" in version["boxes"]
    record(lock, paper, "2026-10-21 Group B", "2026-10-14", "lock-test.exam.md")
    assert len(version["issued"]) == 2


def test_a_newer_reader_warns_but_still_checks():
    lock = issue()
    lock["papers"]["lock-test"]["versions"]["1"]["reader"] = "0.9"
    result = after(lock, PAPER)
    assert codes(result, "warning") == ["lock-reader-changed"]


# --- the command line --------------------------------------------------------

def test_lock_then_check_from_the_command_line(tmp_path, capsys):
    exam = tmp_path / "lock-test.exam.md"
    exam.write_text(PAPER.format(extra=""), encoding="utf-8")
    assert main(["lock", str(exam), "--sitting", "2026-10-20 Group A"]) == 0
    saved = json.loads((tmp_path / "names.lock.json").read_text(encoding="utf-8"))
    assert saved["format"] == "dewmark-names/1"
    assert main(["check", str(exam)]) == 0
    assert "names: version 1, issued for" in capsys.readouterr().out
    exam.write_text(PAPER.format(extra="").replace("(4 marks)", "(3 marks)")
                    .replace("(6 marks)", "(7 marks)"), encoding="utf-8")
    assert main(["check", str(exam)]) == 1
    assert "locked-marks-changed" in capsys.readouterr().out


def test_a_paper_with_problems_is_not_locked(tmp_path, capsys):
    exam = tmp_path / "lock-test.exam.md"
    exam.write_text(PAPER.format(extra="").replace("total marks: 30", "total marks: 31"),
                    encoding="utf-8")
    assert main(["lock", str(exam), "--sitting", "A"]) == 1
    assert not (tmp_path / "names.lock.json").exists()


def test_a_damaged_lock_file_is_a_problem_not_a_crash(tmp_path, capsys):
    exam = tmp_path / "lock-test.exam.md"
    exam.write_text(PAPER.format(extra=""), encoding="utf-8")
    (tmp_path / "names.lock.json").write_text("{not json", encoding="utf-8")
    assert main(["check", str(exam)]) == 1
    assert "lock-unreadable" in capsys.readouterr().out


def test_the_snapshot_of_every_pdp_paper_is_json():
    for path in sorted((ROOT / "samples" / "pdp-5n2927").glob("*.exam.md")):
        paper = read(path.read_text(encoding="utf-8"))
        json.dumps(snapshot(paper, path.name))
