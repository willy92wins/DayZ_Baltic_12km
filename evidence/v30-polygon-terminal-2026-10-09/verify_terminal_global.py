"""Independent full-domain consumer: clip native wet triangles, then measure their boundary."""
from pathlib import Path
import argparse,csv,json,sys,time
import numpy as np
import shapely
from shapely.geometry import LineString
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

B=Path(__file__).parent
B13=Path('E:/DayZ-Baltic-Build/v30-native-turn-optimizer-20261009')
sys.path.insert(0,str(B13))
from verify_native_turns import basic_gate,controls,overlap_areas,domain,topology_gate,visible_error,clip,UNIT
from discover_native_turns import B9,B10,B12,sha


def triangle_contours(h,field,plane):
    rr,cc=np.nonzero(np.isfinite(plane))
    ground=np.c_[h[rr,cc],h[rr,cc+1],h[rr+1,cc],h[rr+1,cc+1]]
    depth=field[rr,cc]-ground
    segments=[];keys=[]
    offsets=np.array([[0.,0.],[6.,0.],[0.,-6.],[6.,-6.]])
    for ti,corners in enumerate(([0,1,3],[0,2,3])):
        depths=depth[:,corners]
        mixed=(depths.min(1)<0)&(depths.max(1)>0)
        for k in np.flatnonzero(mixed):
            # Consume the boundary of the clipped wet polygon, independently of author graph keys.
            weights=clip(UNIT,depths[k])
            zero=abs(weights@depths[k])<1e-9
            edge=weights[zero]
            if len(edge)!=2:raise AssertionError(('unexpected contour boundary',int(rr[k]),int(cc[k]),ti,len(edge)))
            xyz=offsets[corners]+[cc[k]*6,12282-rr[k]*6]
            segments.append(edge@xyz);keys.append((int(rr[k]),int(cc[k]),ti))
    segments=np.array(segments)
    merged=shapely.line_merge(shapely.union_all([LineString(s) for s in segments],grid_size=1e-6))
    lines=[p for p in getattr(merged,'geoms',[merged]) if p.geom_type=='LineString']
    return segments,np.array(keys),lines


def samples(lines):
    values=[];sites=[];total=0.;longs=0
    for line in lines:
        total+=line.length
        if line.length<=24:continue
        points=np.asarray(line.coords);dist=np.r_[0,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
        s=np.arange(0,dist[-1],2)
        q=np.c_[np.interp(s,dist,points[:,0]),np.interp(s,dist,points[:,1])]
        if len(q)<10:continue
        a=q[3:-3]-q[:-6];b=q[6:]-q[3:-3]
        angle=np.degrees(np.arctan2(abs(a[:,0]*b[:,1]-a[:,1]*b[:,0]),np.sum(a*b,axis=1)))
        values.extend(angle);sites.extend(q[3:-3]);longs+=1
    a=np.array(values);q=np.array(sites)
    return dict(chains=len(lines),long_chains=longs,length_m=total,samples=len(a),p90_degrees=float(np.percentile(a,90)),
                over30_share=float(np.mean(a>30)),max_degrees=float(a.max())),a,q


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--candidate',default='candidate');args=ap.parse_args()
    started=time.monotonic();source=Path('E:/DayZ-Baltic-Build/v30-native-hinge-finish-20261009/candidate/terrain.npz');candidate=B/args.candidate/'terrain.npz'
    author=json.loads((B/'authoring.json').read_text())
    expected=author['candidate_sha256'] if args.candidate=='candidate' else json.loads((B/'composition-repair.json').read_text())['candidate_sha256']
    assert sha(source)==author['source_sha256'] and sha(candidate)==expected
    t=dict(np.load(source));u=dict(np.load(candidate));h=t['heights'].astype(float);v=u['heights'].astype(float)
    f=np.load(B12/'preserved-field.npy');p=np.load(B10/'frozen-field-reference/plane.npy')
    fixed=np.load(B/'constraints.npz')['fixed'];allowed=np.zeros(h.shape,bool);tiles=[]
    for raw in (B/'tiles.jsonl').read_text().splitlines():
        tile=json.loads(raw);tiles.append(tile)
        if tile['status']=='INTEGRATE_SOURCE_ONLY':allowed.ravel()[tile['ids']]=True
    gates,physical=basic_gate(h,v,p,f,fixed,allowed)
    gates['metadata_exact']=set(t)==set(u) and all(np.array_equal(t[k],u[k],equal_nan=True) for k in t if k!='heights')
    gates['all_tiles_processed']=len(tiles)==json.loads((B/'discovery.json').read_text())['candidate_boxes']
    gates['no_author_errors']=not any(t['status']=='ERROR_UNCHANGED' for t in tiles)
    gates['perimeters_exact']=all(np.array_equal(h[r0,c0:c1+1],v[r0,c0:c1+1]) and np.array_equal(h[r1,c0:c1+1],v[r1,c0:c1+1]) and np.array_equal(h[r0:r1+1,c0],v[r0:r1+1,c0]) and np.array_equal(h[r0:r1+1,c1],v[r0:r1+1,c1]) for r0,c0,r1,c1 in (job['box_cells'] for job in json.loads((B/'discovery.json').read_text())['jobs']))
    negative=controls()
    wrong=v.copy();ix=int(np.flatnonzero(fixed)[100]);wrong.ravel()[ix]+=.1
    assert not basic_gate(h,wrong,p,f,fixed,allowed)[0]['fixed_exact'];negative.append('fixed_vertex_mutant_rejected');del wrong
    print(json.dumps(dict(stage='physical',gates=gates,physical=physical)),flush=True)
    segments0,keys0,lines0=triangle_contours(h,f,p);segments1,keys1,lines1=triangle_contours(v,f,p)
    assert np.array_equal(keys0,keys1),'Visible sign topology must preserve every mixed triangle'
    distance=float(np.linalg.norm(segments1-segments0,axis=2).max())
    before,a0,q0=samples(lines0);after,a1,q1=samples(lines1)
    gates.update(contour_correspondence=distance<=4.1,global_p90=after['p90_degrees']<=before['p90_degrees']+1e-5,
                 global_over30=after['over30_share']<=before['over30_share']+1e-12,global_max=after['max_degrees']<=before['max_degrees']+1e-5)
    sectors=[]
    for row in range(16):
        for col in range(16):
            aa=[]
            for angles,sites in ((a0,q0),(a1,q1)):
                mask=(sites[:,0]>=col*768)&(sites[:,0]<(col+1)*768)&(sites[:,1]>=row*768)&(sites[:,1]<(row+1)*768)
                theta=angles[mask]
                aa.append(None if not len(theta) else dict(samples=len(theta),p90=float(np.percentile(theta,90)),over30=float(np.mean(theta>30))))
            if aa[0] or aa[1]:sectors.append(dict(x0=col*768,z0=row*768,before=aa[0],after=aa[1]))
    print(json.dumps(dict(stage='contour',before=before,after=after,max_correspondence_m=distance)),flush=True)
    domains={}
    for label,field in (('physical',None),('visible',f)):
        old,new=domain(h,p,field),domain(v,p,field);overlap=overlap_areas(old,new);topology=topology_gate(old,new,overlap)
        contacts=[dict(axis=axis,new=int(((a<=1e-8)&(b>1e-8)).sum()),lost=int(((a>1e-8)&(b<=1e-8)).sum())) for axis,(a,b) in enumerate(zip(old['contacts'],new['contacts']))]
        rr,cc=old['cells'];cls=np.c_[t['cls'][rr,cc],t['cls'][rr,cc+1],t['cls'][rr+1,cc],t['cls'][rr+1,cc+1]]
        dry=np.stack((np.all(cls[:,[0,1,3]]==0,axis=1),np.all(cls[:,[0,2,3]]==0,axis=1)),axis=1).ravel()
        gain=np.maximum(0,new['areas']-overlap);dry_gain=float(gain[dry].sum())
        gates[label+'_topology']=topology['pass_gate'];gates[label+'_contacts']=not any(c['new'] or c['lost'] for c in contacts);gates[label+'_dry_flood']=dry_gain<=1e-8
        max_offset=None
        if label=='visible':
            delta=f[rr,cc]-p[rr,cc,None];delta=np.stack((delta[:,[0,1,3]],delta[:,[0,2,3]]),axis=1).reshape(-1,3)
            max_offset=float(visible_error(new['triangles'],delta,new['areas']).max());gates['visible_offset']=max_offset<=.35001
        domains[label]=dict(topology=topology,contacts=contacts,dry_gain_m2=dry_gain,gained_area_m2=float(gain.sum()),
                            lost_area_m2=float(np.maximum(0,old['areas']-overlap).sum()),max_visible_offset_m=max_offset)
        print(json.dumps(dict(stage=label,result=domains[label])),flush=True)
    figure,axes=plt.subplots(1,2,figsize=(14,6),layout='constrained')
    for ax,angles,sites,title in zip(axes,(a0,a1),(q0,q1),('Antes','Después')):
        ax.scatter(sites[:,0],sites[:,1],s=.12,c='#c9dfd7')
        pick=angles>30;sc=ax.scatter(sites[pick,0],sites[pick,1],s=.5,c=angles[pick],vmin=30,vmax=120,cmap='magma')
        ax.set(xlim=(0,12282),ylim=(0,12282),aspect='equal',title=title,xlabel='X (m)',ylabel='Z (m)')
    prefix='' if args.candidate=='candidate' else args.candidate+'-'
    figure.colorbar(sc,ax=axes,label='Giro a escala de 6 m (grados)');figure.savefig(B/(prefix+'global-contours.png'),dpi=180);plt.close(figure)
    np.savez_compressed(B/(prefix+'contour-samples.npz'),before_angles=a0,before_sites=q0,after_angles=a1,after_sites=q1)
    (B/(prefix+'sectors.json')).write_text(json.dumps(sectors,indent=2)+'\n')
    report=dict(status='PASS_GLOBAL_SOURCE' if all(gates.values()) else 'FAIL_GLOBAL_SOURCE',gates=gates,physical=physical,
        before=before,after=after,corresponding_contour_limit_m=distance,domains=domains,negative_controls=negative,
        source_sha256=sha(source),candidate_sha256=sha(candidate),seconds=time.monotonic()-started,
        limits=['All finite pond/river cells measured; ocean coast and terrain-only creases retain their separate scope.',
                'All sectors reported; a global improvement does not claim every corner is solved.',
                'Compiled coverage, native readback, navigation and visual acceptance remain separate.'])
    target='verification.json' if args.candidate=='candidate' else args.candidate+'-verification.json'
    (B/target).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],failed=[k for k,v in gates.items() if not v],seconds=report['seconds'])),flush=True)


if __name__=='__main__':main()
