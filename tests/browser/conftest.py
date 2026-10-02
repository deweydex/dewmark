"""Shared set-up for the browser rehearsals.

These tests open built exam pages and the marking workbench in a real
Chromium, because the bugs they guard against live in the page, not the
builder: what gets written to browser storage, and when. They need the
playwright package and a Chromium. Where either is missing they are
skipped, unless DEWMARK_REQUIRE_BROWSER is set, as it is in CI, where a
skipped rehearsal would read as a passed one.
"""

import glob
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
import build_exam  # noqa: E402
from dewmark.build import build_pages  # noqa: E402

SAMPLE = ROOT / "samples" / "sample-mixed-paper.exam.md"


def _unavailable(reason):
    if os.environ.get("DEWMARK_REQUIRE_BROWSER"):
        pytest.fail(reason)
    pytest.skip(reason)


def find_chromium():
    """A Chromium to launch: DEWMARK_CHROMIUM if set, else one under
    PLAYWRIGHT_BROWSERS_PATH or /opt/pw-browsers, else None so Playwright
    uses its own download."""
    if os.environ.get("DEWMARK_CHROMIUM"):
        return os.environ["DEWMARK_CHROMIUM"]
    for root in (os.environ.get("PLAYWRIGHT_BROWSERS_PATH"), "/opt/pw-browsers"):
        if root:
            for candidate in sorted(glob.glob(root + "/chromium-*/chrome-linux*/chrome")):
                return candidate
    return None


def _proxy():
    """Behind a proxy that re-signs HTTPS (a sandbox, not CI), Chromium has to
    be told to use it and to trust it. Only the checker page reaches out, to
    load Python from a CDN; every other page here is a file."""
    return os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")


@pytest.fixture(scope="session")
def browser():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        _unavailable("playwright is not installed")
    options = {}
    if _proxy():
        options = {"proxy": {"server": _proxy()}, "args": ["--ignore-certificate-errors"]}
    with sync_playwright() as playwright:
        try:
            launched = playwright.chromium.launch(**options)
        except Exception:
            chromium = find_chromium()
            if not chromium:
                _unavailable("no Chromium to launch")
            launched = playwright.chromium.launch(executable_path=chromium, **options)
        yield launched
        launched.close()


@pytest.fixture(scope="session")
def built(tmp_path_factory):
    """The mixed sample built once: its three pages and its scheme."""
    out = tmp_path_factory.mktemp("built")
    build_exam.build(SAMPLE, out)
    return {
        "student": out / "sample-mixed-2027.student.html",
        "practice": out / "sample-mixed-2027.practice.html",
        "answer_key": out / "sample-mixed-2027.answer-key.html",
        "scheme": out / "dewmark_sample-mixed-2027_marking_scheme.json",
        "dir": out,
    }


# One paper with every kind of box the page draws, for the rehearsals of the
# new page (dewmark/build.py). Each part has its own box, named for its part.
REHEARSAL_PAPER = """\
---
dewmark: 1
code: rehearsal
kind: exam
title: Rehearsal Paper
module: Testing
module code: 5N0000
total marks: 18
time allowed: 1 hour
hand in: Hand it in.
---

## Instructions to candidates

Answer **all** questions.

## Question 1: Writing (6 marks)

### 1(a) (2 marks)

Say something.

```answer
```

### 1(b) (2 marks)

Show the working.

```maths
```

### 1(c) (2 marks)

```essay (about 50 words)
```

## Question 2: Code (4 marks)

### 2(a) (2 marks)

```code
```

### 2(b) (2 marks)

```python exec
print("hi")
```

## Question 3: Filling in (8 marks)

### 3(a) (2 marks)

```choice (choose 2)
A. one
B. two
C. three
```

### 3(b) (2 marks)

```boxes
First: ____
Second: ____
Choose from: leaf / root / stem
```

### 3(c) (2 marks)

```blanks
A ____ has [roots / leaves / seeds].
```

### 3(d) (2 marks)

```table
| Size | Count |
|---|---|
| small | ____ |
| large | ____ |
```

# Marking scheme

### 1(a) (draft)

### 1(b) (draft)

### 1(c) (draft)

### 2(a) (draft)

### 2(b) (draft)

### 3(a)

Answer: A, B

### 3(b)

Answers:
1. root
2. leaf

### 3(c)

Answers:
1. plant
2. leaves

### 3(d)

Answers:
1. 3
2. 4
"""


@pytest.fixture(scope="session")
def pages(tmp_path_factory):
    """The rehearsal paper built once with the new builder: its three pages."""
    out = tmp_path_factory.mktemp("pages")
    for name, text in build_pages(REHEARSAL_PAPER, ROOT).items():
        (out / name).write_text(text, encoding="utf-8")
    return {
        "student": out / "rehearsal.student.html",
        "practice": out / "rehearsal.practice.html",
        "answer_key": out / "rehearsal.answer-key.html",
        "dir": out,
    }


@pytest.fixture
def context(browser):
    """A fresh browser profile: its own storage, shared by every page
    opened in it, as the pages of one college PC's browser are."""
    ctx = browser.new_context(accept_downloads=True, ignore_https_errors=bool(_proxy()))
    yield ctx
    ctx.close()


class Checker:
    """The checker page, open and ready, and every request it has made."""

    def __init__(self, page, requests):
        self.page, self.requests = page, requests


@pytest.fixture(scope="session")
def checker_file(tmp_path_factory):
    sys.path.insert(0, str(ROOT / "dev"))
    import build_site
    return build_site.build_checker(tmp_path_factory.mktemp("checker"))


@pytest.fixture
def checker(context, checker_file):
    """The built checker page, once Python has loaded into it. Python comes
    from a CDN, so where there is no network the rehearsal is skipped, as a
    missing browser is, unless DEWMARK_REQUIRE_BROWSER is set."""
    page = context.new_page()
    requests = []
    page.on("request", lambda request: requests.append(request))
    page.on("dialog", lambda dialog: dialog.accept())
    page.goto(checker_file.as_uri())
    try:
        page.wait_for_function(
            "document.getElementById('load').textContent.startsWith('Ready')", timeout=120000)
    except Exception:
        _unavailable("Python did not load into the checker page: " + page.text_content("#load"))
    return Checker(page, requests)
