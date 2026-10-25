"""One declared interpolation, exact rational moments, no optimizer or repair."""
from pathlib import Path
from fractions import Fraction
import argparse, hashlib, json, math
import numpy as np

HERE=Path(__file__).resolve().parent
Q=HERE.parent
BASE=Q.parent/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
DIRECTION=Q/'ev91-descent/candidate-terrain.npz'
PARENT_PREP=Q/'ev91-descent/prepared.json'
PARENT_REC=Q/'ev91-descent/authoring.json'
PINS={str(BASE):'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
      str(DIRECTION):'865901ab24aa3736da57847f9112d3c73181085213f89b48ef2e3e7a9f6ee702',
      str(PARENT_PREP):'127b906c1d2a5d2aa09172ed47dac16cd489aae6a2955428a96166a325605877',
      str(PARENT_REC):'12be9f321eef9ce586e2c6fe43cce3a55cfed83cc9664ea9f14b8747979d5339'}

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(4194304),b''):h.update(block)
    return h.hexdigest()

def support(kind,r,c):
    if kind=='xx':return ((r,c,1),(r,c+1,-2),(r,c+2,1))
    if kind=='zz':return ((r,c,1),(r+1,c,-2),(r+2,c,1))
    if kind=='xz':return ((r,c,Fraction(-1,4)),(r,c+2,Fraction(1,4)),
                          (r+2,c,Fraction(1,4)),(r+2,c+2,Fraction(-1,4)))
    raise ValueError('unknown stencil')

def energy_moments(b,h,stencils):
    q=[Fraction(0),Fraction(0),Fraction(0)]
    for kind,r,c in stencils:
        bv=sum((Fraction(float(b[rr,cc]))*coef for rr,cc,coef in support(kind,r,c)),Fraction(0))
        hv=sum((Fraction(float(h[rr,cc]))*coef for rr,cc,coef in support(kind,r,c)),Fraction(0))
        dv=hv-bv;w=2 if kind=='xz' else 1
        for i,v in enumerate((w*bv*bv,2*w*bv*dv,w*dv*dv)):q[i]+=v
    return q

def scalar_rule(b,h,stencils,focus=(840,370)):
    q=energy_moments(b,h,stencils);q0,q1,q2=map(float,q)
    if not(q0>0 and q2>0 and q1<0 and sum(q)<=Fraction(3,4)*q[0]):
        raise ValueError('direction does not provide the planned energy interval')
    discriminant=q1*q1-q2*q0
    if discriminant<=0:raise ValueError('no positive energy interval')
    # Stable smaller root of q2*a^2+q1*a+q0/4=0.
    energy_lower=(q0/2)/(-q1+math.sqrt(discriminant))
    r,c=focus;center_b=Fraction(float(b[r,c]));center_d=Fraction(float(h[r,c]))-center_b
    axes={}
    for name,neighbors in {'EW':((r,c-1),(r,c+1)),'NS':((r-1,c),(r+1,c))}.items():
        prom=center_b-max(Fraction(float(b[p])) for p in neighbors)
        if prom<=0:raise ValueError('baseline focus is not prominent on both axes')
        target=Fraction(3,4)*prom;roots=[]
        for p in neighbors:
            start=center_b-Fraction(float(b[p]));slope=center_d-(Fraction(float(h[p]))-Fraction(float(b[p])))
            if slope<0:roots.append(float((target-start)/slope))
        roots=[x for x in roots if 0<=x<=1]
        if not roots:raise ValueError('no focus interval to endpoint')
        axes[name]=min(roots)
    lower=max(energy_lower,*axes.values(),0.)
    if not 0<lower<1:raise ValueError('empty materiality interval')
    return {'energy_moments_fraction':[str(x) for x in q],
            'energy_moments_float64':[float(x) for x in q],
            'energy_lower':energy_lower,'focus_lower_by_axis':axes,
            'materiality_lower':lower,'alpha':(lower+1.)/2.,
            'rule':'midpoint of materiality interval [max(energy25,focus25EW,focus25NS),1]; not a global feasibility interval'}

def prepare():
    pre=json.loads(PARENT_PREP.read_text(encoding='utf-8'))
    parent=json.loads(PARENT_REC.read_text(encoding='utf-8'))
    pins={**pre['source_pins'],**PINS}
    for p in (HERE/'plan.md',HERE/'alpha-interval.json',Path(__file__).resolve()):pins[str(p)]=sha(p)
    for p,wanted in pins.items():
        if sha(p)!=wanted:raise AssertionError(f'input changed: {p}')
    with np.load(BASE,allow_pickle=False) as z:base={k:z[k] for k in z.files}
    with np.load(DIRECTION,allow_pickle=False) as z:direction={k:z[k] for k in z.files}
    if set(base)!=set(direction):raise AssertionError('direction metadata differs')
    for key in base:
        if key!='heights' and not np.array_equal(base[key],direction[key],equal_nan=True):raise AssertionError(key)
    b,h=base['heights'],direction['heights']
    if b.dtype!=np.float32 or h.dtype!=np.float32 or b.shape!=(2048,2048) or h.shape!=b.shape:
        raise AssertionError('wrong grid representation')
    if not np.isfinite(b).all() or not np.isfinite(h).all():raise AssertionError('nonfinite heights')
    selected=set(map(tuple,pre['variables_rc']))
    if not all(tuple(p) in selected for p in np.argwhere(h!=b)):raise AssertionError('direction outside frozen domain')
    rule=scalar_rule(b,h,pre['stencils'])
    independent=json.loads((HERE/'alpha-interval.json').read_text(encoding='utf-8'))
    if not np.allclose(rule['energy_moments_float64'],independent['energy']['quadratic_constant_linear_quadratic'],rtol=1e-13,atol=1e-12):
        raise AssertionError('energy coefficients disagree with independent derivation')
    metadata={**pre,'status':'PREPARED_NO_WRITE','source_pins':pins,
              'plan_sha256':sha(HERE/'plan.md'),'author_source_sha256':sha(__file__),
              'baseline_sha256':PINS[str(BASE)],'direction_sha256':PINS[str(DIRECTION)],
              'parent_prepared_sha256':PINS[str(PARENT_PREP)],'parent_receipt_sha256':PINS[str(PARENT_REC)],
              'scalar_rule':rule,'alpha':rule['alpha'],
              'solver':{'method':'analytic_segment_interpolation','calls':0}}
    return base,h,metadata

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');ap.add_argument('--approved-prepared-sha',default='')
    args=ap.parse_args();base,direction,rec=prepare();prep=HERE/'prepared.json'
    if not args.write:
        prep.write_text(json.dumps(rec,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'status':rec['status'],'alpha':rec['alpha'],'rule':rec['scalar_rule']}));return
    if not prep.is_file() or sha(prep)!=args.approved_prepared_sha:raise AssertionError('prepared identity not authorized')
    if json.loads(prep.read_text(encoding='utf-8'))!=rec:raise AssertionError('prepared inputs/rule changed')
    out=HERE/'candidate-terrain.npz';receipt=HERE/'authoring.json'
    if out.exists() or receipt.exists():raise FileExistsError('output exists')
    with (HERE/'write-started.json').open('x',encoding='utf-8') as f:json.dump(rec,f,indent=2)
    b=base['heights'];h=(b.astype(np.float64)+rec['alpha']*(direction.astype(np.float64)-b.astype(np.float64))).astype(np.float32)
    for rc,limits in zip(rec['variables_rc'],rec['solver_bounds_float32']):
        if not limits[0]<=float(h[tuple(rc)])<=limits[1]:raise AssertionError('quantized bounds violated; no repair')
    if any(h[tuple(x['center'])]<h[tuple(x['witness'])] for x in rec['witnesses']):raise AssertionError('quantized witness violated; no repair')
    for p,wanted in rec['source_pins'].items():
        if sha(p)!=wanted:raise AssertionError('source changed during authoring')
    output={**base,'heights':h}
    with out.open('xb') as f:np.savez_compressed(f,**output)
    rec.update({'status':'AUTHORED_PENDING_INDEPENDENT_CONSUMER','candidate_path':str(out),
                'candidate_sha256':sha(out),'approved_prepared_sha256':args.approved_prepared_sha,
                'changed_vertices':int(np.count_nonzero(h!=b))})
    receipt.write_text(json.dumps(rec,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:rec[k] for k in ('status','alpha','candidate_sha256','changed_vertices')}))

if __name__=='__main__':main()
