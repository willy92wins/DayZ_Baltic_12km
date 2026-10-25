"""Run a tool with the skill's ODOL reader patched in memory for ODOL v56.

binarize.exe of 2026-10-15 23:47 (DayZ Tools) writes the p31 pond pieces as ODOL v56 (EV110's, binarized before, are
v55). v56 carries 4 more bytes in the model info, inside the zero run that holds ht_min .. shadow_offset; the skill's
reader (odol_reader.py:514-519, sha 688aaa90...) does not read them, so ODOL_ModelInfo drifts 4 bytes and the LZO block
of mass_array fails ("overrun M1-first"). Measured on p31_0008cbb73748437c.p3d: v55 1938 B, v56 1942 B, identical but
for the version and 4 zero bytes; with the 4 bytes read after force_not_alpha, every LOD's vertices and faces parse
identical to the v55 file. Which field the bytes belong to, and their exact place in the zero run, is NOT identified:
the pond pieces have zeros there, so any place gives the same parse for them; other models may differ.
This wrapper reads the skill file, inserts the read after force_not_alpha for version == 56 ONLY (the one format that
was checked; every other version keeps the skill's own parse), refuses a v56 file whose 4 extra bytes are not zero (the
only content checked: the pond pieces), loads it as 'odol_reader' (nothing on disk is changed) and runs the tool, whose
own `from odol_reader import ODOL` then gets the patched module.
Usage: run_with_odol56.py <tool.py> <tool args...>"""
import os, runpy, sys, types
SKILL = r"C:\Users\guill\.claude\skills\dayz-p3d-debinarizer\scripts"
ANCHOR = """            if v >= 54:
                mi.force_not_alpha = reader.read_uint32()
            else:
                mi.force_not_alpha = int(reader.read_bool())
"""
PATCH = """        if v == 56:
            mi.v56_extra = reader.read_uint32()   # run_with_odol56.py: 4 bytes added by binarize 2026-10-15
            if mi.v56_extra != 0:
                raise ValueError("run_with_odol56: v56 extra bytes are %#x, not 0: unchecked content, refused" % mi.v56_extra)
"""
src_path = os.path.join(SKILL, "odol_reader.py")
src = open(src_path, encoding="utf-8").read()
if src.count(ANCHOR) != 1:
    raise SystemExit("run_with_odol56: refused: anchor not found once in odol_reader.py (reader changed?)")
if "if v >= 56:" in src or "if v == 56:" in src:
    raise SystemExit("run_with_odol56: refused: odol_reader.py already handles v56; run the tool directly")
sys.path.insert(0, SKILL)
mod = types.ModuleType("odol_reader"); mod.__file__ = src_path
exec(compile(src.replace(ANCHOR, ANCHOR + PATCH), src_path + " (v56 patch)", "exec"), mod.__dict__)
sys.modules["odol_reader"] = mod
tool = sys.argv[1]
sys.argv = [tool] + sys.argv[2:]
runpy.run_path(tool, run_name="__main__")
