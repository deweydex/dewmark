/* Reading settings: how the page looks to the student who is sitting it.

   They are the student's own, so they live in one place on this computer
   (READING_KEY), not with the paper, and they are never in the answer file or
   the PDF: a file handed to a marker must not say that its student needed
   large text or a dyslexia-friendly font. Because a college computer is shared,
   the page says when settings were found, and offers to put them back to
   standard.

   The settings are described once, by dewmark/build.py (MODEL.reading), and
   drawn twice: on the first screen, and in the Aa drawer that every screen has.
   Any control with data-setting="name" is a view of one setting; this file
   keeps them all in step. Nothing is written until a student changes a
   setting. */

const READING_KEY = "dewmark:reading-settings";
const READING_SPEC = MODEL.reading;
const SPACING = { normal: [0, 0], wide: [0.04, 0.12], wider: [0.08, 0.25] };

function readingDefaults() {
  const out = {};
  for (const [key, spec] of Object.entries(READING_SPEC)) out[key] = spec.default;
  return out;
}

/* One setting, made valid: a number is kept in its range and on its step, a
   choice must be one of the choices, a switch is true or false. Anything else
   becomes the default, so a stored value from an older page or an edited one
   can never put the page in a state it cannot draw. */
function validSetting(key, value) {
  const spec = READING_SPEC[key];
  if (!spec) return undefined;
  if (typeof spec.default === "boolean") return value === true;
  if (spec.options) return spec.options.includes(value) ? value : spec.default;
  if (typeof value !== "number" || !Number.isFinite(value)) return spec.default;
  const stepped = Math.round((value - spec.min) / spec.step) * spec.step + spec.min;
  return Math.min(spec.max, Math.max(spec.min, Math.round(stepped * 100) / 100));
}

function sanitizeReading(raw) {
  const out = readingDefaults();
  if (raw && typeof raw === "object" && !Array.isArray(raw)) {
    for (const key of Object.keys(out)) {
      if (Object.prototype.hasOwnProperty.call(raw, key)) out[key] = validSetting(key, raw[key]);
    }
  }
  return out;
}

let reading = readingDefaults();
let readingKept = false;                 // settings were found on this computer, or saved by the student

try {
  const raw = localStorage.getItem(READING_KEY);
  if (raw) {
    reading = sanitizeReading(JSON.parse(raw));
    readingKept = true;
  }
} catch (err) { /* storage unavailable or unreadable: standard settings */ }

const computerAsksForLessMotion = () =>
  window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function applyReading() {
  const root = document.documentElement;
  const set = (name, value) => root.style.setProperty(name, value);
  set("--dm-size", reading.size);
  set("--dm-line", reading.lineHeight);
  set("--dm-font-body", "var(--dm-ff-" + reading.font + ")");
  set("--dm-letter", SPACING[reading.spacing][0]);
  set("--dm-word", SPACING[reading.spacing][1]);
  set("--dm-measure", reading.width);
  set("--dm-code-size", reading.codeSize);
  const flag = (name, on, value) => {
    if (on) root.setAttribute(name, value); else root.removeAttribute(name);
  };
  flag("data-scheme", reading.scheme !== "", reading.scheme);
  flag("data-code", reading.codeScheme !== "auto", reading.codeScheme);
  flag("data-motion", reading.motion || computerAsksForLessMotion(), "reduce");
  flag("data-ruler", reading.ruler, "on");
  flag("data-wrap", reading.wrap, "on");
}

function isStandard() {
  const base = readingDefaults();
  return Object.keys(base).every((key) => reading[key] === base[key]);
}

/* Every control that shows a setting is brought into step with it. */
function syncReadingControls() {
  for (const el of document.querySelectorAll("[data-setting]")) {
    const key = el.dataset.setting;
    if (el.type === "radio") el.checked = String(reading[key]) === el.value;
    else if (el.type === "checkbox") {
      el.checked = key === "motion" ? reading.motion || computerAsksForLessMotion() : reading[key];
    } else el.value = reading[key];
  }
  for (const out of document.querySelectorAll("[data-out]")) {
    out.textContent = reading[out.dataset.out];
  }
  for (const note of document.querySelectorAll("[data-kept]")) {
    note.hidden = !(readingKept && !isStandard());
  }
}

function persistReading() {
  try {
    localStorage.setItem(READING_KEY, JSON.stringify(reading));
    readingKept = true;
  } catch (err) { /* the settings still apply to this page */ }
}

function changeSetting(key, value) {
  reading[key] = validSetting(key, value);
  applyReading();
  persistReading();
  syncReadingControls();
  moveRulerToFocus();
}

function resetReading() {
  reading = readingDefaults();
  readingKept = false;
  try { localStorage.removeItem(READING_KEY); } catch (err) { /* nothing to remove */ }
  applyReading();
  syncReadingControls();
}

document.addEventListener("change", (event) => {
  const el = event.target;
  if (!el.matches || !el.matches("[data-setting]")) return;
  if (el.type === "radio") changeSetting(el.dataset.setting, el.value);
  else if (el.type === "checkbox") changeSetting(el.dataset.setting, el.checked);
});
document.addEventListener("input", (event) => {
  const el = event.target;
  if (el.matches && el.matches('input[type="range"][data-setting]')) {
    changeSetting(el.dataset.setting, Number(el.value));
  }
});
document.addEventListener("click", (event) => {
  const el = event.target.closest && event.target.closest("[data-step], [data-reset]");
  if (!el) return;
  if (el.hasAttribute("data-reset")) { resetReading(); return; }
  const key = el.dataset.step;
  changeSetting(key, reading[key] + Number(el.dataset.d) * READING_SPEC[key].step);
});

/* --- the Aa drawer --------------------------------------------------------------- */

let drawerOpener = null;
const behindDrawer = () => document.querySelectorAll(".dm-band, .dm-screen, #dm-app");

function openDrawer() {
  drawerOpener = document.activeElement;
  $("dm-scrim").hidden = false;
  $("dm-drawer").hidden = false;
  for (const el of behindDrawer()) el.inert = true;
  $("dm-drawer-close").focus();
}

function closeDrawer() {
  $("dm-drawer").hidden = true;
  $("dm-scrim").hidden = true;
  for (const el of behindDrawer()) el.inert = false;
  (drawerOpener && drawerOpener.isConnected ? drawerOpener : $("dm-aa")).focus();
}

$("dm-aa").addEventListener("click", openDrawer);
$("dm-drawer-close").addEventListener("click", closeDrawer);
$("dm-scrim").addEventListener("click", closeDrawer);
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !$("dm-drawer").hidden) {
    event.preventDefault();
    closeDrawer();
  }
});

/* --- the reading ruler ------------------------------------------------------------ */

/* A band across the page, as tall as a line of text. It follows the pointer;
   when the student types, it moves to the line they are on. The line is found
   by laying the text up to the caret out again in an invisible copy of the
   box. */

const rulerHeight = () => parseFloat(getComputedStyle(document.documentElement).fontSize) * reading.lineHeight * 1.15;

function placeRuler(centreY) {
  const ruler = $("dm-ruler");
  const height = rulerHeight();
  ruler.style.height = height + "px";
  ruler.style.top = Math.max(0, centreY - height / 2) + "px";
}

function caretY(field) {
  const box = field.getBoundingClientRect();
  if (field.tagName !== "TEXTAREA") return box.top + box.height / 2;
  const style = getComputedStyle(field);
  const mirror = document.createElement("div");
  for (const name of ["boxSizing", "width", "paddingTop", "paddingRight", "paddingBottom", "paddingLeft",
    "borderTopWidth", "borderRightWidth", "borderBottomWidth", "borderLeftWidth", "fontFamily",
    "fontSize", "fontWeight", "lineHeight", "letterSpacing", "wordSpacing", "tabSize"]) {
    mirror.style[name] = style[name];
  }
  mirror.style.position = "absolute";
  mirror.style.visibility = "hidden";
  mirror.style.whiteSpace = "pre-wrap";
  mirror.style.overflowWrap = "break-word";
  mirror.textContent = field.value.slice(0, field.selectionStart);
  const marker = document.createElement("span");
  marker.textContent = "​";
  mirror.appendChild(marker);
  document.body.appendChild(mirror);
  const line = parseFloat(style.lineHeight) || parseFloat(style.fontSize) * 1.5;
  const y = box.top + marker.offsetTop + line / 2 - field.scrollTop;
  mirror.remove();
  return Math.min(box.bottom - line / 2, Math.max(box.top + line / 2, y));
}

function moveRulerToFocus() {
  if (!reading.ruler) return;
  const field = document.activeElement;
  if (field && field.matches && field.matches("textarea, input[type='text']")) {
    placeRuler(caretY(field));
  }
}

document.addEventListener("pointermove", (event) => {
  if (!reading.ruler) return;
  placeRuler(event.clientY);
});
for (const name of ["focusin", "input", "keyup", "click", "select"]) {
  document.addEventListener(name, (event) => {
    if (reading.ruler && event.target.matches && event.target.matches("textarea, input[type='text']")) {
      moveRulerToFocus();
    }
  });
}

applyReading();
syncReadingControls();
