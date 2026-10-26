"""Read-only local polygon fan reconstruction, checked against observed native Y."""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(W/'tools/water'))
from prepare_visual_probe_v31 import height
D=R/'kit7-nav-tile-diagnostic-20261026';O=R/'kit7-nav-height-reconstruction-20261026';O.mkdir(exist_ok=False)
samples=json.loads((R/'kit7-nav-height-diagnostic-20261026/result.json').read_text())['samples'];rows=[];metadata=[]
for tile in json.loads((D/'result.json').read_text())['tiles']:
    assert len(tile['plausible_vertex_prefixes'])==1 and tile['plausible_vertex_prefixes'][0]['offset_from_header']==104
    verts=np.array(tile['plausible_vertex_prefixes'][0]['vertices']);i=tile['header_integers']
    assert i[9:12]==[0,0,0] and i[13]==0 # observed detail/off-mesh counts only
    path=D/('tile-%d-%d.bin'%tuple(tile['tile']));data=path.read_bytes();tris=[];polys=[]
    offset=104+len(verts)*12
    for k in range(i[6]):
        raw=struct.unpack_from('<I6H6HHBB',data,offset+32*k);count=raw[-2];ids=raw[1:1+count]
        assert 3<=count<=6 and len(set(ids))==count and max(ids)<len(verts)
        assert raw[-1]>>6==0
        poly=verts[list(ids)];fan=np.array([[poly[0],poly[t],poly[t+1]] for t in range(1,count-1)])
        tris.extend(fan);polys.append(dict(indices=ids,flags=raw[-3],area=raw[-1]&63,vertices=poly.tolist()))
    for s in samples:
        if [int(s['nav'][0]//12.5),int(s['nav'][2]//12.5)]!=tile['tile']:continue
        y=height(np.array(tris),np.array(s['nav'])[[0,2]]);assert y is not None
        rows.append(dict(query=s['query'],index=s['index'],native_y=s['nav'][1],polygon_fan_y=y,residual_m=y-s['nav'][1],road_y=s['engine_roadway'][1],failed=s['excess_m']>0))
    metadata.append(dict(tile=tile['tile'],polygons=polys,source_sha256=hashlib.sha256(data).hexdigest()))
assert len(rows)==8
out=dict(status='LOCAL_NAV_HEIGHT_RECONSTRUCTION',max_native_residual_m=max(abs(r['residual_m']) for r in rows),samples=rows,tiles=metadata,limits=['Empirical layout restricted to these three exact TESM9/VAND12 tiles; not a general decoder.','Polygon fan interpolation can explain numerical samples, but does not isolate how generator selected/simplified these polygons.','No artifact correction, tolerance relaxation or AI locomotion acceptance.'])
(O/'result.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='tiles'},indent=2))
