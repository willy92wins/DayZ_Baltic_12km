"""Restore the existing V9 one-micrometre island constraint contract."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];source=ROOT/'tools/navigation/solve_outline_v29_island_planes.py';target=ROOT/'tools/navigation/solve_outline_v30_island_planes.py';assert not target.exists();s=source.read_text()
for a,b in [("OUT=ROOT/'tests/regional_outline_smoothing_v29'","OUT=ROOT/'tests/regional_outline_smoothing_v30'"),("cols=lookup[ids];free=cols>=0;limit=-target-float(weights[~free]@macro.ravel()[ids[~free]])","cols=lookup[ids];free=(cols>=0)&(np.abs(weights)>1e-12);limit=-target+1e-6-float(weights[~free]@macro.ravel()[ids[~free]])"),("asc=OUT/'baltic_outline_smoothing_v29.asc'","asc=OUT/'baltic_outline_smoothing_v30.asc'")]:
    assert s.count(a)==1,a;s=s.replace(a,b)
s=s.replace('island_rows=len(rhs),impossible_fixed=impossible','island_constraint_tolerance_m=1e-6,island_rows=len(rhs),impossible_fixed=impossible')
target.write_text(s);print(target)
