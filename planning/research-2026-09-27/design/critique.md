# Review of planning/PROPOSAL.md, 28 September 2026

The proposal is mostly sound. I checked a sample of its figures and citations against the research and dewlab: 8 commits, 40 files, 18 tests, byte-identical builds at 45–180 ms, 16.4 MB and 2.3–2.9 s, 61 of 271 lines, sixteen hostile cases, 7,189 to 2,050 tokens, `build.py:1515`, `find_gaps` at `:1471`, `tutorial-style.css` lines 1–165, log entries 7.77, 7.179, 7.235 and 7.240, and the 2 Dec 2027 date for the AI Act (the EU law on AI). All of them match their sources. None of the banned words appear.

The findings below are ranked most severe first. I edited no file.

## Blockers (fix before Josh reads it)

**B1. D9 lets a teacher's tick approve sending student text to a cloud service** (§2 D9; also §8.2 and §8.3).
- **What is wrong:** Under data protection law (GDPR) the ETB is the "controller", the body legally responsible for the data. Only the controller can bring in an outside company to process student data, and that needs a signed processing agreement, often with a risk assessment first. A teacher's logged tick creates neither. Decision 18 makes the choice of service the teacher's responsibility, but it cannot move the ETB's legal duties onto the teacher. Recommending (b) could put the ETB on the wrong side of GDPR.
- **Fix:** Recommend (c) until the data protection officer answers the seven questions in `assistant.md` §6.2. After that, offer (b) only for services the college has approved, recorded in a settings file set by the college or IT rather than a per-teacher tick. Add one sentence: "Decision 18 makes the choice the teacher's; it does not move the ETB's duties under GDPR."

**B2. D2(a) creates a way to leak an exam, and the proposal presents "after finishing" as if it kept answers secret** (§2 D2; §5.4; step 8).
- **What is wrong:** A practice page with `show answers: after finishing` or `practice tests` must carry its keys, model answers and tests inside the file. A student who opens the page source can read them before finishing. Decision 14 controls when answers are *shown*, not whether they are *in the file*. Worse, **Make a practice copy** of an exam that has not been sat puts the exam's questions, and optionally its answers, in students' hands.
- **Fix:** In D2's "What follows", say: "Answers in a practice page are hidden from view, not secret; anyone can read the file." Make **Make a practice copy** warn and block when the source exam has an issue with no sitting date in the past. Add a matching leak check to the Before-you-issue list.

## Should fix

**S1. The marking flow is missing, and stage 10 points to the wrong section** (§4 stage 10, which says "Mark in the workbench (§7.4)").
- §7.4 is "By subject". No design in this round covers the marking screens. `architecture.md` §3.6 says: "Marking views, blind marking, keyboard entry … belong to the workbench design", and that design does not exist.
- Josh's brief makes marking half the product, yet step 6 builds "marking by part with propose and evidence" without any design behind it.
- **Fix:**
  - Point stage 10 at `architecture.md` §3.6 and `question-types.md` §2.5.
  - Add a short §4.1 saying plainly that the marking screens (by question or by student, blind marking, keyboard entry, second marker) are not yet designed.
  - Add a workbench design and mockup as the first deliverable of step 6, or as a pre-step.

**S2. Enforced timer: pressing "Start again" resets the clock** (§5.2, §5.3, D4).
- `started_at` is recorded at Begin "unless one exists" (`student-flow.md` line 209). **Start again** sets the old record aside, so a student under `timer: enforced` can restart with full time.
- **Fix:** Under `enforced`, keep `started_at` per paper and student number outside the set-aside record. Also require D4's invigilator code for Start again, and for resuming work saved under a different name.

**S3. Anyone who types a student number sees that student's saved work, and nothing on the PC expires** (§5.2).
- Student numbers are printed on cards. On a shared PC, typing a classmate's number offers "Continue my work". Records stay in the browser indefinitely unless the student presses **Remove my work**.
- This is an integrity risk, and it breaks GDPR's rule that personal data is kept no longer than needed.
- **Fix:**
  - Reuse D4's code to guard a resume under a different name.
  - Delete a record automatically once its answer file has been saved and checked, or after a set number of days (for example 14) when the page opens.
  - List what is on the PC and when it expires in the invigilator view.

**S4. The paste package sends the marking scheme to an outside assistant, and may be too long to paste** (§8.5; step 3 "done when").
- Decision 20's package includes "the teacher's exam", which holds the scheme below `# Marking scheme`. The conversion modes in decision 19 change only the prose above that line.
- Some college-approved assistants limit how much text can be pasted. The package (format guide, specimen paper and the teacher's paper) has not been measured.
- **Fix:**
  - Leave the scheme out by default; include it only for "Draft model answers and schemes".
  - Measure the package against the college's approved assistant in step 3.
  - Also offer the package as a `.txt` file to attach.
  - Add both points to "Things only Josh can find out" #5.

**S5. Step 3 needs a before-and-after screen that its deliverables do not list** (§8.3 note; step 3).
- Decision 19 says "the teacher picks, and sees every change". The paste route ships at step 3 with five modes, but step 3 lists no screen showing each changed line to accept or reject, and no rule refusing a reply that changes a number, mark, fence or the scheme.
- **Fix:** Either add both to step 3 (and include them in the time estimate), or ship only "copy without composing" at step 3 and the other four modes at step 7.

**S6. D3 understates what a PDF made by the page costs** (§2 D3).
- "A font covering Irish and maths characters" will show missing-character boxes for names and answers in other scripts. Classes include students with Arabic, Chinese and Ukrainian names.
- Code with line numbers, photographs, page breaks, and headers and footers on every page carrying the paper's fingerprint and the receipt code is more than "about a week".
- Maths shown "as its LaTeX" (a typesetting code) in the PDF, such as `\frac{3}{4}`, is unreadable to a maths teacher marking inside Moodle's grader.
- **Fix:**
  - Say two to three weeks.
  - State the character-coverage limit and fall back to the print button when a character is missing.
  - Show maths as the plain-text "reads as" line, not LaTeX.

**S7. The 32 px text setting breaks the paper screen** (§5.1 top bar; `mockups/student-start.html`).

| At 32 px text | What happens | Screenshot |
|---|---|---|
| 390 px wide | The top bar, which stays pinned while the page scrolls, is 375 px tall: 44% of the screen | `student-phone-light-06d-code-32px.png` |
| 390 px wide | The save chip is clipped to "Saved 16:54 in this bro…" | same |
| 390 px wide | The page is 490 px wide, so it scrolls sideways (fails WCAG 1.4.10, the accessibility rule on reflowing at narrow widths) | same |
| 1280 px wide | The bar is 160 px and the side panel takes about 44% of the width | `student-desk-light-06d-code-32px.png` |

- A student zoomed to 200% on a 1280 px college screen sees roughly the 640 px case.
- **Fix:** In §5.1, add: "At large text or narrow widths the top bar folds to one row (time, save status, Menu) and stops staying pinned. The side panel becomes a drawer."

**S8. D5's recommended Start screen is the "long scroll" it argues against** (§2 D5; §5.1).
- (a) puts details, the full reading settings with a live preview, and the loading checklist on one screen. The mockup's settings alone are about 2,260 px tall at desktop and 9,200 px at 32 px on a phone (`student-desk-light-03-settings.png`, `student-phone-light-03b-settings-32px.png`).
- **Fix:**
  - Put the four controls most students need on Start: font, text size, colours, reading ruler.
  - Put the rest under "More settings" or in the **Aa** drawer.
  - Say this in D5.
  - Note that (a) adds a screen to decision 9's "one combined screen", so Josh is choosing knowingly.

**S9. Things only Josh can find out: three gaps** (§2).
- **Moodle's maximum upload size.** The page is 16.4–17.4 MB, and the studio mockup says 17.4 MB. Many Moodle sites cap uploads at around 20 MB or less.
- **Python in a folder beside the page cannot go through Moodle as one file.** It needs a zip, and a page opened from inside a zip cannot load its neighbours.
- **Whether managed Chrome and Edge allow saving to a chosen folder from pages opened from disk (`file://`).**
- **Fix:** Add all three. Deliver `room-check.html` by the same route as the paper, downloaded from Moodle, so the room check tests the real route.

**S10. The student page's security rules contradict loading Python from the internet** (§8.1 against §1 and decision 7).
- "Its security policy forbids every connection" cannot hold when `python from: internet`. The cover's line "This page sends nothing anywhere" would also be wrong.
- **Fix:** "…forbids every connection except the one pinned Python address, with checksums, when the paper loads Python from the internet."

**S11. The rule-based "propose a mark" needs its legal footing stated** (§1 "Marking is assisted"; §8.4).
- A reader from the ETB will see "rules propose a mark" beside "a mark-suggesting system is high-risk".
- **Fix:** Add one sentence citing `local-llm.md` line 130: under Recital 12 of the AI Act, rules "defined solely by natural persons" are not AI. Add that assistant-drafted keys and tests become the teacher's rules only when `(draft)` is removed. `docs/AI_ACT_ASSESSMENT.md` should say both.

**S12. Losing the names lock file breaks the "stable names" protection** (§1; §4 folder layout).
- `names.lock.json` lives beside the `.exam.md`. Copying the paper to a new folder, emailing it, or using the step 3 checker (a text box with no folder) loses the lock silently.
- **Fix:** Also write the lock into the issued scheme JSON and the student page. Have the workbench and studio compare names against it, and have the checker ask for an issued page when the paper says `version` has been issued.

**S13. Steps have no size, so Josh cannot answer D6's "which paper, and when"** (§9).
- Only D3 carries an estimate.
- **Fix:** Give each step a rough size (days or weeks) and the earliest realistic date for a first practice sitting.

**S14. Recommendations presented as settled** (§3.3, §4 stage 6, §8.2).
- The "copied, never linked" sharing rule with dewlab, the "I have sat this paper myself" gate, and the choice of OpenAI Chat Completions with Ollama's own format are design recommendations Josh has not decided.
- The API is the direct answer to his question about what to call.
- **Fix:** Mark each as "Recommended; say if not". Or list them in a line under §2: "Also assumed, veto if you disagree".

**S15. Screen-reader testing comes too late** (step 4 "done when").
- Written papers ship at step 4 with only a keyboard-only test. Screen-reader passes wait until step 8, and Q16 (what is promised to a screen-reader user) stays open.
- **Fix:** Add an NVDA pass (a free Windows screen reader) of the start screen, one part of each first-wave box kind, and the finish sheet to step 4's "done when".

**S16. Maths teachers must write LaTeX** (§6, §7.4, §3.3).
- `$…$` typeset at build time means a non-programmer maths teacher writes LaTeX by hand until the assistant helps.
- **Fix:** Name this burden in §4. Add a maths insert with a preview (MathLive is already a step 8 dependency) to the studio in step 7 or 8.

**S17. Sections 1 and 2 take longer than ten minutes, and jargon goes unexplained** (§1–2).
- They run to 2,714 words, about 12–14 minutes before the tables. Terms used without explanation: CI, YAML, JSON, JSON Schema, LaTeX, UDL, Safe Exam Browser, `file:///`, "security policy", "background worker", "mutation test", "Chat Completions".
- **Fix:**
  - Cut D1's table to the four rows that change what teachers type (1, 2, 3, 5), with a pointer to `format.md` §10 for the rest.
  - Move the "What follows" paragraphs for D7–D9 into §5 and §8.
  - Gloss each term on first use, for example "CI (the automatic checks GitHub runs on every change)".

## Minor

- **Mockup differences §4 and §5 do not list** (`mockups/teacher-studio.html` Issue screen; `mockups/student-start.html`). Add these to the out-of-date lists:
  - The Issue screen lists the student page, `practice.html`, the answer key and the scheme JSON as one set (B31's split into `for-students/` and `for-teachers/` is not shown).
  - The Issue screen's Moodle note says "set up an Assignment that accepts .zip files", which contradicts decision 10 (`teacher-desk-dark-09-issue.png`).
  - The student finish card lacks the paper fingerprint (B29) (`student-desk-light-09-finish-saved.png`).
  - Code suggestions are ticked by default; B39 says off (`student-desk-light-03-settings.png`).
  - The settings preview labels "Your answer to 3(a)(i)" under 3(e).
  - The floating "MOCKUP" badge covers content at every size.
- **§1 describes one start screen while D5 recommends two.** Add "(two, if D5(a))".
- **§1's "byte-identical" claim covers today's builder only.** Add "the new reader's Markdown library is not yet probed (step 3)".
- **§3.1 says "The move carries no code changes"**, but the fix-up commit edits the teacher-visible string at `build_exam.py:416` (`architecture.md` §1.2 item 4). Say "no behaviour changes".
- **After decision 2's cleanup, every relative link from PROPOSAL.md into `research-2026-09-27/` breaks.** Rewrite them as links to the `design-round-2026-09` tag during the cleanup.
- **Setting `OLLAMA_ORIGINS` to `*` (§8.2) lets any website the teacher visits use the local model.** Recommend dewmark's own addresses, and test whether pages opened from disk can be allowed without `*`.
- **Photographs from a webcam can capture faces** (D8). Show a preview with cropping before saving.
- **§5.5 uses the key `title` where decision 12 says "paper".** Say which is canonical.
- **§1's "Thirteen kinds … cover programming, maths and biology"** overstates. Biology drawing and graph plotting stay on paper (§7.4).
- **Firefox and Safari were not tested for `input()`** (`dewlab-runtime.md` line 118). The Chrome/Edge 137 note in §2 item 3 should say those two use the pop-up fallback.

## The mockups

I ran Chromium through Playwright at 1280×800 and 390×844, in light and dark, and clicked through every step and scenario of both mockups.

**What the checks found:**
- No requests leave the page, in any configuration.
- No sideways scroll at 390 px with default settings. The only case is at 32 px text (S7).
- No script errors.
- The focus outline is a visible 3 px outline on every tab stop. Its contrast is at least 3.3:1: rust on light is 4.46:1; in the dark studio it is 3.73:1 on the background and 3.32:1 on cards.
- A computed contrast check of all text on every screen found no failures in either theme.
- No step is broken.

**My judgement:**
- **Student pages:** calm and clear. The navy band, a serif front page like a printed paper, and plain-word states read well.
- **Get ready:** balanced at desktop.
- **Finish sheet and invigilator card:** very clear.
- **Settings screen:** a wall of controls (S8).
- **Studio home:** clean and inviting.
- **Studio editor:** its three panes are cramped at 1280 px, with the source cut off at the right edge. It still shows the old YAML format, which the proposal already notes.

Files are in /tmp/claude-0/-home-user/9d1373ae-0961-5985-b2c8-adad08e8b8ed/scratchpad/design-round/critique:
- shots/ — 124 screenshots
- report.json
- shoot.py