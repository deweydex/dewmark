"""Tests for the scheme as JSON (dewmark/scheme_json.py) and for the last two
layers that keep it off the student page (dewmark/secrecy.py,
docs/EXAM_FORMAT.md §4.5).

There is no renderer for the new format yet, so the secrecy layers are tried
on small renderers written here: one that builds the page as it should be
built, and several that each let the scheme through a different way. The
point of the pair of layers is that between them nothing gets past, and
the tests say which layer catches which: the search finds a string wherever
it is written, and the mutation test finds what the search cannot see, a key
too short to look for, one only implied by a class on an option, or one
encoded.
"""

import base64
import html
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from dewmark import secrecy  # noqa: E402
from dewmark.__main__ import main  # noqa: E402
from dewmark.package import split_halves  # noqa: E402
from dewmark.reader import read  # noqa: E402
from dewmark.scheme_json import dumps, scheme_json  # noqa: E402
from dewmark.secrecy import find_leaks, mutate, mutation_test, scheme_strings  # noqa: E402

SPECIMEN = (ROOT / "dewmark" / "data" / "specimen.exam.md").read_text(encoding="utf-8")
FULL = (ROOT / "tests" / "fixtures" / "specimen.exam.md").read_text(encoding="utf-8")
PDP = sorted((ROOT / "samples" / "pdp-5n2927").glob("*.exam.md"))


# --- renderers: one right, several wrong ---------------------------------------------

def page_of(text):
    """What students get: the paper half, and nothing from the scheme."""
    return "<html><body><pre>" + html.escape(split_halves(text, reference=False)[0]) + "</pre>"


def clean(text):
    return page_of(text) + "</body></html>"


def entry_of(text, name):
    return read(text)["scheme"]["entries"][name]


def leaks_a_point_in_a_comment(text):
    return page_of(text) + f"<!-- {entry_of(text, 'q1c')['points'][0]['text']} --></body></html>"


def leaks_the_scheme_in_a_data_block(text):
    data = json.dumps(scheme_json(read(text))).replace("<", "\\u003c")
    return page_of(text) + f'<script type="application/json" id="data">{data}</script></body></html>'


def leaks_a_point_escaped_for_html(text):
    return page_of(text) + f"<p hidden>{html.escape(entry_of(text, 'q1c')['points'][1]['text'])}</p></body></html>"


def leaks_a_point_in_capitals_and_spacing(text):
    point = entry_of(text, "q1c")["points"][2]["text"].upper().replace(" ", "   ")
    return page_of(text) + f"<p hidden>{point}</p></body></html>"


def leaks_a_model_answer_by_its_start(text):
    return page_of(text) + f"<p hidden>{entry_of(text, 'q1c')['points'][0]['text'][:30]}…</p></body></html>"


def marks_the_right_option(text):
    paper = read(text)
    key = entry_of(text, "q1b")["key"][0][0]["text"]
    options = paper["boxes"]["q1b"]["inner"]["options"]
    items = "".join(f'<li class="{"correct" if letter == key else ""}">{letter}. {html.escape(t)}</li>'
                    for letter, t in options.items())
    return page_of(text) + f"<ol>{items}</ol></body></html>"


def prints_a_short_key(text):
    return page_of(text) + f'<input data-answer="{entry_of(text, "q1a")["key"][0][0]["text"]}"></body></html>'


def hides_the_scheme_in_base64(text):
    scheme = text[text.index("# Marking scheme"):]
    return page_of(text) + f'<script>var d="{base64.b64encode(scheme.encode()).decode()}"</script></body></html>'


def keeps_only_the_first_entry_secret_in_the_page(text):
    return page_of(text) + f"<b hidden>{entry_of(text, 'q2b')['points'][0]['text']}</b></body></html>"


# --- the scheme as JSON ------------------------------------------------------------------

def test_the_scheme_json_holds_the_paper_the_names_and_every_entry():
    scheme = scheme_json(read(SPECIMEN))
    assert scheme["format"] == "dewmark-scheme/1" and scheme["total"] == 20
    assert scheme["paper"] == {"code": "specimen-short", "version": "1", "kind": "exam",
                               "title": "Specimen Paper", "module": "Introduction to Computing",
                               "module code": "5N0000"}
    assert [e["name"] for e in scheme["entries"]] == ["q1", "q1a", "q1b", "q1c", "q2", "q2a", "q2b"]
    assert scheme["names"]["boxes"]["q1b"]["options"]["B"] == "total_cost"
    assert scheme["names"]["units"]["q1c"]["marks"] == 6 and scheme["drafts"] == []


def test_each_entry_carries_its_marks_its_box_its_key_and_its_method():
    entries = {e["name"]: e for e in scheme_json(read(SPECIMEN))["entries"]}
    one_a = entries["q1a"]
    assert (one_a["marks"], one_a["box"], one_a["key"], one_a["method"]) == \
        (3, "q1a", [[{"text": "8"}]], "total")
    assert entries["q1c"]["method"] == "points" and entries["q1c"]["box"] is None
    assert [p["marks"] for p in entries["q1c"]["points"]] == [2, 2, 2]
    assert entries["q2a"]["key"] == [[{"text": "float"}, {"text": "decimal number"}],
                                     [{"text": "string"}, {"text": "text"}]]


def test_numbers_with_a_rule_are_numbers_and_everything_else_stays_text():
    entries = {e["name"]: e for e in scheme_json(read(FULL))["entries"]}
    assert entries["q2a"]["key"] == [[{"number": 4.88, "written": "4.88", "tolerance": 0.01,
                                       "percent": False, "unit": "m"}]]
    assert entries["q5b"]["key"][0][0]["dp"] == 2 and entries["q5b"]["key"][0][0]["written"] == "0.50"
    assert entries["q5f"]["key"] == [[{"text": "1 B, 2 A, 3 C"}]]
    assert entries["q3b"]["any_order"] is True
    zero = read(SPECIMEN.replace("Answer: 8", "Answer: 0123"))
    assert scheme_json(zero)["entries"][1]["key"] == [[{"text": "0123"}]]


def test_criteria_bands_tests_models_and_drafts_come_through():
    entries = {e["name"]: e for e in scheme_json(read(FULL))["entries"]}
    six = entries["q6"]
    assert six["method"] == "criteria" and six["criteria"][0]["name"] == "Argument and structure"
    assert six["criteria"][0]["bands"][0] == {"low": 13, "high": 15,
                                              "text": "one position, sustained; each paragraph advances it"}
    assert entries["q1b.i"]["model_is_code"] and entries["q1b.i"]["model"].startswith("def longer_word")
    assert entries["q1b.ii"]["draft"] is True and len(entries["q1b.ii"]["tests"]) == 2
    assert entries["q3a"]["guidance"] == ["An expanded answer earns no marks."]


def test_the_json_is_stable_and_reads_back_as_it_was_written():
    scheme = scheme_json(read(FULL))
    text = dumps(scheme)
    assert text == dumps(scheme_json(read(FULL))) and text.endswith("}\n")
    assert json.loads(text) == scheme


def test_every_pdp_paper_gives_a_scheme_with_its_drafts_listed():
    for path in PDP:
        scheme = scheme_json(read(path.read_text(encoding="utf-8")))
        assert scheme["total"] == 60 and scheme["drafts"] and scheme["entries"]
        assert set(scheme["drafts"]) <= {e["name"] for e in scheme["entries"]}
        json.loads(dumps(scheme))


def test_the_scheme_command_writes_the_json_and_refuses_a_paper_with_problems(tmp_path, capsys):
    paper = tmp_path / "paper.exam.md"
    paper.write_text(SPECIMEN, encoding="utf-8")
    out = tmp_path / "scheme.json"
    assert main(["scheme", str(paper), "-o", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["format"] == "dewmark-scheme/1"
    assert "Keep it away from students." in capsys.readouterr().out
    assert main(["scheme", str(paper)]) == 0 and '"format": "dewmark-scheme/1"' in capsys.readouterr().out
    paper.write_text(SPECIMEN.replace("total marks: 20", "total marks: 21"), encoding="utf-8")
    assert main(["scheme", str(paper), "-o", str(tmp_path / "no.json")]) == 1
    assert not (tmp_path / "no.json").exists()


# --- layer 3: the search ------------------------------------------------------------------

def test_the_scheme_is_listed_a_string_at_a_time_with_what_can_be_searched():
    strings = scheme_strings(SPECIMEN)
    assert len(strings) == 11 and sum(s["searchable"] for s in strings) == 6
    key = next(s for s in strings if s["text"] == "8")
    assert key == {"text": "8", "where": "1(a)", "kind": "key", "searchable": False,
                   "looking for": []}
    assert any(s["kind"] == "point" and s["where"] == "2(b)" for s in strings)


def test_text_between_the_dividing_line_and_the_first_entry_is_a_secret_too():
    text = SPECIMEN.replace("# Marking scheme\n", "# Marking scheme\n\nRemember: question 2 is the hard one.\n")
    notes = [s for s in scheme_strings(text) if s["kind"] == "scheme text"]
    assert [n["text"] for n in notes] == ["Remember: question 2 is the hard one."]
    assert notes[0]["searchable"]


def test_a_point_that_opens_with_the_questions_own_words_is_not_a_leak():
    said = ("Explain why a program should check that a number has been typed, "
            "then give a reason the check helps")
    text = SPECIMEN.replace("a sum on something that is not a number causes an error", said)
    point = next(s for s in scheme_strings(text) if s["where"] == "2(b)" and s["kind"] == "point")
    assert point["searchable"] and len(point["looking for"]) == 2      # the whole and the end; the start is shown
    assert find_leaks(clean(text), scheme_strings(text)) == []
    leaked = clean(text).replace("</body>", f"<p hidden>{said}</p></body>")
    assert [f["where"] for f in find_leaks(leaked, scheme_strings(text))] == ["2(b)"]


def test_the_end_of_a_long_string_is_found_when_a_page_shows_only_that():
    text = SPECIMEN.replace("the function returns twice the parameter",
                            "the function returns twice the parameter it was given, whatever the number")
    long_string = next(s for s in scheme_strings(text) if "whatever the number" in s["text"])
    end = long_string["looking for"][-1]
    assert len(end) == 30 and end.endswith("whatever the number")
    assert find_leaks(page_of(text) + f"<p hidden>… {end}</p>", [long_string])[0]["kind"] == "point"
    assert find_leaks(page_of(text) + "<p hidden>whatever the number</p>", [long_string]) == []


def test_a_string_the_paper_already_shows_is_not_searched_for():
    text = SPECIMEN.replace("Answer: 8", "Answer: price * 2").replace(
        "State what the code prints.", "State what the code prints: price * 2 is the expression.")
    key = next(s for s in scheme_strings(text) if s["kind"] == "key" and s["where"] == "1(a)")
    assert key["searchable"] is False


@pytest.mark.parametrize("renderer", [leaks_a_point_in_a_comment, leaks_the_scheme_in_a_data_block,
                                      leaks_a_point_escaped_for_html,
                                      leaks_a_point_in_capitals_and_spacing,
                                      leaks_a_model_answer_by_its_start])
def test_the_search_finds_a_string_wherever_the_page_writes_it(renderer):
    found = find_leaks(renderer(SPECIMEN), scheme_strings(SPECIMEN))
    assert found, renderer.__name__
    assert all(f["kind"] in ("point", "key", "model answer") and f["found as"] for f in found)


def test_the_search_looks_inside_the_data_block_the_old_check_skipped():
    found = find_leaks(leaks_the_scheme_in_a_data_block(SPECIMEN), scheme_strings(SPECIMEN))
    assert len(found) >= 5 and {"point", "key"} <= {f["kind"] for f in found}


def test_a_string_with_quotes_in_a_data_block_is_found_as_json_escaped():
    text = SPECIMEN.replace("a function called `double` with one parameter",
                            'a function called "double" with one parameter')
    found = find_leaks(leaks_the_scheme_in_a_data_block(text), scheme_strings(text))
    assert [f["found as"] for f in found if "double" in f["text"]] == ["JSON-escaped"]
    escaped = find_leaks(leaks_a_point_escaped_for_html(text.replace("the function returns twice the parameter",
                                                                    "it returns <b>twice</b> & more")),
                         scheme_strings(text.replace("the function returns twice the parameter",
                                                     "it returns <b>twice</b> & more")))
    assert [f["found as"] for f in escaped] == ["HTML-escaped"]


def test_the_search_finds_nothing_on_a_page_built_as_it_should_be():
    for text in (SPECIMEN, FULL):
        assert find_leaks(clean(text), scheme_strings(text)) == []


@pytest.mark.parametrize("renderer", [marks_the_right_option, prints_a_short_key,
                                      hides_the_scheme_in_base64])
def test_the_search_cannot_see_a_key_that_is_short_or_implied_or_encoded(renderer):
    assert find_leaks(renderer(SPECIMEN), scheme_strings(SPECIMEN)) == [], renderer.__name__


# --- layer 4: the mutation test ---------------------------------------------------------------

def test_the_mutated_scheme_reads_as_the_paper_does_with_nothing_of_the_original():
    for text in (SPECIMEN, FULL):
        mutated, changed = mutate(text)
        after, before = read(mutated), read(text)
        assert changed == len(before["scheme"]["entries"])
        assert after["messages"].problems == [] and list(after["boxes"]) == list(before["boxes"])
        assert split_halves(mutated, reference=False)[0] == split_halves(text, reference=False)[0]
        scheme_half = mutated[mutated.index("# Marking scheme"):]
        for item in scheme_strings(text):
            if item["searchable"]:
                assert item["text"] not in scheme_half, item


def test_every_key_is_changed_to_a_different_valid_one():
    mutated, _ = mutate(FULL)
    before = {e["name"]: e for e in scheme_json(read(FULL))["entries"]}
    after = {e["name"]: e for e in scheme_json(read(mutated))["entries"]}
    for name, entry in before.items():
        if entry["key"]:
            assert after[name]["key"] != entry["key"], name
    assert after["q1c"]["key"] == [[{"text": "C"}]]               # choice: the next option
    assert after["q5f"]["key"] == [[{"text": "1 C, 2 B, 3 D"}]]    # match: the next option for each
    assert after["q5d"]["key"][0] != before["q5d"]["key"][0]       # drop-down: another of its choices


def test_the_same_file_always_mutates_the_same_way():
    assert mutate(FULL) == mutate(FULL)


def test_only_the_entries_asked_for_are_changed_and_the_rest_are_kept_as_written():
    mutated, changed = mutate(SPECIMEN, only={"q1c"})
    assert changed == 1
    before, after = read(SPECIMEN)["scheme"]["entries"], read(mutated)["scheme"]["entries"]
    assert after["q1c"]["points"] != before["q1c"]["points"]
    said = lambda entry: [(p["marks"], p["text"]) for p in entry["points"]]   # noqa: E731
    for name in before:
        if name != "q1c":
            assert after[name]["key"] == before[name]["key"] and said(after[name]) == said(before[name])


def test_text_before_the_first_entry_is_dropped_when_all_change_and_kept_when_one_does():
    text = SPECIMEN.replace("# Marking scheme\n", "# Marking scheme\n\nA private note.\n")
    assert "A private note." not in mutate(text)[0]
    assert "A private note." in mutate(text, only={"q1c"})[0]


def test_reference_cards_students_see_stay_with_the_paper():
    text = SPECIMEN.replace("# Marking scheme", "# Reference\n\n## Card\n\nCARD-TEXT\n\n# Marking scheme")
    mutated, _ = mutate(text)
    assert "CARD-TEXT" in mutated and mutation_test(text, clean)["ok"]


def test_a_paper_with_no_scheme_has_nothing_to_mutate():
    practice = SPECIMEN.split("# Marking scheme")[0].replace("kind: exam", "kind: practice")
    assert mutate(practice) == (practice, 0)
    assert mutation_test(practice, clean) == {
        "ok": True, "reason": "the paper has no marking scheme entries to change", "culprits": []}


@pytest.mark.parametrize("text", [SPECIMEN, FULL] + [p.read_text(encoding="utf-8") for p in PDP],
                         ids=["specimen", "full", "pdp-2027", "pdp-practice-1", "pdp-practice-2", "pdp-sample"])
def test_a_page_built_as_it_should_be_does_not_change_when_the_scheme_does(text):
    assert mutation_test(text, clean) == {"ok": True, "reason": "", "culprits": []}


@pytest.mark.parametrize("renderer, culprit", [
    (leaks_a_point_in_a_comment, "1(c)"),
    (leaks_a_point_escaped_for_html, "1(c)"),
    (leaks_a_point_in_capitals_and_spacing, "1(c)"),
    (marks_the_right_option, "1(b)"),
    (prints_a_short_key, "1(a)"),
    (keeps_only_the_first_entry_secret_in_the_page, "2(b)"),
])
def test_the_mutation_test_catches_a_leak_and_says_which_entry_it_came_from(renderer, culprit):
    result = mutation_test(SPECIMEN, renderer)
    assert result["ok"] is False and result["culprits"] == [culprit], renderer.__name__
    assert result["reason"] == "the student page changed when the marking scheme did"


@pytest.mark.parametrize("renderer", [leaks_the_scheme_in_a_data_block, hides_the_scheme_in_base64])
def test_the_mutation_test_catches_a_whole_scheme_however_it_is_carried(renderer):
    result = mutation_test(SPECIMEN, renderer)
    assert result["ok"] is False and len(result["culprits"]) >= 5


def test_between_them_the_two_layers_catch_every_leak_the_renderers_here_make():
    for renderer in (leaks_a_point_in_a_comment, leaks_the_scheme_in_a_data_block,
                     leaks_a_point_escaped_for_html, leaks_a_point_in_capitals_and_spacing,
                     leaks_a_model_answer_by_its_start, marks_the_right_option, prints_a_short_key,
                     hides_the_scheme_in_base64, keeps_only_the_first_entry_secret_in_the_page):
        found = find_leaks(renderer(SPECIMEN), scheme_strings(SPECIMEN))
        assert found or not mutation_test(SPECIMEN, renderer)["ok"], renderer.__name__


def test_a_paper_with_problems_is_not_tested_and_says_why():
    broken = SPECIMEN.replace("total marks: 20", "total marks: 21")
    assert mutation_test(broken, clean) == {
        "ok": False, "reason": "the paper has problems, so it cannot be built", "culprits": []}


def test_a_mutation_that_breaks_the_paper_is_the_testers_fault_not_the_renderers(monkeypatch):
    monkeypatch.setattr(secrecy, "mutate", lambda text, only=None: (text.replace("Answer: 8", "Answer: ", 1)
                                                                    .replace("### 1(b)", "### 9(z)"), 1))
    result = mutation_test(SPECIMEN, clean)
    assert result["ok"] is False and result["reason"].startswith("the nonsense version of the scheme")
