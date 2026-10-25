"""Move superseded Baltic preview mods from the DayZ Workshop folder (C:) to E:, verified by SHA-256 per file.

Each mod is copied to a fresh destination, every file is hashed on both sides, and only then is the source
tree removed. A mod that is a reparse point, or whose destination exists, is skipped. Writes a JSON receipt.
"""
import hashlib, json, os, shutil, stat, time
from pathlib import Path

SRC = Path(r"C:/Program Files (x86)/Steam/steamapps/common/DayZ/!Workshop")
DST = Path(r"E:/DayZ-Baltic-Build/archived-mods-20261011")
KEEP = {"@DayZ_Baltic_V30", "@DayZ_Baltic_IncrementalBankPreviewV1", "@DayZ_Baltic_EV95_WideBankPreviewV1",
        "@DayZ_Baltic_EV96_WaterFixV1", "@DayZ_Baltic_EV97_ReliefV1", "@DayZ_Baltic_ShoreWaveV30_Nav"}
MIN_BYTES = 100 * 1024 * 1024


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def size(d):
    return sum(f.stat().st_size for f in d.rglob("*") if f.is_file())


def main():
    DST.mkdir(parents=True, exist_ok=True)
    receipt = dict(started=time.strftime("%Y-%m-%d %H:%M:%S"), source=str(SRC), destination=str(DST), moved=[], skipped=[])
    for d in sorted(SRC.iterdir()):
        if not d.is_dir() or "baltic" not in d.name.lower() or d.name in KEEP:
            continue
        if os.stat(d, follow_symlinks=False).st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            receipt["skipped"].append([d.name, "reparse point"]); continue
        total = size(d)
        if total < MIN_BYTES:
            continue
        target = DST / d.name
        if target.exists():
            receipt["skipped"].append([d.name, "destination exists"]); continue
        shutil.copytree(d, target)
        files = {}
        for f in d.rglob("*"):
            if f.is_file():
                rel = f.relative_to(d).as_posix()
                a, b = sha(f), sha(target / rel)
                if a != b:
                    raise RuntimeError(f"hash mismatch {d.name}/{rel}")
                files[rel] = a
        shutil.rmtree(d)
        receipt["moved"].append(dict(name=d.name, bytes=total, files=files))
        print("moved", d.name, total, flush=True)
    receipt["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    receipt["moved_bytes"] = sum(m["bytes"] for m in receipt["moved"])
    (DST / "archive-receipt.json").write_text(json.dumps(receipt, indent=1))
    print("done", len(receipt["moved"]), "mods", receipt["moved_bytes"], "bytes; skipped", receipt["skipped"])


if __name__ == "__main__":
    main()
