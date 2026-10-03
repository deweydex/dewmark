"""Receipts and fingerprints (dewmark/receipt.py; docs/ANSWER_FILE.md).

The expected codes below are written out, not computed: they freeze the
format. A change to the canonical form, the alphabet or the material that
makes a code changes every receipt and fingerprint already handed out, so a
test here failing means a decision, not a repair.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

from dewmark import build as build_module  # noqa: E402
from dewmark.__main__ import main  # noqa: E402
from dewmark.build import build_pages  # noqa: E402
from dewmark.receipt import ALPHABET, canonical, fingerprint, paper_text, receipt  # noqa: E402

PAPER = """\
---
dewmark: 1
code: fp-test
kind: exam
title: Fingerprint Test
module: Testing
module code: 5N0000
total marks: 4
time allowed: 1 hour
---

## Question 1: Q (4 marks)

Say something.

```answer
```

```hint
Try a small case.
```

# Marking scheme

### 1

Answer: a very particular answer
"""

RECORD = {
    "format": "dewmark-answers/1",
    "exam": {"code": "x", "version": "1", "title": "T", "fingerprint": "7KQ-4MD"},
    "page": "student",
    "student": {"full name": "Síle Ní Bhriain", "student number": "D00123456"},
    "started_at": "2027-01-12T09:02:11.403Z",
    "saved_at": "2027-01-12T10:01:52.918Z",
    "finished_at": "2027-01-12T10:01:52.918Z",
    "answers": {"q1a": "x ≥ 5 😀\n\ttab \"q\" \\", "q1b": ["B", "A"]},
}


# --- the canonical form ----------------------------------------------------------------------------------------

def test_canonical_sorts_keys_at_every_level_and_has_no_spaces():
    assert canonical({"b": [1, {"d": 1, "c": 2}], "a": None}) == '{"a":null,"b":[1,{"c":2,"d":1}]}'


def test_canonical_writes_everything_outside_printable_ascii_as_lower_case_escapes():
    assert canonical("é") == '"\\u00e9"'
    assert canonical("😀") == '"\\ud83d\\ude00"'
    assert canonical("\x7f") == '"\\u007f"'
    assert canonical("a\nb\tc\"d\\e") == '"a\\nb\\tc\\"d\\\\e"'
    assert canonical("\x00\x1f") == '"\\u0000\\u001f"'
    assert canonical("≥") == '"\\u2265"'


def test_the_canonical_form_of_the_sample_record_is_frozen():
    assert canonical(RECORD) == (
        '{"answers":{"q1a":"x \\u2265 5 \\ud83d\\ude00\\n\\ttab \\"q\\" \\\\","q1b":["B","A"]},'
        '"exam":{"code":"x","fingerprint":"7KQ-4MD","title":"T","version":"1"},'
        '"finished_at":"2027-01-12T10:01:52.918Z","format":"dewmark-answers/1","page":"student",'
        '"saved_at":"2027-01-12T10:01:52.918Z","started_at":"2027-01-12T09:02:11.403Z",'
        '"student":{"full name":"S\\u00edle N\\u00ed Bhriain","student number":"D00123456"}}')


# --- receipts -----------------------------------------------------------------------------------------------------

def test_the_receipt_of_the_sample_record_is_frozen():
    assert receipt(RECORD) == "77FD 81FB"


def test_a_receipt_is_two_groups_of_four_capital_hexadecimal_digits():
    assert re.fullmatch(r"[0-9A-F]{4} [0-9A-F]{4}", receipt(RECORD))


def test_a_receipt_ignores_the_time_of_the_last_save_and_the_receipt_itself():
    same = {**RECORD, "saved_at": "2030-01-01T00:00:00.000Z", "receipt": "0000 0000"}
    assert receipt(same) == receipt(RECORD)


@pytest.mark.parametrize("change", [
    lambda r: r["answers"].update(q1a="x ≥ 6"),
    lambda r: r["answers"].update(q1c="new"),
    lambda r: r["answers"].pop("q1b"),
    lambda r: r["answers"].update(q1b=["A", "B"]),
    lambda r: r["student"].update({"full name": "Síle Ní Bhriain "}),
    lambda r: r["student"].update({"student number": "D00123457"}),
    lambda r: r.update(finished_at="2027-01-12T10:01:53.918Z"),
    lambda r: r.update(finished_at=None),
    lambda r: r.update(started_at=None),
    lambda r: r.update(page="practice"),
    lambda r: r["exam"].update(fingerprint="7KQ-4ME"),
    lambda r: r["exam"].update(version="2"),
])
def test_a_change_to_anything_a_marker_would_care_about_changes_the_receipt(change):
    import copy
    changed = copy.deepcopy(RECORD)
    change(changed)
    assert receipt(changed) != receipt(RECORD)


def test_the_order_of_the_keys_in_a_record_does_not_matter():
    shuffled = dict(reversed(list(RECORD.items())))
    shuffled["answers"] = dict(reversed(list(RECORD["answers"].items())))
    assert receipt(shuffled) == receipt(RECORD)


# --- fingerprints -----------------------------------------------------------------------------------------------

def test_the_fingerprint_of_the_sample_paper_is_frozen():
    assert fingerprint(PAPER) == "D8J-9GX"
    assert fingerprint(PAPER, [("pictures/a.svg", "ab" * 32)]) == "X7Z-0EB"


def test_a_fingerprint_is_three_letters_a_hyphen_and_three_letters_of_the_alphabet():
    code = fingerprint(PAPER)
    assert re.fullmatch(r"[0-9A-HJKMNP-TV-Z]{3}-[0-9A-HJKMNP-TV-Z]{3}", code)
    assert not set(code.replace("-", "")) & set("ILOU") and set(ALPHABET) >= set(code.replace("-", ""))


def test_changing_the_marking_scheme_or_a_hint_does_not_change_the_fingerprint():
    other_scheme = PAPER.replace("a very particular answer", "something else entirely\n\nModel answer: x")
    other_hint = PAPER.replace("Try a small case.", "Think about the empty case.")
    no_hint = PAPER.replace("```hint\nTry a small case.\n```\n\n", "")
    assert fingerprint(other_scheme) == fingerprint(PAPER) == fingerprint(other_hint) == fingerprint(no_hint)


def test_line_endings_and_trailing_spaces_do_not_change_the_fingerprint():
    assert fingerprint(PAPER.replace("\n", "\r\n")) == fingerprint(PAPER)
    assert fingerprint(PAPER.replace("Say something.", "Say something.   ")) == fingerprint(PAPER)
    assert fingerprint("\n\n" + PAPER) == fingerprint(PAPER)


@pytest.mark.parametrize("old, new", [
    ("Say something.", "Say something else."),
    ("(4 marks)", "(3 marks)"),
    ("total marks: 4", "total marks: 3"),
    ("time allowed: 1 hour", "time allowed: 2 hours"),
    ("title: Fingerprint Test", "title: Fingerprint Test 2"),
    ("```answer\n```", "```essay\n```"),
])
def test_changing_anything_students_are_given_changes_the_fingerprint(old, new):
    assert old in PAPER
    assert fingerprint(PAPER.replace(old, new)) != fingerprint(PAPER)


def test_changing_a_picture_changes_the_fingerprint_and_the_order_of_pictures_does_not():
    a, b = ("pictures/a.svg", "11" * 32), ("pictures/b.svg", "22" * 32)
    assert fingerprint(PAPER, [a, b]) == fingerprint(PAPER, [b, a])
    assert fingerprint(PAPER, [a, b]) != fingerprint(PAPER, [a])
    assert fingerprint(PAPER, [a]) != fingerprint(PAPER, [("pictures/a.svg", "33" * 32)])
    assert fingerprint(PAPER, [a]) != fingerprint(PAPER, [("pictures/c.svg", "11" * 32)])


def test_the_paper_text_is_the_part_above_the_scheme_without_hints():
    text = paper_text(PAPER)
    assert "Say something." in text and "Try a small case" not in text and "particular" not in text
    assert text.startswith("---") and not text.endswith("\n")


# --- the builder puts the fingerprint in the pages ------------------------------------------------------------

def test_every_page_of_a_paper_carries_the_same_fingerprint_in_its_model():
    files = build_pages(PAPER, ROOT)
    codes = {re.search(r'"fingerprint": "([^"]*)"', text).group(1)
             for name, text in files.items() if name.endswith(".html")}
    assert codes == {fingerprint(PAPER)}


def test_a_picture_in_the_paper_is_part_of_the_fingerprint_a_picture_in_a_hint_is_not(tmp_path):
    (tmp_path / "pics").mkdir()
    (tmp_path / "pics" / "a.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
    with_picture = PAPER.replace("Say something.", "Say something.\n\n![a square](pics/a.svg)")
    in_hint = PAPER.replace("Try a small case.", "Try a small case.\n\n![a square](pics/a.svg)")
    code = lambda text: re.search(r'"fingerprint": "([^"]*)"', build_pages(text, tmp_path)["fp-test.student.html"]).group(1)  # noqa: E731
    assert code(in_hint) == code(PAPER), "a hint is not what students are given"
    before = code(with_picture)
    (tmp_path / "pics" / "a.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="5"/>')
    assert code(with_picture) != before, "the same words with another picture is another paper"


def test_the_builder_still_passes_the_mutation_test_with_the_fingerprint_in_the_page():
    assert build_pages(PAPER, ROOT)       # raises BuildError if a page changed when the scheme did
    assert build_module.paper_fingerprint(PAPER, build_module.read(PAPER), ROOT) == fingerprint(PAPER)


# --- the commands -----------------------------------------------------------------------------------------------

def written(tmp_path, name, record):
    import json
    path = tmp_path / name
    path.write_text(json.dumps(record), encoding="utf-8")
    return str(path)


def test_the_receipt_command_accepts_a_file_whose_receipt_is_right(tmp_path, capsys):
    good = {**RECORD, "receipt": receipt(RECORD)}
    assert main(["receipt", written(tmp_path, "good.json", good)]) == 0
    out = capsys.readouterr().out
    assert "Síle Ní Bhriain, D00123456" in out and "receipt 77FD 81FB matches" in out
    assert "2 answers; paper ID 7KQ-4MD" in out


def test_the_receipt_command_refuses_a_file_changed_after_it_was_saved(tmp_path, capsys):
    import copy
    edited = copy.deepcopy({**RECORD, "receipt": receipt(RECORD)})
    edited["answers"]["q1b"] = ["C"]
    assert main(["receipt", written(tmp_path, "edited.json", edited)]) == 1
    out = capsys.readouterr().out
    assert "does not match" in out and "changed after it was saved" in out and "77FD 81FB" in out


def test_the_receipt_command_says_when_there_is_no_receipt_and_when_it_is_not_an_answer_file(tmp_path, capsys):
    assert main(["receipt", written(tmp_path, "none.json", RECORD)]) == 1
    assert "no receipt" in capsys.readouterr().out
    assert main(["receipt", written(tmp_path, "other.json", {"format": "x"})]) == 1
    assert "not a dewmark answer file" in capsys.readouterr().out
    (tmp_path / "broken.json").write_text("not json")
    assert main(["receipt", str(tmp_path / "broken.json")]) == 1
    assert "cannot be read" in capsys.readouterr().out
    assert main(["receipt", str(tmp_path / "missing.json")]) == 1


def test_the_receipt_command_checks_every_file_and_fails_if_any_does(tmp_path, capsys):
    good = written(tmp_path, "good.json", {**RECORD, "receipt": receipt(RECORD)})
    bad = written(tmp_path, "bad.json", RECORD)
    assert main(["receipt", good, bad]) == 1
    assert capsys.readouterr().out.count("\n") == 2


def test_the_fingerprint_command_prints_the_papers_id(tmp_path, capsys):
    exam = tmp_path / "paper.exam.md"
    exam.write_text(PAPER, encoding="utf-8")
    assert main(["fingerprint", str(exam)]) == 0
    assert capsys.readouterr().out.strip() == "D8J-9GX"
