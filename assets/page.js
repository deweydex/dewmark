"use strict";

/* The behaviour of a dewmark exam page built from the new format
   (dewmark/build.py). The older page, assets/exam-page.js, is untouched until
   the older builder is retired; this one is organised around a registry of
   answer kinds (KINDS), each saying how to collect an answer from its controls,
   how to put a saved one back, and nothing else. The page never builds HTML
   from what a student or an answer file holds: it sets .value and .textContent. */

const MODEL = JSON.parse(document.getElementById("dewmark-page-model").textContent);

/* Each of a paper's pages keeps its own save slot: the student page, the
   practice page and the answer key are built from one exam code, and a shared
   slot once let one page offer another's work as the student's own. The answer
   key saves nothing at all. */
const VARIANT = MODEL.variant;
const STORAGE_KEY = "dewmark:" + MODEL.exam.code + ":" + VARIANT;
const SAVES = VARIANT !== "answer-key";
const ANSWERS_FORMAT = "dewmark-answers/1";

/* Nothing is written to storage until the student has entered the paper
   (Begin or Continue). Before that the page holds only a blank state, and
   writing it would wipe the saved work the start screen is offering to
   restore. A second copy of the paper in the same browser never writes. */
let canWrite = false;
let secondWindow = false;

let state = {
  format: ANSWERS_FORMAT,
  exam: { code: MODEL.exam.code, version: MODEL.exam.version, title: MODEL.exam.title },
  page: VARIANT,
  student: {},
  started_at: null,
  saved_at: null,
  finished_at: null,
  answers: {},
};
let fileHandle = null;
let fileSaveTimer = null;

const $ = (id) => document.getElementById(id);

/* --- the kinds of answer box ---------------------------------------------------
   An unanswered box is absent from state.answers, so "answered" means present.
   A box that still holds only its starting text counts as unanswered.
   Stored shapes (docs/ANSWER_FILE.md):
     answer, maths, code, essay    a string
     choice                        a list of option letters
     boxes, blanks, table          a list of strings, one for each place to fill
     python exec                   {code: a string}                              */

function changed(field) {
  const text = field.value.trim();
  return text !== "" && text !== field.defaultValue.trim();
}

function textKind(selector) {
  return {
    collect(root) {
      const field = root.querySelector(selector);
      return changed(field) ? field.value : null;
    },
    apply(root, value) {
      if (typeof value === "string") root.querySelector(selector).value = value;
    },
  };
}

const slotKind = {
  places(root) {
    return [...root.querySelectorAll("[data-slot]")]
      .sort((a, b) => Number(a.dataset.slot) - Number(b.dataset.slot));
  },
  collect(root) {
    const values = this.places(root).map((el) => el.value);
    return values.some((v) => v.trim()) ? values : null;
  },
  apply(root, value) {
    if (!Array.isArray(value)) return;
    this.places(root).forEach((el, i) => {
      const given = typeof value[i] === "string" ? value[i] : "";
      // A drop-down only takes one of its own choices.
      el.value = given;
      if (el.value !== given) el.value = "";
    });
  },
};

const KINDS = {
  answer: textKind(".dm-writing"),
  maths: textKind(".dm-writing"),
  essay: textKind(".dm-essay"),
  code: textKind(".dm-code"),
  "python exec": {
    collect(root) {
      const field = root.querySelector(".dm-code");
      return changed(field) ? { code: field.value } : null;
    },
    apply(root, value) {
      if (value && typeof value.code === "string") root.querySelector(".dm-code").value = value.code;
    },
  },
  choice: {
    collect(root) {
      const picked = [...root.querySelectorAll("input:checked")].map((el) => el.value);
      return picked.length ? picked : null;
    },
    apply(root, value) {
      const picked = Array.isArray(value) ? value : [];
      for (const el of root.querySelectorAll("input")) el.checked = picked.includes(el.value);
    },
  },
  boxes: slotKind,
  blanks: slotKind,
  table: slotKind,
};

function collectAnswer(root) {
  const kind = KINDS[root.dataset.kind];
  return kind ? kind.collect(root) : null;
}

function applyAnswer(root, value) {
  const kind = KINDS[root.dataset.kind];
  if (kind && value !== undefined && value !== null) kind.apply(root, value);
}

function gatherState() {
  for (const root of document.querySelectorAll(".dm-answer")) {
    const name = root.dataset.answer;
    const value = collectAnswer(root);
    if (value === null) delete state.answers[name];
    else state.answers[name] = value;
  }
  state.saved_at = new Date().toISOString();
  return state;
}

/* --- saving ----------------------------------------------------------------------- */

function setPill(id, text, cls) {
  const el = $(id);
  el.textContent = text;
  el.className = "dm-save-pill" + (cls ? " " + cls : "");
}

function saveEverywhere() {
  gatherState();
  if (!canWrite) {
    refreshProgress();
    return;
  }
  const clock = new Date().toLocaleTimeString(
    [], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    setPill("dm-save-browser", "Browser ✓ " + clock, "dm-ok");
  } catch (err) {
    setPill("dm-save-browser", "Browser save failed", "dm-off");
  }
  if (fileHandle) {
    clearTimeout(fileSaveTimer);
    fileSaveTimer = setTimeout(async () => {
      try {
        const writable = await fileHandle.createWritable();
        await writable.write(JSON.stringify(state, null, 2));
        await writable.close();
        setPill("dm-save-file", "File ✓ " + clock, "dm-ok");
      } catch (err) {
        fileHandle = null;
        setPill("dm-save-file", "File saving is off", "dm-off");
      }
    }, 800);
  }
  refreshProgress();
}

function safeName(text) {
  return String(text || "").toLowerCase()
    .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "student";
}

function submissionBaseName() {
  const details = state.student || {};
  return "dewmark_" + MODEL.exam.code + "_" + safeName(details["student number"])
    + "_" + safeName(details["full name"]);
}

function validState(candidate) {
  /* An answer file comes from a disk, so it is checked, not trusted. */
  return candidate && typeof candidate === "object"
    && candidate.format === ANSWERS_FORMAT
    && candidate.exam && candidate.exam.code === MODEL.exam.code
    && (!candidate.page || candidate.page === VARIANT)
    && candidate.answers && typeof candidate.answers === "object"
    && !Array.isArray(candidate.answers)
    && candidate.student && typeof candidate.student === "object";
}

function readStoredState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return validState(parsed) ? parsed : null;
  } catch (err) {
    return null;
  }
}

function describeState(candidate, label) {
  const count = Object.keys(candidate.answers || {}).length;
  const when = candidate.saved_at
    ? new Date(candidate.saved_at).toLocaleString() : "an unknown time";
  return label + ": " + count + " answers, saved " + when;
}

function adoptState(candidate) {
  state = candidate;
  const details = state.student || {};
  for (const el of document.querySelectorAll("[data-detail]")) {
    el.value = typeof details[el.dataset.detail] === "string" ? details[el.dataset.detail] : "";
  }
}

/* Starting afresh when this browser holds saved work for the paper keeps that
   work under a set-aside key rather than writing over it, so an invigilator can
   still recover it. */
function setAsideStoredWork() {
  const stored = readStoredState();
  if (!stored || !Object.keys(stored.answers || {}).length) return true;
  const keep = confirm("This browser holds saved work for this paper ("
    + describeState(stored, "saved work") + ").\n\n"
    + "Press OK to start again. The saved work is kept aside on this "
    + "computer, not deleted. Press Cancel to go back and continue from "
    + "it instead.");
  if (!keep) return false;
  try {
    localStorage.setItem(STORAGE_KEY + ":set-aside:"
      + (stored.saved_at || new Date().toISOString()), JSON.stringify(stored));
  } catch (err) {
    alert("The saved work could not be kept aside, so nothing has "
      + "changed. Ask the invigilator for help.");
    return false;
  }
  return true;
}

async function begin() {
  for (const el of document.querySelectorAll("[data-detail]")) {
    if (!el.value.trim()) {
      alert("Please fill in your " + el.dataset.detail + ".");
      el.focus();
      return;
    }
  }
  if (SAVES && !secondWindow && !setAsideStoredWork()) return;
  for (const el of document.querySelectorAll("[data-detail]")) {
    state.student[el.dataset.detail] = el.value.trim();
  }
  if (!state.started_at) state.started_at = new Date().toISOString();

  if (SAVES && !secondWindow && "showSaveFilePicker" in window) {
    try {
      fileHandle = await window.showSaveFilePicker({
        suggestedName: submissionBaseName() + ".json",
        types: [{ description: "dewmark answer file",
                  accept: { "application/json": [".json"] } }],
      });
    } catch (err) {
      fileHandle = null;
    }
  }
  if (!fileHandle) {
    setPill("dm-save-file", SAVES ? "File saving is off"
      : "The answer key saves nothing", "dm-off");
  }
  enterExam();
}

function enterExam() {
  $("dm-start").hidden = true;
  $("dm-app").hidden = false;
  $("dm-top-student").textContent =
    Object.values(state.student).filter(Boolean).join(" · ");
  for (const root of document.querySelectorAll(".dm-answer")) {
    applyAnswer(root, state.answers[root.dataset.answer]);
  }
  countWords();
  buildPanel();
  canWrite = SAVES && !secondWindow;
  if (!SAVES) setPill("dm-save-browser", "The answer key saves nothing", "dm-off");
  saveEverywhere();
}

function loadAnswerFile() {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = "application/json,.json";
  input.onchange = async () => {
    const file = input.files[0];
    if (!file) return;
    let loaded;
    try {
      loaded = JSON.parse(await file.text());
    } catch (err) {
      alert("That file could not be read as an answer file.");
      return;
    }
    if (!validState(loaded)) {
      alert("That file is not an answer file for this paper, so it cannot be "
        + "loaded here.");
      return;
    }
    const stored = readStoredState();
    if (stored && stored.saved_at !== loaded.saved_at
        && Object.keys(stored.answers || {}).length) {
      const keepFile = confirm(
        "This browser also holds saved work for this paper.\n\n"
        + describeState(loaded, "The file") + "\n"
        + describeState(stored, "This browser") + "\n\n"
        + "Press OK to continue from the file, or Cancel to continue "
        + "from this browser.");
      if (!keepFile) { adoptState(stored); enterExam(); return; }
    }
    adoptState(loaded);
    enterExam();
  };
  input.click();
}

/* --- progress and the finish report ------------------------------------------------- */

function partAnswered(part) {
  return part.boxes.some((name) => name in state.answers);
}

function questionAttempted(name) {
  return MODEL.questions[name].parts.some(partAnswered);
}

function refreshProgress() {
  for (const root of document.querySelectorAll(".dm-answer")) {
    root.classList.toggle("dm-answered", root.dataset.answer in state.answers);
  }
  for (const section of MODEL.sections) {
    for (const name of section.questions) {
      const button = document.querySelector('[data-panel-question="' + name + '"]');
      if (button) button.classList.toggle("dm-done", questionAttempted(name));
    }
    const label = document.querySelector('[data-panel-count="' + section.index + '"]');
    if (label && section.any) {
      const attempted = section.questions.filter(questionAttempted).length;
      label.textContent = "answered " + attempted + " · " + section.any + " will count";
    }
  }
}

function buildPanel() {
  const panel = $("dm-panel-questions");
  panel.replaceChildren();
  for (const section of MODEL.sections) {
    if (section.title) {
      const heading = document.createElement("h2");
      heading.textContent = section.title;
      panel.appendChild(heading);
    }
    if (section.any) {
      const note = document.createElement("p");
      note.className = "dm-panel-note";
      note.dataset.panelCount = section.index;
      panel.appendChild(note);
    }
    for (const name of section.questions) {
      const question = MODEL.questions[name];
      const button = document.createElement("button");
      button.type = "button";
      button.className = "dm-panel-q";
      button.dataset.panelQuestion = name;
      const left = document.createElement("span");
      left.textContent = "Question " + question.label;
      const right = document.createElement("span");
      right.textContent = "(" + question.marks + ")";
      button.append(left, right);
      button.addEventListener("click", () => {
        const target = document.querySelector('[data-question="' + name + '"]');
        if (target) target.scrollIntoView({ behavior: "smooth" });
      });
      panel.appendChild(button);
    }
  }
  refreshProgress();
}

function finishReport() {
  const list = document.createElement("ul");
  const line = (text, cls) => {
    const item = document.createElement("li");
    if (cls) item.className = cls;
    item.textContent = text;
    list.appendChild(item);
  };
  const empty = [];
  for (const name of Object.keys(MODEL.questions)) {
    for (const part of MODEL.questions[name].parts) {
      if (part.marks && !partAnswered(part)) empty.push(part);
    }
  }
  if (!empty.length) {
    line("Every part has something in it.", "dm-finish-good");
  } else {
    const total = empty.reduce((sum, part) => sum + part.marks, 0);
    line(empty.length + (empty.length === 1 ? " part is" : " parts are")
      + " empty, worth " + total + " marks: " + empty.map((p) => p.label).join(", "),
      "dm-finish-warn");
  }
  for (const section of MODEL.sections) {
    if (!section.any) continue;
    const attempted = section.questions.filter(questionAttempted).length;
    line(section.title + ": " + attempted + " answered, " + section.any + " will count.",
      attempted >= section.any ? "dm-finish-good" : "dm-finish-warn");
  }
  line("Handing in as: " + Object.values(state.student).filter(Boolean).join(" · "));
  return list;
}

/* --- the files a student keeps ------------------------------------------------------- */

function save(blob, name) {
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = name;
  link.click();
  URL.revokeObjectURL(link.href);
}

function downloadAnswerFile() {
  gatherState();
  save(new Blob([JSON.stringify(state, null, 2)], { type: "application/json" }),
    submissionBaseName() + ".json");
}

function readableCopy() {
  /* The paper with the answers written in as text: the student's own record,
     openable anywhere, with no script in it. Each control is replaced by what
     the student gave, in the place they gave it. */
  gatherState();
  const clone = document.documentElement.cloneNode(true);
  for (const el of clone.querySelectorAll(
      "script, button, #dm-panel, #dm-start, #dm-finish-screen, .dm-save-pill")) {
    el.remove();
  }
  for (const el of clone.querySelectorAll("#dm-app, #dm-topbar")) el.hidden = false;
  const shown = (text, block) => {
    const el = document.createElement(block ? "div" : "span");
    el.className = block ? "dm-given-block" : "dm-given";
    el.textContent = text && text.trim() ? text : "(blank)";
    return el;
  };
  for (const root of clone.querySelectorAll(".dm-answer")) {
    const value = state.answers[root.dataset.answer];
    const kind = root.dataset.kind;
    if (value === undefined) {
      for (const el of root.querySelectorAll("textarea, input, select, .dm-options, .dm-code-bar")) {
        el.remove();
      }
      const none = document.createElement("p");
      none.className = "dm-none";
      none.textContent = "(not attempted)";
      root.appendChild(none);
    } else if (kind === "choice") {
      for (const option of root.querySelectorAll(".dm-option")) {
        const letter = option.querySelector("input").value;
        if (!value.includes(letter)) option.remove();
        else option.querySelector("input").replaceWith("✓");
      }
    } else if (["boxes", "blanks", "table"].includes(kind)) {
      for (const el of root.querySelectorAll("[data-slot]")) {
        el.replaceWith(shown(value[Number(el.dataset.slot) - 1], false));
      }
    } else {
      const text = typeof value === "string" ? value : value.code;
      for (const el of root.querySelectorAll("textarea")) el.replaceWith(shown(text, true));
    }
  }
  const student = Object.entries(state.student)
    .map(([key, value]) => key + ": " + value).join(" · ");
  const note = document.createElement("p");
  note.setAttribute("style", "font-family: system-ui, sans-serif; font-size: 13px;"
    + " border: 1px solid #ddd7cd; padding: 8px 12px;");
  note.textContent = "Readable copy of a dewmark answer file · " + student + " · saved " + state.saved_at;
  clone.querySelector("#dm-paper").before(note);
  return "<!doctype html>\n<html lang=\"en-IE\">" + clone.innerHTML + "</html>";
}

function downloadReadableCopy() {
  save(new Blob([readableCopy()], { type: "text/html" }), submissionBaseName() + ".html");
}

/* --- wiring --------------------------------------------------------------------------- */

function countWords() {
  for (const root of document.querySelectorAll('.dm-answer[data-kind="essay"]')) {
    const words = root.querySelector(".dm-essay").value.trim().split(/\s+/).filter(Boolean).length;
    root.querySelector(".dm-word-count").textContent = words + (words === 1 ? " word" : " words");
  }
}

$("dm-begin").addEventListener("click", begin);
$("dm-load-file").addEventListener("click", loadAnswerFile);
$("dm-download").addEventListener("click", downloadAnswerFile);
$("dm-finish").addEventListener("click", () => {
  gatherState();
  $("dm-finish-report").replaceChildren(finishReport());
  $("dm-app").hidden = true;
  $("dm-finish-screen").hidden = false;
});
$("dm-keep-working").addEventListener("click", () => {
  $("dm-finish-screen").hidden = true;
  $("dm-app").hidden = false;
});
$("dm-submit").addEventListener("click", () => {
  state.finished_at = new Date().toISOString();
  saveEverywhere();
  downloadAnswerFile();
});
$("dm-save-readable").addEventListener("click", downloadReadableCopy);

document.addEventListener("input", (event) => {
  if (event.target.closest(".dm-answer")) {
    countWords();
    saveEverywhere();
  }
});
document.addEventListener("change", (event) => {
  if (event.target.closest(".dm-answer")) saveEverywhere();
});
window.addEventListener("beforeunload", () => {
  if (!canWrite) return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(gatherState()));
  } catch (err) { /* the periodic save already reported storage trouble */ }
});

/* If this browser already holds saved work for this paper, offer to continue
   from it rather than starting blank. */
const stored = readStoredState();
if (stored && Object.keys(stored.answers || {}).length) {
  const note = document.createElement("p");
  note.className = "dm-restore-note";
  note.textContent = "Saved work was found (" + describeState(stored, "this browser") + "). ";
  const resume = document.createElement("button");
  resume.type = "button";
  resume.className = "dm-secondary";
  resume.textContent = "Continue from saved work";
  resume.addEventListener("click", () => { adoptState(stored); enterExam(); });
  note.appendChild(resume);
  $("dm-start").prepend(note);
}

/* A second copy of the paper open in this browser must not save over the first;
   the second copy detects the first and steps back. */
const channel = "BroadcastChannel" in window ? new BroadcastChannel(STORAGE_KEY) : null;
if (channel) {
  let iAmFirst = true;
  channel.onmessage = (event) => {
    if (event.data === "anyone-there?" && iAmFirst) channel.postMessage("yes");
    if (event.data === "yes") {
      iAmFirst = false;
      secondWindow = true;
      canWrite = false;
      /* Every way into the paper is closed, not only the Begin button. */
      for (const button of document.querySelectorAll(
          "#dm-begin, #dm-load-file, .dm-restore-note button")) {
        button.disabled = true;
      }
      alert("This paper is already open in another window on this computer. "
        + "Please continue there; this window will not save.");
    }
  };
  channel.postMessage("anyone-there?");
}
