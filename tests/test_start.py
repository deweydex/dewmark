"""The builder's half of step 4's second slice: the band and its branding,
the two screens before the paper, the list of what a paper needs, and the
reading settings the page draws. What the page does with them is rehearsed in
a browser (tests/browser/test_page.py); what the colours are is checked in
tests/test_page_css.py.
"""

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

from dewmark import build as build_module  # noqa: E402
from dewmark.build import (BuildError, READING, build_page, build_pages, needs,  # noqa: E402
                           page_model, reading_controls)
from dewmark.reader import read  # noqa: E402
from dewmark.render import LOGO_LIMIT, check_buildable, logo_problem  # noqa: E402

SPECIMEN = (ROOT / "dewmark" / "data" / "specimen.exam.md").read_text(encoding="utf-8")
HEADER = """\
---
dewmark: 1
code: start-test
kind: exam
title: Start Test
module: Testing
module code: 5N0000
total marks: 4
time allowed: 1 hour
{extra}---
"""
BODY = "## Question 1: Q (4 marks)\n\n```answer\n```\n\n# Marking scheme\n### 1 (draft)\n"


def paper(extra="", body=BODY):
    return HEADER.format(extra=extra) + body


def student_page(text, base=ROOT):
    return build_pages(text, base)["start-test.student.html"]


# --- the band and its branding ------------------------------------------------------------

def test_the_band_names_the_institution_college_module_code_and_session():
    text = paper("institution: Dublin and Dún Laoghaire ETB\ncollege: Dublin College Dundrum\n"
                 "session: 2026–2027\n")
    band = re.search(r'<header class="dm-band.*?</header>', student_page(text), re.S).group(0)
    assert "Dublin and Dún Laoghaire ETB · Dublin College Dundrum" in band
    assert "Testing (5N0000)" in band and "2026–2027" in band
    assert "Time allowed: 1 hour" in band and "Total marks: 4" in band
    assert "Examination" in band and "<h1" in band


def test_a_band_with_no_branding_has_no_empty_line_or_picture():
    band = re.search(r'<header class="dm-band.*?</header>', student_page(paper()), re.S).group(0)
    assert "dm-band-org" not in band and "<img" not in band and " · ·" not in band


def test_hostile_words_in_the_branding_are_shown_as_text():
    text = paper('institution: <script>alert(1)</script>\ncollege: "><img src=x onerror=1>\n')
    band = re.search(r'<header class="dm-band.*?</header>', student_page(text), re.S).group(0)
    assert "<script" not in band and "<img" not in band and "&lt;script&gt;" in band


@pytest.fixture
def folder(tmp_path):
    (tmp_path / "pictures").mkdir()
    (tmp_path / "pictures" / "logo.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>')
    (tmp_path / "pictures" / "big.png").write_bytes(b"x" * (LOGO_LIMIT + 1))
    (tmp_path / "pictures" / "notes.txt").write_text("not a picture")
    return tmp_path


def test_a_logo_is_carried_in_the_band_with_a_description(folder):
    text = paper("institution: Dublin ETB\nlogo: pictures/logo.svg\n")
    band = re.search(r'<header class="dm-band.*?</header>', student_page(text, folder), re.S).group(0)
    assert re.search(r'<img class="dm-band-logo" alt="Dublin ETB logo" src="data:image/svg\+xml;base64,', band)


def test_a_logo_with_no_institution_is_described_as_a_logo(folder):
    band = re.search(r'<header class="dm-band.*?</header>',
                     student_page(paper("logo: pictures/logo.svg\n"), folder), re.S).group(0)
    assert 'alt="Logo"' in band


@pytest.mark.parametrize("logo, code", [
    ("pictures/missing.svg", "logo-unavailable"), ("pictures/notes.txt", "logo-unavailable"),
    ("../outside.svg", "logo-unavailable"), ("/etc/hostname", "logo-unavailable"),
    ("https://example.com/logo.svg", "logo-unavailable"), ("pictures/big.png", "logo-too-big")])
def test_a_logo_that_cannot_go_in_the_page_stops_the_build(folder, logo, code):
    found = check_buildable(read(paper(f"logo: {logo}\n")), folder)
    assert [m.code for m in found.problems] == [code]
    assert found.problems[0].fix and logo.split("/")[-1] in found.problems[0].what
    with pytest.raises(BuildError):
        build_pages(paper(f"logo: {logo}\n"), folder)


def test_the_limit_on_a_logo_is_150_kilobytes():
    assert LOGO_LIMIT == 150 * 1024
    assert logo_problem({}, ROOT) is None


# --- the two screens ------------------------------------------------------------------------------

def test_a_page_has_two_screens_before_the_paper_in_order_and_the_paper_is_hidden():
    page = student_page(paper())
    start, before, app = page.index('id="dm-start"'), page.index('id="dm-before"'), page.index('id="dm-app"')
    assert start < before < app
    assert re.search(r'<div id="dm-app" hidden>', page) and re.search(r'id="dm-before"[^>]*hidden', page)
    assert 'id="dm-start"' in page and not re.search(r'id="dm-start"[^>]*hidden', page)


def test_the_first_screen_has_the_details_the_settings_and_what_the_paper_needs():
    page = student_page(paper())
    start = page[page.index('id="dm-start"'):page.index('id="dm-before"')]
    assert 'data-detail="full name"' in start and 'data-detail="student number"' in start
    assert 'id="dm-checklist"' in start and "Reading settings" in start and "More settings" in start
    assert 'id="dm-next"' in start and "Instructions to candidates" not in start
    assert 'id="dm-restore"' in start and re.search(r'id="dm-restore"[^>]*hidden', start)


def test_the_second_screen_has_the_instructions_the_answer_file_the_time_and_begin():
    page = build_pages(SPECIMEN, ROOT / "dewmark" / "data")["specimen-short.student.html"]
    before = page[page.index('id="dm-before"'):page.index('id="dm-app"')]
    assert "Instructions to candidates" in before and "Answer <strong>all</strong>" in before
    assert 'id="dm-choose-file"' in before and "Time allowed: 1 hour." in before
    assert 'id="dm-begin"' in before and 'id="dm-back"' in before
    assert "Press Begin when your invigilator tells you to start." in before


def test_the_wording_under_begin_depends_on_the_page():
    files = build_pages(SPECIMEN, ROOT / "dewmark" / "data")
    assert "invigilator tells you to start" in files["specimen-short.student.html"]
    for name in ("practice", "answer-key"):
        assert "Press Begin when you are ready." in files[f"specimen-short.{name}.html"]


def test_the_answer_key_has_no_place_to_choose_a_file():
    page = build_pages(SPECIMEN, ROOT / "dewmark" / "data")["specimen-short.answer-key.html"]
    assert 'id="dm-choose-file"' not in page and "saves nothing, and has no answer file" in page


def test_the_number_example_is_the_hint_and_is_escaped():
    page = student_page(paper("number example: D00123456\n"))
    assert "As on your student card, for example D00123456." in page
    page = student_page(paper('number example: <b onclick="x()">\n'))
    assert '<b onclick' not in page and "&lt;b onclick" in page
    assert "As on your student card." in student_page(paper())


def test_every_page_has_the_aa_button_the_drawer_and_the_ruler():
    for name, page in build_pages(SPECIMEN, ROOT / "dewmark" / "data").items():
        if name.endswith(".html"):
            assert 'id="dm-aa"' in page and 'id="dm-drawer"' in page and 'id="dm-ruler"' in page
            assert 'role="dialog" aria-modal="true"' in page


# --- what the paper needs --------------------------------------------------------------------------

def test_a_paper_with_no_python_needs_only_itself_its_fonts_and_saving():
    keys = [key for key, *_ in needs(read(paper()), "student")]
    assert keys == ["paper", "fonts", "storage", "file"]


def test_a_paper_with_a_python_box_lists_python_and_where_it_comes_from():
    text = paper(body=BODY.replace("```answer\n```", "```python exec\nprint(1)\n```"))
    items = needs(read(text), "student")
    assert [key for key, *_ in items] == ["paper", "fonts", "python", "storage", "file"]
    assert dict((k, d) for k, _, d, _ in items)["python"] == "From this file"
    online = paper("python from: internet\n", BODY.replace("```answer\n```", "```python exec\nprint(1)\n```"))
    assert dict((k, d) for k, _, d, _ in needs(read(online), "student"))["python"] == "From the internet"


def test_packages_and_set_up_code_are_listed_when_the_paper_declares_them():
    body = BODY.replace("```answer\n```", "```python setup\nimport math\n```\n\n```python exec\nprint(1)\n```")
    items = needs(read(paper("python packages: pandas, sqlite3\n", body)), "student")
    names = {key: label for key, label, _, _ in items}
    assert names["packages"] == "Packages: pandas, sqlite3" and names["setup"] == "Set-up code"


def test_the_answer_key_lists_nothing_about_saving():
    assert [key for key, *_ in needs(read(paper()), "answer-key")] == ["paper", "fonts"]


def test_each_item_names_a_check_the_page_has():
    script = (ROOT / "assets" / "page-start.js").read_text(encoding="utf-8")
    declared = set(re.findall(r"^  (\w+): ", script[script.index("const CHECKS"):script.index("async function runChecks")], re.M))
    used = {check for _, _, _, check in needs(read(paper(body=BODY.replace("```answer\n```", "```python exec\nx\n```"))), "student")}
    assert used <= declared


def test_the_list_is_drawn_with_a_state_in_words_and_not_in_colour_alone():
    page = student_page(paper())
    rows = re.findall(r'<li data-need="[^"]*" data-check="[^"]*" data-state="checking">', page)
    assert len(rows) == 4 and page.count('<span class="dm-cw">Checking</span>') == 4


# --- the reading settings ---------------------------------------------------------------------------

def test_the_page_model_carries_the_description_of_each_setting():
    model = page_model(read(paper()), "student")
    assert model["reading"] == READING
    assert set(READING) == {"font", "size", "scheme", "ruler", "lineHeight", "spacing", "width",
                            "motion", "codeSize", "codeScheme", "wrap"}


def test_every_choice_the_page_draws_is_one_the_description_allows():
    page = student_page(paper())
    for key, spec in READING.items():
        if "options" in spec:
            drawn = re.findall(rf'name="drawer-{key}" value="([^"]*)"', page)
            assert drawn == spec["options"], key
    for key, spec in READING.items():
        if "min" in spec:
            assert re.search(rf'data-setting="{key}" min="{spec["min"]}" max="{spec["max"]}" step="{spec["step"]}"', page)


def test_the_first_screen_shows_four_settings_and_the_rest_sit_under_more_settings():
    key = reading_controls("start", "key")
    more = reading_controls("start", "more")
    assert set(re.findall(r'data-setting="(\w+)"', key)) == {"font", "size", "scheme", "ruler"}
    assert set(re.findall(r'data-setting="(\w+)"', more)) == {
        "lineHeight", "spacing", "width", "motion", "codeSize", "codeScheme", "wrap"}
    page = student_page(paper())
    start = page[page.index('id="dm-start"'):page.index('id="dm-before"')]
    assert start.index("More settings") < start.index('data-setting="lineHeight"')
    assert start.index('data-setting="ruler"') < start.index("More settings")


def test_the_drawer_has_every_setting():
    drawer = reading_controls("drawer", "all")
    assert set(re.findall(r'data-setting="(\w+)"', drawer)) == set(READING)


def test_the_same_setting_drawn_twice_never_shares_a_radio_group():
    page = student_page(paper())
    names = re.findall(r'<input type="radio" name="([^"]+)"', page)
    assert {n.split("-")[0] for n in names} == {"start", "drawer"}
    assert all(re.match(r"(start|drawer)-\w+$", n) for n in names)
    ids = re.findall(r'\bid="([^"]+)"', page)
    assert len(ids) == len(set(ids)), "an id is used twice: " + str([i for i in ids if ids.count(i) > 1])


def test_a_font_choice_shows_its_own_name_in_its_own_face():
    drawer = reading_controls("drawer", "all")
    for face in ("serif", "sans", "lexend", "dyslexic"):
        assert f"dm-sample dm-f-{face}" in drawer
    assert "Lexend" in drawer and "OpenDyslexic" in drawer


def test_the_reading_fonts_are_carried_in_the_page_and_the_policy_allows_only_those():
    page = student_page(paper())
    assert page.count("@font-face") == 4 and page.count("data:font/woff2;base64,") == 4
    policy = re.search(r'Content-Security-Policy" content="([^"]*)"', page).group(1)
    assert "font-src data:" in policy and "default-src 'none'" in policy and "connect-src" not in policy


def test_nothing_in_the_settings_or_the_screens_adds_an_address():
    for name, page in build_pages(SPECIMEN, ROOT / "dewmark" / "data").items():
        if name.endswith(".html"):
            assert not re.search(r'(src|href|action)="https?:', page), name
            assert not re.search(r"url\((?!data:)", page), name


def test_the_script_is_the_three_files_in_order_and_never_writes_markup():
    """What a student or an answer file holds goes into the page as text only."""
    assert build_module.SCRIPTS == ("page.js", "page-reading.js", "page-start.js")
    for name in build_module.SCRIPTS:
        script = (ROOT / "assets" / name).read_text(encoding="utf-8")
        assert not re.search(r"\.(innerHTML|outerHTML)\s*=|insertAdjacentHTML|document\.write|eval\(", script), name


def test_the_script_never_writes_the_reading_settings_before_they_change():
    """Reading settings are written by changeSetting and persistReading only."""
    script = (ROOT / "assets" / "page-reading.js").read_text(encoding="utf-8")
    writes = [m.start() for m in re.finditer(r"localStorage\.setItem", script)]
    assert len(writes) == 1
    assert script.rfind("function ", 0, writes[0]) == script.index("function persistReading")


def test_a_built_page_is_the_same_every_time():
    assert build_pages(SPECIMEN, ROOT / "dewmark" / "data") == build_pages(SPECIMEN, ROOT / "dewmark" / "data")
