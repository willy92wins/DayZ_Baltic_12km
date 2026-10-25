"""Read-only road audit at 1m stations, independent of the solver's source stations."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
from scipy.ndimage import distance_transform_edt
from waterway_common import sample
ROOT=Path(__file__).resolve().parents[2]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,default=ROOT/'evidence/foundation-followup-2026-10-01/dense-road-sections.json')
    ap.add_argument('--terrain-npz',type=Path,default=ROOT/'tests/regional_foundation_combined_v10/reference.npz')
    args=ap.parse_args();out=args.out
    assert not out.exists(),'Preserve evidence'
    roadpath=ROOT/'tests/regional_foundation_roads_v6/reference.npz'
    terrainpath=args.terrain_npz
    roads=np.load(roadpath);data=np.load(terrainpath);h=data['candidate']
    assert h.shape==(2048,2048) and np.isfinite(h).all()
    wd=distance_transform_edt(~(data['wet']|data['ocean']))*6
    chains=json.loads((ROOT/'evidence/regional-foundation-v1/road-grade-chains-v6.json').read_text(encoding='utf-8'))['chains']
    reports=[];worst=[]
    for number,indices in enumerate(chains):
        p=roads['xy'][indices]
        if len(p)<4:continue
        station=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
        s=np.linspace(0,station[-1],int(np.ceil(station[-1]))+1)
        q=np.column_stack([np.interp(s,station,p[:,d]) for d in [0,1]])
        tangent=np.gradient(q,axis=0);norm=np.linalg.norm(tangent,axis=1)
        if np.any(norm<1e-8):raise ValueError('Degenerate tangent')
        normal=np.column_stack([-tangent[:,1],tangent[:,0]])/norm[:,None]
        rr=np.clip(np.rint((12282-q[:,1])/6).astype(int),0,2047);cc=np.clip(np.rint(q[:,0]/6).astype(int),0,2047)
        valid=(wd[rr,cc]>48)&(np.linalg.norm(q-[2417.1428225906,6889.8850822322],axis=1)>470)&(s>18)&(s<station[-1]-18)
        if not valid.any():continue
        offsets=np.arange(-4,4.01,.5)
        sections=np.array([q+normal*v for v in offsets])
        elev=np.array([sample(h,v[:,0]+200000,v[:,1]) for v in sections])
        cross=np.ptp(elev,axis=0);tyres=np.ptp(elev[abs(offsets)<=1],axis=0)
        offset_ds=np.linalg.norm(np.diff(sections,axis=1),axis=2)
        grade=np.max(abs(np.diff(elev,axis=1)/offset_ds),axis=0)
        pairs=valid[:-1]&valid[1:];centre_grade=abs(np.diff(elev[8])/np.diff(s))
        bad=valid&(cross>.03)
        for i in np.flatnonzero(bad):
            worst.append(dict(chain=number,station_m=float(s[i]),xz=q[i].tolist(),cross_8m=float(cross[i]),cross_2m=float(tyres[i])))
        reports.append(dict(chain=number,samples=int(valid.sum()),cross8m_failures=int(bad.sum()),max_cross8m=float(cross[valid].max()),max_cross2m=float(tyres[valid].max()),centre_grade_failures=int(((centre_grade>.065)&pairs).sum()),max_all_width_grade=float(grade[pairs].max()) if pairs.any() else None))
    report=dict(status='DENSE_GEOMETRY_DIAGNOSTIC_NOT_RUNTIME',step_m_at_most=1,lateral_offsets_m=offsets.tolist(),inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [roadpath,terrainpath]},
        samples=sum(x['samples'] for x in reports),cross8m_failures=sum(x['cross8m_failures'] for x in reports),centre_grade_failures=sum(x['centre_grade_failures'] for x in reports),chains=reports,worst=sorted(worst,key=lambda x:-x['cross_8m'])[:100],limits=['Normals at resampled polyline corners differ from sparse solver normals.','Cross8m is height spread of17lateral samples; not a measured pothole or abrupt vertical vehicle displacement.','No new terrain or gate tolerances applied.'])
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['status','samples','cross8m_failures','centre_grade_failures']}))

if __name__=='__main__':main()
