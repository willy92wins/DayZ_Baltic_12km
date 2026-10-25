"""Create a reviewable V28 builder from the frozen shoreline implementation."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];folder=ROOT/'tools/navigation'
text=(folder/'prepare_outline_smoothing_v24.py').read_text()
def replace(old,new):
    global text
    assert text.count(old)==1,old[:120]
    text=text.replace(old,new)
replace("OUT=ROOT/'tests/regional_outline_smoothing_v24a'","OUT=ROOT/'tests/regional_outline_smoothing_v28'")
replace("from scipy.ndimage import gaussian_filter,distance_transform_edt,binary_dilation","from scipy.ndimage import gaussian_filter,distance_transform_edt,binary_dilation")
replace("geos=[shape(f['geometry']) for f in fs];levels=np.array([f['properties']['level_m'] for f in fs]+[1.05])",'''source_geos=[shape(f['geometry']) for f in fs]
    small_lakes=[i for i,f in enumerate(fs) if f['properties']['body'].startswith('lake_') and source_geos[i].buffer(-6*math.sqrt(2)).is_empty]
    geos=[g.buffer(6) if i in small_lakes else g for i,g in enumerate(source_geos)]
    levels=np.array([f['properties']['level_m'] for f in fs]+[1.05])
    (OUT/'shore-transition.json').write_text(json.dumps(dict(status='FROZEN_SHORE_DESIGN',source_hashes=hashes,transition_m=6,bodies=[fs[i]['properties']['body'] for i in small_lakes],meaning='Dry freeboard begins outside a one-cell shore transition only at these narrow lakes. Original water mesh/vector sources remain unchanged.'),indent=2)+'\\n')''')
replace("target[fixed]=base[fixed];target[wet&~editable]=base[wet&~editable]",'''island_support=ref['island_support_conservative']
    target[island_support]=np.maximum(target[island_support],base[island_support])
    target[(~wet)&(~fixed)]=np.maximum(target[(~wet)&(~fixed)],1.4)
    target[fixed]=base[fixed];target[wet&~editable]=base[wet&~editable]''')
replace("core=geos[number].buffer(-6*math.sqrt(2))\n        if core.is_empty:continue",'''core=source_geos[number].buffer(-4.5 if number in small_lakes else -6*math.sqrt(2))
        if core.is_empty:
            p=source_geos[number].representative_point();point_bound([[p.x,p.y]],float(levels[number]-.15),'lake_core',upper=True)
            continue''')
replace("lower=np.where(wet.ravel()[variables],lower,np.maximum(lower,1.4))\n    bounds=list(zip(lower,base.ravel()[variables]+6))+[(0,None)]*n",'''lower=np.where(wet.ravel()[variables],lower,np.maximum(lower,1.4))
    island_variables=island_support.ravel()[variables]
    lower[island_variables]=np.maximum(lower[island_variables],base.ravel()[variables][island_variables])
    upper=base.ravel()[variables].astype(float)+6
    bad_rows=[]
    for first in range(0,len(rhs),250000):
        chunk=matrix[first:first+250000];minimum=chunk.maximum(0)@lower+chunk.minimum(0)@upper
        bad_rows.extend((first+np.flatnonzero(minimum>rhs[first:first+len(minimum)]+1e-7)).tolist())
    selected=matrix[bad_rows]
    assert np.all(selected.data<=1e-9),'An individual non-dry conflict requires separate diagnosis'
    seeds=np.unique(selected.indices);seedgrid=np.zeros(base.shape,bool);seedgrid.ravel()[variables[seeds]]=True
    region=distance_transform_edt(~seedgrid)*6<=48 if len(seeds) else np.zeros(base.shape,bool)
    exception=region.ravel()[variables]&wet.ravel()[variables]
    upper[exception]=base.ravel()[variables][exception]+15
    pre=dict(status='FROZEN_BEFORE_SOLVE',source_npz_sha256=sha(source),seed_vertices=[dict(xz=[int(variables[i]%2048*6),int(12282-variables[i]//2048*6)],height=float(base.ravel()[variables[i]])) for i in seeds],local_exception_vertices=int(exception.sum()),local_exception_radius_m=48,ordinary_delta_limit_m=6,maximum_upward_delta_in_exception_m=15,small_lake_transition_m=6,small_lakes=[fs[i]['properties']['body'] for i in small_lakes],island_vertices_may_not_be_lowered=True)
    (OUT/'pre-solve.json').write_text(json.dumps(pre,indent=2)+'\\n')
    np.savez_compressed(OUT/'local-exception.npz',region=region,lo=lower,hi=upper)
    bounds=list(zip(lower,upper))+[(0,None)]*n''')
replace("candidate=macro.astype('float32');candidate.ravel()[variables]=solved.x[:n].astype('float32')",'''candidate=macro.astype('float32');candidate.ravel()[variables]=solved.x[:n].astype('float32')
        repair=(~wet)&(~fixed)&(candidate<np.float32(1.4));candidate[repair]=np.float32(1.4)
        assert np.all(candidate[island_support]>=base[island_support]-1e-5)''')
replace("asc=OUT/'baltic_outline_smoothing_v24.asc'","asc=OUT/'baltic_outline_smoothing_v28.asc'")
target=folder/'prepare_outline_smoothing_v28.py';assert not target.exists();target.write_text(text)
print(target)
