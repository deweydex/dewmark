/* The finish sheet's three steps: check the answers, save the answer file and
   the PDF, hand them in.

   Saving is one press. In Chrome and Edge the student chose a folder on the screen
   before the paper, and both files go into it; the page then reads them back from
   the folder and says what it found ("Checked: the file holds 17 answers. Receipt
   7F3A 92C1."), so the student does not hand in a file that was not written. In
   other browsers a page may not write into a folder or look inside a file it
   downloaded, so both files are downloaded and the page says plainly that it
   cannot check them. The receipt is fixed once for the press, so the file and
   every page of the PDF carry the same one (docs/ANSWER_FILE.md, docs/PDF_FILE.md).
   A change to an answer afterwards withdraws the receipt and asks for another save. */

async function writeToFolder(name, data) {
  const handle = await directory.getFileHandle(name, { create: true });
  const writable = await handle.createWritable();
  await writable.write(data);
  await writable.close();
}

async function readFromFolder(name) {
  const handle = await directory.getFileHandle(name);
  return new Uint8Array(await (await handle.getFile()).arrayBuffer());
}

const sameBytes = (a, b) => a.length === b.length && a.every((value, i) => value === b[i]);

/* What the page found when it read the files back, or why it could not say. */
async function checkFolder(files) {
  for (const file of files) {
    let found;
    try {
      found = await readFromFolder(file.name);
    } catch (err) {
      return "The file " + file.name + " is not in your folder.";
    }
    if (!sameBytes(found, file.bytes)) return "The file " + file.name + " in your folder is not the one the page saved.";
  }
  const record = JSON.parse(new TextDecoder().decode(files[0].bytes));
  if (receiptOf(record) !== state.receipt || record.receipt !== state.receipt) {
    return "The receipt in the answer file does not match its answers.";
  }
  return "";
}

function showConfirmation(names) {
  const details = state.student || {};
  const fields = {
    "dm-c-name": details["full name"], "dm-c-number": details["student number"],
    "dm-c-paper": MODEL.exam.title + " (" + MODEL.exam.code + ", version " + MODEL.exam.version + ")",
    "dm-c-id": state.exam.fingerprint,
    "dm-c-answers": plural(Object.keys(state.answers).length, "answer", "answers"),
    "dm-c-saved": new Date(state.finished_at).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }),
    "dm-c-receipt": state.receipt, "dm-c-files": names.join(", "),
  };
  for (const [id, value] of Object.entries(fields)) $(id).textContent = value || "";
  $("dm-confirm").hidden = false;
}

/* The note about characters the PDF could not draw, or how many pages it has. */
function pdfNote(made) {
  if (!made) {
    return "The PDF could not be made on this computer. Your answer file is saved. Press Print or save as PDF "
      + "to make a PDF with your browser.";
  }
  if (!made.missing.length) return "";
  const one = made.missing.length === 1;
  return "The PDF could not show " + (one ? "this character" : "these characters") + ": " + made.missing.join(" ")
    + ". It shows a box in " + (one ? "its" : "their") + " place. Your answer file has everything exactly as you "
    + "typed it. Press Print or save as PDF for a copy that shows it.";
}

async function saveEverything() {
  for (const id of ["dm-saved", "dm-problem", "dm-confirm", "dm-pdf-note", "dm-again-row", "dm-changed"]) {
    $(id).hidden = true;
  }
  fixReceipt();
  const base = submissionBaseName();
  const files = [{ name: base + ".json", bytes: new TextEncoder().encode(answerFileText()),
    type: "application/json" }];
  let made = null;
  try {
    made = await makePdf();
    files.push({ name: base + ".pdf", bytes: made.bytes, type: "application/pdf" });
  } catch (err) {
    made = null;
  }
  const answers = plural(Object.keys(state.answers).length, "answer", "answers");
  const names = files.map((file) => file.name);
  const pages = made ? " The PDF has " + plural(made.pages, "page", "pages") + "." : "";

  if (directory && SAVES) {
    let trouble = "";
    try {
      for (const file of files) await writeToFolder(file.name, file.bytes);
      trouble = await checkFolder(files);
    } catch (err) {
      trouble = "The page could not write into your folder (" + (err && err.name ? err.name : "an error") + ").";
    }
    if (trouble) {
      say("dm-problem", trouble + " Your answers are safe in this browser. Choose the folder again, or press "
        + "Save my answer file and PDF once more. You can also keep a copy with Save a copy at the top of the paper.");
      $("dm-rechoose").hidden = false;
      return;
    }
    $("dm-rechoose").hidden = true;
    say("dm-saved", "Checked: the file holds " + answers + ". Receipt " + state.receipt + "." + pages
      + " Both are in the folder " + directory.name + ".");
  } else {
    for (const file of files) save(new Blob([file.bytes], { type: file.type }), file.name);
    say("dm-saved", "Saved. Your browser put " + (files.length === 1 ? "a file" : "two files") + " in its "
      + "downloads folder: " + names.join(" and ") + ". Receipt " + state.receipt + "." + pages
      + " A page cannot look inside a file it downloaded, so open " + (files.length === 1 ? "it" : "them")
      + " to check.");
    $("dm-again-row").hidden = false;
  }
  say("dm-pdf-note", pdfNote(made));
  showConfirmation(names);
}

$("dm-submit").addEventListener("click", async () => {
  const button = $("dm-submit");
  button.disabled = true;
  try {
    await saveEverything();
  } finally {
    button.disabled = false;
  }
});

/* In a browser that downloads, a file the browser held back can be saved again. */
$("dm-again-file").addEventListener("click", () => { fixReceipt(); downloadAnswerFile(); });
$("dm-again-pdf").addEventListener("click", async () => {
  fixReceipt();
  try {
    const made = await makePdf();
    save(new Blob([made.bytes], { type: "application/pdf" }), submissionBaseName() + ".pdf");
    say("dm-pdf-note", pdfNote(made));
  } catch (err) {
    say("dm-pdf-note", pdfNote(null));
  }
});

$("dm-rechoose").addEventListener("click", async () => {
  await chooseFolder();
  if (directory) saveEverything();
});

/* The browser's own print window, for a PDF as the browser would make it. It
   prints the paper, so the finish sheet steps aside while the window is open. */
$("dm-print").addEventListener("click", () => {
  const app = $("dm-app"), finish = $("dm-finish-screen");
  app.hidden = false;
  finish.hidden = true;
  window.addEventListener("afterprint", () => { app.hidden = true; finish.hidden = false; }, { once: true });
  window.print();
});
