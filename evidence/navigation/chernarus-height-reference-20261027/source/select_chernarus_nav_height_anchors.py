"""Freeze reference locations independently of any navigation-height results."""
from pathlib import Path
import csv,hashlib,json,math
R=Path(__file__).parent
source=Path('E:/DayZ-Baltic-Build/vanilla-tricks-20261013/data/chernarus_objects.csv')
groups={kind:[] for kind in ('leaf','sand','moss')}
with source.open(newline='',encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        for kind in groups:
            if row['shape'].lower()=='dz\\water\\streambed\\streambed_'+kind+'_long_straight.p3d':
                groups[kind].append(row)
assert {k:len(v) for k,v in groups.items()}=={'leaf':218,'sand':188,'moss':148}
selected=[]
for kind,rows in groups.items():
    rows.sort(key=lambda r:(float(r['z']),float(r['x']),r['shape']))
    indices=[i*(len(rows)-1)//7 for i in range(8)];assert len(set(indices))==8
    for j in indices:
        row=rows[j];pos=[float(row[k]) for k in ['x','y','z']]
        axes=[[float(row[k+'_'+axis]) for axis in ['x','y','z']] for k in ['ax','ay','az']]
        assert all(math.isfinite(v) for v in pos+[x for a in axes for x in a])
        selected.append(dict(id='ref_'+str(len(selected)).zfill(2),family=kind,selection_index=j,family_count=len(rows),shape=row['shape'].lower(),historical_position=pos,historical_axes=axes))
O=R/'chernarus-nav-height-reference-20261027';O.mkdir(exist_ok=False)
result=dict(status='LOCATORS_FROZEN_NOT_CURRENT_OBJECT_PROOF',method='Eight floor(i*(N-1)/7) order statistics per family, sorted by(z,x,shape); no nav/height outcome read.',source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),selector_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),anchors=selected,expected_anchor_count=24,expected_queries=49,limits=['Historical native survey locators only; exact model and current position must be checked in new native run.','No substitute anchors after observing results. No change to Baltic queries or acceptance.'])
(O/'anchors.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(status=result['status'],anchors=len(selected),expected_queries=49,counts={k:len(v) for k,v in groups.items()})))
