import re
subject, sep, rest = commit.message.partition(b"\n")
subject = re.sub(rb"\(#(\d+)\)$", rb"(deweydex/dewlab#\1)", subject)
subject = re.sub(rb"^Merge pull request #(\d+)", rb"Merge pull request deweydex/dewlab#\1", subject)
msg = (subject + sep + rest).rstrip(b"\n")
last = msg.rsplit(b"\n\n", 1)[-1]
is_trailer_block = all(re.match(rb"^[A-Za-z-]+: ", l) for l in last.split(b"\n")) and b"\n\n" in msg
trailer = b"Imported-from: deweydex/dewlab@" + commit.original_id[:12]
commit.message = msg + (b"\n" if is_trailer_block else b"\n\n") + trailer + b"\n"
