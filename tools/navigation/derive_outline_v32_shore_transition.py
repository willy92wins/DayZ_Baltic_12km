"""Prepare one-cell freshwater banks while proving dry land above sea range."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
src=ROOT/'tools/navigation/prepare_outline_smoothing_v28.py'
dst=ROOT/'tools/navigation/prepare_outline_smoothing_v32.py'
assert not dst.exists()
t=src.read_text().replace('regional_outline_smoothing_v28','regional_outline_smoothing_v32')
def change(old,new):
    global t
    assert t.count(old)==1,old
    t=t.replace(old,new)
change("    geos=[g.buffer(6) if i in small_lakes else g for i,g in enumerate(source_geos)]",
       "    lake_indices=[i for i,f in enumerate(fs) if f['properties']['body'].startswith('lake_')]\n    geos=[g.buffer(6) if i in lake_indices else g for i,g in enumerate(source_geos)]")
change("bodies=[fs[i]['properties']['body'] for i in small_lakes],meaning=", "bodies=[fs[i]['properties']['body'] for i in lake_indices],scope='all_freshwater_with_marine_floor',marine_floor_m=1.4,small_core_bodies=[fs[i]['properties']['body'] for i in small_lakes],meaning=")
change("    union=unary_union(geos);land=box(0,0,12282,12282).difference(union)",
       "    union=unary_union(geos);land=box(0,0,12282,12282).difference(union)\n    original_union=unary_union(source_geos+[ocean]);original_land=box(0,0,12282,12282).difference(original_union)")
change("coastcells=rasterize([(union.boundary,1)]", "coastcells=rasterize([(union.boundary,1),(original_union.boundary,1)]")
change("        aa=np.c_[x,z];bb=np.c_[x+6,z];dd=np.c_[x+6,z-6];ee=np.c_[x,z-6]",
       "        local_sea_safe_land=original_land.intersection(box(float(x.min()),float(z.min()-6),float(x.max()+6),float(z.max())))\n        aa=np.c_[x,z];bb=np.c_[x+6,z];dd=np.c_[x+6,z-6];ee=np.c_[x,z-6]")
change("                if drypart.area>1e-8:point_bound(get_coordinates(drypart),float(ceil[k]),'dry_plane')",
       "                if drypart.area>1e-8:point_bound(get_coordinates(drypart),float(ceil[k]),'dry_plane')\n            # Source shoreline remains exact for the global sea floor. The lake\n            # freeboard rises over one cell; the pond mesh itself is unchanged.\n            sea_clips=intersection(tris,local_sea_safe_land)\n            for drypart in sea_clips:\n                if drypart.area>1e-8:point_bound(get_coordinates(drypart),1.4,'dry_sea_floor')")
change("    ident=eye(n,format='csr');zero=csr_matrix(matrix.shape)",
       "    return  # Matrix only; exact island and frozen-point constraints follow.\n    ident=eye(n,format='csr');zero=csr_matrix(matrix.shape)")
t=t.replace('only at these narrow lakes','at freshwater lakes; original dry geometry also has a1.4m marine floor')
dst.write_text(t)
print(dst)
