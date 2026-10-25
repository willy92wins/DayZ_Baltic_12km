from pathlib import Path
import hashlib,json
R=Path(__file__).parent;B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018')
old=B/'personal-view-visual-20261024-r/points.json';new=R/'runtime-midpoint-b/full/points.json';O=R/'road-sections-f';assert not O.exists()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
a=json.loads(old.read_text());b=json.loads(new.read_text());assert len(a['road_sections'])==11
prior={x['id']:x for x in a['points']};by_xz={(p['x'],p['z']):p for p in b['points']};rows=[];missing=[]
for section in a['road_sections']:
    mapped=[]
    for i in section['ids']:
        p=prior[i];q=by_xz.get((p['x'],p['z']))
        if q is None:missing.append(dict(original_id=i,x=p['x'],z=p['z']));continue
        assert abs(p['ground']-q['ground'])<1e-6 and q['expect']==p['expect']=='dry'
        mapped.append(q['id'])
    rows.append(dict(station_m=section['station_m'],ids=mapped))
O.mkdir();report=dict(status='EXACT_11_SECTIONS_BOUND_TO_F_PROBE' if not missing else 'MISSING_FIXED_ROAD_POINTS',source_sha256=sha(old),F_points_sha256=sha(new),sections=rows,missing=missing,limits=['Coordinate and expected-ground parity only; native result pending.'])
(O/'binding.json').write_text(json.dumps(report,indent=2)+'\n')
if not missing:
    b['road_sections']=rows;(O/'points.json').write_text(json.dumps(b,indent=2)+'\n')
print(json.dumps(dict(status=report['status'],sections=11,missing=len(missing))))
