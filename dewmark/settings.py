"""The settings at the top of an exam file (docs/EXAM_FORMAT.md §4.9).

Settings are `key: value` lines between two `---` lines. A key's
capitals, spaces, underscores and hyphens do not matter. Every value is
text until a known key converts it, which is how `No`, `1.10` and `0123`
survive as written. Unknown keys, repeated keys and values outside a
key's list are refused with the nearest match.
"""

import difflib
import re

# Every setting the format knows, with its list of allowed values where it
# has one. None means free text.
SWITCH = ("on", "off")
KNOWN = {
    "dewmark": None,
    "code": None,
    "version": None,
    "kind": ("exam", "practice", "sample"),
    "title": None,
    "module": None,
    "module code": None,
    "institution": None,
    "college": None,
    "session": None,
    "logo": None,
    "total marks": None,
    "time allowed": None,
    "timer": ("none", "shown", "enforced"),
    "breaks": SWITCH,
    "calculator": ("none", "basic", "scientific"),
    "maths input": None,
    "hand in": None,
    "python from": ("this file", "internet"),
    "python packages": None,
    "python time limit": None,
    "code completion": SWITCH,
    "error hints": SWITCH,
    "python reference": ("yes", "no"),
    "show answers": ("never", "after finishing"),
    "practice tests": ("never", "after finishing", "while working"),
    "weighting": None,
    "technique": None,
    "outcomes": None,
    "number example": None,
}
SWITCH_WORDS = {"on": "on", "yes": "on", "true": "on",
                "off": "off", "no": "off", "false": "off"}
REQUIRED = ("code", "kind", "total marks", "time allowed")
REQUIRED_FOR_EXAM = ("title", "module", "module code")
MATHS_INPUTS = ("text", "visual", "photo")
CODE_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def normal_key(key):
    return re.sub(r"[\s_\-]+", " ", key.strip().lower())


def _nearest(word, choices):
    near = difflib.get_close_matches(word, choices, n=1, cutoff=0.6)
    return near[0] if near else None


def read_settings(lines, messages):
    """Read the settings block from the start of the file.

    `lines` is the list of (line number, text). Returns (settings, index of
    the first line after the block).
    """
    settings = {}
    seen = {}
    if not lines or lines[0][1].strip() != "---":
        messages.problem(
            "no-settings", lines[0][0] if lines else 1,
            "The file must begin with its settings, between two lines of three dashes.",
            "Start the file with ---, the settings one per line, then --- again.")
        return settings, 0
    for index in range(1, len(lines)):
        number, text = lines[index]
        if text.strip() == "---":
            _after(settings, seen, messages)
            return settings, index + 1
        if not text.strip() or text.lstrip().startswith("#"):
            continue
        if ":" not in text:
            messages.problem(
                "setting-without-colon", number,
                f"This settings line has no colon: \"{text.strip()}\".",
                "Write each setting as a name, a colon, then its value.")
            continue
        raw_key, value = text.split(":", 1)
        key, value = normal_key(raw_key), value.strip()
        if key not in KNOWN:
            near = _nearest(key, list(KNOWN))
            messages.problem(
                "unknown-setting", number,
                f"dewmark doesn't know the setting \"{raw_key.strip()}\".",
                f"Did you mean \"{near}\"?" if near else
                "The settings dewmark knows are listed in docs/EXAM_FORMAT.md §4.9.")
            continue
        if key in seen:
            messages.problem(
                "repeated-setting", number,
                f"\"{key}\" is set twice (lines {seen[key]} and {number}).",
                "Keep one of them.")
            continue
        seen[key] = number
        allowed = KNOWN[key]
        if allowed is SWITCH:
            converted = SWITCH_WORDS.get(value.lower())
            if converted is None:
                messages.problem(
                    "setting-value", number,
                    f"\"{key}\" is a switch, so it can be on or off, not \"{value}\".")
                continue
            value = converted
        elif allowed and allowed == ("yes", "no"):
            converted = SWITCH_WORDS.get(value.lower())
            if converted is None:
                messages.problem(
                    "setting-value", number,
                    f"\"{key}\" can be yes or no, not \"{value}\".")
                continue
            value = "yes" if converted == "on" else "no"
        elif allowed:
            if value.lower() not in allowed:
                near = _nearest(value.lower(), list(allowed))
                extra = " The student can always hide the timer themselves." if key == "timer" else ""
                messages.problem(
                    "setting-value", number,
                    f"\"{key}: {value}\" isn't one of the choices. \"{key}\" can be "
                    + ", ".join(allowed[:-1]) + f" or {allowed[-1]}." + extra,
                    f"Did you mean \"{near}\"?" if near else "")
                continue
            value = value.lower()
        elif key == "maths input":
            chosen = [w.strip().lower() for w in value.split(",") if w.strip()]
            wrong = [w for w in chosen if w not in MATHS_INPUTS]
            if wrong or not chosen:
                messages.problem(
                    "setting-value", number,
                    "\"maths input\" lists text, visual or photo, separated by commas, "
                    f"not \"{value}\".")
                continue
            value = ", ".join(chosen)
        settings[key] = value
        settings.setdefault("_lines", {})[key] = number
    messages.problem(
        "settings-never-end", lines[0][0],
        "The settings at the top never end.",
        "Add a line of three dashes after the last setting.")
    return settings, len(lines)


def _after(settings, seen, messages):
    """Checks that need the whole settings block."""
    first = 1
    kind = settings.get("kind")
    for key in REQUIRED + (REQUIRED_FOR_EXAM if kind == "exam" else ()):
        if key not in settings:
            messages.problem(
                "missing-setting", first,
                f"The settings need \"{key}\"." + (
                    " An exam paper must name its title, module and module code."
                    if key in REQUIRED_FOR_EXAM else ""),
                f"Add a line \"{key}: …\" between the dashes.")
    if "dewmark" not in settings:
        messages.warning(
            "no-format-version", first,
            "The settings don't say which version of the exam format this file uses.",
            "Add \"dewmark: 1\" as the first setting.")
    code = settings.get("code")
    if code and not CODE_RE.match(code):
        messages.problem(
            "code-shape", seen.get("code", first),
            f"\"code: {code}\" must use only small letters, digits and hyphens, "
            "because it names files and the saved answers.",
            f"For example: code: {re.sub(r'[^a-z0-9]+', '-', code.lower()).strip('-') or 'my-exam-2027'}")
    if kind == "exam":
        for key in ("show answers", "practice tests"):
            if settings.get(key, "never") != "never":
                messages.problem(
                    "exam-shows-answers", seen.get(key, first),
                    f"An exam paper can't have \"{key}: {settings[key]}\". Only practice "
                    "and sample papers show answers or run tests.",
                    f"Remove the \"{key}\" line, or make this a practice paper.")
    if "timer" not in settings:
        settings["timer"] = "shown" if settings.get("time allowed") else "none"
    for key, default in (("breaks", "off"), ("calculator", "none"), ("maths input", "text"),
                         ("python from", "this file"), ("code completion", "off"),
                         ("error hints", "on"), ("python reference", "no"),
                         ("show answers", "never"), ("practice tests", "never"),
                         ("version", "1")):
        settings.setdefault(key, default)
    if settings.get("python from") == "internet" and kind == "exam":
        messages.warning(
            "python-from-internet", seen.get("python from", first),
            "This exam loads Python from the internet, so it cannot run code in a room "
            "without a connection.",
            "Use \"python from: this file\" for an exam room.")
