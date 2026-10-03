"""What the browser rehearsals share: sitting a paper in a real Chromium.

A page opens with a stand-in for the browser's save window (FAKE_PICKER),
because Chromium cannot show a window to a test; the stand-in keeps what is
written to the chosen file in window.__saved. The helpers go through the two
screens as a student does, and read browser storage as the page wrote it.
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

# A stand-in for the browser's save window: it hands the page a file that keeps
# every write in window.__saved.
FAKE_PICKER = """
window.__saved = [];
window.showSaveFilePicker = async (options) => ({
  name: options.suggestedName,
  createWritable: async () => {
    let text = "";
    return { write: async (data) => { text = data; },
             close: async () => { window.__saved.push(text); } };
  },
});
"""
NO_PICKER = "delete window.showSaveFilePicker;"
CANCELLED_PICKER = ("window.showSaveFilePicker = async () => "
                    "{ throw new DOMException('cancelled', 'AbortError'); };")
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


def choose_file(page):
    if page.is_visible("#dm-choose-file"):
        page.click("#dm-choose-file")
        wait_for(page, "document.getElementById('dm-file-status').textContent.length > 0")


def press_begin(page):
    page.click("#dm-begin")
    page.wait_for_selector("#dm-app:not([hidden])")


def begin(page, name="Agnes Nitt", number="S12345", choose=True):
    """The whole way in: details, Next, where the file goes, Begin."""
    type_details(page, name, number)
    next_screen(page)
    if choose:
        choose_file(page)
    press_begin(page)


def resume(page, number="S12345"):
    """Type the number, Continue my work, then Begin."""
    page.fill("#dm-number", number)
    page.wait_for_selector("#dm-restore:not([hidden])")
    page.click("#dm-continue")
    page.wait_for_selector("#dm-before:not([hidden])")
    choose_file(page)
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
