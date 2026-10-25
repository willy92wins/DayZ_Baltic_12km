"""Prepare a terrain-only main-road grading candidate with reserved water crossings.

Shared-node chains are resampled at <=3m. A graph profile constrains maximum
longitudinal grade, while a supported flat transverse band avoids 6m-grid ruts.
Independent triangle sampling is required before import or a smooth-road claim.
"""
from collections import defaultdict
import heapq
import hashlib
import json
from pathlib import Path
import sys
import math
import numpy as np
import rasterio
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix,diags
from scipy.sparse.linalg import spsolve
from scipy.ndimage import distance_transform_edt
from shapely.geometry import shape,LineString,Point
from shapely.ops import unary_union
from rasterio.features import rasterize
from affine import Affine

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from geo_common import save_json
from waterway_common import sample
EV=ROOT/'evidence/regional-foundation-v1'
OUT=ROOT/'tests/regional_foundation_roads_v1'
TX=Affine(6,0,-3,0,-6,12285)


def envelope(values,adj,grade):
    """Minimum Lipschitz majorant on an undirected length-weighted graph."""
    result=values.copy()
    queue=[(-float(v),i) for i,v in enumerate(values)]
    heapq.heapify(queue)
    while queue:
        neg,i=heapq.heappop(queue)
        value=-neg
        if value < result[i]-1e-10:continue
        for j,length in adj[i]:
            proposal=value-grade*length
            if proposal>result[j]+1e-10:
                result[j]=proposal
                heapq.heappush(queue,(-proposal,j))
    return result


def main():
    assert not OUT.exists(),'Fresh candidate required'
    basepath=ROOT/'tests/regional_outline_v3/baltic_regional_outline_v3.asc'
    assert hashlib.sha256(basepath.read_bytes()).hexdigest()=='3e2f6a9643ba4a8c58a86534c75de6033b7dbdf7a3de5d09a5ea46ff66680ac6'
    with rasterio.open(basepath) as ds:base=ds.read(1)
    src=json.loads((EV/'road-network-routes.json').read_text())
    source_nodes={int(k):v for k,v in src['nodes'].items()}
    source_edges=json.loads((EV/'road-network-game.json').read_text())['features']
    connections=defaultdict(list)
    for f in source_edges:
        a,b=f['properties']['node_a'],f['properties']['node_b']
        connections[a].append(b);connections[b].append(a)
    terminals={n for n,neighbors in connections.items() if len(neighbors)!=2}
    terminals.update(a['node_id'] for a in src['anchors'])
    walked=set(); chains=[]
    # A ring lacking a junction still gets an explicit seed.
    starts=sorted(terminals)+sorted(set(connections)-terminals)
    for a in starts:
        for b in connections[a]:
            key=tuple(sorted((a,b)))
            if key in walked:continue
            path=[a,b];walked.add(key)
            while path[-1] not in terminals and path[-1]!=path[0]:
                nexts=[n for n in connections[path[-1]] if n!=path[-2]]
                if len(nexts)!=1:raise ValueError('Unexpected degree in chain')
                n=nexts[0];key=tuple(sorted((path[-1],n)))
                if key in walked:break
                walked.add(key);path.append(n)
            chains.append(path)
    assert len(walked)==len(source_edges)
    coords=[]; endpoints={};edges=[];chain_indices=[]
    def endpoint(node):
        if node not in endpoints:
            endpoints[node]=len(coords);coords.append(source_nodes[node])
        return endpoints[node]
    for chain in chains:
        line=LineString([source_nodes[n] for n in chain])
        if line.length<.001:raise ValueError('Degenerate chain')
        stations=np.linspace(0,line.length,max(2,int(math.ceil(line.length/3))+1))
        indices=[endpoint(chain[0])]
        for distance in stations[1:-1]:
            p=line.interpolate(float(distance));indices.append(len(coords));coords.append([p.x,p.y])
        indices.append(endpoint(chain[-1]))
        for a,b in zip(indices,indices[1:]):
            length=math.dist(coords[a],coords[b])
            if length<1e-5:raise ValueError('Degenerate resampled edge')
            edges.append((a,b,length))
        chain_indices.append(indices)
    xy=np.array(coords)
    source_y=sample(base,xy[:,0]+200000,xy[:,1]).astype(float)
    n=len(xy);adj=[[] for _ in range(n)];rows=[];cols=[];weights=[];mass=np.zeros(n)
    for a,b,length in edges:
        adj[a].append((b,length));adj[b].append((a,length))
        rows.extend([a,b]);cols.extend([b,a]);weights.extend([1/length,1/length]);mass[a]+=length/2;mass[b]+=length/2
    W=coo_matrix((weights,(rows,cols)),shape=(n,n)).tocsr()
    L=diags(np.asarray(W.sum(axis=1)).ravel())-W
    M=diags(mass)
    # H2 fairing suppresses vertical kinks, using physical segment lengths.
    A=M+(35.**4)*(L@diags(1/mass)@L)
    smooth=spsolve(A,mass*source_y)
    # Independent minimum-grade envelopes bound the result on every graph edge.
    upper=envelope(smooth,adj,.055)
    lower=-envelope(-smooth,adj,.055)
    profile=(upper+lower)/2
    # Reserve every reference water crossing. Never make a terrain causeway.
    reference=np.load(ROOT/'tests/regional_outline_v3/reference.npz')
    water=reference['water'].astype(bool)
    wet_distance=distance_transform_edt(~water)*6
    cols_i=np.clip(np.rint(xy[:,0]/6).astype(int),0,2047)
    rows_i=np.clip(np.rint((12282-xy[:,1])/6).astype(int),0,2047)
    crossing=water[rows_i,cols_i]
    # Design elevation until the hydrology layer supplies exact water levels.
    minimum=np.full(n,-1000.)
    minimum[crossing]=np.maximum(1.25,source_y[crossing]+1.25)+8.
    bridge_envelope=envelope(minimum,adj,.04)
    profile=np.maximum(profile,bridge_envelope)
    profile=np.maximum(profile,1.4)
    grades=np.array([abs(profile[a]-profile[b])/length for a,b,length in edges])
    if grades.max()>.055001:raise ValueError('Profile grade constraint failed')
    print(f'{len(chains)} chains, {n} profile samples; max grade {grades.max():.6f}',flush=True)
    # Rasterize a support corridor, then interpolate the nearest exact profile segment.
    lines=[LineString(xy[ids]) for ids in chain_indices]
    corridor=rasterize([(g.buffer(34),1) for g in lines],out_shape=base.shape,transform=TX,dtype='uint8').astype(bool)
    rr,cc=np.where(corridor)
    query=np.column_stack([cc*6.,12282-rr*6.])
    edge_nodes=np.array([(a,b) for a,b,_ in edges])
    pa=xy[edge_nodes[:,0]];pb=xy[edge_nodes[:,1]];dv=pb-pa;length2=np.einsum('ij,ij->i',dv,dv)
    tree=cKDTree((pa+pb)/2)
    _,nearest=tree.query(query,k=8)
    va=pa[nearest];delta=dv[nearest]
    t=np.clip(np.einsum('ijk,ijk->ij',query[:,None,:]-va,delta)/length2[nearest],0,1)
    projected=va+t[:,:,None]*delta
    dist=np.linalg.norm(query[:,None,:]-projected,axis=2)
    j=dist.argmin(axis=1);choice=nearest[np.arange(len(query)),j]
    d=dist[np.arange(len(query)),j];fraction=t[np.arange(len(query)),j]
    target=profile[edge_nodes[choice,0]]*(1-fraction)+profile[edge_nodes[choice,1]]*fraction
    # 4m running half-width plus a full cell diagonal of interpolation support.
    blend=np.clip((34-d)/(34-(4+6*np.sqrt(2))),0,1)
    blend=blend*blend*(3-2*blend)
    # Preserve the validated Narva pilot and all water/shore supports.
    fit=json.loads((ROOT/'evidence/narva/evidence/narva-fit.json').read_text())
    centre=np.array(fit['bridge_centre_tb'])-[200000,0]
    radial=np.linalg.norm(query-centre,axis=1)
    blend*=np.clip((radial-400)/60,0,1)
    blend*=np.clip((wet_distance[rr,cc]-18)/24,0,1)
    candidate=base.copy()
    candidate[rr,cc]=(base[rr,cc]*(1-blend)+target*blend).astype(np.float32)
    changed=candidate!=base
    assert not np.any(changed&water)
    OUT.mkdir(parents=True)
    asc=OUT/'baltic_roads_pre_hydrology_v1.asc'
    with asc.open('w',encoding='ascii',newline='\n') as handle:
        handle.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n')
        np.savetxt(handle,candidate,fmt='%.9f')
    with rasterio.open(asc) as ds:assert np.array_equal(ds.read(1),candidate)
    np.savez_compressed(OUT/'reference.npz',base=base,candidate=candidate,changed=changed,corridor=corridor,
                        xy=xy,profile=profile,source_y=source_y,edges=np.array(edges),crossing=crossing)
    save_json(EV/'road-grade-design.json',{'status':'CANDIDATE_NOT_IMPORTED_OR_ACCEPTED','chains':len(chains),'profile_samples':n,
        'length_m':sum(length for _,_,length in edges),'max_design_grade':float(grades.max()),
        'changed_vertices':int(changed.sum()),'water_vertices_changed':int((changed&water).sum()),
        'max_cut_m':float((base-candidate).max()),'max_fill_m':float((candidate-base).max()),
        'candidate_sha256':hashlib.sha256(asc.read_bytes()).hexdigest(),
        'limits':['Bridge profiles are reservations; exact deck levels depend on final water and chosen structure.',
                  'Reference water and Narva pilot excluded; approach joins require combined-layer validation.',
                  'Graph grades do not prove native triangle smoothness or vehicle behaviour.']})
    save_json(EV/'road-grade-chains.json',{'chains':chain_indices})
    print(json.dumps({'candidate':str(asc),'changed_vertices':int(changed.sum())}))


if __name__=='__main__':main()
