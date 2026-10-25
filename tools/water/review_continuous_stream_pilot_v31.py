"""Consume saved pilot geometry; detect folds, false endpoint success and terrain regressions.

This is an OFFLINE gate; motor water/collision and human visual acceptance remain
separate. Has a deletion negative: removing the last water chunk must lose the
frozen endpoint while leaving interior water present.
"""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,Point
from shapely.ops import unary_union
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0,'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/py3d')
import py3d
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mesh_quality_v31 import closed_component
from stream_reference_v31 import recover,require_original_endpoints,PINS


def vertices(lod,face,origin):
    return np.array([lod.points[v.point_index].coords for v in face.vertices])+origin


def require_authored_support(authored,base,candidate):
    if authored.shape!=base.shape or candidate.shape!=base.shape or not all(np.isfinite(h).all() for h in (authored,base,candidate)):
        raise ValueError('invalid terrain shape or heights')
    changed=authored!=base
    if not changed.any() or not np.array_equal(candidate[changed],authored[changed]):
        raise ValueError('review terrain does not retain the authored pilot support')


def main():
    p=argparse.ArgumentParser();p.add_argument('pilot');p.add_argument('build');p.add_argument('--terrain',type=Path);p.add_argument('--output',type=Path)
    p.add_argument('--base-terrain',type=Path);p.add_argument('--base-footprint',type=Path)
    p.add_argument('--expected-base-sha256');p.add_argument('--expected-footprint-sha256');a=p.parse_args()
    out=Path(a.pilot);B=Path(a.build);rep=json.loads((out/'author-report.json').read_text())
    original=recover(B,[s['site'] for s in rep['sites']])
    dest=a.output or out
    if a.output:dest.mkdir(parents=True,exist_ok=False)
    bp=a.base_terrain or B/'water-fix-b/terrain.npz';fp_path=a.base_footprint or B/'water-fix-b/bury-work/fp0/footprint.npz'
    if a.base_terrain or a.base_footprint:
        if not (a.base_terrain and a.base_footprint and a.expected_base_sha256 and a.expected_footprint_sha256):
            raise ValueError('explicit review base requires both paths and both pinned hashes')
    base_hash=hashlib.sha256(bp.read_bytes()).hexdigest();fp_hash=hashlib.sha256(fp_path.read_bytes()).hexdigest()
    assert base_hash==(a.expected_base_sha256 or '07054c46ebf2861bc905fe2d68fb3b734d7b8e9ad1d538c73a7ee745edd56d62')
    assert fp_hash==(a.expected_footprint_sha256 or '49ee2a69db85f047425f8e1d31a964f92771ceb19b203c42570b04c3c6207de5')
    assert rep['terrain_input_sha256']==base_hash and rep['footprint_sha256']==fp_hash
    authored_path=out/'terrain.npz';terrain_path=a.terrain or authored_path
    authored_hash=hashlib.sha256(authored_path.read_bytes()).hexdigest()
    assert authored_hash==rep['terrain_sha256'], 'authored terrain changed'
    terrain_hash=hashlib.sha256(terrain_path.read_bytes()).hexdigest()
    H=np.load(terrain_path)['heights'];base=np.load(bp)
    require_authored_support(np.load(authored_path)['heights'],base['heights'],H)
    changed=H!=base['heights'];reports=[];checks={}
    assert rep['sites'] and len({s['site'] for s in rep['sites']})==len(rep['sites'])
    fig,axes=plt.subplots(len(rep['sites']),2,figsize=(12,5*len(rep['sites'])),squeeze=False,constrained_layout=True)
    for si,site in enumerate(rep['sites']):
        name=site['site'];z=np.load(out/(name+'-surfaces.npz'))
        require_original_endpoints(site['original_raw_endpoints'],original[name])
        bed=z['bed'];water=z['water'];axis=z['axis'];s=z['station']
        # Independent edge orientation sign: no silently reversed offset cells.
        flat=bed[...,[0,2]]
        u=flat[1:,:-1]-flat[:-1,:-1];v=flat[1:,1:]-flat[:-1,:-1]
        area=u[...,0]*v[...,1]-u[...,1]*v[...,0]
        u2=flat[1:,1:]-flat[:-1,:-1];v2=flat[:-1,1:]-flat[:-1,:-1]
        area2=u2[...,0]*v2[...,1]-u2[...,1]*v2[...,0]
        sign=np.sign(np.median(area))
        folds=int((area*sign<=0).sum()+(area2*sign<=0).sum())
        wf=water[...,[0,2]];wa=wf[1:,:-1]-wf[:-1,:-1];wb=wf[1:,1:]-wf[:-1,:-1];wc=wf[:-1,1:]-wf[:-1,:-1]
        water_folds=int(((wa[...,0]*wb[...,1]-wa[...,1]*wb[...,0])*sign<=0).sum()+((wb[...,0]*wc[...,1]-wb[...,1]*wc[...,0])*sign<=0).sum())
        polys=[];water_road=[];volumes=[];model_counts=[];closure=[]
        instances=[i for i in rep['instances'] if i['site']==name]
        for inst in instances:
            origin=np.array(inst['origin']);path=out/'source'/Path(inst['model'].replace('\\','/'))
            model=py3d.P3D(open(path,'rb'));vis=model.lods[0];geo=model.lods[1];road=model.lods[3]
            pp=[]
            for f in vis.faces:
                assert f.texture and f.material
                if 'water_streambed.rvmat' in f.material:
                    v=vertices(vis,f,origin);pp.append(Polygon(v[:,[0,2]]))
            polys.append(unary_union(pp))
            for f in road.faces:
                if 'water_ext.paa' in f.texture:
                    v=vertices(road,f,origin);water_road.append(Polygon(v[:,[0,2]]))
            for selection in geo.selections.values():
                closure.append(closed_component([vertices(geo,f,np.zeros(3)) for f in selection.faces]))
                allv=np.array([p.coords for p in selection.points]);centre=allv.mean(0)
                volume=0.
                for face in selection.faces:
                    tri=vertices(geo,face,np.zeros(3))-centre
                    volume+=np.dot(tri[0],np.cross(tri[1],tri[2]))/6
                volumes.append(volume)
            model_counts.append(dict(model=path.name,faces=len(vis.faces),collision_components=len(geo.selections),bytes=path.stat().st_size))
        polygon=unary_union(polys);roadpoly=unary_union(water_road)
        endpoints=np.array(site['original_raw_endpoints'])
        end_hit=[polygon.buffer(.00002).covers(Point(q)) for q in endpoints]
        end_road=[roadpoly.buffer(.00002).covers(Point(q)) for q in endpoints]
        tail_index=next((i for i,p in enumerate(polys) if p.buffer(.00002).covers(Point(endpoints[-1]))),len(polys))
        removed=unary_union(polys[:tail_index])
        # Independent last-source endpoint, not a shortened author wet_span.
        negative_lost=not removed.buffer(.00002).covers(Point(endpoints[-1]))
        negative_keeps=removed.covers(Point(axis[len(axis)//3]))
        row=dict(site=name,offset_fold_triangles=folds,water_fold_triangles=water_folds,water_connected=polygon.geom_type=='Polygon',
                 endpoint_visual=end_hit,endpoint_road=end_road,negative_tail_removed_detected=negative_lost and negative_keeps,
                 collision_closed_volume_max=max(volumes),collision_components=len(closure),
                 invalid_closed_components=sum(not c['closed'] for c in closure),models=model_counts)
        reports.append(row)
        checks[name]=bool(folds==water_folds==0 and row['water_connected'] and all(end_hit) and all(end_road) and closure and all(c['closed'] for c in closure) and max(volumes)<0 and row['negative_tail_removed_detected'])
        ax=axes[si,0]
        oldrep=json.loads((B/'water-fix-b/kit/kit-report.json').read_text())
        oldaxis=np.array(next(r for r in oldrep['sites'] if r['site']==name)['lattice'])
        ax.plot(oldaxis[:,0],oldaxis[:,1],c='#c15943',label='Eje actual',lw=1.5)
        ax.plot(axis[:,0],axis[:,1],c='#1683ad',label='Piloto continuo',lw=2)
        ax.scatter(endpoints[:,0],endpoints[:,1],c='#142a36',s=22,label='Extremos de referencia')
        ax.set_aspect('equal');ax.set_title(name+' · trazado');ax.legend(fontsize=8);ax.grid(alpha=.2)
        ax=axes[si,1]
        for j in range(0,bed.shape[1],2):ax.plot(s,bed[:,j,1],lw=.65,alpha=.65)
        ax.plot(s,z['level'],c='#1683ad',lw=2,label='Agua visual')
        ax.set_title(name+' · perfil del lecho y márgenes');ax.set_xlabel('Estación (m)');ax.set_ylabel('Altura (m)');ax.grid(alpha=.2)
    fp=np.load(fp_path);m=np.isfinite(fp['plane'])
    pond=np.zeros_like(changed)
    for dr in (0,1):
        for dc in (0,1):pond[dr:dr+2047,dc:dc+2047]|=m
    checks['current_pond_corners_unchanged']=not bool((changed&pond).any())
    checks['frozen_unchanged']=not bool((changed&(base['reserve']|base['platform']|base['narva'])).any())
    checks['no_new_sea_vertices']=not bool(((base['heights']>=.75)&(H<.75)).any())
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'terrain'))
    from shape_repair_constraints_ev112 import s3_road_guard
    road_guard,road_hashes=s3_road_guard()
    checks['road_triangles_unchanged']=not bool((changed&road_guard).any())
    for key in ('v31_bridge_cut','v31_bridge_fill','v31_dam','v31_causeway','v31_shore_ramp','v31_continuous_pilot','v31_road_repair','v31_road_mesh_repair'):
        if key in base.files:checks[key+'_unchanged']=not bool((changed&base[key]).any())
    rr,cc=np.mgrid[:2048,:2048]
    checks['protected_01545_unchanged']=not bool((changed&(np.hypot(cc*6.-10397.4,12282.-rr*6.-9421.9)<=60)).any())
    fig.suptitle('EV112 · candidato geométrico, todavía sin aceptación en motor')
    fig.savefig(dest/'pilot-preview.png',dpi=160);plt.close(fig)
    result=dict(status='OFFLINE_PASS' if all(checks.values()) else 'FAIL',checks=checks,sites=reports,prekit_reference_sha256=PINS,
                changed_vertices=int(changed.sum()),scope='Saved MLOD geometry only; no engine or visual claim.')
    result.update(base_terrain_sha256=base_hash,base_footprint_sha256=fp_hash,road_reference_hashes=road_hashes,
                  reviewed_terrain_path=str(terrain_path),reviewed_terrain_sha256=terrain_hash,authored_terrain_sha256=authored_hash)
    (dest/'review.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='sites'},indent=2))
    print(json.dumps([{k:v for k,v in r.items() if k!='models'} for r in reports],indent=2))
    sys.exit(0 if all(checks.values()) else 1)


if __name__=='__main__':main()
