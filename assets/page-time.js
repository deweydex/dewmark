/* The clock, extra time, breaks, and the paper closing when its time is over
   (docs/ANSWER_FILE.md, `time`; planning/PROPOSAL.md §5.3; decision 11 and D4).

   The clock is the wall clock: the time left is the moment the student pressed
   Begin, plus the time allowed, plus any extra time, plus the time spent on a
   break or with the paper closed, less now. Closing the page does not stop it.
   Only a break does, and a break is recorded. Everything the clock needs is in
   state.time, so a saved record carries it, and a student who comes back to a
   saved paper finds the clock where it was.

   timer: none      the page has no clock.
   timer: shown     a clock, which the student may hide. At zero nothing closes.
                    The student types any extra time they have been given.
   timer: enforced  the same clock. At zero the page saves, the boxes become
                    read-only and the finish sheet opens. The invigilator's code
                    adds time, which reopens the paper. Extra time is only ever
                    added with the code.

   A practice page never enforces (dewmark/build.py, timer_block). */

const TIMER = MODEL.timer;
const ENFORCED = TIMER.mode === "enforced";
const TEN_MINUTES = 10 * 60 * 1000;
const STALE_CLOCK = 36 * 60 * 60 * 1000;           // a kept clock older than this belongs to an earlier sitting

const clockFlags = { hidden: false, ten: false, over: false, timer: null };
let pendingExtra = [];                              // extra time added with the code before Begin

const extraMinutes = () => state.time.extra.reduce((sum, grant) => sum + grant.minutes, 0);
const lastOf = (list) => list[list.length - 1];
const openIn = (list) => (list.length && !lastOf(list).end ? lastOf(list) : null);
const clockTime = (iso) => new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

function pausedMilliseconds(now) {
  let total = 0;
  for (const list of [state.time.breaks, state.time.closed]) {
    for (const pause of list) {
      total += Math.max(0, (pause.end ? Date.parse(pause.end) : now) - Date.parse(pause.start));
    }
  }
  return total;
}

/* Milliseconds left: what the student has been given, less what has passed outside
   a pause. Zero or less means the time is over. */
function millisecondsLeft(now) {
  return Date.parse(state.started_at) + (TIMER.minutes + extraMinutes()) * 60000
    + pausedMilliseconds(now) - now;
}

function digitsOf(milliseconds) {
  const seconds = Math.max(0, Math.ceil(milliseconds / 1000));
  const two = (n) => String(n).padStart(2, "0");
  const hours = Math.floor(seconds / 3600), minutes = Math.floor(seconds / 60) % 60;
  return (hours ? hours + ":" + two(minutes) : String(minutes)) + ":" + two(seconds % 60);
}

function renderClock(left) {
  const clock = $("dm-clock");
  if (!clock) return;
  let text, urgent = left <= TEN_MINUTES;
  if (openIn(state.time.breaks)) {
    text = "On a break";
    urgent = false;
  } else if (left <= 0) {
    text = ENFORCED ? "Time is up" : "Time allowed is over";
  } else if (urgent) {
    text = "Less than 10 minutes left: " + digitsOf(left);
  } else {
    text = digitsOf(left) + " left";
  }
  clock.textContent = text;
  clock.classList.toggle("dm-urgent", urgent);
}

/* Once, at ten minutes: words, an icon and weight on the clock itself, a line for a
   screen reader, and no sound and no change of focus. A student who has hidden the
   clock is not told, unless the paper is going to close. */
function announceTenMinutes() {
  clockFlags.ten = true;
  if (clockFlags.hidden && !ENFORCED) return;
  const words = ENFORCED
    ? "Ten minutes left. When the time is over, the page saves your work and closes your paper."
    : "Ten minutes left.";
  say("dm-clock-live", words);
  if (ENFORCED) say("dm-clock-note", words);
}

function tick() {
  if (!entered || TIMER.mode === "none" || !state.started_at) return;
  const now = Date.now();
  const left = millisecondsLeft(now);
  renderClock(left);
  if (left > TEN_MINUTES) {
    clockFlags.ten = false;
    clockFlags.over = false;
    say("dm-clock-note", "");
  } else if (!clockFlags.ten && left > 0) {
    announceTenMinutes();
  }
  if (left <= 0 && !openIn(state.time.breaks)) timeIsUp();
}

function timeIsUp() {
  if (!ENFORCED) {
    if (!clockFlags.over && !clockFlags.hidden) say("dm-clock-live", "The time allowed is over.");
    clockFlags.over = true;
    return;
  }
  closePaper();
}

/* --- hiding the clock -------------------------------------------------------------- */

if ($("dm-clock-toggle")) {
  $("dm-clock-toggle").addEventListener("click", () => {
    clockFlags.hidden = !clockFlags.hidden;
    $("dm-clock").hidden = clockFlags.hidden;
    $("dm-clock-toggle").textContent = clockFlags.hidden ? "Show time" : "Hide time";
  });
}

/* --- the paper closing and opening again ------------------------------------------- */

/* A box that is read-only can still be read, selected and copied; a choice, a
   drop-down or a button cannot be changed, so it is disabled. */
function setReadOnly(root, on) {
  for (const el of root.querySelectorAll("textarea, input, select, button")) {
    if (el.matches("textarea, input[type='text']")) el.readOnly = on;
    else el.disabled = on;
  }
}

/* The time is over under an enforced clock: the answers are saved, the boxes stop
   taking changes, and the finish sheet opens. Nothing is added to the record, so a
   student who had already saved still holds a receipt that matches: a closed paper
   is the clock's answer (no time left), found again on every load. */
function closePaper() {
  if (paperClosed) return;
  paperClosed = true;
  for (const root of document.querySelectorAll(".dm-answer")) setReadOnly(root, true);
  gatherState();
  saveEverywhere();
  showFinishSheet();
}

/* The paper opens again because time was added. The time it spent closed is
   recorded as a pause, from the moment the time ran out (which may be before the
   page noticed: a paper opened again the next morning) to now, so that the minutes
   added are minutes the student can use, counted from now. */
function reopenPaper(now) {
  const left = millisecondsLeft(now);
  if (left < 0) state.time.closed.push({ start: new Date(now + left).toISOString(), end: new Date(now).toISOString() });
  paperClosed = false;
  for (const root of document.querySelectorAll(".dm-answer")) setReadOnly(root, false);
}

/* --- extra time ----------------------------------------------------------------- */

const EXTRA_BY = { student: "said by the student", invigilator: "added by the invigilator" };

function describeExtra(time) {
  const bits = ["student", "invigilator"].map((by) => {
    const minutes = time.extra.filter((grant) => grant.by === by).reduce((sum, grant) => sum + grant.minutes, 0);
    return minutes ? plural(minutes, "minute", "minutes") + ", " + EXTRA_BY[by] : "";
  }).filter(Boolean);
  return bits.join("; ");
}

function describeBreaks(time) {
  const done = time.breaks.filter((pause) => pause.end);
  if (!done.length) return "";
  const minutes = Math.round(done.reduce((sum, pause) => sum + Date.parse(pause.end) - Date.parse(pause.start), 0) / 60000);
  return plural(done.length, "break", "breaks") + ", " + (minutes ? plural(minutes, "minute", "minutes") : "under a minute") + " in all";
}

/* The line on the Before you begin screen under an enforced clock, and the clock's
   own extra time when a student resumes. */
function refreshExtra() {
  const time = { extra: [...(begun.resuming ? state.time.extra : []), ...pendingExtra] };
  const line = $("dm-extra-line");
  if (line) {
    line.textContent = time.extra.length ? "Extra time: " + describeExtra(time) + "." : "Extra time: none.";
  }
  const field = $("dm-extra");
  if (field && begun.resuming && !field.dataset.touched) {
    const given = state.time.extra.filter((grant) => grant.by === "student").reduce((sum, grant) => sum + grant.minutes, 0);
    field.value = given ? String(given) : "";
  }
}

/* The minutes the student typed for their own extra time, or an error. Empty means none. */
function typedExtra() {
  const field = $("dm-extra");
  if (!field) return { minutes: 0 };
  const typed = field.value.trim();
  if (!typed) return { minutes: 0 };
  const minutes = /^\d{1,4}$/.test(typed) ? Number(typed) : 0;
  if (minutes < 1 || minutes > EXTRA_LIMIT) {
    return { error: "Type the extra time as a whole number of minutes, from 1 to " + EXTRA_LIMIT
      + ". Leave the box empty if you have none." };
  }
  return { minutes };
}

/* Called when Begin is pressed: the student's own extra time and the invigilator's, if
   any was added before Begin, become part of the record. */
function applyExtraAtBegin(minutes) {
  state.time.extra = state.time.extra.filter((grant) => grant.by !== "student");
  if (minutes) state.time.extra.push({ minutes, by: "student", at: new Date().toISOString() });
  state.time.extra.push(...pendingExtra);
  pendingExtra = [];
}

/* The invigilator adds time, from the finish sheet or before Begin. */
async function addTime() {
  const result = await askInvigilator("To add time, the invigilator types their code and the number of minutes.",
    { minutes: true });
  if (!result) return;
  const grant = { minutes: result.minutes, by: "invigilator", at: new Date().toISOString() };
  const words = plural(grant.minutes, "minute", "minutes") + " added by your invigilator.";
  if (!entered) {
    pendingExtra.push(grant);
    refreshExtra();
    return;
  }
  const wasClosed = paperClosed;
  if (wasClosed) reopenPaper(Date.now());
  state.time.extra.push(grant);
  noteChangeAfterFinish("time");
  saveEverywhere();
  tick();
  say("dm-time-added", words + (wasClosed ? " You can go back to your paper." : ""));
  $("dm-closed").hidden = !paperClosed;
  $("dm-keep-working").hidden = paperClosed;
}

/* What was typed or added for one student is not kept for the next. */
function forgetExtra() {
  pendingExtra = [];
  const field = $("dm-extra");
  if (field) {
    field.value = "";
    delete field.dataset.touched;
  }
  refreshExtra();
}

if ($("dm-add-time")) $("dm-add-time").addEventListener("click", addTime);
if ($("dm-add-extra")) $("dm-add-extra").addEventListener("click", addTime);
if ($("dm-extra")) $("dm-extra").addEventListener("input", () => {
  $("dm-extra").dataset.touched = "yes";
  $("dm-extra").removeAttribute("aria-invalid");
  say("dm-extra-err", "");
});

/* --- breaks ---------------------------------------------------------------------- */

function showBreak() {
  const pause = openIn(state.time.breaks);
  hideScreens();
  $("dm-app").hidden = true;
  say("dm-breaking-text", "Your break began at " + clockTime(pause.start) + ".");
  $("dm-breaking").hidden = false;
  $("dm-breaking-h").focus();
  window.scrollTo(0, 0);
}

function takeBreak() {
  if (paperClosed || openIn(state.time.breaks)) return;
  state.time.breaks.push({ start: new Date().toISOString(), end: null });
  noteChangeAfterFinish("time");
  saveEverywhere();
  tick();
  showBreak();
}

function endBreak() {
  const pause = openIn(state.time.breaks);
  if (!pause) return;
  pause.end = new Date().toISOString();
  noteChangeAfterFinish("time");
  saveEverywhere();
  $("dm-breaking").hidden = true;
  $("dm-app").hidden = false;
  tick();
  $("dm-paper").focus({ preventScroll: true });
}

if ($("dm-break")) {
  $("dm-break").addEventListener("click", takeBreak);
  $("dm-end-break").addEventListener("click", endBreak);
}

/* --- the clock kept apart from the saved work ------------------------------------------ */

/* Under an enforced clock, the moment a student began is kept for the paper, the
   sitting and the student number, apart from the saved work. Starting again sets
   the work aside, but not the clock (D4). */
const numberKey = (number) => String(number || "").trim().toLowerCase().replace(/\s+/g, "");
const clockKey = (number) => "dewmark:clock:" + MODEL.exam.code + ":" + VARIANT + ":"
  + encodeURIComponent((INVIGILATOR && INVIGILATOR.sitting) || "") + ":" + numberKey(number);

function keepClock() {
  if (!ENFORCED || !canWrite || !state.started_at) return;
  try {
    localStorage.setItem(clockKey((state.student || {})["student number"]),
      JSON.stringify({ started_at: state.started_at, time: state.time }));
  } catch (err) { /* the save indicator already reports a browser that will not keep things */ }
}

function keptClock(number) {
  try {
    const kept = JSON.parse(localStorage.getItem(clockKey(number)));
    if (kept && Number.isFinite(Date.parse(kept.started_at))
        && Date.now() - Date.parse(kept.started_at) < STALE_CLOCK) {
      return { started_at: kept.started_at, time: cleanTime(kept.time) };
    }
  } catch (err) { /* no clock was kept, or it cannot be read */ }
  return null;
}

/* --- starting ------------------------------------------------------------------------- */

/* The clock begins when the student enters the paper, and a paper that was left
   on a break, or that closed while the page was shut, is found as it was left. */
function startClock() {
  if ($("dm-timebox")) $("dm-timebox").hidden = false;
  if ($("dm-break")) $("dm-break").hidden = false;
  clearInterval(clockFlags.timer);
  if (TIMER.mode !== "none") {
    clockFlags.timer = setInterval(tick, 1000);
    document.addEventListener("visibilitychange", tick);
    tick();
  }
  if (openIn(state.time.breaks)) showBreak();
}
