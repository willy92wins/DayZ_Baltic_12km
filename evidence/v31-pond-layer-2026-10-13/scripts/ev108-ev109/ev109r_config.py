import re
SRC = r"E:\DayZ-Baltic-Build\v31-pond-layer-20261013\ev109\stage\root\dayz_baltic_12km_dev\tb\narva_trial\config.cpp"
DST = r"E:\DayZ-Baltic-Build\v31-pond-layer-20261013\ev109r\stage\root\dayz_baltic_12km_dev\tb\narva_trial\config.cpp"
s = open(SRC, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in s else "\n"
anchor = r'		midDetailTexture="DZ\worlds\chernarusplus\data\middle_sat_mco.paa";'
assert s.count(anchor) == 1
add = (anchor + nl
       + r'		terrainNormalTexture="dayz_baltic_12km_dev\tb\narva_trial\data\baltic_global_nohq.paa";' + nl
       + "\t\theightBlendingMode=1;" + nl
       + "\t\tbicubicMode=1;")
s = s.replace(anchor, add)
open(DST, "w", encoding="utf-8", newline="").write(s)
print("ok", nl == "\r\n")
