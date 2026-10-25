"""Inventory both original wet endpoints of every declared EV112 stream site.

Reference comes from pre-kit wet component or declared stem, not wet_span.
Coverage is descriptive: endpoint loss is a repair candidate, not proof of its
intended receiver or client appearance. Does not alter any water or kit.
"""
import argparse,hashlib,json,sys
from pathlib import Path
from collections import Counter
import numpy as np
from scipy.ndimage import label
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import streambed_kit_v31 as K
from prepare_visual_probe_v31 import triangles,height


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('build');ap.add_argument('pilot');ap.add_argument('merged');ap.add_argument('output');a=ap.parse_args()
    B=Path(a.build);P=Path(a.pilot);M=Path(a.merged);out=Path(a.output);assert not out.exists();out.mkdir(parents=True)
    sitespath=B.parent/'ev112-ot1-20261018/sites-d.json';sites=json.loads(sitespath.read_text())
    records=json.loads((B/'water-fix-b/kit/kit-records.json').read_text());surf=K.KitSurface(records,K.load_models())
    ref=np.load(B.parent/'bridges/terrain-ev107.npz')['heights'];pl=np.load(B.parent/'bridges/fp-ev107/footprint.npz')['plane']
    vp=K.c2v_max(np.where(np.isfinite(pl),pl,-np.inf));wet=np.isfinite(vp)&(ref<vp);lab,_=label(wet,np.array([[1,1,0],[1,1,1],[0,1,1]]))
    H=np.load(M/'terrain-buried.npz')['heights'];Hbase=np.load(B/'water-fix-b/terrain.npz')['heights']
    actualplane=np.load(M/'bury-work/fp0/footprint.npz')['plane'];current=K.c2v_max(np.where(np.isfinite(actualplane),actualplane,-np.inf))
    pilotrep=json.loads((P/'author-report.json').read_text());pilotwet={s['site']:triangles(np.load(P/(s['site']+'-surfaces.npz'))['water']) for s in pilotrep['sites']}
    rows=[];built={r['site'] for r in records}
    for site in sites:
        sid=site['id']
        if site.get('mode','component')=='component':
            body,_,_,_,_=K.site_axis(site,vp,wet,lab);seed=tuple(np.argwhere(body)[0]);path=K.path_between(body,K.path_between(body,seed)[0])
            if vp[path[0]]<vp[path[-1]]:path=path[::-1]
        else:path=site['stem']
        for endpoint,rc in zip(('up','dn'),(path[0],path[-1])):
            r,c=map(int,rc);q=np.array([c*6,12282-r*6]);g=float(K.tri_h(H,*q));gb=float(K.tri_h(Hbase,*q))
            road,owner=surf.max_height([q],'road_ext',owner=True);visual=surf.max_height([q],'water')[0]
            oldheight=float(road[0]) if np.isfinite(road[0]) else None
            pw=height(pilotwet[sid],q) if sid in pilotwet else None
            ph=float(current[r,c]) if np.isfinite(current[r,c]) else None
            old_wet=bool((oldheight is not None and oldheight>gb+.1) or (ph is not None and ph>gb))
            new_wet=bool((pw is not None and pw-.25>g+.1) or (sid not in pilotwet and oldheight is not None and oldheight>g+.1) or (ph is not None and ph>g))
            receptor=site.get('ends',{}).get(endpoint,'natural_component')
            rows.append(dict(site=sid,end=endpoint,mode=site.get('mode','component'),built=sid in built,x=float(q[0]),z=float(q[1]),
                             reference_ground=float(ref[r,c]),reference_plane=float(vp[r,c]),ground=g,pond_plane=ph,
                             old_kit_water_road=oldheight,old_kit_visual=None if not np.isfinite(visual) else float(visual),
                             old_covering_site=records[int(owner[0])]['site'] if owner[0]>=0 else None,
                             candidate_water_road=None if pw is None else pw-.25,baseline_wet=old_wet,candidate_wet=new_wet,
                             declared_receptor=receptor,declared_extension=site.get('extend',{}).get(endpoint),
                             status='OFFLINE_COVERED' if new_wet else 'LOSS_CANDIDATE_PENDING_RECEIVER_REVIEW'))
    result=dict(status='INVENTORY_NOT_ACCEPTANCE',sites=len(sites),built_sites=len(built),ends=len(rows),
                baseline_missing=sum(not r['baseline_wet'] for r in rows),candidate_missing=sum(not r['candidate_wet'] for r in rows),
                counts=dict(Counter(r['status'] for r in rows)),points=rows,
                inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (sitespath,B/'water-fix-b/kit/kit-records.json',M/'terrain-buried.npz')},
                limits=['Point coverage does not prove continuous connection to a receiver.','No nearest receiver inference or silent routing change.','Not a global custom-geometry rollout.'])
    (out/'inventory.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k not in ('points','inputs')},indent=2))


if __name__=='__main__':main()
