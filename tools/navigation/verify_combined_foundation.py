"""Native-triangle consumer of combined roads, water and bank modifications."""
from pathlib import Path
import argparse,json
import numpy as np
from scipy.ndimage import distance_transform_edt
from shapely.geometry import shape
from waterway_common import sample
ROOT=Path(__file__).resolve().parents[2];EV=ROOT/'evidence/regional-foundation-v1'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--version',default='v1');args=ap.parse_args()
    data=np.load(ROOT/f'tests/regional_foundation_combined_{args.version}/reference.npz')
    h=data['candidate'];base=data['base'];surface=data['surfaces'];wet=data['wet']|data['ocean']
    changed=h!=base
    a=h[:-1,:-1];b=h[:-1,1:];c=h[1:,:-1];d=h[1:,1:]
    s1=np.degrees(np.arctan(np.hypot(b-a,d-b)/6));s2=np.degrees(np.arctan(np.hypot(d-c,c-a)/6))
    affected=changed[:-1,:-1]|changed[:-1,1:]|changed[1:,:-1]|changed[1:,1:]
    dry=~(wet[:-1,:-1]|wet[:-1,1:]|wet[1:,:-1]|wet[1:,1:])
    slope=np.maximum(s1,s2)
    worst=np.unravel_index(np.argmax(np.where(affected,slope,0)),slope.shape)
    terrain={'maximum_affected_triangle_degrees':float(slope[affected].max()),'affected_over_35deg':int((affected&(slope>35.01)).sum()),
             'dry_affected_over_35deg':int((affected&dry&(slope>35.01)).sum()),'worst_xz':[int(worst[1]*6),int(12282-worst[0]*6)]}
    rivers=[]
    for feature in json.loads((EV/'fairways-main-game.json').read_text())['features']:
        line=shape(feature['geometry']);s=np.linspace(0,line.length,max(3,int(np.ceil(line.length/2))+1))
        p=np.array([line.interpolate(float(v)).coords[0] for v in s]);delta=np.gradient(p,axis=0)
        normal=np.column_stack([-delta[:,1],delta[:,0]])/np.linalg.norm(delta,axis=1)[:,None]
        q=np.concatenate([p+normal*offset for offset in (-12,-6,0,6,12)])
        q[:,0]=np.clip(q[:,0],.01,12281.99);q[:,1]=np.clip(q[:,1],.01,12281.99)
        bottom=sample(h,q[:,0]+200000,q[:,1]);level=sample(surface,q[:,0]+200000,q[:,1])
        finite=np.isfinite(level)
        rivers.append({'river':feature['properties']['river'],'part':feature['properties']['part'],'samples':len(q),
                       'missing_surface_samples':int((~finite).sum()),'minimum_depth_m':float(np.min(level[finite]-bottom[finite])) if finite.any() else None,
                       'shallow_samples':int(((level-bottom)<3).sum())})
    roads=np.load(ROOT/'tests/regional_foundation_roads_v6/reference.npz');xy=roads['xy']
    chains=json.loads((EV/'road-grade-chains-v6.json').read_text())['chains']
    # Same interior gates, plus a distinct junction diagnostic. A water crossing
    # remains a future bridge; it is never filled merely to pass a road profile.
    wd=distance_transform_edt(~wet)*6
    bridge=np.array(json.loads((ROOT/'evidence/narva/evidence/narva-fit.json').read_text())['bridge_centre_tb'])-[200000,0]
    roadstats=[]
    for number,indices in enumerate(chains):
        p=xy[indices]
        if len(p)<4:continue
        delta=np.gradient(p,axis=0);norm=np.linalg.norm(delta,axis=1)
        if np.any(norm<1e-8):continue
        normal=np.column_stack([-delta[:,1],delta[:,0]])/norm[:,None]
        cc=np.clip(np.rint(p[:,0]/6).astype(int),0,2047);rr=np.clip(np.rint((12282-p[:,1])/6).astype(int),0,2047)
        station=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
        eligible=(wd[rr,cc]>48)&(np.linalg.norm(p-bridge,axis=1)>470)
        interior=eligible&(station>18)&(station<station[-1]-18)
        elev=np.array([sample(h,p[:,0]+normal[:,0]*off+200000,p[:,1]+normal[:,1]*off) for off in (-4,0,4)])
        cross=np.ptp(elev,axis=0);ds=np.diff(station);grade=np.diff(elev[1])/ds
        chord=abs(elev[1,1:-1]-(elev[1,:-2]*ds[1:]+elev[1,2:]*ds[:-1])/(ds[:-1]+ds[1:]))
        for name,valid in [('interior',interior),('junction',eligible&~interior)]:
            pairs=valid[:-1]&valid[1:];triples=valid[:-2]&valid[1:-1]&valid[2:]
            roadstats.append({'chain':number,'zone':name,'samples':int(valid.sum()),'rough':int(((cross>.03)&valid).sum()),
                              'grade':int(((abs(grade)>.065)&pairs).sum()),'chord':int(((chord>.03)&triples).sum())})
    totals={zone:{key:sum(r[key] for r in roadstats if r['zone']==zone) for key in ('samples','rough','grade','chord')} for zone in ('interior','junction')}
    report={'status':'GEOMETRY_REPORT_NOT_RUNTIME_ACCEPTANCE','terrain':terrain,'rivers':rivers,'roads':roadstats,'road_totals':totals,
            'water_missing':sum(r['missing_surface_samples'] for r in rivers),'water_shallow':sum(r['shallow_samples'] for r in rivers)}
    (EV/f'combined-geometry-{args.version}.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('rivers','roads')},indent=2))

if __name__=='__main__':main()
