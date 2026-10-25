"""Read-only actual contour graph and movable support census for R1/R2."""
from pathlib import Path
import hashlib,json,sys
from collections import defaultdict
import numpy as np
from scipy import ndimage

W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-native-turn-optimizer-20261009')
B9=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008')
B10=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
B12=Path('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def graph(h,field,cells):
    nodes=[];keys={};segments=[];zero=[]
    def edge(ids,water):
        ids=np.asarray(ids);water=np.asarray(water);order=np.argsort(ids);ids=ids[order];water=water[order]
        delta=h.ravel()[ids]-water
        if np.any(delta==0):
            k=int(np.flatnonzero(delta==0)[0]);key=('vertex',int(ids[k]),float(water[k]));zero.append(int(ids[k]))
        else:key=('edge',int(ids[0]),int(ids[1]),float(water[0]),float(water[1]))
        if key not in keys:
            index=len(nodes);keys[key]=index
            rr,cc=np.divmod(ids,2048);xz=np.c_[cc*6,12282-rr*6]
            nodes.append(dict(ids=ids.tolist(),water=water.tolist(),xz=xz.tolist(),key=key))
        return keys[key]
    for r,c in cells:
        f=field[r,c];ids=np.array([r*2048+c,r*2048+c+1,(r+1)*2048+c,(r+1)*2048+c+1])
        d=h.ravel()[ids]-f
        for corners in ((0,1,3),(0,2,3)):
            crossings=[]
            for ia,ib in ((0,1),(1,2),(2,0)):
                a,b=corners[ia],corners[ib]
                if (d[a]<=0<d[b]) or (d[b]<=0<d[a]):crossings.append(edge(ids[[a,b]],f[[a,b]]))
            if len(crossings)==2 and crossings[0]!=crossings[1]:segments.append(crossings)
    adjacency=defaultdict(set)
    for a,b in segments:adjacency[a].add(b);adjacency[b].add(a)
    branches={str(k):len(v) for k,v in adjacency.items() if len(v)>2}
    chains=[];seen=set()
    for initial in list(k for k,v in adjacency.items() if len(v)==1)+list(adjacency):
        for neighbor in adjacency[initial]:
            if tuple(sorted((initial,neighbor))) in seen:continue
            chain=[initial];previous,current=initial,neighbor
            while True:
                seen.add(tuple(sorted((previous,current))));chain.append(current)
                nexts=[v for v in adjacency[current] if v!=previous and tuple(sorted((current,v))) not in seen]
                if not nexts:break
                if len(nexts)>1:break
                previous,current=current,nexts[0]
            chains.append(chain)
    return dict(nodes=nodes,segments=segments,chains=chains,branch_nodes=branches,exact_zero_support=sorted(set(zero)))

def positions(h,nodes):
    ids=np.array([n['ids'] for n in nodes]);water=np.array([n['water'] for n in nodes]);xy=np.array([n['xz'] for n in nodes])
    depth=h.ravel()[ids]-water;t=depth[:,0]/(depth[:,0]-depth[:,1])
    return xy[:,0]+t[:,None]*(xy[:,1]-xy[:,0])

def stats(points,chains):
    values=[];length=0.;used=0
    for chain in chains:
        pts=points[chain];dist=np.r_[0,np.cumsum(np.linalg.norm(np.diff(pts,axis=0),axis=1))]
        if dist[-1]<=24:continue
        used+=1;length+=float(dist[-1]);s=np.arange(0,dist[-1],2)
        sample=np.c_[np.interp(s,dist,pts[:,0]),np.interp(s,dist,pts[:,1])]
        if len(sample)<10:continue
        a=sample[3:-3]-sample[:-6];b=sample[6:]-sample[3:-3]
        values.extend(np.degrees(np.arccos(np.clip(np.sum(a*b,axis=1)/np.maximum(np.linalg.norm(a,axis=1)*np.linalg.norm(b,axis=1),1e-12),-1,1))).tolist())
    assert values,'No contour observations'
    return dict(chains=used,length_m=length,samples=len(values),p90_degrees=float(np.percentile(values,90)),
                mean_degrees=float(np.mean(values)),over30_share=float(np.mean(np.array(values)>30)),max_degrees=float(max(values)))

def main():
    B.mkdir(parents=True,exist_ok=True)
    terrain=B10/'measured-bank-bed-r2/terrain.npz';assert sha(terrain)=='e7daa6c62cde457b666507ec7eae7e6d16015ad714028585fdb352ace678e52c'
    fieldpath=B12/'preserved-field.npy';assert sha(fieldpath)=='7a5d0900533670a1e533965b36a6dcf28be2715f96f94ccbfbe6a846bdf98e37'
    h=np.load(terrain)['heights'].astype(float);field=np.load(fieldpath);plane=np.load(B10/'frozen-field-reference/plane.npy')
    masks=np.load(B9/'candidate-a/masks.npz');fixed=masks['fixed'].copy()
    references=[W/'evidence/v30-global-water-risk-2026-10-09/halo-r2-consumers-reference.json',
                W/'evidence/v30-global-water-risk-2026-10-09/scalar-r2-temporal-reference.json',
                W/'evidence/v30-water-visual-fix-2026-10-08/stitch-probe-reference.json']
    controls=np.zeros_like(fixed)
    for path in references:
        for point in json.loads(path.read_text())['points']:
            r=int(np.floor((12282-point['z'])/6));c=int(np.floor(point['x']/6));controls[max(0,r):min(2048,r+2),max(0,c):min(2048,c+2)]=True
    fixed|=controls
    axes=json.loads(Path('E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2/axes.json').read_text());summary={}
    for reach in ('R1','R2'):
        rc=np.array(axes[reach]['removed_cells']);r0,c0=np.maximum(rc.min(0)-3,0);r1,c1=np.minimum(rc.max(0)+4,2047)
        cells=[(r,c) for r in range(r0,r1) for c in range(c0,c1) if np.isfinite(plane[r,c])]
        g=graph(h,field,cells);p=positions(h,g['nodes']);support=np.unique(np.array([n['ids'] for n in g['nodes']]).ravel())
        # Endpoint and exact-zero support must stay fixed in a shape-only pilot.
        localfixed=fixed.copy();boundary=[]
        for chain in g['chains']:
            if chain[0]!=chain[-1]:boundary.extend(g['nodes'][j]['ids'] for j in (chain[0],chain[-1]))
        if boundary:localfixed.ravel()[np.unique(boundary)]=True
        localfixed.ravel()[g['exact_zero_support']]=True
        movable=support[~localfixed.ravel()[support]]
        counts={k:int(v) for k,v in zip(['contour_support','movable_contour_support','fixed_contour_support'],[len(support),len(movable),np.count_nonzero(localfixed.ravel()[support])])}
        result=dict(reach=reach,box_cells=[int(r0),int(c0),int(r1),int(c1)],stats=stats(p,g['chains']),counts=counts,
                    nodes=len(g['nodes']),segments=len(g['segments']),branches=g['branch_nodes'],zero_support=len(g['exact_zero_support']))
        summary[reach]=result
        (B/(reach+'-graph.json')).write_text(json.dumps(dict(g,discovery=result))+'\n')
        np.savez_compressed(B/(reach+'-constraints.npz'),fixed=localfixed,movable=movable,controls=controls)
    report=dict(status='NATIVE_GRAPH_DISCOVERY_NOT_TERRAIN_CHANGE',terrain_sha256=sha(terrain),field_sha256=sha(fieldpath),reaches=summary,
                protected_control_vertices=int(controls.sum()),input_control_files={str(p):sha(p) for p in references},
                constraints='Candidate-A engineering/border/sea policy, current corridors, historical water controls, graph endpoints and exact-zero support.',
                limits=['Movable supports do not prove that a smoother feasible terrain exists. No optimizer or map change has run.'])
    (B/'discovery.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
