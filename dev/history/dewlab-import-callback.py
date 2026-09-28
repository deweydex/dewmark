# The commit callback used once, in September 2026, to bring dewmark's
# history out of deweydex/dewlab (DECISIONS_LOG.md, entry 0.1):
#
#   git filter-repo --subdirectory-filter dewmark --prune-degenerate always \
#     --commit-callback "$(cat dev/history/dewlab-import-callback.py)"
#
# It rewrites a subject's "(#N)" and "Merge pull request #N" to
# deweydex/dewlab#N, so GitHub links the pull request in the repository it
# belongs to, and adds an "Imported-from: deweydex/dewlab@<sha>" trailer to
# the existing trailer block. Only the subject is rewritten: a body's "(#21)"
# can be an open-question number, not a pull request. Kept as the record of
# how the import was made, not to be run again.
import re
subject, sep, rest = commit.message.partition(b"\n")
subject = re.sub(rb"\(#(\d+)\)$", rb"(deweydex/dewlab#\1)", subject)
subject = re.sub(rb"^Merge pull request #(\d+)", rb"Merge pull request deweydex/dewlab#\1", subject)
msg = (subject + sep + rest).rstrip(b"\n")
last = msg.rsplit(b"\n\n", 1)[-1]
is_trailer_block = all(re.match(rb"^[A-Za-z-]+: ", l) for l in last.split(b"\n")) and b"\n\n" in msg
trailer = b"Imported-from: deweydex/dewlab@" + commit.original_id[:12]
commit.message = msg + (b"\n" if is_trailer_block else b"\n\n") + trailer + b"\n"
