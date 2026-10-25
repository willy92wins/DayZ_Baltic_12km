"""Measure native wet polygon splits, independently of the frozen flow axes."""
from pathlib import Path
import sys,json
import shapely
B=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008')
code=(B/'verify_contour_valley.py').read_text()
scope={'__name__':'component_audit'}
exec(code[:code.index('cut=before.boundary')],scope)
before,after=scope['before'],scope['after']
def parts(g):
    return [p for p in getattr(g,'geoms',[g]) if p.geom_type=='Polygon' and p.area>=1.]
old,new=parts(before),parts(after)
splits=[]
for i,p in enumerate(old):
    overlaps=[]
    for j,q in enumerate(new):
        a=p.intersection(q).area
        if a>=1.: overlaps.append(dict(after_id=j,overlap_m2=a,after_area_m2=q.area))
    if len(overlaps)>1:
        splits.append(dict(before_id=i,before_area_m2=p.area,bounds=list(p.bounds),after_parts=overlaps))
out=dict(status='FAIL_NATIVE_COMPONENT_SPLIT' if splits else 'NO_NEW_COMPONENT_SPLIT_ABOVE_1M2',before_components=len(old),after_components=len(new),splits=splits,method='Native triangle clipping against the frozen stitched water field; same complete domain for source and candidate. Components and overlaps below 1 square metre excluded as numerical/sliver noise.',limits=['Only the three pilot domains are measured. Water vertices at exact zero are included. This measures rendered water footprint, not nominal physical pond occupancy.'])
(scope['E']/f'native-components-{scope["label"]}.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
