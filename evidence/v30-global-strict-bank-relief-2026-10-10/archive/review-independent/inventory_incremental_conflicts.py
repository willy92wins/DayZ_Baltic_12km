"""Read-only complete inventory for deterministic rejection; never an acceptance gate."""
import hashlib, importlib.util, json, sys, time
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
EV=HERE.parent
ROOT=EV.parent
OUT=HERE/'incremental-conflict-inventory.json'
SOURCE_REPORT=HERE/'coverage-contract-review.json'
SOURCE_SHA='079557bc0419bad0ed35c1472e34fad7e4e27089229c26403d95a7dd498fb2b9'
CONSUMER=HERE/'verify_coverage_contract.py'
CONSUMER_SHA='214f0eddda08d84ce18c921fcdbe01298f608c9a5c19b7e5246bb9e71df5dc2b'

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4194304),b''):h.update(b)
    return h.hexdigest()

def save(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def residual_rows(m,h,p,f,cells,kind,exposed,design):
    rows=[]
    for r,c in sorted(cells):
        d=design[(r,c)];actual=exposed[(r,c)]
        if kind=='visible':
            known=[];xy=m.cell_xy(r,c)
            for tri in m.TRIS:
                _,_,tc=m.cell_tri_target(r,c,kind,tri,p,f)
                if tc is not None:known.append(Polygon(xy[list(tri)]))
            domain=unary_union(known) if known else Polygon()
            d=d.intersection(domain);actual=actual.intersection(domain)
        band=m.band_polygon(r,c,h,p,f,kind,m.EPS[kind])
        missing=d.difference(actual);growth=actual.difference(d)
        rows.append({'cell':[r,c],'missing_m2':float(missing.area),'growth_m2':float(growth.area),
                     'missing_outside_band_m2':float(missing.difference(band).area),
                     'growth_outside_band_m2':float(growth.difference(band).area)})
    return rows

def main():
    start=time.monotonic()
    assert not OUT.exists(),'Preserve prior inventory; do not overwrite'
    assert sha(SOURCE_REPORT)==SOURCE_SHA and sha(CONSUMER)==CONSUMER_SHA
    report=json.loads(SOURCE_REPORT.read_text(encoding='utf-8'))
    assert report['status']=='FAIL_EV87_REPRESENTATION_CONSUMER'
    inputs=dict(report['inputs'])
    for path,digest in inputs.items():assert sha(path)==digest,('source drift',path)
    inputs[str(Path(__file__))]=sha(__file__);inputs[str(SOURCE_REPORT)]=SOURCE_SHA
    spec=importlib.util.spec_from_file_location('frozen_coverage',CONSUMER)
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
    assert sha(HERE/'verify_ev87.py')==m.HELPER_SHA
    m.ev=m.load_ev87(HERE/'verify_ev87.py');ev=m.ev
    raw=json.loads(m.RAW.read_text(encoding='utf-8'))
    cells={tuple(x['cell']) for k in ('physical','visible') for x in raw['information']['surface_coverage']['by_surface'][k]['cells']}
    assert len(cells)==41008
    hb=ev.load_npz(ROOT/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz')['heights'].astype(np.float64)
    hh=ev.load_npz(EV/'candidate-terrain.npz')['heights'].astype(np.float64)
    p=np.load(ROOT/'v30-narva-dry-bank-relief-20261010/candidate/plane.npy')
    f=np.load(ROOT/'v30-narva-dry-bank-relief-20261010/candidate/visible-field.npy')
    unknown,_=m.classify_unknown_f(hb,hh,f)
    wrp=ROOT/'v30-mixed-bank-incremental-fixed-20261010/package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
    print('Scanning compiled faces and all affected/frontier cells',flush=True)
    exp,support,meta,bad,ustatic=m.exposed_pair_and_support(hb,hh,p,f,cells|unknown['changed_cells'],wrp,m.W,m.MODEL_DIR,m.BOUNDS,unknown)
    save(HERE/'incremental-conflict-face-checkpoint.json',{'status':'INVENTORY_IN_PROGRESS','height_violations_untruncated':bad,'model_hashes':meta['model_hashes']})
    metrics={};conflicts={};hole_cells=set()
    for kind in ('physical','visible'):
        metrics[kind]={}
        for label,h in (('B',hb),('candidate',hh)):
            design=m.make_design(h,p,f,cells,kind)
            rows=residual_rows(m,h,p,f,cells,kind,exp[label][kind],design)
            holes=[]
            for cell in sorted(cells):
                hole=design[cell].difference(support[kind][cell]);area=float(hole.area)
                if area>1e-12:holes.append({'cell':list(cell),'area_m2':area})
                if label=='candidate' and area>1e-10:hole_cells.add(cell)
            metrics[kind][label]={'residual_cells_untruncated':rows,'support_holes_untruncated':holes}
            if kind=='physical':
                for row in rows:
                    if max(row['missing_outside_band_m2'],row['growth_outside_band_m2'])>1e-12:
                        conflicts.setdefault(tuple(row['cell']),set()).add(label+'_physical_outside_band')
    for label,rows in bad.items():
        for row in rows:
            conflicts.setdefault(tuple(row['cell']),set()).add(label+'_'+row['kind']+'_above_field')
    for cell in hole_cells:conflicts.setdefault(cell,set()).add('nominal_support_hole')
    ledger=EV/'queue-ledger.jsonl';inputs[str(ledger)]=sha(ledger)
    events=[json.loads(s) for s in ledger.read_text(encoding='utf-8').splitlines()]
    events=[e for e in events if e.get('event')=='patch' and e['state']=='accepted']
    reject={}
    for e in events:
        hit=[]
        for r,c in e['mutable_nodes']:
            for dr in (-1,0):
                for dc in (-1,0):
                    cell=(r+dr,c+dc)
                    if cell in conflicts:hit.append(cell)
        if hit:reject[e['queue_id']]={'center':e['center'],'conflict_cells':[list(c) for c in sorted(set(hit))]}
    for path,digest in inputs.items():assert sha(path)==digest,('end drift',path)
    for name,digest in meta['model_hashes'].items():assert sha(m.MODEL_DIR/name)==digest
    out={'status':'COMPLETE_READ_ONLY_CONFLICT_INVENTORY','acceptance':False,'inputs':inputs,'seconds':time.monotonic()-start,
         'scan_cells':len(cells),'model_hashes':meta['model_hashes'],'height_violations_untruncated':bad,'metrics':metrics,
         'conflict_cells':[{'cell':list(cell),'reasons':sorted(reasons)} for cell,reasons in sorted(conflicts.items())],
         'suggested_rejected_patches':reject,'unknown_static':ustatic,
         'limits':['No terrain or policy changed','Inherited discrepancies remain unresolved','No render claim']}
    save(OUT,out)
    print(json.dumps({'status':out['status'],'seconds':out['seconds'],'conflict_cells':len(conflicts),'reject_ids':sorted(reject),'inventory_sha256':sha(OUT)}),flush=True)

if __name__=='__main__':main()
