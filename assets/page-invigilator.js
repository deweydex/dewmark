/* The invigilator's code, and what it opens (planning/DECISIONS_2026-09-27.md,
   D4; dewmark/invigilator.py).

   The code is made when the pages are built, for one sitting, and the page holds
   only a hash of it (MODEL.invigilator.check). It adds time to a paper whose clock
   closes it (assets/page-time.js), lets a student start again under that clock,
   lets a student continue work saved under a different name, and opens the list
   of work saved on this computer.

   It guards against accidents, not against a student with developer tools: the
   hash is in the page and a six-digit number is quickly searched. The answer file
   records every grant of time, so the invigilator and the marker can see it.

   A page built without a sitting has no code (INVIGILATOR is null); the things
   that need one then cannot be done on that page, and the page says so. */

const INVIGILATOR = MODEL.invigilator;
const GATE_TRIES = 3;                 // wrong codes before the page makes the invigilator wait
const GATE_WAIT = 30000;              // milliseconds
const gate = { tries: 0, until: 0, settled: true, resolve: null, wantsMinutes: false };

/* What the page keeps instead of the code: the same 16 digits dewmark/invigilator.py
   makes from the paper's code and the digits typed. */
function invigilatorCheck(digits) {
  return hex(sha256(new TextEncoder().encode("dewmark-invigilator/1:" + MODEL.exam.code + ":" + digits)))
    .slice(0, 16);
}

/* Ask for the code in a small window. Resolves to null if the invigilator cancels (or
   the page has no code), and otherwise to {minutes}, with the minutes typed if the
   window was asked for them. */
function askInvigilator(reason, options) {
  const wants = Boolean(options && options.minutes);
  return new Promise((resolve) => {
    const dialog = $("dm-gate");
    if (!INVIGILATOR || !dialog) { resolve(null); return; }
    gate.settled = false;
    gate.resolve = resolve;
    gate.wantsMinutes = wants;
    $("dm-gate-reason").textContent = reason;
    $("dm-gate-code").value = "";
    $("dm-gate-minutes").value = "";
    $("dm-gate-minutes-field").hidden = !wants;
    say("dm-gate-err", "");
    dialog.showModal();
    $("dm-gate-code").focus();
  });
}

function settleGate(result) {
  if (gate.settled) return;
  gate.settled = true;
  gate.resolve(result);
}

function gateWait() {
  const seconds = Math.ceil((gate.until - Date.now()) / 1000);
  return seconds > 0 ? seconds : 0;
}

if ($("dm-gate")) {
  $("dm-gate-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const waiting = gateWait();
    if (waiting) {
      say("dm-gate-err", "Too many tries. Wait " + plural(waiting, "second", "seconds") + ", then try again.");
      return;
    }
    let minutes = 0;
    if (gate.wantsMinutes) {
      const typed = $("dm-gate-minutes").value.trim();
      minutes = /^\d{1,4}$/.test(typed) ? Number(typed) : 0;
      if (minutes < 1 || minutes > EXTRA_LIMIT) {
        say("dm-gate-err", "Type the minutes as a whole number from 1 to " + EXTRA_LIMIT + ".");
        $("dm-gate-minutes").focus();
        return;
      }
    }
    const digits = $("dm-gate-code").value.replace(/\D/g, "");
    if (!digits || invigilatorCheck(digits) !== INVIGILATOR.check) {
      gate.tries += 1;
      if (gate.tries >= GATE_TRIES) {
        gate.until = Date.now() + GATE_WAIT;
        gate.tries = 0;
        say("dm-gate-err", "That code is not right. Wait " + plural(GATE_WAIT / 1000, "second", "seconds")
          + ", then try again.");
      } else {
        say("dm-gate-err", "That code is not right. Check the sitting card.");
      }
      $("dm-gate-code").value = "";
      $("dm-gate-code").focus();
      return;
    }
    gate.tries = 0;
    settleGate({ minutes });
    $("dm-gate").close();
  });
  $("dm-gate-cancel").addEventListener("click", () => $("dm-gate").close());
  /* Escape and Cancel both close the window; a window closed without a right code is a no. */
  $("dm-gate").addEventListener("close", () => settleGate(null));
  for (const button of document.querySelectorAll("[data-minutes]")) {
    button.addEventListener("click", () => {
      $("dm-gate-minutes").value = button.dataset.minutes;
      $("dm-gate-minutes").focus();
    });
  }
}

/* --- the list of work saved on this computer ----------------------------------------- */

/* Who a record belongs to, shown so that the invigilator can ask "is this you?"
   without the list telling a student another student's name: initials, and the
   last digits of the number. */
function maskedWho(record) {
  const details = record.student || {};
  const initials = String(details["full name"] || "").split(/\s+/).filter(Boolean)
    .map((word) => Array.from(word)[0].toUpperCase() + ".").join("");
  const number = String(details["student number"] || "");
  return (initials || "No name") + " · number " + (number.length > 4 ? "ending " + number.slice(-3) : "not shown");
}

/* The records this browser holds for this page of this paper: the current one and
   the ones set aside when a student started again. Newest first. */
function savedRecords() {
  const found = [];
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key !== STORAGE_KEY && !key.startsWith(STORAGE_KEY + ":set-aside:")) continue;
    try {
      const record = JSON.parse(localStorage.getItem(key));
      if (validState(record)) found.push({ key, record, aside: key !== STORAGE_KEY });
    } catch (err) { /* a record that cannot be read is not listed */ }
  }
  return found.sort((a, b) => String(b.record.saved_at).localeCompare(String(a.record.saved_at)));
}

function workRow(entry) {
  const { record, aside } = entry;
  const item = document.createElement("li");
  const text = document.createElement("div");
  const who = document.createElement("strong");
  who.textContent = maskedWho(record);
  const detail = document.createElement("span");
  detail.className = "dm-hint-text";
  detail.textContent = plural(countAnswers(record), "answer", "answers") + ", saved " + whenSaved(record)
    + (aside ? ", set aside" : ", the work now kept for this paper")
    + (sameVersion(record) ? "" : ", on version " + (record.exam || {}).version + " of the paper")
    + (sameSitting(record) ? "" : ", in another sitting");
  text.append(who, detail);
  const actions = document.createElement("div");
  actions.className = "dm-actions";
  const file = document.createElement("button");
  file.type = "button";
  file.className = "dm-secondary";
  file.textContent = "Save as a file";
  file.addEventListener("click", () => {
    save(new Blob([JSON.stringify(record, null, 2)], { type: "application/json" }),
      submissionBaseName(record.student || {}) + ".json");
    say("dm-work-msg", "Saved a copy of this work as a file.");
  });
  actions.append(file);
  if (sameVersion(record) && sameSitting(record)) {
    const use = document.createElement("button");
    use.type = "button";
    use.className = "dm-secondary";
    use.textContent = "Continue from this work";
    use.addEventListener("click", () => {
      /* The work the page holds now is set aside, not lost, before this work takes its place. */
      if (aside && !setAsideStoredWork(true)) return;
      $("dm-work").close();
      resumeWork(record);
    });
    actions.append(use);
  } else {
    const note = document.createElement("span");
    note.className = "dm-hint-text";
    note.textContent = "It cannot be continued on this page.";
    actions.append(note);
  }
  item.append(text, actions);
  return item;
}

function openWork() {
  const entries = SAVES ? savedRecords() : [];
  $("dm-work-list").replaceChildren(...entries.map(workRow));
  $("dm-work-empty").hidden = entries.length > 0;
  say("dm-work-msg", "");
  $("dm-work").showModal();
}

if ($("dm-open-work")) {
  $("dm-open-work").addEventListener("click", async () => {
    const result = await askInvigilator("To see the work saved on this computer, the invigilator types "
      + "their code.");
    if (result) openWork();
  });
  $("dm-work-close").addEventListener("click", () => $("dm-work").close());
}
