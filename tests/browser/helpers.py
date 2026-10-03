"""What the browser rehearsals share: sitting a paper in a real Chromium.

A page opens with a stand-in for the browser's folder window (FAKE_PICKER),
because Chromium cannot show a window to a test; the stand-in is a folder in
memory, window.__folder, of name -> what was written. The helpers go through the
two screens as a student does, and read browser storage as the page wrote it.
window.__folderFails makes the folder misbehave: "folder" refuses to open a
file, "write" refuses to write one, "altered" reads the PDF back wrongly.
"""

import json
import re


KEY = "dewmark:rehearsal:student"
READING = "dewmark:reading-settings"
WRITING = '[data-answer="q1a"] textarea'

EVERYTHING = {
    "q1a": "alpha",
    "q1b": "x = 2",
    "q1c": "one two three",
    "q2a": "print(1)",
    "q2b": {"code": "print(2)"},
    "q3a": ["A", "C"],
    "q3b": ["root", "stem"],
    "q3c": ["plant", "leaves"],
    "q3d": ["3", "4"],
}

# A stand-in for the browser's folder window: a folder kept in window.__folder.
FAKE_PICKER = """
window.__folder = {};
window.__folderFails = null;
window.showDirectoryPicker = async () => ({
  name: "answers-folder",
  getFileHandle: async (name, options) => {
    if (window.__folderFails === "folder") throw new DOMException("denied", "NotAllowedError");
    if (!(name in window.__folder)) {
      if (!(options && options.create)) throw new DOMException("none", "NotFoundError");
      window.__folder[name] = "";
    }
    return {
      name,
      createWritable: async () => {
        if (window.__folderFails === "write") throw new DOMException("denied", "NotAllowedError");
        let data = "";
        return { write: async (d) => { data = d; }, close: async () => { window.__folder[name] = data; } };
      },
      getFile: async () => {
        const altered = window.__folderFails === "altered" && name.endsWith(".pdf");
        return new File([altered ? "not the same" : window.__folder[name]], name);
      },
    };
  },
});
"""
NO_PICKER = "delete window.showDirectoryPicker;"
CANCELLED_PICKER = ("window.showDirectoryPicker = async () => "
                    "{ throw new DOMException('cancelled', 'AbortError'); };")
BLOCKED_PICKER = ("window.showDirectoryPicker = async () => "
                  "{ throw new DOMException('blocked', 'SecurityError'); };")
BROKEN_STORAGE = ("Storage.prototype.setItem = function () "
                  "{ throw new DOMException('full', 'QuotaExceededError'); };")


def open_page(context, path, accept_dialogs=False, picker=FAKE_PICKER, init=None):
    page = context.new_page()
    page.errors, page.dialogs = [], []
    page.on("pageerror", lambda e: page.errors.append(str(e)))

    def on_dialog(dialog):
        page.dialogs.append(dialog.message)
        if accept_dialogs:
            dialog.accept()
        else:
            dialog.dismiss()

    page.on("dialog", on_dialog)
    for script in (picker, init):
        if script:
            page.add_init_script(script)
    page.goto(path.resolve().as_uri())
    return page


def wait_for(page, expression, timeout=5000):
    """Wait until a JavaScript expression is true in the page. Playwright's own
    wait_for_function evaluates a string, which the page's policy forbids."""
    waited = 0
    while not page.evaluate("() => " + expression):
        page.wait_for_timeout(50)
        waited += 50
        assert waited < timeout, f"never true: {expression}"


def type_details(page, name="Agnes Nitt", number="S12345"):
    page.fill("#dm-name", name)
    page.fill("#dm-number", number)


def next_screen(page):
    page.click("#dm-next")
    page.wait_for_selector("#dm-before:not([hidden])")


def choose_folder(page):
    if page.is_visible("#dm-choose-folder"):
        page.click("#dm-choose-folder")
        wait_for(page, "document.getElementById('dm-file-status').textContent.length > 0")


def press_begin(page):
    page.click("#dm-begin")
    page.wait_for_selector("#dm-app:not([hidden])")


def begin(page, name="Agnes Nitt", number="S12345", choose=True):
    """The whole way in: details, Next, where the file goes, Begin."""
    type_details(page, name, number)
    next_screen(page)
    if choose:
        choose_folder(page)
    press_begin(page)


def resume(page, number="S12345", name="Agnes Nitt"):
    """Type the name and number, Continue my work, then Begin."""
    page.fill("#dm-name", name)
    page.fill("#dm-number", number)
    page.wait_for_selector("#dm-restore:not([hidden])")
    page.click("#dm-continue")
    page.wait_for_selector("#dm-before:not([hidden])")
    choose_folder(page)
    press_begin(page)


def write(page, value):
    page.fill(WRITING, value)
    page.wait_for_timeout(200)


def stored(page):
    """Every dewmark record in this browser profile's storage, parsed."""
    return page.evaluate("""() => {
        const out = {};
        for (const key of Object.keys(localStorage)) {
            if (key.startsWith("dewmark")) {
                try { out[key] = JSON.parse(localStorage.getItem(key)); }
                catch (e) { out[key] = localStorage.getItem(key); }
            }
        }
        return out;
    }""")


def holds(records, name, value):
    """True if some stored record has `value` as the answer to `name`."""
    return any((record or {}).get("answers", {}).get(name) == value
               for record in records.values() if isinstance(record, dict))


def sit_and_leave(context, path, value, number="S12345"):
    page = open_page(context, path)
    begin(page, number=number)
    write(page, value)
    page.close()


def fill_everything(page):
    page.fill('[data-answer="q1a"] textarea', "alpha")
    page.fill('[data-answer="q1b"] textarea', "x = 2")
    page.fill('[data-answer="q1c"] textarea', "one two three")
    page.fill('[data-answer="q2a"] textarea', "print(1)")
    page.fill('[data-answer="q2b"] textarea', "print(2)")
    page.check('[data-answer="q3a"] input[value="A"]')
    page.check('[data-answer="q3a"] input[value="C"]')
    page.select_option('[data-answer="q3b"] [data-slot="1"]', "root")
    page.select_option('[data-answer="q3b"] [data-slot="2"]', "stem")
    page.fill('[data-answer="q3c"] input[data-slot="1"]', "plant")
    page.select_option('[data-answer="q3c"] select[data-slot="2"]', "leaves")
    page.fill('[data-answer="q3d"] [data-slot="1"]', "3")
    page.fill('[data-answer="q3d"] [data-slot="2"]', "4")
    page.wait_for_timeout(200)


def finish_and_download(page, tmp_path, button="#dm-submit"):
    page.click("#dm-finish")
    with page.expect_download() as caught:
        page.click(button)
    target = tmp_path / caught.value.suggested_filename
    caught.value.save_as(target)
    return target


# --- the folder and the finish sheet --------------------------------------------------------------------------

def folder_names(page):
    return page.evaluate("() => Object.keys(window.__folder)")


def folder_bytes(page, name):
    return bytes(page.evaluate(
        "(n) => { const d = window.__folder[n]; "
        "return Array.from(typeof d === 'string' ? new TextEncoder().encode(d) : d); }", name))


def answer_file(page):
    """The answer file in the folder, as a dictionary."""
    name = next(n for n in folder_names(page) if n.endswith(".json"))
    return json.loads(folder_bytes(page, name))


def pdf_file(page):
    name = next(n for n in folder_names(page) if n.endswith(".pdf"))
    return folder_bytes(page, name)


def save_both(page):
    """Finish, press the one button, and wait for the page to say how it went."""
    page.click("#dm-finish")
    page.click("#dm-submit")
    page.wait_for_selector("#dm-saved:not([hidden]), #dm-problem:not([hidden])")


def downloads_of_both(page, tmp_path):
    """For a page with no folder: finish, press the one button, and keep the two
    files it downloads, as {'json': path, 'pdf': path}."""
    caught = []
    page.on("download", lambda download: caught.append(download))
    page.click("#dm-finish")
    page.click("#dm-submit")
    waited = 0
    while len(caught) < 2 and waited < 8000:
        page.wait_for_timeout(100)
        waited += 100
    assert len(caught) == 2, [d.suggested_filename for d in caught]
    out = {}
    for download in caught:
        target = tmp_path / download.suggested_filename
        download.save_as(target)
        out[target.suffix.lstrip(".")] = target
    return out
