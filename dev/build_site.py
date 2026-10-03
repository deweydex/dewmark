"""Build dewmark's GitHub Pages site into site/.

The site is what a teacher reaches from a link: the marking workbench, every
sample paper built fresh from its exam file, the hand-built papers that came
before dewmark, and the design mockups. The deploy workflow runs this on
every push to main, so the published samples cannot drift from the exam
files they come from.

    python dev/build_site.py            # writes site/
"""

import html
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

# What each built file is, in the order a teacher would want them. Each
# page keeps its own save slot and the answer key saves nothing
# (DECISIONS_LOG.md, entry 0.6), so all three can sit side by side.
VARIANTS = (
    (".student.html", "Student paper"),
    (".practice.html", "Practice version"),
    (".answer-key.html", "Answer key"),
)


def build_samples() -> list[tuple[str, list[tuple[str, str]]]]:
    """Build every sample exam into site/samples/<sample>/ and return, per
    sample, its title and the pages written. A sample that fails to build
    stops the whole site: publishing a half-built set would hide the
    failure behind the pages that did build."""
    listing = []
    for exam in sorted((ROOT / "samples").glob("*.exam.md")):
        name = exam.name.removesuffix(".exam.md")
        out = SITE / "samples" / name
        subprocess.run([sys.executable, str(ROOT / "build_exam.py"),
                        str(exam), "--output", str(out)], check=True)
        # Anything the builder wrote that is not published is removed, not
        # just left unlinked: an unlinked page is still one address away.
        for built in out.iterdir():
            if not built.name.endswith(tuple(suffix for suffix, _ in VARIANTS)):
                built.unlink()
        pages = []
        for suffix, label in VARIANTS:
            for page in sorted(out.glob("*" + suffix)):
                pages.append((f"samples/{name}/{page.name}", label))
        listing.append((title_of(exam), pages))
    return listing


# The papers in the new format that are published as pages to try. The four
# papers under samples/pdp-5n2927 are built by the tests and not published here;
# their trial runs are already published, as they were first made, below.
NEW_FORMAT_SAMPLES = (ROOT / "dewmark" / "data" / "specimen.exam.md",)


def build_new_pages() -> list[tuple[str, list[tuple[str, str]]]]:
    """Build each new-format sample into site/new/<code>/ with the new builder
    (dewmark/build.py) and return, per sample, its title and the pages written.
    The marking scheme the builder also writes is a secret and stays out of
    the site, as every file that is not a page does."""
    sys.path.insert(0, str(ROOT))
    from dewmark.build import build

    listing = []
    for exam in NEW_FORMAT_SAMPLES:
        scratch = SITE / "new" / ".building"
        build(exam, scratch)
        pages = []
        for suffix, label in VARIANTS:
            for page in sorted(scratch.glob("*" + suffix)):
                code = page.name.removesuffix(suffix)
                target = SITE / "new" / code
                target.mkdir(parents=True, exist_ok=True)
                shutil.move(str(page), target / page.name)
                pages.append((f"new/{code}/{page.name}", label))
        shutil.rmtree(scratch)
        listing.append((title_of(exam), pages))
    return listing


def title_of(exam: Path) -> str:
    """The exam's title from its exam block, or its file name if none."""
    for line in exam.read_text(encoding="utf-8").splitlines():
        if line.startswith("title:"):
            return line.partition(":")[2].strip().strip("\"'")
    return exam.name


# The reader, as the browser runs it: every file of the dewmark package the
# checker page calls, put into the page so it checks with the same code the
# command line runs. The converter for the old hand-built pages and the
# command-line entry point are not needed there, and neither is the builder
# of the pages: it needs the markdown and maths libraries, which the checker
# page has no way to load, and nothing a checker does builds a page.
NOT_IN_THE_PAGE = {"__main__.py", "convert_pdp.py", "build.py", "render.py"}


def reader_sources() -> dict[str, str]:
    sources = {}
    for path in sorted((ROOT / "dewmark").rglob("*")):
        if (path.is_file() and path.suffix in {".py", ".md", ".txt"}
                and "__pycache__" not in path.parts and path.name not in NOT_IN_THE_PAGE):
            sources[path.relative_to(ROOT).as_posix()] = path.read_text(encoding="utf-8")
    return sources


def build_checker(out: Path) -> Path:
    """Write the checker page, with the reader's sources in its data block.
    `<` is written as \\u003c so no source can end the block early."""
    blob = json.dumps(reader_sources(), ensure_ascii=False).replace("<", "\\u003c")
    template = (ROOT / "checker" / "index.html").read_text(encoding="utf-8")
    marker = ">__READER_SOURCES__</script>"
    assert template.count(marker) == 1, "the data block's marker is missing from checker/index.html"
    out.mkdir(parents=True, exist_ok=True)
    page = out / "index.html"
    page.write_text(template.replace(marker, ">" + blob + "</script>"), encoding="utf-8")
    return page


def copy_folders() -> None:
    shutil.copytree(ROOT / "workbench", SITE / "workbench")
    shutil.copytree(ROOT / "experiments", SITE / "experiments",
                    ignore=shutil.ignore_patterns("*.md"))
    shutil.copytree(ROOT / "planning" / "mockups", SITE / "mockups")


# How the hand-built pages are listed on the home page; a file not named
# here is listed by its file name.
EXPERIMENT_NAMES = {
    "hvit-database-exam.student.html": "Database Methods practical, 2025–26: student paper",
    "hvit-database-exam.answers.html": "Database Methods practical, 2025–26: sample answers",
    "mit-5n18396-maths.student.html": "Maths for Information Technology 5N18396, 2025–26: student paper",
    "mit-5n18396-maths.assessor.html": "Maths for Information Technology 5N18396, 2025–26: assessor version",
    "PDP_5N2927_Sample_Exam.html": "Programming and Design Principles 5N2927: sample exam",
    "PDP_5N2927_Practice_Exam_1.html": "Programming and Design Principles 5N2927: practice exam 1",
    "PDP_5N2927_Practice_Exam_2.html": "Programming and Design Principles 5N2927: practice exam 2",
    "PDP_5N2927_Exam_2027.html": "Programming and Design Principles 5N2927: written exam 2026–27 (trial)",
}


def links(items: list[tuple[str, str]]) -> str:
    return "".join(f'<li><a href="{html.escape(href)}">{html.escape(text)}</a></li>'
                   for href, text in items)


def write_home(samples, new_pages) -> None:
    # While only the student paper is published, a sample's title is its
    # link; with several variants each gets a link under the title.
    sample_rows = "".join(
        f'<li><a href="{html.escape(pages[0][0])}">{html.escape(title)}</a></li>'
        if len(pages) == 1 else
        f"<li><span class=t>{html.escape(title)}</span><ul class=row>"
        f"{links(pages)}</ul></li>" for title, pages in samples)
    experiments = sorted(p.relative_to(SITE).as_posix()
                         for p in (SITE / "experiments").rglob("*.html"))
    exp_items = [(p, EXPERIMENT_NAMES.get(Path(p).name, Path(p).stem))
                 for p in experiments]
    new_rows = "".join(
        f"<li><span class=t>{html.escape(title)}</span><ul class=row>{links(pages)}</ul></li>"
        for title, pages in new_pages)
    page = HOME.format(samples=sample_rows, new_pages=new_rows, experiments=links(exp_items))
    (SITE / "index.html").write_text(page, encoding="utf-8")


HOME = """<!doctype html>
<html lang="en-IE">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>dewmark</title>
<style>
:root {{ --bg:#f7f5f0; --ink:#1f2328; --muted:#5b6168; --line:#dcd8cf; --accent:#1f4e79; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --bg:#16181b; --ink:#e8e6e1; --muted:#a3a8ae; --line:#33373c; --accent:#8cb8e6; }}
}}
* {{ box-sizing: border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink);
  font:17px/1.6 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }}
main {{ max-width:46rem; margin:0 auto; padding:3rem 1rem 4rem; }}
h1 {{ font-size:2rem; margin:0 0 .25rem; letter-spacing:-.01em; }}
h2 {{ font-size:1.1rem; margin:2.5rem 0 .5rem; border-bottom:1px solid var(--line); padding-bottom:.3rem; }}
p {{ margin:.5rem 0; }}
.lede {{ color:var(--muted); }}
a {{ color:var(--accent); }}
a:focus-visible {{ outline:3px solid var(--accent); outline-offset:2px; }}
ul {{ padding-left:1.1rem; }}
li {{ margin:.35rem 0; }}
.t {{ font-weight:600; }}
.row {{ list-style:none; padding:0; display:flex; flex-wrap:wrap; gap:.25rem 1rem; margin:.1rem 0 .6rem; }}
.big {{ font-size:1.1rem; font-weight:600; }}
footer {{ margin-top:3rem; color:var(--muted); font-size:.9rem; }}
</style>
</head>
<body>
<main>
<h1>dewmark</h1>
<p class=lede>Exams that run in a web browser, with no server. A teacher writes
an exam as one file; students sit it as a web page, offline if need be; the
teacher marks the submissions on their own computer.</p>
<p>dewmark is being rebuilt to the plan in its
<a href="https://github.com/deweydex/dewmark/blob/main/planning/PROPOSAL.md">design proposal</a>.
What is here today are working drafts: try them, but do not sit a real class
on them yet.</p>

<h2>Write and check</h2>
<p class=big><a href="checker/">The exam file checker</a></p>
<p>Paste an exam file and see every problem, with its line and what to do.
Or have an assistant reword or convert a paper, and check what it sends back
before you use a word of it.</p>

<h2>Mark</h2>
<p class=big><a href="workbench/">The marking workbench</a></p>
<p>Open a folder of submissions and a marking scheme, mark by student or by
question, and export graded papers and a marks spreadsheet. Nothing leaves
your computer.</p>

<h2>Try a sample</h2>
<p>Each sample is built fresh from its exam file in the repository, as a
student paper, a practice version with hints, and an answer key.</p>
<ul>{samples}</ul>

<h2>The new page, a first draft</h2>
<p>The page that will replace the ones above, built from an exam file in the
<a href="https://github.com/deweydex/dewmark/blob/main/docs/EXAM_FORMAT.md">new format</a>.
It has every kind of answer box but the few still to come, two start screens,
reading settings (the <b>Aa</b> button) and saves as the others do. It has no
timer, breaks or PDF yet, so it cannot be sat as an exam.</p>
<ul>{new_pages}</ul>

<h2>Before dewmark</h2>
<p>Hand-built exam pages that dewmark learnt from, kept as they were.</p>
<ul>{experiments}</ul>

<h2>Design</h2>
<ul>
<li><a href="mockups/student-start.html">Mockup: the student's start, paper and finish</a></li>
<li><a href="mockups/teacher-studio.html">Mockup: the teacher's studio</a></li>
</ul>

<footer>
<p><a href="https://github.com/deweydex/dewmark">dewmark on GitHub</a> ·
began inside <a href="https://deweydex.github.io/dewlab/">dewlab</a> ·
<a href="https://github.com/deweydex/dewmark/blob/main/LICENSE.md">licence</a></p>
</footer>
</main>
</body>
</html>
"""


def main() -> None:
    shutil.rmtree(SITE, ignore_errors=True)
    SITE.mkdir()
    samples = build_samples()
    new_pages = build_new_pages()
    copy_folders()
    build_checker(SITE / "checker")
    write_home(samples, new_pages)
    print(f"built {sum(len(p) for _, p in samples + new_pages)} sample pages into {SITE}")


if __name__ == "__main__":
    main()
