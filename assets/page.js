"use strict";

/* The behaviour of a dewmark exam page built from the new format
   (dewmark/build.py joins this file, assets/page-reading.js and
   assets/page-start.js into one script, in that order, so they share names).
   The older page, assets/exam-page.js, is untouched until the older builder is
   retired.

   This file holds the answer kinds, saving and finishing; it is organised
   around a registry of kinds (KINDS), each saying how to collect an answer from
   its controls, how to put a saved one back, and nothing else. The page never
   builds HTML from what a student or an answer file holds: it sets .value and
   .textContent. */

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

function blankState() {
  return {
    format: ANSWERS_FORMAT,
    exam: {
      code: MODEL.exam.code, version: MODEL.exam.version, title: MODEL.exam.title,
      fingerprint: MODEL.exam.fingerprint,
    },
    page: VARIANT,
    student: {},
    started_at: null,
    saved_at: null,
    finished_at: null,
    receipt: null,
    answers: {},
  };
}
let state = blankState();

/* --- receipts ----------------------------------------------------------------------
   The receipt is the start of a SHA-256 of the record in a canonical form, and
   dewmark/receipt.py makes the same code from the same record (the workbench
   will show it again from the file). The hash is written out here so that the
   receipt does not depend on crypto.subtle, which browsers offer only to a
   secure context, and so that it is worked out at once and not in a promise.
   tests/browser/test_page.py checks it, and the canonical text, against
   Python's hashlib and receipt(). */

const SHA_K = new Uint32Array([
  0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
  0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
  0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
  0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
  0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
  0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
  0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
  0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
]);

/* SHA-256 of a Uint8Array, as a Uint8Array of 32 bytes. */
function sha256(bytes) {
  const rotr = (x, n) => (x >>> n) | (x << (32 - n));
  const h = new Uint32Array([0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
    0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]);
  const padded = new Uint8Array(((bytes.length + 9 + 63) >> 6) << 6);
  padded.set(bytes);
  padded[bytes.length] = 0x80;
  const view = new DataView(padded.buffer);
  view.setUint32(padded.length - 8, Math.floor(bytes.length / 0x20000000));
  view.setUint32(padded.length - 4, (bytes.length * 8) >>> 0);
  const w = new Uint32Array(64);
  for (let offset = 0; offset < padded.length; offset += 64) {
    for (let i = 0; i < 16; i++) w[i] = view.getUint32(offset + i * 4);
    for (let i = 16; i < 64; i++) {
      const s0 = rotr(w[i - 15], 7) ^ rotr(w[i - 15], 18) ^ (w[i - 15] >>> 3);
      const s1 = rotr(w[i - 2], 17) ^ rotr(w[i - 2], 19) ^ (w[i - 2] >>> 10);
      w[i] = w[i - 16] + s0 + w[i - 7] + s1;
    }
    let [a, b, c, d, e, f, g, k] = h;
    for (let i = 0; i < 64; i++) {
      const t1 = k + (rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25)) + ((e & f) ^ (~e & g)) + SHA_K[i] + w[i];
      const t2 = (rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22)) + ((a & b) ^ (a & c) ^ (b & c));
      k = g; g = f; f = e; e = (d + t1) | 0; d = c; c = b; b = a; a = (t1 + t2) | 0;
    }
    h[0] += a; h[1] += b; h[2] += c; h[3] += d; h[4] += e; h[5] += f; h[6] += g; h[7] += k;
  }
  const out = new Uint8Array(32);
  const result = new DataView(out.buffer);
  h.forEach((word, i) => result.setUint32(i * 4, word));
  return out;
}

const hex = (bytes) => Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");

/* Keys in the order Python sorts them: by code point, not by UTF-16 unit. */
function compareCodePoints(a, b) {
  const x = Array.from(a), y = Array.from(b);
  for (let i = 0; i < Math.min(x.length, y.length); i++) {
    const difference = x[i].codePointAt(0) - y[i].codePointAt(0);
    if (difference) return difference;
  }
  return x.length - y.length;
}

function sortedCopy(value) {
  if (Array.isArray(value)) return value.map(sortedCopy);
  if (value && typeof value === "object") {
    const out = Object.create(null);          // so a key named __proto__ stays a key
    for (const key of Object.keys(value).sort(compareCodePoints)) out[key] = sortedCopy(value[key]);
    return out;
  }
  return value;
}

/* The text that is hashed: sorted keys, no spaces, and every character outside
   printable ASCII written as a lower-case \uXXXX escape. */
function canonicalJSON(value) {
  return JSON.stringify(sortedCopy(value)).replace(
    /[^\x20-\x7e]/g, (c) => "\\u" + c.charCodeAt(0).toString(16).padStart(4, "0"));
}

/* The receipt of an answer record, as "7F3A 92C1": everything but saved_at and
   the receipt itself. */
function receiptOf(record) {
  const material = Object.assign({}, record);
  delete material.saved_at;
  delete material.receipt;
  const code = hex(sha256(new TextEncoder().encode(canonicalJSON(material)))).slice(0, 8).toUpperCase();
  return code.slice(0, 4) + " " + code.slice(4);
}

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
  /* The work now continues on this copy of the paper, whichever copy it began on. */
  state.exam = blankState().exam;
  const details = state.student || {};
  for (const el of document.querySelectorAll("[data-detail]")) {
    el.value = typeof details[el.dataset.detail] === "string" ? details[el.dataset.detail] : "";
  }
}

/* Starting afresh when this browser holds saved work for the paper keeps that
   work under a set-aside key rather than writing over it, so an invigilator can
   still recover it. */
function setAsideStoredWork(confirmed) {
  const stored = readStoredState();
  if (!stored || !Object.keys(stored.answers || {}).length) return true;
  const keep = confirmed || confirm("This browser holds saved work for this paper ("
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

function hideScreens() {
  for (const el of document.querySelectorAll(".dm-screen")) el.hidden = true;
}

/* The student has entered the paper: from here the page saves. */
function enterExam() {
  hideScreens();
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
  if (!fileHandle) {
    setPill("dm-save-file", SAVES ? "File saving is off" : "The answer key saves nothing", "dm-off");
  }
  saveEverywhere();
  const paper = $("dm-paper");
  paper.setAttribute("tabindex", "-1");
  paper.focus({ preventScroll: true });
  window.scrollTo(0, 0);
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
      "script, button, #dm-panel, .dm-screen, #dm-drawer, #dm-scrim, #dm-aa, #dm-ruler, "
      + "#dm-fonts, .dm-save-pill")) {
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

$("dm-download").addEventListener("click", downloadAnswerFile);
$("dm-finish").addEventListener("click", () => {
  gatherState();
  $("dm-finish-report").replaceChildren(finishReport());
  $("dm-app").hidden = true;
  $("dm-finish-screen").hidden = false;
  $("dm-changed").hidden = !changedAfterFinish;
  $("dm-finish-h").focus();
  window.scrollTo(0, 0);
});
$("dm-keep-working").addEventListener("click", () => {
  $("dm-finish-screen").hidden = true;
  $("dm-app").hidden = false;
  $("dm-paper").focus({ preventScroll: true });
});
/* Saving the answer file is what finishes the paper: the time is fixed, the
   receipt is made from the whole record, and the page says what it saved. */
let changedAfterFinish = false;

function showSaved() {
  const answers = Object.keys(state.answers).length;
  const saved = $("dm-saved");
  saved.textContent = "Saved. The file holds " + (answers === 1 ? "1 answer" : answers + " answers")
    + ". Receipt " + state.receipt + ". Paper ID " + state.exam.fingerprint + ".";
  saved.hidden = false;
  $("dm-changed").hidden = true;
}

/* The paper is handed in as it now is. If it was already saved and has not
   changed since, the receipt stays the same, so every file saved from one
   finish sheet carries one receipt. */
function fixReceipt() {
  gatherState();
  if (state.finished_at && state.receipt) return;
  state.finished_at = new Date().toISOString();
  state.receipt = receiptOf(state);
  changedAfterFinish = false;
  saveEverywhere();
}

$("dm-submit").addEventListener("click", () => {
  fixReceipt();
  downloadAnswerFile();
  showSaved();
});

/* A change after the paper was saved means the file and its receipt no longer
   describe the paper, so the student is asked to save again. */
function noteChangeAfterFinish() {
  if (!state.finished_at) return;
  state.finished_at = null;
  state.receipt = null;
  changedAfterFinish = true;
  $("dm-saved").hidden = true;
}
$("dm-save-readable").addEventListener("click", downloadReadableCopy);

document.addEventListener("input", (event) => {
  if (event.target.closest(".dm-answer")) {
    noteChangeAfterFinish();
    countWords();
    saveEverywhere();
  }
});
document.addEventListener("change", (event) => {
  if (event.target.closest(".dm-answer")) {
    noteChangeAfterFinish();
    saveEverywhere();
  }
});
window.addEventListener("beforeunload", () => {
  if (!canWrite) return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(gatherState()));
  } catch (err) { /* the periodic save already reported storage trouble */ }
});

/* The top bar is as tall as its contents, which change with the text size;
   the side panel sticks just below it. */
if ("ResizeObserver" in window) {
  new ResizeObserver(() => {
    const height = $("dm-topbar").offsetHeight;
    if (height) document.documentElement.style.setProperty("--dm-bar", height + "px");
  }).observe($("dm-topbar"));
}
