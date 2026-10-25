"""Apply exact text replacements to a file: each old string must occur once; single binary write, fsync, read-back."""
import json
import os
import sys

target, patches = sys.argv[1], json.load(open(sys.argv[2], encoding="utf-8"))
data = open(target, "rb").read()
crlf = data.count(b"\r\n")
text = data.decode("utf-8")
for old, new in patches:
    n = text.count(old)
    assert n == 1, f"expected one match, found {n}: {old[:60]!r}"
    text = text.replace(old, new)
out = text.encode("utf-8")
assert b"\0" not in out and out.count(b"\r\n") == crlf, "line endings changed"
with open(target, "wb") as f:
    f.write(out)
    f.flush()
    os.fsync(f.fileno())
assert open(target, "rb").read() == out
print(f"patched {len(patches)} block(s), {len(data)} -> {len(out)} bytes: {target}")
