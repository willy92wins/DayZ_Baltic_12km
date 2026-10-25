"""Build two diagnostic world PBOs from reference B: D1 takes only the EV95 WRP, D2 only the EV95 layer PAAs.

Packing mirrors build-wide-slope/package.py (FileBank with the base PBO properties). Outputs go to a fresh
folder on E: and are then copied into fresh mod folders; nothing existing is overwritten.
"""
import hashlib, shutil, struct, subprocess, sys
from pathlib import Path

B_PBO = Path("P:/Mods/@DayZ_Baltic_IncrementalBankPreviewV1/Addons/narva_trial.pbo")
EV95_PBO = Path("P:/Mods/@DayZ_Baltic_EV95_WideBankPreviewV1/Addons/narva_trial.pbo")
WATER = Path("P:/Mods/@DayZ_Baltic_IncrementalBankPreviewV1/Addons/baltic_water_v30.pbo")
ROOT = Path("E:/DayZ-Baltic-Build/review-claude-20261011/bisect")
MODS = Path("P:/Mods")
FILEBANK = "C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe"
EXPECT = {B_PBO: "b11c825b6c14ecc5649ac668b40c7dc6c9f52c64c26ddfa748983c04b340c36c",
          EV95_PBO: "f1a148cab3e7d1d63473f0232a0971d45a9fea04e0fb456f01973235f4644b7d",
          WATER: "3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14"}


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def read_pbo(path):
    f = open(path, "rb")
    ents, props = [], {}

    def cstr():
        b = bytearray()
        while True:
            c = f.read(1)
            if c in (b"\0", b""):
                return b.decode("latin1")
            b += c

    while True:
        name = cstr()
        mt, orig, res, ts, size = struct.unpack("<5I", f.read(20))
        if name == "" and mt == 0x56657273:
            while True:
                k = cstr()
                if k == "":
                    break
                props[k] = cstr()
            continue
        if name == "":
            break
        ents.append((name.replace(chr(92), "/"), size))
    off = f.tell()
    out = {}
    for n, s in ents:
        f.seek(off)
        out[n] = f.read(s)
        off += s
    return props, out


def build(label, entries, props, replace):
    dist = ROOT / label / "distribution" / "narva_trial"
    packed = ROOT / label / "packed"
    dist.mkdir(parents=True, exist_ok=False)
    packed.mkdir(parents=True, exist_ok=False)
    for name, data in entries.items():
        path = dist / name
        assert path.resolve().is_relative_to(dist.resolve())
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(replace.get(name, data))
    cmd = [FILEBANK]
    for k, v in props.items():
        cmd += ["-property", k + "=" + v]
    done = subprocess.run(cmd + ["-dst", str(packed), str(dist)], capture_output=True, text=True)
    (ROOT / label / "filebank.log").write_text(done.stdout + "\n" + done.stderr)
    assert done.returncode == 0, done.stderr
    pbo = packed / "narva_trial.pbo"
    p2, after = read_pbo(pbo)
    assert p2 == props and after.keys() == entries.keys()
    assert all(after[k] == replace.get(k, entries[k]) for k in entries)
    mod = MODS / f"@DayZ_Baltic_Bisect{label}" / "Addons"
    mod.mkdir(parents=True, exist_ok=False)
    for src in (pbo, WATER):
        shutil.copyfile(src, mod / src.name)
        assert sha(src) == sha(mod / src.name)
    print(label, "world", sha(mod / "narva_trial.pbo"), "replaced", len(replace))


def main():
    for p, h in EXPECT.items():
        assert sha(p) == h, p
    props, b = read_pbo(B_PBO)
    _, e = read_pbo(EV95_PBO)
    assert b.keys() == e.keys()
    diff = [k for k in b if b[k] != e[k]]
    wrp = {k: e[k] for k in diff if k.lower().endswith(".wrp")}
    paa = {k: e[k] for k in diff if k.lower().endswith(".paa")}
    assert len(wrp) == 1 and len(paa) == 996 and len(diff) == 997
    ROOT.mkdir(parents=True, exist_ok=True)
    build(sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] == "D2" else "D1", b, props, wrp) if len(sys.argv) > 1 and sys.argv[1] == "D1" else None
    if len(sys.argv) == 1:
        build("D1", b, props, wrp)
        build("D2", b, props, paa)


if __name__ == "__main__":
    main()
