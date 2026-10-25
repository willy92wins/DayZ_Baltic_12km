"""Prepare one bounded 30x2s diagnostic. No acceptance gate or live mission is changed."""
from pathlib import Path
import hashlib,json
O=Path(__file__).parent;D=O/'water-temporal-ae';assert not D.exists()
source=O/'probe-live-prepared/init.c';raw=source.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='9a5ac56ceb0679cc4fbfeaab0b8684a322d1b29ce2b5e78c4019ca91d43e6c2c'
s=raw.decode().replace('\r\n','\n')
def replace(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
s=s.replace('baltic_bridge_probe_v2.log','baltic_water_temporal_ev112.log')
replace('BALTIC_BRIDGE_PROBE_V2;BalticTrial','BALTIC_WATER_TEMPORAL_EV112;BalticTrial')
replace('protected bool m_Done;','protected bool m_Done;\n    protected int m_Sample;')
replace('LogRow("BEGIN;" + m_Rows.Count());','LogRow("BEGIN;30;" + m_Rows.Count());')
replace('row = "P;" + m_Fields[0] + ";" + ground;','row = "P;" + m_Sample + ";" + GetGame().GetTime() + ";" + m_Fields[0] + ";" + ground;')
replace('row = row + ";" + m_Objects.Count();','row = row + ";" + m_Objects.Count();\n            row = row + ";" + GetGame().GetWaterSurfaceHeightWithFakeWave(above);\n            row = row + ";" + GetGame().SurfaceGetSeaWaveCurrent();')
replace('LogRow("END;" + m_Rows.Count());\n        m_Done = true;','m_Sample = m_Sample + 1;\n        m_StartMs = GetGame().GetTime() + 2000;\n        if (m_Sample >= 30)\n        {\n            LogRow("END;30;" + m_Rows.Count());\n            m_Done = true;\n        }')
ps=json.loads((O/'probe-c/points.json').read_text());byid={p['id']:p for p in ps}
selected=[byid[i] for i in (2733,3807,3808,3836)]
# Controls chosen by unchanged reference geometry, not by later temporal results.
selected.append(next(p for p in ps if p['family']=='kit' and p['kind']=='kit_axis' and p['water_ext']-p['ground']>=0.4))
selected.append(next(p for p in ps if p['family']=='kit' and p['kind']=='kit_side' and p['ground']-p['kit_water']>=0.4))
selected.append(next(p for p in ps if p['family']=='kit' and p.get('expect')=='test' and p['kind']=='kit_joint'))
selected.append(next(p for p in ps if p['family']=='shores' and p['expect']=='dry' and p.get('islet')))
assert len({p['id'] for p in selected})==8
original_csv=(O/'probe-c/points.csv').read_text().splitlines();csv_byid={int(l.split(';')[0]):l for l in original_csv}
D.mkdir();(D/'init.c').write_text(s,encoding='utf-8');(D/'points.csv').write_text('\n'.join(csv_byid[p['id']] for p in selected)+'\n');(D/'points.json').write_text(json.dumps(selected,indent=2)+'\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=dict(status='PREPARED_DIAGNOSTIC_ONLY',samples=30,interval_ms=2000,points=len(selected),source_init_sha256=sha(source),files={p.name:sha(p) for p in D.iterdir()},criteria='Keep raw strict FAIL. Check whether identical points cross depth zero over time while ground and pond/sea flags stay stable, and whether depth tracks with-fake surface. No gate change or repeated acceptance selection.',source_apis='P:/scripts/3_game/global/game.c:1192-1202,1533-1534; existing mission supplies other signatures.')
(D/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest))
