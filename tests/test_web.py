"""Tests for the browser's door into the reader (dewmark/web.py) and for the
checker page's build (dev/build_site.py).

web.py takes text and returns JSON text so the browser and the command line
can be compared string for string (tests/browser/test_checker.py does that
in Chromium). Here: what the JSON holds, and that the sources the page
embeds are enough on their own, run by a bare interpreter that has only the
standard library and none of this repository around it.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "dev"))
import build_site  # noqa: E402
from dewmark import READER_VERSION, web  # noqa: E402
from dewmark.package import PAPER_BEGIN, PAPER_END, split_halves  # noqa: E402

SPECIMEN = (ROOT / "dewmark" / "data" / "specimen.exam.md").read_text(encoding="utf-8")


def test_the_modes_are_listed_with_the_details_a_copy_needs():
    modes = json.loads(web.modes_json())
    about = modes.pop()
    assert [m["key"] for m in modes] == ["copy", "tidy", "plain", "udl", "invite"]
    assert all(m["label"] and m["summary"] for m in modes)
    assert about == {"about": ["code", "kind", "title", "module", "module code",
                               "total marks", "time allowed"]}


def test_check_gives_a_summary_and_every_message_as_plain_data():
    clean = json.loads(web.check_json(SPECIMEN))
    assert clean["messages"] == []
    assert clean["summary"] == {"questions": 2, "boxes": 5, "rough": 0, "marks": 20,
                                "entries": 7, "drafts": 0, "title": "Specimen Paper",
                                "code": "specimen-short", "kind": "exam",
                                "kinds": {"answer": 2, "blanks": 1, "choice": 1, "python exec": 1}}
    broken = json.loads(web.check_json(SPECIMEN.replace("(3 marks)", "(4 marks)", 1)))
    [message] = broken["messages"]
    assert message["code"] == "marks-sum" and message["level"] == "problem"
    assert message["line"] == 21 and message["where"] == "Question 1"
    assert message["what"].startswith("Question 1's parts add up to 13 marks")
    assert set(message) == {"code", "line", "what", "fix", "where", "level"}


def test_the_same_text_always_gives_the_same_json():
    assert web.check_json(SPECIMEN) == web.check_json(SPECIMEN)
    assert web.version() == READER_VERSION


def test_a_package_comes_back_with_its_findings_and_what_was_left_out():
    made = json.loads(web.package_json("tidy", SPECIMEN))
    assert made["text"].startswith("THIS CONTAINS YOUR EXAM PAPER.") and made["left_out"]
    assert "Answer: 8" not in made["text"] and made["problems"] == [] and made["findings"] == []
    found = json.loads(web.package_json("tidy", SPECIMEN.replace("Read this code.", "Mail jo@college.ie.")))
    assert [f["what"] for f in found["findings"]] == ["an e-mail address"]


def test_a_copy_package_without_its_details_makes_no_text_and_says_what_is_missing():
    made = json.loads(web.package_json("copy", "Question one (5 marks)", "{}"))
    assert made["text"] == "" and len(made["problems"]) == 7


def test_a_reply_comes_back_with_its_changes_and_takes_the_ones_chosen():
    head, _ = split_halves(SPECIMEN)
    head = head.replace("Read this code.", "Look at this code.").replace(
        "Complete the sentences.", "Fill in the sentences.")
    reply = f"{PAPER_BEGIN}\n{head}\n{PAPER_END}"
    every = json.loads(web.reply_json("tidy", SPECIMEN, reply))
    assert every["ok"] and [h["id"] for h in every["hunks"]] == [1, 2]
    assert "Look at this code." in every["text"] and "Fill in the sentences." in every["text"]
    one = json.loads(web.reply_json("tidy", SPECIMEN, reply, "{}", "[2]"))
    assert "Read this code." in one["text"] and "Fill in the sentences." in one["text"]
    assert [h["accepted"] for h in one["hunks"]] == [False, True]
    none = json.loads(web.reply_json("tidy", SPECIMEN, reply, "{}", "[]"))
    assert none["text"] == SPECIMEN


def test_a_refused_reply_has_no_text_and_follow_up_hands_its_problems_back():
    head, _ = split_halves(SPECIMEN)
    reply = f"{PAPER_BEGIN}\n{head.replace('with the value 21', 'with the value 12')}\n{PAPER_END}"
    refused = json.loads(web.reply_json("tidy", SPECIMEN, reply))
    assert not refused["ok"] and refused["text"] is None
    text = web.follow_up_json(json.dumps(refused["messages"]))
    assert "Fix only these" in text and "number" in text and PAPER_BEGIN in text


def test_follow_up_leaves_out_warnings_when_there_are_problems():
    messages = [{"code": "a", "line": 1, "what": "A problem.", "fix": "", "where": "", "level": "problem"},
                {"code": "b", "line": 2, "what": "Only a warning.", "fix": "", "where": "", "level": "warning"}]
    text = web.follow_up_json(json.dumps(messages))
    assert "A problem." in text and "Only a warning." not in text
    assert "Only a warning." in web.follow_up_json(json.dumps(messages[1:]))


# --- the page --------------------------------------------------------------------

def test_the_page_carries_the_readers_own_sources_and_nothing_it_does_not_need():
    sources = build_site.reader_sources()
    assert {"dewmark/__init__.py", "dewmark/reader.py", "dewmark/web.py", "dewmark/reply.py",
            "dewmark/package.py", "dewmark/data/cheat-sheet.txt",
            "dewmark/data/specimen.exam.md"} <= set(sources)
    assert "dewmark/__main__.py" not in sources and "dewmark/convert_pdp.py" not in sources
    assert "dewmark/build.py" not in sources and "dewmark/render.py" not in sources, \
        "the page builder needs libraries the checker page cannot load"
    assert not [name for name in sources if "__pycache__" in name]


def test_the_sources_in_the_page_run_on_their_own_in_a_bare_interpreter(tmp_path):
    """Python -S has no site-packages and -I ignores the environment, and the
    working directory is an empty folder: only what the page carries can be
    imported, as in Pyodide."""
    for name, text in build_site.reader_sources().items():
        target = tmp_path / "reader" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    (tmp_path / "paper.exam.md").write_text(SPECIMEN.replace("(3 marks)", "(4 marks)", 1),
                                            encoding="utf-8")
    code = ("import sys; sys.path.insert(0, 'reader'); from dewmark import web;"
            "print(web.check_json(open('paper.exam.md', encoding='utf-8').read()))")
    out = subprocess.run([sys.executable, "-S", "-I", "-c", code], cwd=tmp_path, check=True,
                         capture_output=True, text=True, encoding="utf-8").stdout.strip()
    assert out == web.check_json(SPECIMEN.replace("(3 marks)", "(4 marks)", 1))


def test_the_built_page_holds_the_sources_and_cannot_be_ended_early_by_them(tmp_path, monkeypatch):
    monkeypatch.setattr(build_site, "reader_sources",
                        lambda: {"x.py": "a = '</script><!-- <b>'  # & more"})
    page = build_site.build_checker(tmp_path).read_text(encoding="utf-8")
    block = re.search(r'<script type="application/json" id="reader-sources">(.*?)</script>', page, re.S)
    assert json.loads(block.group(1)) == {"x.py": "a = '</script><!-- <b>'  # & more"}
    assert "<b>" not in block.group(1) and "</script>" not in block.group(1)
    assert page.count('"__READER_SOURCES__"') == 1, "the page's own check for an unbuilt copy must survive"


def test_the_template_refuses_a_build_that_lost_its_data_block(tmp_path, monkeypatch):
    broken = tmp_path / "template"
    broken.mkdir()
    (broken / "checker").mkdir()
    (broken / "checker" / "index.html").write_text("<p>no data block</p>", encoding="utf-8")
    monkeypatch.setattr(build_site, "ROOT", broken)
    try:
        build_site.build_checker(tmp_path / "out")
    except AssertionError as error:
        assert "data block" in str(error)
    else:
        raise AssertionError("a template with no data block should stop the build")


def test_the_page_asks_for_nothing_beyond_python_and_sends_nothing():
    page = (ROOT / "checker" / "index.html").read_text(encoding="utf-8")
    policy = re.search(r'Content-Security-Policy" content="([^"]*)"', page).group(1)
    assert "default-src 'none'" in policy and "form-action 'none'" in policy
    assert re.search(r"connect-src https://cdn\.jsdelivr\.net(;|$)", policy)
    assert "fetch(" not in page and "XMLHttpRequest" not in page and "sendBeacon" not in page
    assert "localStorage" not in page and "sessionStorage" not in page and "indexedDB" not in page
