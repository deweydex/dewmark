"""Checking an assistant's reply (docs/EXAM_FORMAT.md §4.10,
planning/PROPOSAL.md §8.3, decisions 19 and 20).

The teacher pastes back what the assistant returned. Four of decision 19's
modes ("tidy", "plain", "udl", "invite") change only the words of a paper
that is already an exam file. A reply is refused, not merely flagged, if it
changes anything else: a setting, a heading's number, marks or "any N"
rule, a line inside an answer box or listing, a number or a formula in the
prose, or a picture's file name, or if it brings a marking scheme with it.
Every change of wording that passes is shown as a difference for the
teacher to accept or reject, and a rejected difference leaves the teacher's
own words. "Copy" puts a Word paper into the format and promises not to
compose: its reply is read by the reader, its settings must be the ones the
teacher gave, and any word or number that differs from the Word text is
reported.

    result = check_reply(original, reply, "tidy")
    result["ok"]        # False if the reply must be refused
    result["messages"]  # what was found, with stable codes
    result["hunks"]     # each change of wording, with an id
    result["text"]      # the file, with the accepted changes made

`check_reply` is a function of its inputs, so the page calls it again with
the ids the teacher accepted.
"""

import difflib
import re
from collections import Counter

from .messages import Messages
from .numbers import NUMBER_RE, split_title
from .package import (MODES, NOTES_BEGIN, NOTES_END, PAPER_BEGIN, PAPER_END,
                      settings_block, split_halves)
from .reader import (FENCE_RE, HEADING_RE, _any_of, _is_closing, _marks_of,
                     _tidy, read)

SPAN_RE = re.compile(r"`[^`]*`|\$[^$]*\$|\]\([^)]*\)")
NUMBER_TOKEN_RE = re.compile(r"\d+(?:[.,]\d+)*")
LIST_MARKER_RE = re.compile(r"^\s*(?:\d+[.)]|[-*+])\s+")
OUTER_FENCE_RE = re.compile(r"^(`{3,}|~{3,})\s*(?:markdown|md|text)?\s*$", re.I)
WORD_RE = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*")
STRUCTURE_WORDS = {"mark", "marks", "question", "section"}
MOST = 25      # messages of one kind shown before "and N more"
MAX_LINES = 4000      # the longest paper or reply the comparison will take
MAX_WORDS = 20000     # the most words "copy" will compare


# --- finding the paper in the reply -----------------------------------------

def _is_marker(line, marker):
    return line.strip().strip("*`# ").strip() == marker


def _strip_outer_fence(lines):
    """A reply often wraps the whole paper in a code fence; take it off."""
    while lines and not lines[0].strip():
        lines = lines[1:]
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    if len(lines) >= 2:
        opener = OUTER_FENCE_RE.match(lines[0].strip())
        if opener and _is_closing(lines[-1], opener.group(1)):
            return lines[1:-1]
    return lines


def extract_reply(text):
    """Find the paper in a reply. Returns (paper text, the assistant's notes,
    messages): the paper is what lies between the two markers, or the whole
    reply if it has none, with any code fence around it and any chat above
    the settings taken off."""
    messages = Messages()
    lines = _tidy(text).split("\n")
    begin = next((i for i, l in enumerate(lines) if _is_marker(l, PAPER_BEGIN)), None)
    notes = []
    if begin is None:
        body = lines
    else:
        end = next((i for i in range(begin + 1, len(lines))
                    if _is_marker(lines[i], PAPER_END)), None)
        if end is None:
            messages.warning(
                "reply-no-end", begin + 1,
                f"The reply never says {PAPER_END}, so it may have been cut off.",
                "If the paper stops early, ask the assistant to send the rest.")
            end = next((i for i in range(begin + 1, len(lines))
                        if _is_marker(lines[i], NOTES_BEGIN)), len(lines))
        body = lines[begin + 1:end]
        start = next((i for i in range(end, len(lines)) if _is_marker(lines[i], NOTES_BEGIN)), None)
        if start is not None:
            stop = next((i for i in range(start + 1, len(lines))
                         if _is_marker(lines[i], NOTES_END)), len(lines))
            notes = lines[start + 1:stop]
    body = _strip_outer_fence(body)
    first = next((i for i, l in enumerate(body) if l.strip()), 0)
    if body and body[first].strip() != "---":
        settings = next((i for i in range(first, min(first + 15, len(body)))
                         if body[i].strip() == "---"), None)
        if settings is not None:
            messages.warning(
                "reply-preamble", settings + 1,
                f"The reply has {settings - first} line(s) of its own above the settings; "
                "they were left out.")
            body = body[settings:]
    else:
        body = body[first:]
    return "\n".join(body), "\n".join(notes).strip(), messages


# --- what a wording mode may not change -------------------------------------

def _heading_key(level, text):
    """What a heading with marks holds that a reply may not change: its
    level, number, marks and "any N" rule. Its title is prose."""
    marks, core = _marks_of(text)
    if marks is None:
        return None
    if level == 1:
        m = re.match(r"section\s+\S+", core, re.I)
        ident = m.group(0) if m else core
    else:
        numtext = split_title(core)[0]
        m = NUMBER_RE.match(numtext)
        ident = m.group(0) if m and m.group(0).strip() else numtext
    ident = re.sub(r"[\s.:]+", "", ident).lower()
    return ("heading", level, ident, marks, _any_of(core) if level < 4 else None)


def _classify(lines):
    """One entry per line: (kind, key). Settings, fence lines (an opener, its
    body and its closer) and headings with marks are fixed, and their key is
    what must stay the same; the rest is prose or blank."""
    entries, index = [], 0
    if lines and lines[0].strip() == "---":
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"),
                   len(lines) - 1)
        entries += [("settings", ("settings", l.rstrip())) for l in lines[:end + 1]]
        index = end + 1
    fence = None
    for line in lines[index:]:
        if fence:
            entries.append(("fence", ("fence", line.rstrip())))
            if _is_closing(line, fence):
                fence = None
            continue
        opener = FENCE_RE.match(line)
        if opener:
            fence = opener.group(1)
            entries.append(("fence", ("fence", line.rstrip())))
            continue
        heading = HEADING_RE.match(line)
        if heading and len(heading.group(1)) <= 4:
            key = _heading_key(len(heading.group(1)), heading.group(2))
            if key:
                entries.append(("heading", key))
                continue
        entries.append(("prose" if line.strip() else "blank", None))
    return entries


def _spans(lines):
    return Counter(m.group(0) for line in lines for m in SPAN_RE.finditer(line))


def _numbers(lines):
    text = "\n".join(SPAN_RE.sub(" ", LIST_MARKER_RE.sub("", l)) for l in lines)
    return Counter(NUMBER_TOKEN_RE.findall(text))


def _core(lines):
    """A passage without the blank lines at its edges: (lead, core, trail)."""
    start = 0
    while start < len(lines) and not lines[start].strip():
        start += 1
    stop = len(lines)
    while stop > start and not lines[stop - 1].strip():
        stop -= 1
    return lines[:start], lines[start:stop], lines[stop:]


def _same_words(a, b):
    return [l.rstrip() for l in a if l.strip()] == [l.rstrip() for l in b if l.strip()]


def _excerpt(lines, size=70):
    text = " ".join(l.strip() for l in lines if l.strip())
    return text if len(text) <= size else text[:size - 1].rstrip() + "…"


def _changed(before, after):
    return ", ".join(sorted(before - after)) or "nothing", ", ".join(sorted(after - before)) or "nothing"


def _describe(kind):
    return {"settings": "a setting", "heading": "the number, marks or \"any\" rule of a heading",
            "fence": "a line of an answer box or listing"}[kind]


def _fixed_problems(original, reply, messages):
    """Compare the fixed lines of the two papers. Returns (agree, pairs,
    tail): `pairs` are the fixed lines that match, as (line in the paper, line
    in the reply, whether it follows the previous pair directly), so the
    passages between them can still be compared when others disagree; `tail`
    says whether the passage after the last fixed line can be."""
    o_kinds, r_kinds = _classify(original), _classify(reply)
    o_fixed = [(i, k) for i, (kind, k) in enumerate(o_kinds) if k]
    r_fixed = [(i, k) for i, (kind, k) in enumerate(r_kinds) if k]
    matcher = difflib.SequenceMatcher(None, [k for _, k in o_fixed], [k for _, k in r_fixed],
                                      autojunk=False)
    agree, shown, pairs, tail = True, 0, [], False
    opcodes = matcher.get_opcodes()
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            pairs += [(o_fixed[i1 + n][0], r_fixed[j1 + n][0], n > 0 or (i1 == 0 and j1 == 0))
                      for n in range(i2 - i1)]
            tail = i2 == len(o_fixed) and j2 == len(r_fixed)
            continue
        tail = False
        agree = False
        if shown == MOST:
            shown += 1
            messages.problem("reply-structure-changed", 1,
                             "The reply has more changes like these, which are not listed.",
                             "Ask the assistant to leave the settings, headings' numbers and "
                             "marks, and answer boxes exactly as they were.", "the reply")
        if shown > MOST:
            continue
        shown += 1
        kind = o_kinds[o_fixed[i1][0]][0] if i1 < i2 else r_kinds[r_fixed[j1][0]][0]
        code = {"settings": "reply-settings-changed", "heading": "reply-heading-changed",
                "fence": "reply-box-changed"}[kind]
        at = r_fixed[j1][0] + 1 if j1 < len(r_fixed) else len(reply)
        if tag == "delete":
            what = (f"The reply leaves out {_describe(kind)} that your paper has, at line "
                    f"{o_fixed[i1][0] + 1} of your paper: \"{original[o_fixed[i1][0]].strip()[:70]}\"")
            what += f" (and {i2 - i1 - 1} more lines)." if i2 - i1 > 1 else "."
        elif tag == "insert":
            what = (f"The reply adds {_describe(kind)} that your paper does not have: "
                    f"\"{reply[r_fixed[j1][0]].strip()[:70]}\"")
            what += f" (and {j2 - j1 - 1} more lines)." if j2 - j1 > 1 else "."
        else:
            what = (f"The reply changes {_describe(kind)}. Your paper, line "
                    f"{o_fixed[i1][0] + 1}: \"{original[o_fixed[i1][0]].strip()[:70]}\". "
                    f"The reply: \"{reply[r_fixed[j1][0]].strip()[:70]}\"")
            what += f" (and {max(i2 - i1, j2 - j1) - 1} more lines)." if max(i2 - i1, j2 - j1) > 1 else "."
        messages.problem(code, at, what,
                         "Ask the assistant to leave it exactly as it was.", "the reply")
    return agree, pairs, tail


# --- the wording changes ------------------------------------------------------

def _plan(original, reply, pairs, tail, messages):
    """Line up the two papers on their fixed lines and find each passage the
    reply worded differently. Returns (plan, hunks): the plan is a list of
    ("keep", lines) and ("hunk", hunk) in order. Where fixed lines
    disagree, only the passages between lines that match are compared, and
    the plan is not used."""
    o_entries = _classify(original)
    plan, hunks = [], []
    where = ""
    o_from = r_from = 0

    def passage(o_seg, r_seg):
        lead, before, trail = _core(o_seg)
        _, after, _ = _core(r_seg)
        if not before:        # words added where the paper had none
            lead, trail = o_seg or [""], [""]
        hunk = {"id": len(hunks) + 1, "line": o_from + len(lead) + 1, "where": where,
                "kind": "text", "before": before, "after": after, "original": o_seg,
                "lead": lead, "trail": trail, "reply_line": r_from + 1}
        _check_hunk(hunk, messages)
        hunks.append(hunk)
        plan.append(("hunk", hunk))

    for oi, ri, follows in pairs:
        o_seg, r_seg = original[o_from:oi], reply[r_from:ri]
        if not follows:
            plan.append(("keep", o_seg))
        elif _same_words(o_seg, r_seg):
            plan.append(("keep", o_seg))
        else:
            passage(o_seg, r_seg)
        line, new = original[oi], reply[ri]
        if o_entries[oi][0] == "heading" and line.rstrip() != new.rstrip():
            hunk = {"id": len(hunks) + 1, "line": oi + 1, "where": where, "kind": "heading",
                    "before": [line], "after": [new], "original": [line], "lead": [],
                    "trail": [], "reply_line": ri + 1}
            _check_hunk(hunk, messages)
            hunks.append(hunk)
            plan.append(("hunk", hunk))
        else:
            plan.append(("keep", [line]))
        if o_entries[oi][0] == "heading":
            m = HEADING_RE.match(line)
            where = _marks_of(m.group(2))[1] if m else ""
        o_from, r_from = oi + 1, ri + 1
    o_seg, r_seg = original[o_from:], reply[r_from:]
    if not tail or _same_words(o_seg, r_seg):
        plan.append(("keep", o_seg))
    else:
        passage(o_seg, r_seg)
    return plan, hunks


def _check_hunk(hunk, messages):
    """A change of wording may not lose or change a number, a formula, a
    piece of code in backticks or a picture's file name."""
    before, after = hunk["before"], hunk["after"]
    where, at = hunk["where"], hunk["reply_line"]
    if _spans(before) != _spans(after):
        gone, new = _changed(_spans(before), _spans(after))
        messages.problem(
            "reply-formula-changed", at,
            f"The reply changes a formula, a piece of code or a picture's file name in "
            f"\"{_excerpt(before)}\". It drops {gone} and adds {new}.",
            "Ask the assistant to keep every formula, piece of code and file name as it was.",
            "the reply")
    if _numbers(before) != _numbers(after):
        gone, new = _changed(_numbers(before), _numbers(after))
        messages.problem(
            "reply-number-changed", at,
            f"The reply changes a number in \"{_excerpt(before)}\". It drops {gone} and "
            f"adds {new}.",
            "Ask the assistant to keep every number exactly as it was.", "the reply")


def _assemble(plan, accepted):
    lines = []
    for kind, item in plan:
        if kind == "keep":
            lines += item
        elif item["id"] in accepted:
            lines += item["lead"] + item["after"] + item["trail"]
        else:
            lines += item["original"]
    return lines


def _public(hunk, accepted):
    return {"id": hunk["id"], "line": hunk["line"], "where": hunk["where"],
            "kind": hunk["kind"], "before": hunk["before"], "after": hunk["after"],
            "accepted": hunk["id"] in accepted}


# --- copy without composing ---------------------------------------------------

def _skeleton(paper):
    """A marking scheme of `(draft)` entries for a paper that has none: one
    for each part that has marks of its own. The teacher fills them."""
    out = ["", "# Marking scheme", ""]
    for name, unit in paper["units"].items():
        if unit["level"] == 2 and unit["children"]:
            out += [f"## Question {unit['label']}", ""]
        elif not unit["children"]:
            out += [f"### {unit['label']} (draft)", ""]
    return "\n".join(out)


def _prose_words(lines, has_settings):
    """The words of a paper, with the line each is on: not its settings, not
    the fence lines that open and close answer boxes, and not the words that
    only mark structure ("marks", "Question")."""
    words, index = [], 0
    if has_settings and lines and lines[0].strip() == "---":
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), len(lines) - 1)
        index = end + 1
    fence = None
    for number, line in enumerate(lines[index:], index + 1):
        if fence:
            if _is_closing(line, fence):
                fence = None
                continue
        else:
            opener = FENCE_RE.match(line)
            if opener:
                fence = opener.group(1)
                continue
        for m in WORD_RE.finditer(line):
            word = m.group(0).lower().replace("’", "'")
            if word not in STRUCTURE_WORDS:
                words.append((word, number))
    return words


def _copy_problems(original, paper_lines, messages):
    """How far a "copy" reply keeps the words and numbers of the Word text.
    Returns the fraction of the paper's words the reply keeps, in order, or
    None if the paper is too long to compare word by word."""
    kept = _compare_words(original, paper_lines, messages)
    have, given = _numbers(original.split("\n")), _numbers(paper_lines)
    gone = sorted(n for n in have if n not in given)
    fewer = sorted(n for n in have if 0 < given[n] < have[n])
    if gone:
        messages.problem(
            "reply-number-lost", 1,
            "These numbers are in your paper and not in the reply: " + ", ".join(gone) + ".",
            "Ask the assistant to copy every number exactly, or put them back in the reply.",
            "the reply")
    if fewer:
        messages.warning(
            "reply-number-fewer", 1,
            "These numbers are in the reply fewer times than in your paper: "
            + ", ".join(fewer) + ".",
            "Marks written twice in the Word paper are often written once here. Check "
            "that none of them is a number the assistant dropped.", "the reply")
    return kept


def _compare_words(original, paper_lines, messages):
    o_words = _prose_words(original.split("\n"), False)
    r_words = _prose_words(paper_lines, True)
    if max(len(o_words), len(r_words)) > MAX_WORDS:
        messages.warning(
            "reply-words-not-compared", 1,
            f"The paper has more than {MAX_WORDS} words, so its words were not compared "
            "with the reply's.", "Read the paper against the Word text yourself.", "the reply")
        return None
    matcher = difflib.SequenceMatcher(None, [w for w, _ in o_words], [w for w, _ in r_words],
                                      autojunk=False)
    shown = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        shown += 1
        if shown == MOST + 1:
            messages.warning("reply-words-changed", 1,
                             "There are more differences in wording, not listed here.",
                             "", "the reply")
        if shown > MOST:
            continue
        gone = " ".join(w for w, _ in o_words[i1:i2])[:80]
        new = " ".join(w for w, _ in r_words[j1:j2])[:80]
        at = r_words[j1][1] if j1 < len(r_words) else len(paper_lines)
        if tag == "replace":
            what = f"The reply has \"{new}\" where your paper has \"{gone}\"."
        elif tag == "insert":
            what = f"The reply adds the words \"{new}\", which are not in your paper."
        else:
            what = f"The reply leaves out the words \"{gone}\", which are in your paper."
        messages.warning("reply-words-changed", at, what,
                         "Copy without composing means no word changes. Correct it in the "
                         "reply, or ask the assistant to copy the words exactly.", "the reply")
    kept = sum(b.size for b in matcher.get_matching_blocks())
    return kept / len(o_words) if o_words else 1.0


def _check_copy(original, paper, about, messages):
    lines = paper.split("\n")
    block, missing = settings_block(about)
    if missing:
        messages.problem(
            "reply-about-missing", 1,
            "The reply can't be checked until the paper's details are filled in: "
            + " ".join(missing), "Fill in the details and check again.", "the paper's details")
        return None, 0.0
    if lines[:len(block.split("\n"))] != block.split("\n"):
        messages.problem(
            "reply-settings-changed", 1,
            "The settings at the top of the reply are not the ones you gave.",
            "Put back the settings dewmark gave the assistant, or ask it to use them exactly.",
            "the reply")
    kept = _copy_problems(original, lines, messages)
    try:
        first = read(paper)
    except Exception as error:      # the reader never raises; belt and braces
        messages.problem("reply-unreadable", 1, f"The reply couldn't be read ({error}).", "", "the reply")
        return None, kept
    return paper.rstrip("\n") + "\n" + _skeleton(first), kept


# --- the check ----------------------------------------------------------------

def check_reply(original, reply, mode, about=None, accept=None):
    """Check what an assistant returned.

    `original` is the teacher's paper: an exam file for the wording modes, a
    Word paper's text for "copy" (which also needs `about`, the paper's
    settings). `accept` is a list of hunk ids the teacher has accepted;
    None accepts them all. Returns a dict: "ok", "messages", "hunks",
    "text" (the file with the accepted changes made, or None), "notes"
    (what the assistant said it changed) and "kept" (for "copy", the share
    of the paper's words the reply keeps).
    """
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}; the modes are {', '.join(MODES)}")
    original = _tidy(original)
    paper, notes, messages = extract_reply(reply)
    result = {"ok": False, "messages": messages, "hunks": [], "text": None,
              "notes": notes, "kept": None}
    if not paper.strip():
        messages.problem("reply-empty", 1, "The reply has no paper in it.",
                         "Paste everything the assistant returned.", "the reply")
        return result
    if max(paper.count("\n"), original.count("\n")) >= MAX_LINES:
        messages.problem(
            "reply-too-long", 1,
            f"The paper or the reply is longer than {MAX_LINES} lines, which is more than "
            "dewmark compares.", "Convert or reword the paper in parts.", "the reply")
        return result

    if not MODES[mode].words:
        text, kept = _check_copy(original, paper, about, messages)
        result["kept"], result["text"] = kept, text
    else:
        head, rest = split_halves(original)
        reply_head, reply_rest = split_halves(paper)
        if reply_rest.strip():
            what = "a marking scheme" if any(
                l.strip().lower().startswith("# mark") for l in reply_rest.split("\n")) \
                else "cards under # Reference"
            messages.problem(
                "reply-has-scheme", 1,
                f"The reply has {what} in it. dewmark keeps your own and never takes one "
                "from an assistant.", "Ask for the paper only, without a scheme.", "the reply")
        o_lines, r_lines = head.split("\n"), reply_head.split("\n")
        agree, pairs, tail = _fixed_problems(o_lines, r_lines, messages)
        plan, hunks = _plan(o_lines, r_lines, pairs, tail, messages)
        if agree and not any(m.level == "problem" for m in messages):
            every = {h["id"] for h in hunks}
            chosen = every if accept is None else every & set(accept)
            result["hunks"] = [_public(h, chosen) for h in hunks]
            text = "\n".join(_assemble(plan, chosen))
            result["text"] = text + ("\n" + rest if rest else "")
    if result["text"] is not None:
        baseline = set()
        if MODES[mode].words:       # problems the teacher's paper already had
            baseline = {(m.code, m.where) for m in read(original)["messages"]}
        for m in read(result["text"])["messages"]:
            if (m.code, m.where) not in baseline:
                messages.append(m)
    result["ok"] = result["text"] is not None and not any(
        m.level == "problem" and m.code.startswith("reply-") for m in messages)
    return result
