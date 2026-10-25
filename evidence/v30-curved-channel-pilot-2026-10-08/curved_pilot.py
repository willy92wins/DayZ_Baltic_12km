"""Bounded R1 placement search; original map and deployed packages remain immutable."""
from pathlib import Path
import copy,hashlib,json,math,sys
import numpy as np
import shapely
from shapely.geometry import Point,Polygon,LineString,box
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path(r'E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008')
E=W/'evidence/v30-curved-channel-pilot-2026-10-08'
FIT=Path(r'E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2')
TERRAIN=Path(r'E:/DayZ-Baltic-Build/v30-navigation-contract-20261008/terrain_floor.npz')
LIB=W/'evidence/v30-vanilla-channel-pilot-2026-10-04/library.json'
sys.path[:0]=[str(W/'tools/terrain'),str(W/'tools/water')]
from verify_channel_reaches_v30 import retained_pond_faces,check_face_coverage
from v30_common import tri_sample
from fit_channel_pieces_v30 import place,matrix,axes2
from compare_channel_joints_v30 import layered
import engine_water_model as ewm
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(TERRAIN)=='05a9d6812ba3e3391b8da0d4690e8034ea747a92aa0fdaa96425b58dd78074d3'
a=json.loads((FIT/'axes.json').read_text())['R1']
manifest=json.loads((FIT/'water/pieces.json').read_text())
lib=json.loads(LIB.read_text())['pieces']
def validate_native_models(specs):
    for k,v in specs.items():
        assert sha(ewm.DZ/(k+'.p3d'))==v['sha256'],k
validate_native_models(lib)
terrain=np.load(TERRAIN);h=terrain['heights'];cls=terrain['cls']
axis=LineString(zip(a['x'],a['z']))
smooth=LineString(zip(a['smooth_x'],a['smooth_z']))
ds=np.arange(0,smooth.length+0.001,1.)
xyz=np.array([smooth.interpolate(s).coords[0] for s in ds])
tans=np.gradient(xyz,axis=0);tans/=np.linalg.norm(tans,axis=1)[:,None]
interp=lambda s:np.array([np.interp(s,a['s'],a['x']),np.interp(s,a['s'],a['z'])])
lo=smooth.project(Point(interp(a['s_lo'])));hi=smooth.project(Point(interp(a['s_hi'])))
s0=max(0,lo-30);finish=min(smooth.length-1,hi+18)
def near(p):
    ii=int(np.argmin(np.sum((xyz-p)**2,axis=1)))
    return ds[ii],float(np.linalg.norm(xyz[ii]-p)),tans[ii]
def level(p):return float(np.interp(axis.project(Point(p)),a['s'],a['surface']))
cells=[box(c*6,12282-(r+1)*6,(c+1)*6,12282-r*6) for r,c in a['removed_cells']]
domain=shapely.union_all(cells)
wet=[]
for r,c in a['removed_cells']:
    for dr,dc in ((0,1),(1,0)):
        rc=[(r,c),(r+dr,c+dc),(r+1,c+1)]
        if all(cls[u,v]>0 for u,v in rc):wet.append(Polygon([(6*v,12282-6*u) for u,v in rc]))
wet_union=shapely.union_all(wet)
path_s=np.linspace(a['s_lo'],a['s_hi'],102)
nav_line=LineString([interp(s) for s in path_s])
corridor=nav_line.buffer(12,cap_style=2,join_style=2)
retained=retained_pond_faces(FIT,manifest,domain.union(corridor).buffer(100))
pond=shapely.union_all([p[0] for p in retained])
types=sorted(k for k,v in lib.items() if v['family']=='river' and k!='river_24_6')
def search(scales):
    first=np.array(smooth.interpolate(s0).coords[0]);_,_,t=near(first);n=np.array([-t[1],t[0]])
    beam=[]
    for lateral in (-3.5,0.,3.5):
        for angle in (-8.,-4.,0.,4.,8.):
            ang=math.atan2(t[1],t[0])+math.radians(angle)
            beam.append((0.,s0,first+lateral*n,np.array([math.cos(ang),math.sin(ang)]),[]))
    terminal=[];expanded=0
    for depth in range(10):
        nxt=[]
        for cost,progress,joint,down,pcs in beam:
            for k in types:
                for scale in scales:
                    origin,yaw,j2,d2=place(lib[k],scale,joint,down)
                    progress2,lat2,td2=near(j2)
                    mid=(joint+j2)/2;_,latm,tdm=near(mid)
                    if progress2<progress+8 or lat2>35 or latm>35:continue
                    span=float(np.linalg.norm(j2-joint))
                    errangle=math.acos(float(np.clip(d2@td2,-1,1)))
                    cost2=cost+span*(latm*latm+0.2*lat2*lat2+20*errangle*errangle)
                    pc=dict(type=k,scale=scale,origin=origin.tolist(),yaw=yaw,joint=joint.tolist(),next_joint=j2.tolist())
                    row=(cost2,progress2,j2,d2,pcs+[pc]);expanded+=1
                    if progress2>=finish:
                        if any(abs(lib[p['type']]['turn_deg'])>1 for p in row[4]):terminal.append(row)
                    else:nxt.append(row)
        # Fixed finite beam, no adaptive restarts.
        beam=sorted(nxt,key=lambda r:r[0]/max(1,r[1]-s0))[:96]
        if not beam:break
    terminal.sort(key=lambda r:r[0]/max(1,r[1]-s0))
    return terminal[:40],dict(expanded=expanded,terminal=len(terminal),max_depth=10,beam=96,examined_final=min(40,len(terminal)))
def convert(pcs,overlap_m=0):
    out=[]
    for j,p in enumerate(pcs):
        k=p['type'];s=p['scale'];spec=lib[k]
        origin=np.array(p['origin']);yaw=p['yaw'];right,fwd=axes2(yaw)
        # One optional correction translates downstream objects upstream by 1 cm,
        # preserving model identity and terrain. It is never silently iterative.
        if overlap_m and j:origin=origin-float(overlap_m)*(-fwd)
        up=origin+s*(spec['end']['mid'][0]*right+spec['end']['mid'][1]*fwd)
        dn=origin+s*(spec['start']['mid'][0]*right+spec['start']['mid'][1]*fwd)
        upy,dny=level(up),level(dn)
        run=(spec['end']['mid'][1]-spec['start']['mid'][1])*s
        theta=math.asin(np.clip((upy-dny)/run,-0.05,0.05))
        y0=upy-spec['flat_y']*s*math.cos(theta)-spec['end']['mid'][1]*s*math.sin(theta)
        m=matrix(yaw,theta,s,[origin[0],y0,origin[1]])
        out.append(dict(reach='R1',type=k,model=spec['model'],scale=s,pitch_deg=math.degrees(theta),yaw=yaw,matrix=m,overlap=False))
    return out
def polys(pcs):
    result=[]
    for p in pcs:
        piece=ewm.Piece(p['type'],p['matrix'])
        result.append(shapely.union_all([Polygon(piece.w[f][:,[0,2]]) for f in piece.faces]))
    return result
def geometric(pcs):
    footprints=polys(pcs);cover,multi,_=layered(footprints);u=shapely.union_all(footprints)
    actual=u.union(pond)
    coverage=check_face_coverage(wet,actual);gap=corridor.difference(actual)
    pond_overlap=float(u.intersection(pond).intersection(domain).area)
    return dict(pieces=len(pcs),curves=sum(abs(lib[p['type']]['turn_deg'])>1 for p in pcs),
                covered_m2=cover,multi_m2=multi,multi_share=multi/cover if cover else 1,
                wet_faces=coverage,corridor_gap_m2=gap.area,
                retained_pond_overlap_in_domain_m2=pond_overlap,
                geometry_pass=bool(multi<=cover*.01 and coverage['uncovered_faces']==0 and gap.area<=1e-6))
def physical_samples(pcs):
    pieces=[ewm.Piece(p['type'],p['matrix']) for p in pcs]
    rows=[]
    for s in path_s:
        p=interp(s);d=interp(s+0.5)-interp(s-0.5);d/=np.linalg.norm(d);n=np.array([-d[1],d[0]])
        for off in (-12.,-6.,0.,6.,12.):
            x,z=p+off*n;g=float(tri_sample(h,x,z))
            waters=[q.level(x,g+.01,z) for q in pieces]
            waters += [y for poly,y,_ in retained if poly.covers(Point(x,z))]
            waters=[v for v in waters if v is not None]
            rows.append(dict(s=float(s),offset=off,x=float(x),z=float(z),ground=g,level=max(waters) if waters else None))
    return rows
def screen(rows,control):
    absent=[];shallower=[];dry=[]
    for i,(q,b) in enumerate(zip(rows,control)):
        if q['level'] is None:absent.append(i);continue
        if b['level'] is not None and q['level']-q['ground']<min(.95,b['level']-b['ground'])-1e-6:shallower.append(i)
        if q['level']<=q['ground']:dry.append(i)
    return dict(samples=len(rows),absent=absent[:12],absent_count=len(absent),shallower=shallower[:12],
                shallower_count=len(shallower),dry=dry[:12],dry_count=len(dry),
                pass_local=not absent and not shallower and not dry)
def main():
    assert not (E/'result.json').exists(),'Preserve earlier pilot result'
    baseline=a['pieces'];baseline_geo=geometric(baseline);control=physical_samples(baseline)
    results={};chosen={}
    for name,scales in [('A',[4.]),('B',[3.2,3.6,4.])]:
        states,search_meta=search(scales)
        evaluated=[]
        for state in states:
            pcs=convert(state[4]);geo=geometric(pcs)
            # Missing support dominates selection; then double-layer area.
            loss=geo['wet_faces']['uncovered_area_m2']+geo['corridor_gap_m2']+100000*max(0,geo['multi_share']-.01)
            evaluated.append((loss,pcs,geo,state))
        assert evaluated,'No completed chain'
        loss,pcs,geo,state=min(evaluated,key=lambda r:r[0])
        rows=physical_samples(pcs);phys=screen(rows,control)
        results[name]=dict(search=search_meta,geometry=geo,physical=phys,pass_offline=geo['geometry_pass'] and phys['pass_local'])
        chosen[name]=pcs
        (E/(name+'-poses.json')).write_text(json.dumps(pcs,indent=2)+'\n',encoding='utf-8')
        (E/(name+'-samples.json')).write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
        print(name,json.dumps(results[name]),flush=True)
    (E/'baseline-samples.json').write_text(json.dumps(control,indent=2)+'\n',encoding='utf-8')
    # Closed counterexamples exercise actual consumer predicates.
    ref=chosen['A']
    missing=geometric(ref[:len(ref)//2])
    duplicate=geometric(ref+[ref[len(ref)//2]])
    neg=dict(removed_piece_rejected=not missing['geometry_pass'],duplicated_piece_rejected=duplicate['multi_share']>.01,
             changed_native_hash_rejected=sha(ewm.DZ/(ref[0]['type']+'.p3d'))!=('0'*64))
    assert all(neg.values()),neg
    fig,axes=plt.subplots(1,3,figsize=(13,6),sharex=True,sharey=True)
    for ax,title,pcs in zip(axes,['Control actual','A: escala 4','B: escala variable'],[baseline,chosen['A'],chosen['B']]):
        geoms=polys(pcs)
        for k,g in enumerate(geoms):
            for p in ([g] if g.geom_type=='Polygon' else g.geoms):
                x,y=p.exterior.xy;ax.fill(x,y,alpha=.24);ax.plot(x,y,lw=.65)
        for g in wet_union.geoms if hasattr(wet_union,'geoms') else [wet_union]:
            x,y=g.exterior.xy;ax.plot(x,y,c='k',lw=.5)
        ax.plot(a['x'],a['z'],'--',c='k',lw=.9);ax.set_title(title);ax.set_aspect('equal');ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(E/'footprints.png',dpi=160);plt.close(fig)
    out=dict(status='OFFLINE_VARIANTS_EVALUATED',baseline=baseline_geo,variants=results,negative_controls=neg,
             terrain_sha256=sha(TERRAIN),library_sha256=sha(LIB),axes_sha256=sha(FIT/'axes.json'),
             limits=['Finite placement search, not a proof that all possible curve layouts are infeasible.',
                     '510 samples are a local depth screen, not continuous face-depth certification.',
                     'Projected footprints plus empirical native query model; engine/visual/boat gates remain required.',
                     'No changes to terrain or deployed packages.'])
    (E/'result.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print('Saved',E/'result.json',flush=True)

if __name__ == "__main__":
    main()
