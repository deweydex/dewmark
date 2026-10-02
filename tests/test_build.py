"""Tests for the reader's content blocks, the renderer (dewmark/render.py) and
the build (dewmark/build.py).

The pages are built from a small paper written here, so each test can change
one thing: a kind of box, a hint, a piece of hostile wording, a leak. What
matters most is the last group: every sample paper is built with both leak
checks run on the pages the real renderer makes, which is the work the search
and the mutation test were written to do (dewmark/secrecy.py).
"""

import html as html_module
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest

pytest.importorskip("markdown")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from dewmark import build as build_module  # noqa: E402
from dewmark.__main__ import main  # noqa: E402
from dewmark.build import BuildError, build, build_pages, page_model  # noqa: E402
from dewmark.reader import read  # noqa: E402
from dewmark.render import (NOT_BUILT, check_buildable, render_markdown,  # noqa: E402
                            render_paper)

SPECIMEN = (ROOT / "dewmark" / "data" / "specimen.exam.md").read_text(encoding="utf-8")
PDP = sorted((ROOT / "samples" / "pdp-5n2927").glob("*.exam.md"))

HEADER = """\
---
dewmark: 1
code: build-test
kind: exam
title: Build Test
module: Testing
module code: 5N0000
total marks: {total}
time allowed: 1 hour
---
"""


def paper(body, scheme="", total=10, base=None):
    text = HEADER.format(total=total) + body
    if scheme:
        text += "\n# Marking scheme\n" + scheme
    return text


def one_box(box, marks=10, extra="", scheme=""):
    return paper(f"## Question 1: Q ({marks} marks)\n\n{extra}\n{box}\n", scheme or
                 "### 1 (draft)\n", total=marks)


def page(text, variant="student", base=None):
    return render_paper(read(text), variant, base)


class Balanced(HTMLParser):
    """Checks that the tags a page opens, it closes, in order."""

    VOID = {"input", "img", "br", "meta", "hr", "link", "col"}

    def __init__(self):
        super().__init__()
        self.stack, self.problems = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        if not self.stack or self.stack[-1] != tag:
            self.problems.append(f"</{tag}> where {self.stack[-1:] or 'nothing'} was open")
        else:
            self.stack.pop()


def balanced(markup):
    parser = Balanced()
    parser.feed(markup)
    return parser.problems + [f"<{t}> never closed" for t in parser.stack]


# --- what the reader keeps ------------------------------------------------------------------

def test_the_reader_keeps_the_papers_content_in_the_order_it_was_written():
    blocks = read(SPECIMEN)["blocks"]
    kinds = [b["type"] if b["type"] not in ("unit", "box") else b["type"] + ":" + b.get("name", "")
             for b in blocks]
    assert kinds[:4] == ["text", "section", "unit:q1", "unit:q1a"]
    assert kinds.index("listing") < kinds.index("box:q1a") < kinds.index("unit:q1b")
    assert blocks[0]["front"] is True and blocks[0]["lines"][0] == "## Instructions to candidates"
    assert not any(b["front"] for b in blocks[1:] if b["type"] == "text")


def test_an_ordinary_heading_is_text_and_a_heading_with_marks_is_a_part():
    text = one_box("```answer\n```", extra="#### Look closely\n\nRead on.")
    blocks = read(text)["blocks"]
    assert [b["type"] for b in blocks] == ["unit", "text", "box"]
    assert blocks[1]["lines"][0] == "#### Look closely"


def test_a_hint_is_a_known_fence_kept_with_the_part_it_sits_under():
    text = one_box("```answer\n```\n\n```hint\nTry a smaller case first.\n```")
    result = read(text)
    assert [m.code for m in result["messages"] if m.code != "no-scheme-entry"] == []
    hint = next(b for b in result["blocks"] if b["type"] == "hint")
    assert hint["body"] == "Try a smaller case first." and hint["unit"] == "q1"


def test_material_listings_and_setup_are_kept_and_a_listing_is_not_a_box():
    text = one_box("```answer\n```", extra="```material Figure 1\nA table of numbers.\n```\n\n"
                   "```sql\nSELECT 1;\n```\n\n```python setup\nx = 1\n```")
    blocks = read(text)["blocks"]
    assert {b["type"] for b in blocks} >= {"material", "listing", "setup"}
    assert next(b for b in blocks if b["type"] == "material")["label"] == "Figure 1"
    assert next(b for b in blocks if b["type"] == "listing")["lang"] == "sql"


# --- the kinds of box ---------------------------------------------------------------------------

def test_an_answer_box_is_a_text_area_that_starts_with_what_the_file_gave_it():
    out = page(one_box("```answer 1: working (4 lines)\nStart here\n```"))
    assert 'data-kind="answer"' in out and 'rows="4"' in out and ">Start here</textarea>" in out
    assert "working" in out


def test_how_tall_a_box_starts_follows_the_marks():
    rows = lambda marks: re.search(r'rows="(\d+)"', page(one_box("```answer\n```", marks))).group(1)  # noqa: E731
    assert (rows(2), rows(5), rows(9)) == ("3", "6", "10")


def test_an_essay_has_a_word_count_and_says_how_long_it_should_be():
    out = page(one_box("```essay (about 800 words)\n```"))
    assert "About 800 words" in out and "dm-word-count" in out and "dm-essay" in out


def test_code_and_python_exec_are_code_editors_and_only_python_has_a_label():
    code = page(one_box("```code\nprint(1)\n```"))
    exec_ = page(one_box("```python exec\nprint(1)\n```"))
    assert 'data-kind="code"' in code and "dm-code-bar" not in code and "print(1)</textarea>" in code
    assert 'data-kind="python exec"' in exec_ and "dm-code-bar" in exec_


def test_a_choice_is_radio_buttons_or_check_boxes_when_more_than_one_may_be_chosen():
    box = "```choice{note}\nA. one\nB. two\nC. three\n```"
    one = page(one_box(box.format(note="")))
    several = page(one_box(box.format(note=" (choose 2)")))
    assert one.count('type="radio"') == 3 and 'value="B"' in one and "checkbox" not in one
    assert several.count('type="checkbox"') == 3 and "radio" not in several


def test_an_option_that_holds_code_keeps_its_listing():
    out = page(one_box("````choice\nA. text\nB.\n```python\nfor n in range(5):\n    print(n)\n```\n````"))
    assert "<pre><code" in out and "for n in range(5):" in out


def test_boxes_make_one_input_for_each_gap_or_line_and_a_bank_makes_drop_downs():
    text = one_box("```boxes\nName: ____\nHeight: ____ and width: ____\nNo gap on this line\n```")
    out = page(text)
    assert out.count('data-slot=') == 4 and "<select" not in out
    with_bank = page(one_box("```boxes\nPart 1: ____\nPart 2: ____\nChoose from: leaf / root / stem\n```"))
    assert with_bank.count("<select") == 2 and with_bank.count("<option") == 8 and "root" in with_bank


def test_blanks_take_typed_gaps_and_choices_in_the_sentence():
    out = page(one_box("```blanks\nA ____ has [roots / leaves / seeds] and a `stem`.\n```"))
    assert out.count('data-slot=') == 2 and out.count("<select") == 1
    assert "<code>stem</code>" in out and "leaves" in out


def test_a_gap_inside_code_or_maths_is_not_a_gap():
    out = page(one_box("```blanks\nUse `a____b` and $x____y$ then ____.\n```"))
    assert out.count('data-slot=') == 1


def test_a_table_has_a_box_in_each_cell_marked_____and_says_where_it_is():
    table = "| Size | Count |\n|---|---|\n| small | ____ |\n| large | ____ |"
    out = page(one_box(f"```table\n{table}\n```"))
    assert out.count('data-slot=') == 2 and "<table>" in out
    assert "row 1, column 2" in out and "row 2, column 2" in out


def test_a_kind_no_page_draws_yet_stops_the_build_with_a_message_and_a_way_out():
    for kind in NOT_BUILT:
        found = check_buildable(read(one_box(f"```{kind}\n1. one\nA. two\n```")), ROOT)
        assert [m.code for m in found.problems] == ["kind-not-built"], kind
        assert kind in found.problems[0].what and found.problems[0].fix


def test_listings_are_numbered_by_line_and_material_is_set_apart():
    out = page(one_box("```answer\n```", extra="```python\na = 1\n\nb = 2\n```\n\n"
                                               "```material Figure 2\nThe **data** table.\n```"))
    assert out.count('class="dm-line"') == 3 and 'data-lang="python"' in out
    assert "<figcaption>Figure 2</figcaption>" in out and "<strong>data</strong>" in out


def test_maths_between_dollar_signs_becomes_mathml():
    out = page(one_box("```answer\n```", extra="Solve $x^2 - 4 = 0$ for $x$."))
    assert out.count("<math") == 2


def test_the_questions_parts_and_sub_parts_nest_and_close():
    text = paper("# Section A: All (10 marks)\n\n## Question 1: Q (10 marks)\n\n"
                 "### 1(a): A (6 marks)\n\n#### (i) One (2 marks)\n\n```answer\n```\n\n"
                 "#### (ii) Two (4 marks)\n\n```answer\n```\n\n### 1(b): B (4 marks)\n\n```answer\n```\n",
                 "### 1 (draft)\n")
    for variant in ("student", "practice", "answer-key"):
        out = page(text, variant)
        assert balanced(out) == [], variant
        assert out.index('id="q1a.i"') < out.index('id="q1a.ii"') < out.index('id="q1b"')
    assert re.findall(r"<h5[^>]*>([^<]*)", page(text))[0].startswith("(i)")


def test_a_paper_with_no_sections_still_draws_its_questions():
    out = page(one_box("```answer\n```"))
    assert "dm-section" not in out and 'id="q1"' in out and balanced(out) == []


# --- who sees what ----------------------------------------------------------------------------------------

HINTED = paper("## Question 1: Q (4 marks)\n\n```answer\n```\n\n```hint\nTry a small case first.\n```\n",
               "### 1\n\nAnswer: a very particular answer\n\nModel answer: the model answer, in full\n",
               total=4)


def test_only_the_practice_page_and_the_key_show_a_hint():
    assert "small case" not in page(HINTED, "student")
    for variant in ("practice", "answer-key"):
        assert "small case" in page(HINTED, variant)


def test_only_the_answer_key_shows_the_marking_scheme():
    for variant in ("student", "practice"):
        out = page(HINTED, variant)
        assert "particular answer" not in out and "model answer" not in out
    key = page(HINTED, "answer-key")
    assert "very particular answer" in key and "the model answer, in full" in key


def test_the_key_shows_each_entry_once_and_a_draft_is_marked_as_one():
    text = paper("## Question 1: Q (4 marks)\n\n### 1(a): A (4 marks)\n\n```answer\n```\n",
                 "### 1(a) (draft)\n\nAnswer: the one answer\n")
    key = page(text, "answer-key")
    assert key.count("the one answer") == 1 and "Draft: not yet approved" in key


def test_numbers_with_a_rule_are_shown_in_the_key_as_a_marker_would_write_them():
    scheme = ("### 1(a)\n\nAnswer: 4.88 ± 0.01 m\n\n### 1(b)\n\n"
              "Answer: 0.50 ± 0.005 per minute (2 d.p.)\n")
    text = paper("## Question 1: Q (4 marks)\n\n### 1(a) (2 marks)\n\n```answer\n```\n\n"
                 "### 1(b) (2 marks)\n\n```answer\n```\n", scheme, total=4)
    key = page(text, "answer-key")
    assert "4.88 m ± 0.01" in key
    assert "0.50 per minute ± 0.005 (2 d.p.)" in key


def test_a_front_page_is_the_instructions_and_is_not_repeated_in_the_paper():
    result = read(SPECIMEN)
    from dewmark.render import render_front
    front = render_front(result, ROOT)
    assert "Instructions to candidates" in front and "Answer <strong>all</strong>" in front
    assert "Instructions to candidates" not in page(SPECIMEN)


# --- a paper is not trusted ----------------------------------------------------------------------------------------

@pytest.fixture
def folder(tmp_path):
    (tmp_path / "pictures").mkdir()
    (tmp_path / "pictures" / "ok.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
    (tmp_path.parent / f"{tmp_path.name}-secret.png").write_bytes(b"not for the page")
    return tmp_path


def test_raw_html_in_prose_is_shown_as_text_and_never_run():
    out = render_markdown('Hello <script>alert(1)</script> <img src=x onerror=alert(1)> '
                          '<b onclick="x()">b</b> <a href="https://x" onclick="y()">a</a>')
    assert "<script" not in out and "<img" not in out and "<b " not in out and "<a " not in out
    assert "&lt;script&gt;" in out and "onerror" in out    # visible, as words


def test_code_in_backticks_with_angle_brackets_is_shown_not_run():
    assert "<code>&lt;script&gt;</code>" in render_markdown("`<script>`")


def test_a_link_is_shown_as_text_with_its_address_and_a_bad_one_as_text_alone():
    web = render_markdown("[the docs](https://example.com/a?b=1&c=2)")
    assert "<a" not in web and "the docs" in web and "https://example.com/a?b=1&amp;c=2" in web
    for bad in ("javascript:alert(1)", "data:text/html,x", "file:///etc/passwd", "//evil.example"):
        out = render_markdown(f"[click]({bad})")
        assert "<a" not in out and "href" not in out and bad not in out, bad


def test_a_picture_is_embedded_only_from_inside_the_papers_own_folder(folder):
    good = render_markdown("![a small drawing](pictures/ok.svg)", folder)
    assert good.startswith('<p><img alt="a small drawing" src="data:image/svg+xml;base64,')
    for bad in ("https://evil.example/pixel.png", "//evil.example/p.png", "../" + folder.name + "-secret.png",
                "/etc/passwd", "pictures/missing.png", "C:\\secret.png", "data:image/png;base64,AAAA"):
        out = render_markdown(f"![a drawing]({bad})", folder)
        assert "<img" not in out and "picture not available" in out, bad


def test_a_picture_that_is_not_a_picture_file_is_refused(folder):
    (folder / "pictures" / "notes.txt").write_text("secret")
    assert "<img" not in render_markdown("![x](pictures/notes.txt)", folder)


def test_a_link_to_a_picture_outside_through_a_symlink_is_refused(folder):
    secret = folder.parent / f"{folder.name}-secret.png"
    try:
        (folder / "pictures" / "link.png").symlink_to(secret)
    except OSError:
        pytest.skip("this system cannot make symbolic links")
    assert "<img" not in render_markdown("![x](pictures/link.png)", folder)


def test_a_picture_that_is_undescribed_unavailable_or_remote_stops_the_build(folder):
    text = one_box("```answer\n```", extra="![](pictures/ok.svg)\n\n![a drawing](https://evil.example/a.png)\n\n"
                                          "![a map](pictures/ok.svg)")
    found = check_buildable(read(text), folder)
    assert [m.code for m in found.problems] == ["picture-undescribed", "picture-unavailable"]
    assert "evil.example" in found.problems[1].what and found.problems[0].fix


def test_pictures_in_a_hint_a_choice_and_material_are_checked_too():
    text = one_box("````choice\nA. ![](x.png)\n````", extra="```material\n![](y.png)\n```\n\n```hint\n![z](z.png)\n```")
    assert {m.code for m in check_buildable(read(text), ROOT).problems} == {
        "picture-undescribed", "picture-unavailable"}


def test_a_built_page_connects_to_nothing_and_holds_no_address_but_a_pictures():
    files = build_pages(SPECIMEN, ROOT / "dewmark" / "data")
    for name, text in files.items():
        if name.endswith(".html"):
            policy = re.search(r'Content-Security-Policy" content="([^"]*)"', text).group(1)
            assert "default-src 'none'" in policy and "connect-src" not in policy
            assert "form-action 'none'" in policy and "img-src data:" in policy
            assert not re.search(r'(src|href|action)="https?:', text), name


# --- the page model -------------------------------------------------------------------------------------

def test_the_page_model_names_the_questions_parts_and_boxes_without_any_scheme():
    model = page_model(read(SPECIMEN), "student")
    assert model["format"] == "dewmark-page/1" and model["variant"] == "student"
    assert model["exam"] == {"code": "specimen-short", "version": "1", "title": "Specimen Paper",
                             "kind": "exam", "marks": 20}
    assert model["sections"] == [{"index": 1, "title": "Section A: Short questions", "any": None,
                                  "questions": ["q1", "q2"]}]
    assert [p["name"] for p in model["questions"]["q1"]["parts"]] == ["q1a", "q1b", "q1c"]
    assert model["questions"]["q1"]["parts"][1] == {"name": "q1b", "label": "1(b)", "marks": 3, "boxes": ["q1b"]}


def test_a_part_with_no_parts_of_its_own_is_its_own_part_and_rough_work_is_not_marked():
    text = paper("## Question 1: Q (6 marks)\n\n### 1(a): A (6 marks)\n\n```answer\n```\n\n"
                 "```answer 1(a): rough (not marked)\n```\n", "### 1(a) (draft)\n")
    model = page_model(read(text), "student")
    assert model["questions"]["q1"]["parts"][0]["boxes"] == ["q1a"]


# --- building ---------------------------------------------------------------------------------------------

def test_a_build_makes_three_pages_and_the_scheme_and_always_the_same_bytes():
    first = build_pages(SPECIMEN, ROOT / "dewmark" / "data")
    assert list(first) == ["specimen-short.student.html", "specimen-short.practice.html",
                           "specimen-short.answer-key.html",
                           "dewmark_specimen-short_marking_scheme.json"]
    assert first == build_pages(SPECIMEN, ROOT / "dewmark" / "data")
    assert json.loads(first["dewmark_specimen-short_marking_scheme.json"])["format"] == "dewmark-scheme/1"
    for name, text in first.items():
        if name.endswith(".html"):
            assert balanced(text) == [] and text.startswith("<!doctype html>")


def test_the_data_block_holds_no_scheme_and_each_page_says_which_it_is():
    files = build_pages(SPECIMEN, ROOT / "dewmark" / "data")
    for variant in ("student", "practice", "answer-key"):
        text = files[f"specimen-short.{variant}.html"]
        model = json.loads(re.search(r'id="dewmark-page-model">(.*?)</script>', text, re.S).group(1))
        assert model["variant"] == variant and f'data-variant="{variant}"' in text
        assert "decimal number" not in json.dumps(model)


def test_the_band_says_what_kind_of_page_it_is():
    files = build_pages(SPECIMEN, ROOT / "dewmark" / "data")
    assert "Examination" in files["specimen-short.student.html"]
    assert "Practice version" in files["specimen-short.practice.html"]
    assert "Answer key: not for students" in files["specimen-short.answer-key.html"]


def test_a_paper_with_problems_is_refused_with_every_one_of_them():
    with pytest.raises(BuildError) as error:
        build_pages(SPECIMEN.replace("total marks: 20", "total marks: 21").replace("(3 marks)", "(4 marks)", 1),
                    ROOT)
    assert len(error.value.messages) == 2 and "marks-sum" in error.value.messages[0] + error.value.messages[1]


def test_a_paper_using_a_kind_no_page_draws_is_refused():
    with pytest.raises(BuildError) as error:
        build_pages(one_box("```match\n1. a\nA. b\n```"), ROOT)
    assert "can't be built into a page yet" in error.value.messages[0]


# --- the leak checks, on the pages the real renderer makes ------------------------------------------------------

def leaky(extra_for):
    """A renderer that is right except that it adds `extra_for(variant, paper)`."""
    real = build_module.render_paper

    def render(paper, variant, base_dir):
        return real(paper, variant, base_dir) + extra_for(variant, paper)

    return render


def test_a_renderer_that_lets_the_scheme_into_the_student_page_is_caught(monkeypatch):
    monkeypatch.setattr(build_module, "render_paper", leaky(
        lambda v, p: "<!-- " + p["scheme"]["entries"]["q1c"]["points"][0]["text"] + " -->" if v != "answer-key" else ""))
    with pytest.raises(BuildError) as error:
        build_pages(SPECIMEN, ROOT)
    said = "\n".join(error.value.messages)
    assert "not built" in said and "student page" in said and "practice page" in said
    assert "a function called `double` with one parameter" in said


def test_a_renderer_that_marks_the_right_option_is_caught_though_the_search_cannot_see_it(monkeypatch):
    monkeypatch.setattr(build_module, "render_paper", leaky(
        lambda v, p: f'<i class="right-{p["scheme"]["entries"]["q1b"]["key"][0][0]["text"]}"></i>'
        if v != "answer-key" else ""))
    with pytest.raises(BuildError) as error:
        build_pages(SPECIMEN, ROOT)
    said = "\n".join(error.value.messages)
    assert "the student page changed when the marking scheme and hints did: 1(b)" in said


def test_a_renderer_that_lets_a_hint_into_the_student_page_is_caught(monkeypatch):
    real = build_module.render_paper

    def render(paper, variant, base_dir):
        out = real(paper, variant, base_dir)
        if variant == "student":
            out += "".join(f"<!-- {b['body']} -->" for b in paper["blocks"] if b["type"] == "hint")
        return out

    monkeypatch.setattr(build_module, "render_paper", render)
    with pytest.raises(BuildError) as error:
        build_pages(HINTED, ROOT)
    said = "\n".join(error.value.messages)
    assert "hint text from a hint is in the student page" in said and "the hints" in said


def test_a_hint_is_no_leak_on_the_practice_page_where_it_belongs():
    assert build_pages(HINTED, ROOT)       # builds: the practice page shows its hint on purpose


def test_a_refused_build_writes_nothing(tmp_path, monkeypatch):
    exam = tmp_path / "paper.exam.md"
    exam.write_text(SPECIMEN, encoding="utf-8")
    monkeypatch.setattr(build_module, "render_paper", leaky(
        lambda v, p: "<!-- decimal number -->" if v == "student" else ""))
    with pytest.raises(BuildError):
        build(exam, tmp_path / "out")
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("path", [ROOT / "dewmark" / "data" / "specimen.exam.md"] + PDP,
                         ids=lambda p: p.name)
def test_every_sample_builds_with_both_leak_checks_run_on_the_real_pages(path, tmp_path):
    names = build(path, tmp_path)
    assert len(names) == 4 and all((tmp_path / n).is_file() for n in names)
    assert not any(n.endswith(".html") and "decimal" in (tmp_path / n).read_text() and "student" in n
                   for n in names if path.name.startswith("specimen"))


# --- the command line ---------------------------------------------------------------------------------------------

def test_build_from_the_command_line(tmp_path, capsys):
    exam = tmp_path / "paper.exam.md"
    exam.write_text(SPECIMEN, encoding="utf-8")
    assert main(["build", str(exam)]) == 0 and "builds cleanly; no files written" in capsys.readouterr().out
    assert not (tmp_path / "out").exists()
    assert main(["build", str(exam), "-o", str(tmp_path / "out")]) == 0
    assert sorted(p.name for p in (tmp_path / "out").iterdir()) == [
        "dewmark_specimen-short_marking_scheme.json", "specimen-short.answer-key.html",
        "specimen-short.practice.html", "specimen-short.student.html"]


def test_build_refuses_a_paper_with_problems_and_one_whose_lock_it_breaks(tmp_path, capsys):
    exam = tmp_path / "paper.exam.md"
    exam.write_text(SPECIMEN, encoding="utf-8")
    assert main(["lock", str(exam), "--sitting", "A"]) == 0
    capsys.readouterr()
    exam.write_text(SPECIMEN.replace("(3 marks)", "(4 marks)", 1).replace("(12 marks)", "(13 marks)")
                    .replace("total marks: 20", "total marks: 21"), encoding="utf-8")
    assert main(["build", str(exam), "-o", str(tmp_path / "out")]) == 1
    shown = capsys.readouterr().out
    assert "not built" in shown and "locked-marks-changed" in shown
    assert not (tmp_path / "out").exists()
