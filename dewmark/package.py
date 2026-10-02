"""The paste route: the package a teacher gives to an assistant
(docs/EXAM_FORMAT.md §4.10, planning/PROPOSAL.md §8.5, decisions 19, 20).

With no model connected to dewmark, a teacher can still have an assistant
convert or reword a paper. dewmark builds one block of text to paste into
any assistant the college allows: what to do, the rules for the reply, the
format's cheat sheet, and the paper. The reply is checked by
`dewmark/reply.py`. The package holds an exam paper and never a marking
scheme, and a scan for student information runs before it is offered.

    package = build_package("tidy", paper_text)
    package["text"]        # give this to the assistant
    package["findings"]    # things that may be student information

The five modes are decision 19's. Only "copy" reads a Word paper; the
other four take an exam file and change its wording, never its numbers,
marks, answer boxes or scheme.
"""

import datetime
import re
from pathlib import Path

from . import READER_VERSION
from .reader import (FENCE_RE, REFERENCE_LINE_RE, SCHEME_LINE_RE, _is_closing,
                     _tidy)
from .settings import KNOWN, normal_key

DATA = Path(__file__).resolve().parent / "data"

PAPER_BEGIN, PAPER_END = "=== BEGIN PAPER ===", "=== END PAPER ==="
NOTES_BEGIN, NOTES_END = "=== BEGIN NOTES ===", "=== END NOTES ==="

HEADER = (
    "THIS CONTAINS YOUR EXAM PAPER. IT CONTAINS NO STUDENT INFORMATION.\n"
    "Paste it only into an assistant your college allows for exam material."
)

# The settings a teacher gives for a paper converted from Word, in the order
# they are written. The rest of the settings can be added later, in the file.
ABOUT_KEYS = ("code", "kind", "title", "module", "module code", "total marks",
              "time allowed")

RULES = f"""\
THE RULES FOR YOUR REPLY
1. Reply with the whole paper again, between the line {PAPER_BEGIN} and the
   line {PAPER_END}. Put nothing else between them.
2. Do not change: the lines between the two --- lines at the top; the number
   and the marks in any heading (only the words after the number may change);
   any line inside a fence (a line of three or more backticks, and everything
   up to the fence that closes it); any number; any formula between $ signs or
   code between backticks; any picture file name; the order of the paper.
3. Do not add a marking scheme, answers, hints or solutions. Do not add or
   remove a question, a part or a mark.
4. Do not make any question easier or harder. Keep the word that sets its
   level (state, describe, explain, evaluate, calculate).
5. After the paper, between the line {NOTES_BEGIN} and the line
   {NOTES_END}, write one line for each change and say why you made it.
"""

COPY_RULES = f"""\
THE RULES FOR YOUR REPLY
1. Reply with the whole exam file, between the line {PAPER_BEGIN} and the
   line {PAPER_END}. Put nothing else between them.
2. Start with the settings exactly as they are under THE SETTINGS, and add
   no other line to them.
3. Copy every word of the paper as written. Do not correct, shorten, reword
   or add words, even where you think there is a mistake. Do not change any
   number or formula.
4. Give each question and part a heading with its number and its marks, as
   the format shows. Use the numbers printed in the paper. Where the paper
   shows a mark as [3] or (3), write it as (3 marks).
5. Put an answer box under each part that asks for an answer. Choose the
   kind of box that fits (see THE FORMAT). If you cannot tell, use ```answer.
6. Do not write a marking scheme, answers, hints or solutions.
7. After the file, between the line {NOTES_BEGIN} and the line {NOTES_END},
   list anything you were not sure of, one line each.
"""


class Mode:
    def __init__(self, key, label, summary, task, words=True):
        self.key, self.label, self.summary, self.task = key, label, summary, task
        self.words = words      # changes wording of an exam file (not copy)


MODES = {m.key: m for m in (
    Mode("copy", "Copy without composing",
         "Puts a Word paper into the exam file format. It adds headings, marks "
         "and answer boxes, and does not change a word.",
         "The paper below was written in Word. Put it into the dewmark exam "
         "file format shown under THE FORMAT, and change nothing else. "
         "THE SPECIMEN shows what a finished file looks like.", words=False),
    Mode("tidy", "Tidy the wording",
         "Fixes spelling, punctuation and unclear words, and keeps the meaning "
         "and the level.",
         "Tidy the wording of this paper. Fix spelling, punctuation and "
         "grammar. Use one term for one thing all through the paper. Where a "
         "word such as \"this\", \"it\" or \"the above\" could point to more "
         "than one thing, say which. Keep the meaning, the tone and the length "
         "about the same."),
    Mode("plain", "Check the language is accessible",
         "Rewrites hard wording in plain language for a reader who may be "
         "reading in a second language. Technical terms stay.",
         "Make the language of this paper accessible. Write for a reader with "
         "about two thousand common English words, who may be reading in a "
         "second language. Give every sentence a verb. Prefer short sentences, "
         "and put what the question asks for first. Use the common word (\"get\", "
         "not \"obtain\"). Avoid phrasal verbs such as \"work out\" and \"carry "
         "on\", idioms, and double negatives. Keep every technical term the "
         "module teaches, exactly as it is written now: never swap one for an "
         "everyday word."),
    Mode("udl", "Make it more UDL-friendly",
         "Makes the paper easier to take in without changing what it "
         "assesses: steps in order, one task to a sentence, words explained.",
         "Make this paper more friendly to Universal Design for Learning "
         "(UDL) without changing what it assesses. Put instructions that "
         "have several steps into a numbered list. Give each sentence one task. "
         "Where a question uses an everyday word that a student might not "
         "know and that the module does not teach, add a short plain "
         "explanation in brackets. Replace a cultural reference or idiom that "
         "a student may not share with a plain one. Where a picture's "
         "description is missing or says only \"figure\", write one sentence "
         "that says what it shows. Do not add hints."),
    Mode("invite", "Rephrase commands as invitations",
         "Turns commands into questions and invitations, and keeps each "
         "question's verb so it asks the same thing.",
         "Rephrase the commands in this paper as invitations. Keep each "
         "question's verb, so it asks for the same thing: \"Explain why the "
         "loop stops.\" becomes \"Can you explain why the loop stops?\". Leave "
         "rules as rules (time, hand-in, permitted materials, conduct). Do not "
         "add praise, encouragement or hints, and do not add \"let's\"."),
)}

# What may be student information. A paper has numbers of its own, so a
# finding is a question for the teacher, never a refusal.
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PPS_RE = re.compile(r"\b\d{7}[A-Wa-w][A-Ia-iWw]?\b")
LONG_NUMBER_RE = re.compile(r"(?<!\w)(?<!\d\.)\d{6,}(?!\w|[.,]\d)")
PHONE_RE = re.compile(r"(?<!\w)\+?\d[\d ()-]{8,}\d(?!\w)")
STUDENT_ID_RE = re.compile(r"\bstudent\s*(?:number|no\.?|id)\b[\s:#-]*\S*\d", re.I)


def split_halves(text, reference=True):
    """Split an exam file into (paper, rest): the paper half is everything
    above `# Reference` or `# Marking scheme`, whichever comes first; the
    rest starts at that line and is kept as it is, to be joined back after
    an assistant has worked on the paper. With `reference=False` only the
    marking scheme ends the paper, so the reference cards, which students
    see, stay in it. A line inside a fence does not count."""
    lines = _tidy(text).split("\n")
    fence = None
    for index, line in enumerate(lines):
        if fence:
            if _is_closing(line, fence):
                fence = None
            continue
        f = FENCE_RE.match(line)
        if f:
            fence = f.group(1)
        elif SCHEME_LINE_RE.match(line) or (reference and REFERENCE_LINE_RE.match(line)):
            return "\n".join(lines[:index]), "\n".join(lines[index:])
    return "\n".join(lines), ""


def settings_block(about):
    """The settings block for a paper converted from Word, from the
    teacher's answers: {"code": ..., "title": ...}. Returns (text,
    problems), where problems say what is missing or unknown."""
    problems, lines = [], ["---", "dewmark: 1"]
    given = {normal_key(k): str(v).strip() for k, v in (about or {}).items()}
    for key in given:
        if key not in KNOWN:
            problems.append(f"\"{key}\" is not a setting dewmark knows.")
    for key in ABOUT_KEYS:
        if given.get(key):
            lines.append(f"{key}: {given[key]}")
        else:
            problems.append(f"The paper's \"{key}\" is missing.")
    lines.append("---")
    return "\n".join(lines), problems


WINDOW, OVERLAP = 1000, 100


def _windows(line):
    """A long line in windows of WINDOW characters that overlap by OVERLAP, so
    no pattern is ever run over more than a window: a pasted line of a
    hundred thousand letters must not make the scan crawl."""
    if len(line) <= WINDOW:
        yield 0, line
        return
    for start in range(0, len(line), WINDOW - OVERLAP):
        yield start, line[start:start + WINDOW]
        if start + WINDOW >= len(line):
            return


def scan_for_student_data(text):
    """What in `text` may be student information: e-mail addresses, PPS
    numbers, phone numbers, long numbers, and "student number: …". Returns
    a list of {"line", "what", "excerpt"}."""
    found = []
    checks = ((EMAIL_RE, "an e-mail address"), (PPS_RE, "a PPS number"),
              (STUDENT_ID_RE, "a student number"), (PHONE_RE, "a phone number"),
              (LONG_NUMBER_RE, "a long number"))
    for number, line in enumerate(_tidy(text).split("\n"), 1):
        spans, seen = [], set()
        for offset, window in _windows(line):
            for pattern, what in checks:
                for m in pattern.finditer(window):
                    start, end = offset + m.start(), offset + m.end()
                    if (start, what) in seen or any(a <= start < b for a, b in spans):
                        continue
                    seen.add((start, what))
                    spans.append((start, end))
                    found.append({"line": number, "what": what,
                                  "excerpt": m.group(0).strip()[:40]})
    return found


def build_package(mode, paper_text, about=None, cheat_sheet=None, specimen=None,
                  made_on=None):
    """Build the package for `mode` from a paper.

    `paper_text` is a Word paper's text for "copy", or an exam file for the
    other modes (its `# Marking scheme` and `# Reference` are left out).
    `about` gives the settings for "copy". Returns a dict: "text", "mode",
    "problems" (what stops a package being made), "findings" (things that
    may be student information), "sent" (the paper text that went in).
    """
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}; the modes are {', '.join(MODES)}")
    chosen = MODES[mode]
    cheat_sheet = (DATA / "cheat-sheet.txt").read_text(encoding="utf-8") \
        if cheat_sheet is None else cheat_sheet
    made_on = made_on or datetime.date.today().isoformat()
    problems, parts = [], [HEADER, f"Made by dewmark {READER_VERSION} on {made_on}."]
    parts += ["", "WHAT TO DO", chosen.task, ""]

    if chosen.words:
        sent, rest = split_halves(paper_text)
        parts += [RULES, "THE FORMAT (so you leave it whole)", cheat_sheet.rstrip(), ""]
        settings = None
    else:
        sent, rest = _tidy(paper_text), ""
        settings, problems = settings_block(about)
        specimen = (DATA / "specimen.exam.md").read_text(encoding="utf-8") \
            if specimen is None else specimen
        parts += [COPY_RULES, "THE FORMAT", cheat_sheet.rstrip(), "",
                  "THE SPECIMEN (a finished file; write yours in the same way)",
                  specimen.rstrip(), "", "THE SETTINGS (use exactly these)", settings, ""]

    parts += ["THE PAPER" + (" (as written in Word)" if not chosen.words else ""),
              PAPER_BEGIN, sent.strip("\n"), PAPER_END, ""]
    text = "\n".join(parts)
    return {"text": text, "mode": mode, "problems": problems, "sent": sent,
            "settings": settings, "findings": scan_for_student_data(sent),
            "left_out": bool(rest.strip())}


def follow_up(messages, mode):
    """The text for "Copy these problems": the reader's messages, worded
    for the assistant, to paste back for another round."""
    lines = ["The paper you returned has these problems. Fix only these, change "
             "nothing else, and reply with the whole paper again between "
             f"{PAPER_BEGIN} and {PAPER_END}.", ""]
    for message in messages:
        head = f"Line {message.line}" + (f", {message.where}" if message.where else "")
        lines.append(f"- {head}: {message.what}" + (f" {message.fix}" if message.fix else ""))
    return "\n".join(lines) + "\n"
