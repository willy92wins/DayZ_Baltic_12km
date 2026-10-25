from __future__ import annotations
import hashlib, json, os
from pathlib import Path
import numpy as np

GIS_PY = Path(r'C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe')
OUT = Path(r'E:/DayZ-Baltic-Build/v30-bank-multiscale-census-20261010/source-comparison')
B_PATH = Path(r'E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz')
SRC_PATH = Path(r'P:/DayZ_Baltic_12km_dev/source/baltic_relief3x_2048_6m.asc')
CENSUS_NPZ = Path(r'E:/DayZ-Baltic-Build/v30-bank-multiscale-census-20261010/multiscale-arrays-and-rankings.npz')
CENSUS_SUMMARY = Path(r'E:/DayZ-Baltic-Build/v30-bank-multiscale-census-20261010/summary.json')
COORD_SOURCE = Path(r'P:/DayZ_Baltic_12km_dev/tools/geo_common.py')
N=2048; CELL=6.0
EXPECTED = {
    'B':'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
    'relief3x_ASC':'ecb2bd99a1751362bfcab0c150f10d18649bf3a50b24ea49a3eb0ffdb48bdf1f',
    'census_arrays':'6bdd42b298e538b4ecce3063a8a53e3aafb65b0f15373d78254ea8bc57e0c213',
    'census_summary':'12cd2f71a6f719d019db6dbf71d843d52d3d6233b96e0c8b68beef0774a49eda',
}
SAMPLES=[(0,0),(100,100),(840,370),(1024,1024),(1800,1500)]

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''): h.update(block)
    return h.hexdigest()

def atomic_json(path:Path,obj):
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    os.replace(tmp,path)

def read_ascii_header(path):
    with path.open('r',encoding='ascii') as f:
        lines=[f.readline().strip() for _ in range(6)]
    header={}
    for line in lines:
        key,*vals=line.split()
        if len(vals)!=1: raise ValueError(f'Invalid ASC header line: {line!r}')
        header[key.lower()]=float(vals[0])
    return header

def raw_ascii_samples(path, rows_needed):
    # Independent token-level read of the original text rows; this does not use np.loadtxt.
    out={}
    with path.open('r',encoding='ascii') as f:
        for _ in range(6): f.readline()
        for r,line in enumerate(f):
            if r in rows_needed:
                vals=line.split()
                if len(vals)!=N: raise ValueError(f'ASC row {r} has {len(vals)} cells, expected {N}')
                for rr,c in SAMPLES:
                    if rr==r: out[(rr,c)]=float(vals[c])
            if len(out)==len(SAMPLES): break
    if len(out)!=len(SAMPLES): raise ValueError('Independent ASCII sample read missed rows')
    return out

def qstats(values):
    a=np.asarray(values,dtype=np.float64)
    a=a[np.isfinite(a)]
    if not a.size: return {'n':0}
    q=np.quantile(a,[0,.01,.25,.5,.75,.95,.99,1],method='linear')
    return {'n':int(a.size),'mean':float(a.mean()),'mean_abs':float(np.abs(a).mean()),
            'quantiles':{'min':float(q[0]),'p01':float(q[1]),'p25':float(q[2]),'p50':float(q[3]),'p75':float(q[4]),'p95':float(q[5]),'p99':float(q[6]),'max':float(q[7])}}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    paths={'B':B_PATH,'relief3x_ASC':SRC_PATH,'census_arrays':CENSUS_NPZ,'census_summary':CENSUS_SUMMARY,'coordinate_contract_source':COORD_SOURCE}
    before={k:sha(v) for k,v in paths.items()}
    for k,v in EXPECTED.items():
        if before[k].lower()!=v.lower(): raise RuntimeError(f'{k} hash mismatch: {before[k]} != {v}')
    header=read_ascii_header(SRC_PATH)
    expected_header={'ncols':2048.0,'nrows':2048.0,'xllcorner':200000.0,'yllcorner':0.0,'cellsize':6.0,'nodata_value':-9999.0}
    if header!=expected_header: raise RuntimeError(f'ASC header mismatch: {header}')
    source=np.loadtxt(SRC_PATH,skiprows=6,dtype=np.float32)
    if source.shape!=(N,N): raise RuntimeError(f'ASC shape mismatch: {source.shape}')
    if not np.all(np.isfinite(source)): raise RuntimeError('Source contains non-finite values')
    nodata=float(header['nodata_value'])
    nodata_count=int(np.count_nonzero(source==nodata))
    bdict={}
    with np.load(B_PATH,allow_pickle=False) as z:
        bdict={k:z[k] for k in z.files}
    B=bdict['heights']
    if B.shape!=(N,N) or B.dtype!=np.float32: raise RuntimeError(f'B height shape/dtype mismatch: {B.shape}/{B.dtype}')
    with np.load(CENSUS_NPZ,allow_pickle=False) as z:
        masks={k:z[k] for k in ('bank','interior','eligible','explicit_fixed_protected','wet_support','seed6_pre_spacing')}
        bprom={(d,axis):z[f'd{d}_{axis}_m'] for d in (1,2,4) for axis in ('ew','ns')}
        valid={d:z[f'd{d}_valid'] for d in (1,2,4)}
    if any(v.shape!=(N,N) for v in masks.values()) or any(v.shape!=(N,N) for v in bprom.values()): raise RuntimeError('Census mask/prominence shape mismatch')
    if not np.array_equal(masks['eligible'],(masks['eligible']&masks['bank'])|(masks['eligible']&masks['interior'])|(masks['eligible']&masks['wet_support'])):
        raise RuntimeError('Eligible population partition is not exact')
    eligible_bank=masks['eligible']&masks['bank']
    eligible_interior=masks['eligible']&masks['interior']
    eligible_wet_support=masks['eligible']&masks['wet_support']
    pop={
        'all':np.ones((N,N),dtype=bool),
        'eligible':masks['eligible'],
        'eligible_bank':eligible_bank,
        'eligible_interior':eligible_interior,
        'eligible_wet_support':eligible_wet_support,
        'explicit_fixed_protected':masks['explicit_fixed_protected'],
    }
    if int(pop['eligible_bank'].sum()+pop['eligible_interior'].sum()+pop['eligible_wet_support'].sum())!=int(pop['eligible'].sum()):
        raise RuntimeError('Eligible populations do not partition the eligible mask')
    # Source relief3x and B are sampled at the same 2048x2048 indices.
    delta_height=B.astype(np.float64)-source.astype(np.float64)
    relation=np.zeros((N,N),dtype=np.uint8)
    relation[eligible_bank]=1
    relation[eligible_interior]=2
    relation[eligible_wet_support]=3
    relation[masks['eligible']&~(masks['bank']|masks['interior']|masks['wet_support'])]=4
    relation[masks['explicit_fixed_protected']&~masks['eligible']]=5
    common_bits=np.zeros((N,N),dtype=np.uint8)
    b_only_bits=np.zeros_like(common_bits); source_only_bits=np.zeros_like(common_bits)
    valid_context_bits=np.zeros((N,N),dtype=np.uint8)
    for ci,d in enumerate((1,2,4)): valid_context_bits[valid[d]] |= (1 << ci)
    saved={'height_delta_B_minus_relief3x_m':delta_height.astype(np.float32),'population_code':relation,
           'valid_context_bits_d1_d2_d4':valid_context_bits,'source_nodata_mask':(source==nodata)}
    relation_axes={}
    for di,d in enumerate((1,2,4)):
        ew=np.full((N,N),np.nan,np.float32); ns=np.full((N,N),np.nan,np.float32)
        ew[d:N-d,d:N-d]=np.maximum(0.0,source[d:N-d,d:N-d]-np.maximum(source[d:N-d,0:N-2*d],source[d:N-d,2*d:N]))
        ns[d:N-d,d:N-d]=np.maximum(0.0,source[d:N-d,d:N-d]-np.maximum(source[0:N-2*d,d:N-d],source[2*d:N,d:N-d]))
        saved[f'relief3x_d{d}_ew_prominence_m']=ew
        saved[f'relief3x_d{d}_ns_prominence_m']=ns
        relation_per_d={}
        for ai,axis in enumerate(('ew','ns')):
            bp=bprom[(d,axis)]
            sp=ew if axis=='ew' else ns
            bpos=valid[d]&(bp>0)
            spos=valid[d]&(sp>0)
            bit=1 << (di*2+ai)
            common_bits[(bpos&spos)] |= bit
            b_only_bits[(bpos&~spos)] |= bit
            source_only_bits[(spos&~bpos)] |= bit
            relation_per_d[axis]={'B_positive':bpos,'source_positive':spos,'common':bpos&spos,'B_only':bpos&~spos,'source_only':spos&~bpos}
        relation_axes[d]=relation_per_d
    saved['same_axis_scale_common_positive_bits']=common_bits
    saved['B_only_positive_bits']=b_only_bits
    saved['relief3x_only_positive_bits']=source_only_bits
    atomic_npz=OUT/'relief3x-prominence-comparison.npz'
    tmp=OUT/'relief3x-prominence-comparison.tmp.npz'
    np.savez_compressed(tmp,**saved);os.replace(tmp,atomic_npz)
    # Grouped scalar summaries: raw height difference and per-axis prominence differences and support overlap.
    summary={'schema':'B-relief3x-multiscale-diagnostic-v1','interpretation':'Diagnostic comparison only. relief3x is a project source representation, not independent ground truth; no terrain edits, defect labels, or acceptance thresholds follow from these deltas.',
      'inputs':{k:{'path':str(v),'sha256':before[k]} for k,v in paths.items()},
      'grid':{'shape':[N,N],'cell_m':CELL,'source_ASC_header':header,'row0':'north','source_cell_center_X_m':'200000 + (col + 0.5)*6','source_cell_center_Y_m':'(0 + 2048*6) - (row + 0.5)*6','no_data_sentinel':nodata,'no_data_count':nodata_count,'all_source_samples_finite':bool(np.all(np.isfinite(source))),'source_min_m':float(source.min()),'source_max_m':float(source.max()),'source_exact_minus12_count':int(np.count_nonzero(source==-12.0))},
      'formula':{'per_axis':'prom_d = max(0, H[row,col] - max(H[row-d,col], H[row+d,col])) for NS; analogously columns for EW','distances_nodes':[1,2,4],'distances_m':[6,12,24],'positive_support':'strictly > 0, for same axis and same distance on both grids','difference':'B prominence minus relief3x prominence; no new tolerance'},
      'populations':{},'old_EV87_seed_support':{},'relation_map_codes':{'0':'none of the defined populations','1':'eligible bank','2':'eligible interior','3':'eligible and wet_support (outside bank/interior)','4':'eligible partition remainder; expected zero','5':'explicitly protected and not eligible'},
      'context_bit_map':{'bit0':'d=1 (6m) complete cardinal context','bit1':'d=2 (12m) complete cardinal context','bit2':'d=4 (24m) complete cardinal context'},
      'support_bit_map':{'bit0':'6m EW','bit1':'6m NS','bit2':'12m EW','bit3':'12m NS','bit4':'24m EW','bit5':'24m NS','common':'B and relief3x both have positive prominence at same node/axis/scale','B_only':'B positive and relief3x not positive at same node/axis/scale','relief3x_only':'relief3x positive and B not positive at same node/axis/scale'},
      'samples':[]}
    for name,mask in pop.items():
        item={'vertices':int(mask.sum()),'height_delta_B_minus_relief3x_m':qstats(delta_height[mask])}
        per_d={}
        for d in (1,2,4):
            m=mask&valid[d]
            axes={}
            for axis in ('ew','ns'):
                bp=bprom[(d,axis)].astype(np.float64)
                sp=saved[f'relief3x_d{d}_{axis}_prominence_m'].astype(np.float64)
                diff=bp-sp
                rel=relation_axes[d][axis]
                axes[axis]={'context_vertices':int(m.sum()),'B_prominence_m':qstats(bp[m]),'relief3x_prominence_m':qstats(sp[m]),'difference_B_minus_relief3x_m':qstats(diff[m]),
                   'support':{'B_positive':int((m&rel['B_positive']).sum()),'relief3x_positive':int((m&rel['source_positive']).sum()),'common_positive':int((m&rel['common']).sum()),'B_only_positive':int((m&rel['B_only']).sum()),'relief3x_only_positive':int((m&rel['source_only']).sum())}}
            per_d[f'd{d}']={'distance_m':d*CELL,'axes':axes}
        seed=masks['seed6_pre_spacing']&mask
        seed_item={'seeds':int(seed.sum()),'same_axis_source_support':{}}
        for d in (1,2,4):
            seed_item['same_axis_source_support'][f'd{d}']={}
            for axis in ('ew','ns'):
                bp=bprom[(d,axis)]
                sp=saved[f'relief3x_d{d}_{axis}_prominence_m']
                same=seed&valid[d]&(bp>0)&(sp>0)
                bpos=seed&valid[d]&(bp>0);spos=seed&valid[d]&(sp>0)
                seed_item['same_axis_source_support'][f'd{d}'][axis]={'B_positive':int(bpos.sum()),'relief3x_positive':int(spos.sum()),'common_positive':int(same.sum())}
        summary['populations'][name]=item
        summary['populations'][name]['prominence_comparison']=per_d
        summary['old_EV87_seed_support'][name]=seed_item
    for r,c in SAMPLES:
        src=float(source[r,c]); bh=float(B[r,c]);
        x=200000.0+(c+.5)*CELL; y=12288.0-(r+.5)*CELL
        summary['samples'].append({'row':r,'col':c,'source_cell_center_xy_m':[x,y],'relief3x_m':src,'B_m':bh,'B_minus_relief3x_m':bh-src,'source_sentinel_nodata':bool(src==nodata),'independent_ASC_token_read_m':None})
    raw=raw_ascii_samples(SRC_PATH,{r for r,_ in SAMPLES})
    for sample in summary['samples']:
        k=(sample['row'],sample['col']); v=raw[k]
        if np.float32(v)!=np.float32(sample['relief3x_m']): raise RuntimeError(f'Raw token sample mismatch at {k}: {v} vs {sample["relief3x_m"]}')
        sample['independent_ASC_token_read_m']=v
        sample['token_cast_to_float32_matches_loadtxt']=True
    # Hash every input again before final publication to reject TOCTOU.
    after={k:sha(v) for k,v in paths.items()}
    if before!=after: raise RuntimeError('An input changed during the diagnostic')
    summary['inputs_rehashed_after_run']=after
    summary['outputs']={'npz_path':str(atomic_npz),'npz_sha256':sha(atomic_npz),'script_path':str(Path(__file__).resolve()),'script_sha256':sha(Path(__file__).resolve())}
    summary['classification_limit']='Positive support is a formula-level descriptor. Same-node B/source agreement does not prove feature identity, naturalness, source correctness, or visual quality; disagreement is not automatically an artifact.'
    atomic_json(OUT/'summary.json',summary)
    note='''# Comparación B ↔ relief3x: diagnóstico, no selector\n\nSe compara la base B congelada con el ASC `relief3x` en los mismos 2048×2048 índices. El ASC declara `NODATA_value -9999`; no se hallaron celdas con ese sentinel y todos sus valores son finitos. `-12` es un valor del raster, no se ha reinterpretado como NoData. Cinco valores fueron contrastados con lectura independiente de tokens de las filas ASCII.\n\nPara cada eje cardinal y d=1,2,4 (6/12/24 m), ambos campos usan `max(0, Hc−max(H−d,H+d))`. El summary incluye distribuciones B−relief3x, cuantiles de prominencia por población, coincidencias de soporte positivo en el mismo eje/escala, y conteos de semillas EV87 con soporte de la fuente en esas posiciones. El NPZ guarda prominencias relief3x y mapas de población/soporte. Las salidas son descriptivas; relief3x es una representación de proyecto, no ground truth ni etiqueta automática de defecto. No establecen umbral ni autorizan cambios de terreno.\n\nAnclas: B `f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0`; relief3x ASC `ecb2bd99a1751362bfcab0c150f10d18649bf3a50b24ea49a3eb0ffdb48bdf1f`; censo previo `6bdd42b298e538b4ecce3063a8a53e3aafb65b0f15373d78254ea8bc57e0c213`.\n'''
    (OUT/'README.md').write_text(note,encoding='utf-8')
    print(json.dumps({'status':'DIAGNOSTIC_COMPLETE','summary':str(OUT/'summary.json'),'arrays':str(atomic_npz),'npz_sha256':sha(atomic_npz),'script_sha256':sha(Path(__file__).resolve()),'source_nodata_count':nodata_count,'populations':{k:v['vertices'] for k,v in summary['populations'].items()},'samples':summary['samples']},ensure_ascii=False))

if __name__=='__main__': main()


