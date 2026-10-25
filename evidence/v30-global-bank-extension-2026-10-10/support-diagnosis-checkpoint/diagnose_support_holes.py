#!/usr/bin/env python
"""One-pass, read-only EV93 support-footprint diagnosis for attempt-04."""
from __future__ import annotations
import hashlib, importlib.util, json, sys, time
from collections import defaultdict
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

G=Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010')
OUT=G/'support-hole-diagnosis'
CONSUMER=G/'consumer-global/verify_layer.py'
REPORT=G/'consumer-global/runs/attempt-04/ev93-review.json'
PREPARED=G/'fairing-layer1/prepared.json'
RECEIPT=G/'fairing-layer1/authoring.json'
EXPECTED_REPORT='ed9a071d359dc446b5146a255c3ab9f15481c92e24c2169b6da47dd4ad27c0ec'
LIMIT=1e-7
EPS={'physical':1e-5,'visible':2e-5}

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''): h.update(b)
    return h.hexdigest()

def load_module(name,path):
    s=importlib.util.spec_from_file_location(name,path)
    if s is None or s.loader is None: raise ImportError(path)
    m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m

def direct_support_cells(ev87,cv,selected_cells,base,candidate,p,f,ev87mod):
    """Enumerate ODOL faces for <=3 cells, independently of EV93 face shards."""
    if not selected_cells:return {}
    WRP=ev87.B/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
    _,objects,models,_=ev87.compiled_objects(WRP,ev87.W,selected_cells,ev87.MODEL_DIR,ev87.BOUNDS_JSON)
    out={cell:{k:{'B':[],'candidate':[]} for k in ('physical','visible')} for cell in selected_cells}
    for obj,mat,_bounds in objects:
        basename=obj['name'].replace('\\','/').split('/')[-1]
        model=models[basename]
        tx,ty,tz=map(float,(mat[9],mat[10],mat[11]))
        for kind,res in (('physical',float(np.float32(3e15))),('visible',1.0)):
            lods=[lod for lod in model.lods if lod.resolution==res]
            if len(lods)!=1: raise AssertionError(f'nonunique direct {kind} LOD: {basename}')
            lod=lods[0]
            verts=np.asarray([(v.x+tx,v.y+ty,v.z+tz) for v in lod.vertices],dtype=np.float64)
            for face in lod.faces:
                ids=np.asarray(face.vertex_indices,dtype=np.int64)
                if len(ids)!=3: raise AssertionError('ODOL face not triangular')
                xyz=verts[ids];xy=xyz[:,(0,2)]
                face_poly=Polygon(xy)
                if face_poly.is_empty or face_poly.area<=0: continue
                coeff=ev87.affine_coeff(xy,xyz[:,1])
                for r,c in selected_cells:
                    cellxy=ev87.cell_xy(r,c)
                    for ti,tri in enumerate(ev87.TRIS):
                        ix=np.asarray(tri,dtype=np.int64)
                        piece=face_poly.intersection(Polygon(cellxy[ix]))
                        if piece.is_empty or piece.area<=0: continue
                        _,_,target=cv.cell_tri_target(r,c,kind,tri,p,f)
                        if target is None: continue
                        match=cv.clip_affine_band(piece,coeff-target,EPS[kind])
                        if match.is_empty: continue
                        for side,h in (('B',base),('candidate',candidate)):
                            # Support itself is candidate-height independent in C; retain
                            # both keys to make direct and indexed hole calculations explicit.
                            out[(r,c)][kind][side].append(match)
    return {cell:{kind:{side:(unary_union(polys) if polys else Polygon())
                        for side,polys in sides.items()} for kind,sides in kinds.items()}
            for cell,kinds in out.items()}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    started=time.monotonic()
    def progress(stage,**kw):
        row={'stage':stage,'elapsed_seconds':round(time.monotonic()-started,3),**kw}
        with (OUT/'progress.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row)+'\n')
        print(json.dumps(row),flush=True)
    if sha(REPORT)!=EXPECTED_REPORT: raise AssertionError('attempt-04 report hash changed')
    report=json.loads(REPORT.read_text(encoding='utf-8'))
    if report['status']!='FAIL_INCREMENTAL_NONREGRESSION': raise AssertionError('unexpected report status')
    progress('report_anchored',report_sha256=sha(REPORT),failed=[k for k,v in report['gates'].items() if not v])
    vl=load_module('ev93_support_diag_consumer',CONSUMER)
    ev,ev91,ev87,cv,shape,ev92,index_module=vl.load_helpers()
    bundle=ev.checked_sources();base_npz=bundle['B'];base=np.asarray(base_npz['heights'],dtype=np.float32)
    prepared,receipt,entries,ledger,ledger_path=vl.verify_prepared(PREPARED,RECEIPT,base)
    details=vl.validate_detail_hashes(prepared,entries)
    candidate,changed,accepted,owner=vl.reconstruct_candidate(base_npz,receipt,entries,ledger,details,RECEIPT.parent)
    cells=vl.affected_cells(ev87,changed)
    if len(cells)!=int(report['information']['changed_support_cells']): raise AssertionError('affected-cell count differs from attempt-04')
    qmeta={int(e['queue_id']):{'seed_id':int(e['seed_id']),'center_rc':e['center_rc'],
          'window_rc':e['window_rc'],'core_rc':e['core_rc']} for e in entries}
    cell_qids=defaultdict(set)
    for (r,c),qid in owner.items():
        for cr,cc in ((r-1,c-1),(r-1,c),(r,c-1),(r,c)):
            if (cr,cc) in cells: cell_qids[(cr,cc)].add(int(qid))
    p,f=bundle['P'],bundle['F']
    # Build exact support cells from the indexed ODOL faces, with the same
    # triangle intersections and affine-band predicate as C; no residual gates.
    index=index_module.FaceRangeIndex(vl.INDEX_RUN)
    all_faces=index.query_window(0,ev87.N-2,0,ev87.N-2)
    bitmap=np.zeros((ev87.N-1,ev87.N-1),dtype=bool)
    rc=np.asarray(sorted(cells),dtype=np.int32);bitmap[rc[:,0],rc[:,1]]=True
    selected=vl.rectangle_any(bitmap,all_faces['cell_range_rc'])&(all_faces['degenerate']==0)
    faces={k:v[selected] for k,v in all_faces.items()}
    support={k:{cell:[] for cell in cells} for k in ('physical','visible')}
    labels={0:'physical',1:'visible'}
    progress('index_loaded',cells=len(cells),index_faces=len(all_faces['kind']),candidate_faces=len(faces['kind']))
    for i in range(len(faces['kind'])):
        kind=labels[int(faces['kind'][i])]
        xyz=faces['xyz'][i];face_xy=xyz[:,(0,2)];face_poly=Polygon(face_xy)
        if face_poly.is_empty or face_poly.area<=0: continue
        coeff=np.asarray(faces['plane_y_xz'][i],dtype=np.float64)
        r0,r1,c0,c1=map(int,faces['cell_range_rc'][i])
        for r in range(max(0,r0),min(ev87.N-2,r1)+1):
            for c in range(max(0,c0),min(ev87.N-2,c1)+1):
                if (r,c) not in cells: continue
                xy=ev87.cell_xy(r,c)
                for tri in ev87.TRIS:
                    ids=np.asarray(tri,dtype=np.int64)
                    piece=face_poly.intersection(Polygon(xy[ids]))
                    if piece.is_empty or piece.area<=0: continue
                    _,_,target=cv.cell_tri_target(r,c,kind,tri,p,f)
                    if target is None: continue
                    match=cv.clip_affine_band(piece,coeff-target,EPS[kind])
                    if not match.is_empty:support[kind][(r,c)].append(match)
        if (i+1)%100000==0: progress('index_scan',faces_done=i+1)
    support={kind:{cell:(unary_union(polys) if polys else Polygon()) for cell,polys in bycell.items()}
             for kind,bycell in support.items()}
    design={side:{kind:cv.make_design(h,p,f,cells,kind) for kind in ('physical','visible')}
            for side,h in (('B',base),('candidate',candidate))}
    rows=[];totals={k:{s:0.0 for s in ('B','candidate')} for k in ('physical','visible')}
    maxima={k:{s:0.0 for s in ('B','candidate')} for k in ('physical','visible')}
    for kind in ('physical','visible'):
        for cell in sorted(cells):
            for side,h in (('B',base),('candidate',candidate)):
                d=design[side][kind][cell];sp=support[kind][cell]
                if kind=='visible':
                    r,c=cell;xy=ev87.cell_xy(r,c);known=[]
                    for tri in cv.TRIS:
                        ids=np.asarray(tri,dtype=np.int64)
                        if np.isfinite(f[r,c,ids]).all():known.append(Polygon(xy[ids]))
                    domain=unary_union(known) if known else Polygon()
                    d=d.intersection(domain);sp=sp.intersection(domain)
                area=float(d.difference(sp).area)
                totals[kind][side]+=area;maxima[kind][side]=max(maxima[kind][side],area)
                if area>LIMIT:
                    qids=sorted(cell_qids.get(cell,()))
                    rows.append({'kind':kind,'side':side,'cell_rc':list(cell),'hole_m2':area,
                                 'qid_originals':[{'queue_id':q,'seed_id':qmeta[q]['seed_id'],
                                   'center_rc':qmeta[q]['center_rc'],'window_rc':qmeta[q]['window_rc'],
                                   'core_rc':qmeta[q]['core_rc']} for q in qids]})
    rows.sort(key=lambda x:x['hole_m2'],reverse=True)
    expected=report['information']['compiled_coverage']['metrics']
    for kind in ('physical','visible'):
        for side in ('B','candidate'):
            want=float(expected[kind]['support_hole_total_m2'][side]);wantmax=float(expected[kind]['support_hole_max_cell_m2'][side])
            if abs(totals[kind][side]-want)>2e-10 or abs(maxima[kind][side]-wantmax)>2e-10:
                raise AssertionError(f'{kind}/{side} footprint does not reconcile to C: got {totals[kind][side]}/{maxima[kind][side]}, expected {want}/{wantmax}')
    progress('footprint_complete',flagged_cells=len(rows),physical_total=totals['physical'],visible_total=totals['visible'])
    # At most three cell centers are checked by fresh ODOL enumeration.
    chosen=[]
    for row in rows:
        cell=tuple(row['cell_rc'])
        if cell not in chosen:chosen.append(cell)
        if len(chosen)==3:break
    direct=direct_support_cells(ev87,cv,chosen,base,candidate,p,f,ev87)
    direct_rows=[]
    for cell in chosen:
        for kind in ('physical','visible'):
            d=design['candidate'][kind][cell]
            if kind=='visible':
                r,c=cell;xy=ev87.cell_xy(r,c);known=[]
                for tri in cv.TRIS:
                    ids=np.asarray(tri,dtype=np.int64)
                    if np.isfinite(f[r,c,ids]).all():known.append(Polygon(xy[ids]))
                domain=unary_union(known) if known else Polygon();d=d.intersection(domain)
            ind=support[kind][cell]
            dr=direct[cell][kind]['candidate']
            hole_i=float(d.difference(ind).area);hole_d=float(d.difference(dr).area)
            diff=float(ind.symmetric_difference(dr).area)
            direct_rows.append({'cell_rc':list(cell),'kind':kind,'indexed_support_area_m2':float(ind.area),
                'direct_odol_support_area_m2':float(dr.area),'indexed_vs_direct_symdiff_m2':diff,
                'candidate_hole_indexed_m2':hole_i,'candidate_hole_direct_odol_m2':hole_d,
                'independent_reader_reproduces_hole':abs(hole_i-hole_d)<=2e-9})
    index.reverify()
    output={'status':'SUPPORT_FOOTPRINT_COMPLETE','scope':'One support-footprint pass for attempt-04; no height/residual/global gates. Direct ODOL support for at most three largest cells.',
      'source_hashes':{'consumer':sha(CONSUMER),'attempt04_report':sha(REPORT),'prepared':sha(PREPARED),'receipt':sha(RECEIPT),
        'index_manifest':sha(vl.INDEX_MANIFEST),'index_builder':sha(vl.INDEX_SOURCE)},
      'cells_scanned':len(cells),'changed_vertices':int(len(changed)),'accepted_windows':len(accepted),
      'threshold_m2':LIMIT,'totals_m2':totals,'maxima_m2':maxima,'flagged_cell_rows':len(rows),
      'flagged_cells':rows,'top_three_direct_odol':direct_rows,
      'direct_source':'verify_ev87.compiled_objects + actual pinned ODOL physical/visible LOD faces, independently enumerated for only selected cells',
      'index_reverify':'PASS'}
    (OUT/'support-hole-report.json').write_text(json.dumps(output,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    progress('finished',output=str(OUT/'support-hole-report.json'),direct_cells=len(chosen))
    print(json.dumps({'status':output['status'],'flagged_cell_rows':len(rows),'top':rows[:4],
      'direct':direct_rows,'output':str(OUT/'support-hole-report.json')},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
