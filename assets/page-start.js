/* The two screens before the paper (decision 25), and the start of the page.

   Start: the student's details; saved work, offered only once the student
   number matches the work (so a computer never shows one student another's
   work); the reading settings (assets/page-reading.js); and what the paper
   needs. Before you begin: the instructions, where the answer file goes, and
   Begin.

   Nothing here writes the student's work. The one write before Begin that
   touches saved work is setAsideStoredWork(), when a student starts again;
   the reading settings and the storage test (a small key, removed at once) are
   not the student's work. The page holds a blank state until Begin or
   Continue, which is the rule in CLAUDE.md. */

const FILE_PICKER = "showSaveFilePicker" in window;
const begun = { resuming: false, startAgain: false, fileDecided: false };

function showScreen(name) {
  hideScreens();
  const screen = $(name === "start" ? "dm-start" : "dm-before");
  screen.hidden = false;
  screen.querySelector("h2").focus();
  window.scrollTo(0, 0);
}

function say(id, text) {
  const el = $(id);
  el.textContent = text;
  el.hidden = !text;
}

const detailField = (key) => document.querySelector('[data-detail="' + key + '"]');
const detailValue = (key) => detailField(key).value.trim();
const countAnswers = (record) => Object.keys((record && record.answers) || {}).length;
const plural = (n, one, many) => n + " " + (n === 1 ? one : many);
const whenSaved = (record) => record.saved_at
  ? new Date(record.saved_at).toLocaleString([], { dateStyle: "medium", timeStyle: "short" })
  : "at an unknown time";

/* --- details --------------------------------------------------------------------- */

const DETAIL_ERRORS = [
  ["full name", "dm-name-err", "Type your full name."],
  ["student number", "dm-number-err", "Type your student number."],
];

function validateDetails() {
  let first = null;
  for (const [key, errorId, message] of DETAIL_ERRORS) {
    const field = detailField(key);
    const missing = !field.value.trim();
    if (missing) field.setAttribute("aria-invalid", "true");
    else field.removeAttribute("aria-invalid");
    say(errorId, missing ? message : "");
    if (missing && !first) first = field;
  }
  if (first) first.focus();
  return !first;
}

/* --- saved work, offered after the number is typed --------------------------------- */

/* Work saved on another version of the paper is not offered: a teacher raises
   the version when names or marks have changed, so its answers may not belong
   to these boxes. It is still on the computer, and Begin sets it aside. */
const sameVersion = (record) => String((record.exam || {}).version) === String(MODEL.exam.version);
const savedWork = SAVES ? readStoredState() : null;
const holdsWork = countAnswers(savedWork) > 0 && sameVersion(savedWork);
const sameNumber = (a, b) => a !== "" && a.toLowerCase() === b.trim().toLowerCase();

function offerSavedWork() {
  const mine = holdsWork && !begun.resuming
    && sameNumber(detailValue("student number"), String((savedWork.student || {})["student number"] || ""));
  $("dm-restore").hidden = !mine;
  if (mine) {
    $("dm-restore-text").textContent = "This computer has your work on this paper: "
      + plural(countAnswers(savedWork), "answer", "answers") + ", last saved " + whenSaved(savedWork) + ".";
  } else {
    begun.startAgain = false;
  }
  $("dm-again-text").hidden = !begun.startAgain;
  say("dm-restore-err", "");
}

function resumeWork(record) {
  const corrected = Boolean(record.exam.fingerprint)
    && record.exam.fingerprint !== MODEL.exam.fingerprint;
  adoptState(record);
  begun.resuming = true;
  begun.startAgain = false;
  $("dm-restore").hidden = true;
  say("dm-resume-line", "Your work is ready to continue: "
    + plural(countAnswers(record), "answer", "answers") + ", saved " + whenSaved(record) + "."
    + (corrected ? " The paper has been corrected since you saved this work. Your answers are kept."
      : ""));
  showScreen("before");
}

/* A student who goes back and changes the student number is no longer the
   student the saved work belongs to: the work is let go, and not loaded into
   the paper. A name corrected by a letter is still the same student, and the
   work keeps the corrected name. */
document.addEventListener("input", (event) => {
  const field = event.target;
  if (!field.matches || !field.matches("[data-detail]")) return;
  if (begun.resuming) {
    if (field.dataset.detail === "student number"
        && field.value.trim() !== String((state.student || {})["student number"] || "")) {
      begun.resuming = false;
      state = blankState();
      say("dm-resume-line", "");
    } else if (field.dataset.detail === "full name" && field.value.trim()) {
      state.student["full name"] = field.value.trim();
    }
  }
  const entry = DETAIL_ERRORS.find(([key]) => key === field.dataset.detail);
  if (entry && field.value.trim()) {
    field.removeAttribute("aria-invalid");
    say(entry[1], "");
  }
  if (field.dataset.detail === "student number") offerSavedWork();
});

$("dm-continue").addEventListener("click", () => resumeWork(savedWork));
$("dm-again").addEventListener("click", () => {
  begun.startAgain = true;
  say("dm-restore-err", "");
  $("dm-again-text").hidden = false;
});
$("dm-not-me").addEventListener("click", () => {
  const field = detailField("student number");
  field.value = "";
  offerSavedWork();
  field.focus();
});

$("dm-details").addEventListener("submit", (event) => {
  event.preventDefault();
  if (secondWindow || !validateDetails()) return;
  if (!begun.resuming && !$("dm-restore").hidden && !begun.startAgain) {
    say("dm-restore-err", "Choose Continue my work or Start again first.");
    $("dm-continue").focus();
    return;
  }
  if (!begun.resuming) {
    for (const [key] of DETAIL_ERRORS) state.student[key] = detailValue(key);
  }
  showScreen("before");
});

/* --- an answer file the student already has ------------------------------------------- */

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
      say("dm-file-msg", "That file could not be read as an answer file. Nothing has changed.");
      return;
    }
    if (!validState(loaded)) {
      say("dm-file-msg", "That file is not an answer file for this paper, so it cannot be loaded here. "
        + "Nothing has changed.");
      return;
    }
    if (!sameVersion(loaded)) {
      say("dm-file-msg", "That file was saved on version " + loaded.exam.version + " of this paper, and "
        + "this page is version " + MODEL.exam.version + ", so its answers may not fit. Nothing has changed. "
        + "Ask your invigilator for the page that matches your file.");
      return;
    }
    say("dm-file-msg", "");
    const stored = SAVES ? readStoredState() : null;
    if (stored && stored.saved_at !== loaded.saved_at && countAnswers(stored)) {
      const keepFile = confirm(
        "This browser also holds saved work for this paper.\n\n"
        + describeState(loaded, "The file") + "\n"
        + describeState(stored, "This browser") + "\n\n"
        + "Press OK to continue from the file, or Cancel to continue "
        + "from this browser.");
      if (!keepFile) { resumeWork(stored); return; }
      /* The browser's work is not lost by choosing the file: it is kept aside. */
      setAsideStoredWork(true);
    }
    resumeWork(loaded);
  };
  input.click();
}
$("dm-load-file").addEventListener("click", loadAnswerFile);

/* --- where the answer file goes ------------------------------------------------------- */

async function chooseFile() {
  begun.fileDecided = true;
  try {
    fileHandle = await window.showSaveFilePicker({
      suggestedName: submissionBaseName() + ".json",
      types: [{ description: "dewmark answer file", accept: { "application/json": [".json"] } }],
    });
    say("dm-file-status", "Your answer file is " + fileHandle.name + ". The page saves into it as you work.");
    $("dm-choose-file").textContent = "Choose a different place…";
  } catch (err) {
    fileHandle = null;
    say("dm-file-status", err && err.name === "AbortError"
      ? "No place was chosen. The page will keep your work in this browser only. You can save a copy at any time."
      : "Your browser did not let the page choose a place. The page will keep your work in this browser only. "
        + "You can save a copy at any time.");
  }
}

if (SAVES && $("dm-choose-file")) {
  if (FILE_PICKER) {
    $("dm-choose-file").addEventListener("click", chooseFile);
  } else {
    $("dm-choose-file").hidden = true;
    say("dm-file-status", "Your browser downloads files instead of saving into one as you work. The page keeps "
      + "your work in this browser. When you press Finish, or Save a copy, it gives you a file to keep.");
  }
}

/* --- begin ------------------------------------------------------------------------- */

function begin() {
  if (secondWindow) return;
  if (!begun.resuming) {
    if (SAVES && !setAsideStoredWork(begun.startAgain)) return;
    const details = state.student;
    state = blankState();
    state.student = details;
  }
  if (SAVES && FILE_PICKER && !fileHandle && !begun.fileDecided && !confirm(
      "You have not chosen where to save your answer file.\n\n"
      + "Press OK to begin anyway. The page then keeps your work in this browser only, "
      + "and you can save a copy at any time. Press Cancel to go back and choose.")) {
    return;
  }
  if (!state.started_at) state.started_at = new Date().toISOString();
  enterExam();
}
$("dm-begin").addEventListener("click", begin);
$("dm-back").addEventListener("click", () => showScreen("start"));

/* --- what the paper needs -------------------------------------------------------------- */

/* Each check says whether this computer and this browser can do one thing the
   paper needs. They may take time (the Python check will), so each returns a
   state now or a promise of one. A problem is shown plainly and never stops
   Begin: the student can still read and write, and the invigilator decides. */
const CHECKS = {
  inside: () => ({ state: "ready", word: "Ready" }),
  storage: () => {
    try {
      const probe = "dewmark:storage-test";
      localStorage.setItem(probe, "1");
      localStorage.removeItem(probe);
      return { state: "ready", word: "Ready" };
    } catch (err) {
      return { state: "problem", word: "Problem",
        detail: "This browser will not keep your work here. Tell your invigilator." };
    }
  },
  file: () => FILE_PICKER
    ? { state: "ready", word: "Ready", detail: "You choose the place on the next screen" }
    : { state: "note", word: "Note",
        detail: "This browser downloads files instead. Press Save a copy to keep one." },
  python: () => ({ state: "problem", word: "Not ready",
    detail: "This page cannot run Python yet" }),
};

async function runChecks() {
  let problems = 0;
  for (const item of document.querySelectorAll("#dm-checklist li")) {
    const check = CHECKS[item.dataset.check];
    const result = check ? await check() : { state: "problem", word: "Problem" };
    item.dataset.state = result.state;
    item.querySelector(".dm-cw").textContent = result.word;
    if (result.detail) item.querySelector(".dm-cs").textContent = result.detail;
    if (result.state === "problem") problems += 1;
  }
  const line = problems
    ? "Something this paper needs is not ready. Tell your invigilator before you begin."
    : "Everything this paper needs is ready.";
  $("dm-load-status").textContent = line;
  $("dm-ready-line").textContent = line;
}
runChecks();

/* --- a second copy of the paper in this browser must not save over the first -------------- */

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
      for (const id of ["dm-next", "dm-begin", "dm-load-file", "dm-continue", "dm-again", "dm-choose-file"]) {
        const button = $(id);
        if (button) button.disabled = true;
      }
      alert("This paper is already open in another window on this computer. "
        + "Please continue there; this window will not save.");
    }
  };
  channel.postMessage("anyone-there?");
}
