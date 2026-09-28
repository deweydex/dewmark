"""Convert a hand-built PDP exam page into an exam file
(docs/EXAM_FORMAT.md §6, §9).

The PDP 5N2927 pages (experiments/pdp-5n2927/) carry their paper as
Markdown inside <script id="exam-src">. That paper is already close to the
exam format; the converter changes only what differs:

- the settings are renamed (exam_id becomes code, duration_minutes becomes
  time allowed, the module title and code are split, dead keys go);
- the # heading that repeats the title goes (the title comes from the
  settings);
- ```python LABEL, a cell the student runs, becomes ```python exec LABEL;
  ```text, a listing, becomes ```python, as the PDP pages showed it;
  ```fields becomes ```boxes; (optional) becomes (not marked);
- a bold sub-part lead with marks becomes a #### heading;
- the 2027 paper's HTML maths becomes $…$, and its inline SVG figure a
  picture file;
- a marking-scheme skeleton is added: one (draft) entry per marked part,
  for the teacher to fill.

    python -m dewmark.convert_pdp OUTPUT_FOLDER PAGE.html [PAGE.html ...]
"""

import html
import json
import os
import re
import sys

KEYS = {"exam_id": "code", "title": "title", "session": "session",
        "institution": "institution", "college": "college", "kind": "kind",
        "total_marks": "total marks"}
SWITCHES = {"allow_completion": "code completion", "error_hints": "error hints"}
DROPPED = ("reference_theory",)
HAND_IN = ("Save your answer file and your PDF, then upload both to the exam's "
           "assignment on Moodle. Show your invigilator the confirmation.")


def exam_source(page_html):
    m = re.search(r'<script type="application/json" id="exam-src">(.*?)</script>',
                  page_html, re.S)
    if not m:
        raise ValueError("no <script id=\"exam-src\"> in this page")
    return json.loads(m.group(1))


def _settings(front, notes):
    out = ["---", "dewmark: 1"]
    for key, value in front.items():
        if key == "module":
            m = re.match(r"^(.*?)\s+(\d[A-Z]\d{3,5})$", value)
            if m:
                out += [f"module: {m.group(1)}", f"module code: {m.group(2)}"]
            else:
                out.append(f"module: {value}")
        elif key == "duration_minutes":
            minutes = int(value)
            hours, rest = divmod(minutes, 60)
            if rest == 0:
                out.append(f"time allowed: {hours} hour{'s' if hours != 1 else ''}")
            else:
                out.append(f"time allowed: {minutes} minutes")
        elif key == "time_limit_seconds":
            out.append(f"python time limit: {value} seconds")
        elif key == "show_reference":
            out.append("python reference: " + ("yes" if value.lower() == "true" else "no"))
        elif key in SWITCHES:
            out.append(f"{SWITCHES[key]}: " + ("on" if value.lower() == "true" else "off"))
        elif key in KEYS:
            out.append(f"{KEYS[key]}: {value}")
        elif key in DROPPED:
            notes.append(f"dropped the setting {key}, which the PDP page never read")
        else:
            notes.append(f"left out an unknown setting {key}: {value}")
    out += ["timer: shown", "python from: this file", f"hand in: {HAND_IN}", "---"]
    return out


def _maths(line):
    """The 2027 paper writes a few formulas as HTML; the format writes $…$."""
    def tex(text):
        text = re.sub(r"<i>(\w)</i>", r"\1", text)
        return text.replace("²", "^2").replace("³", "^3").replace("π", "\\pi ")
    line = re.sub(r'<span class="frac"><span>(.*?)</span><span>(.*?)</span></span>',
                  lambda m: "$\\frac{" + tex(m.group(1)) + "}{" + tex(m.group(2)) + "}$", line)
    line = re.sub(r'√<span class="sqrt">(.*?)</span>',
                  lambda m: "$\\sqrt{" + tex(m.group(1)) + "}$", line)
    line = re.sub(r"<i>(\w)</i>([²³]?)", lambda m: "$" + m.group(1) + tex(m.group(2)) + "$", line)
    # The HTML wrote one formula as several pieces with π and = between
    # them ("4π$r^2$", "$V$ = $\frac{4}{3}$π$r^3$"); join each into one.
    line = re.sub(r"(\d+)π\$", lambda m: "$" + m.group(1) + "\\pi ", line)
    joined = None
    while joined != line:
        joined = line
        line = re.sub(r"\$([^$]+)\$(\s*=\s*|π)\$([^$]+)\$",
                      lambda m: "$" + m.group(1) + (" = " if "=" in m.group(2) else "\\pi ")
                      + m.group(3) + "$", line)
    return line


def convert(page_html, stem, pictures_dir=None):
    """Return (exam file text, notes about what needs a person's eye)."""
    source = exam_source(page_html).replace("\r\n", "\n")
    m = re.match(r"^---\n([\s\S]*?)\n---\n", source)
    front = {}
    for line in m.group(1).split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            front[key.strip()] = value.strip()
    notes = []
    out = _settings(front, notes)
    parts = []            # (kind, text) for the scheme skeleton
    figures = 0
    fence = None
    question = part = None
    for line in source[m.end():].split("\n"):
        if fence:
            if line.strip() == fence:
                fence = None
            out.append(line)
            continue
        f = re.match(r"^(`{3,})(\w*)(.*)$", line)
        if f:
            fence, kind, rest = f.group(1), f.group(2), f.group(3)
            rest = re.sub(r"\(optional\)\s*$", "(not marked)", rest)
            if kind == "python" and not rest.strip().startswith("setup"):
                kind = "python exec"
            elif kind == "text":
                kind = "python"
            elif kind == "fields":
                kind = "boxes"
            out.append(fence + kind + rest)
            continue
        if re.match(r"^#\s", line):
            notes.append(f"removed the title heading \"{line[2:].strip()}\"; "
                         "the title comes from the settings")
            continue
        h = re.match(r"^(#{2,3})\s+(.*\((\d+(?:\.5)?) marks?\))\s*$", line)
        if h:
            if len(h.group(1)) == 2:
                question = re.match(r"Question\s+(\d+)", h.group(2)).group(1)
                parts.append(("question", question))
            else:
                part = h.group(2).split(":")[0].strip()
                parts.append(("part", part))
        b = re.match(r"^\*\*\(([ivx]+)\)\s+(.+?)\s+\((\d+) marks?\)\.?\*\*\s*(.*)$", line)
        if b:
            out += [f"#### ({b.group(1)}) {b.group(2)} ({b.group(3)} marks)", "", b.group(4)]
            parts.append(("sub", f"{part}({b.group(1)})"))
            continue
        figure = re.match(r'^<figure class="exam-fig" aria-label="(.*?)">(<svg.*</svg>)</figure>$', line)
        if figure:
            figures += 1
            name = f"pictures/{stem}-figure-{figures}.svg"
            if pictures_dir:
                os.makedirs(pictures_dir, exist_ok=True)
                with open(os.path.join(pictures_dir, os.path.basename(name)), "w",
                          encoding="utf-8") as handle:
                    handle.write(figure.group(2))
            out.append(f"![{html.unescape(figure.group(1))}]({name})")
            notes.append(f"saved a figure as {name}; its description is only "
                         f"\"{figure.group(1)}\" and needs writing out in full")
            continue
        converted = _maths(line)
        if converted != line:
            notes.append("turned HTML maths into $…$: check it reads the same")
        out.append(converted)
    out += _skeleton(parts)
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(out).rstrip() + "\n")
    return text, sorted(set(notes))


def _skeleton(parts):
    """One (draft) entry per marked part: the parts with no sub-parts, and
    the sub-parts."""
    out = ["", "# Marking scheme", ""]
    has_subs = {p.split("(")[0] for kind, p in parts if kind == "sub"}
    for kind, value in parts:
        if kind == "question":
            out += [f"## Question {value}", "", "Topic:", "Outcomes:", ""]
        elif kind == "part" and value not in has_subs:
            out += [f"### {value} (draft)", ""]
        elif kind == "sub":
            out += [f"### {value} (draft)", ""]
    return out


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip())
        return 2
    folder = argv[0]
    os.makedirs(folder, exist_ok=True)
    for path in argv[1:]:
        stem = re.sub(r"[^a-z0-9]+", "-", os.path.basename(path).lower()
                      .removesuffix(".html")).strip("-")
        with open(path, encoding="utf-8") as handle:
            text, notes = convert(handle.read(), stem, os.path.join(folder, "pictures"))
        target = os.path.join(folder, stem + ".exam.md")
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(text)
        print(f"{target}: {len(text.splitlines())} lines")
        for note in notes:
            print("  - " + note)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
