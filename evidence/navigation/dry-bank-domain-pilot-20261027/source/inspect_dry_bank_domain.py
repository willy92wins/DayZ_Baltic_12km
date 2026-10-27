"""Describe a completed candidate; never edits it or changes acceptance."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent
context=json.loads((R/'dry-bank-domain-setup-fixed-20261027/context.json').read_text(encoding='utf-8-sig'))
W=Path(context['worktree']);O=R/'dry-bank-domain-analysis-20261027';O.mkdir(exist_ok=False)
source=Path(context['paths']['source']);candidate=R/'dry-bank-domain-pilot-20261027/candidate-surfaces.npz'
before=np.load(source);after=np.load(candidate)
result=json.loads((R/'dry-bank-domain-run-20261027/result.json').read_text(encoding='utf-8-sig'))
sys.path.insert(0,str(W/'tools/water'));from streambed_kit_v31 import tri_h
H=np.load(context['paths']['support'])['heights']
rows=json.loads(Path(context['paths']['attribution']).read_text(encoding='utf-8-sig'))['rows']
qs=np.unique(np.r_[np.arange(-18,19.),-2.25,2.25])
fig,axes=plt.subplots(3,1,figsize=(11,9),layout='constrained')
fig.suptitle('Kit-7 · toda la orilla seca\nEnsayo offline sin integrar — '+result['status'],fontsize=14)
for ax,(mesh,query) in zip(axes,[('nav12','kit7_piece_116_right'),('nav12p5','kit7_piece_124_right'),('nav12p5','kit7_piece_133_right')]):
    row=next(r for r in rows if r['mesh']==mesh and r['query']==query and r['index']==1)
    i=int(np.argmin(abs(before['station']-row['selected']['station_m'])))
    b=before['bed'][i];c=after['bed'][i];d=np.sign(qs)*np.linalg.norm(b[:,[0,2]]-before['axis'][i],axis=1)
    ax.plot(d,b[:,1],color='#b05712',lw=2,label='Orilla original')
    ax.plot(d,c[:,1],color='#19804f',lw=2,label='Piloto seco completo')
    ax.plot(d,tri_h(H,b[:,0],b[:,2]),ls='--',color='#646464',label='Terreno soporte')
    ax.plot([-2.25,2.25],[before['water'][i,0,1]]*2,lw=3,color='#238bd2',label='Agua intacta')
    ax.axvspan(-2.25,2.25,color='#dce7eb',alpha=.4,label='Lecho fijo')
    ax.set_title(query+' · estación '+str(round(float(before['station'][i]),1))+' m')
    ax.set_ylabel('Cota (m)');ax.set_xlabel('Distancia real transversal al eje (m)');ax.grid(alpha=.2)
axes[0].legend(ncols=3,fontsize=8);fig.savefig(O/'profiles.png',dpi=135);plt.close(fig)
locations={}
for name,arr in [('baseline',before),('candidate',after)]:
    bed=arr['bed'];summary={}
    for axis,label in ((0,'longitudinal'),(1,'transverse')):
        distance=np.linalg.norm(np.diff(bed[:,:,[0,2]],axis=axis),axis=2)
        values=abs(np.diff(bed[:,:,1],axis=axis))/distance
        index=tuple(map(int,np.unravel_index(np.argmax(values),values.shape)))
        other=list(index);other[axis]+=1
        summary[label]=dict(maximum=float(values[index]),index=index,station=float(arr['station'][index[0]]),
            q=float(qs[index[1]]),vertices=[bed[index].tolist(),bed[tuple(other)].tolist()])
    locations[name]=summary
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
visual=before['water'][:,0,1,None]
assert np.array_equal(before['water'][:,0,1],before['water'][:,1,1])
was_visual_dry=before['bed'][:,:,1]>=visual+.025
water_floor_exact=bool(np.all((after['bed'][:,:,1]>=visual+.025)[was_visual_dry]))
visual_margins={}
for q in (-4.,-3.,3.,4.):
    col=int(np.flatnonzero(qs==q)[0]);visual_margins[str(q)]={}
    for label,data in [('baseline',before),('candidate',after)]:
        margin=data['bed'][:,col,1]-visual[:,0]
        visual_margins[str(q)][label]=dict(minimum=float(margin.min()),maximum=float(margin.max()),
            quantiles=dict(zip(('p01','p05','p25','p50','p75','p95','p99'),map(float,np.quantile(margin,[.01,.05,.25,.5,.75,.95,.99])))))
(O/'visual-water-freeboard.json').write_text(json.dumps(dict(status='PASS' if water_floor_exact else 'FAIL',
    baseline_sha256=sha(source),candidate_sha256=sha(candidate),was_visual_dry_count=int(was_visual_dry.sum()),
    previously_dry_floor_preserved=water_floor_exact,margin_q3_q4=visual_margins,
    water_visual_minus_level_range=[float((visual[:,0]-before['level']).min()),float((visual[:,0]-before['level']).max())],
    note='Actual saved water Y, after 1/512 quantization. The solver/result uses level as its floor reference. This independent report supplies actual visual margins; no P14/native certification.'),indent=2)+'\n',encoding='utf-8')
(O/'locations.json').write_text(json.dumps(dict(status=result['status'],source_sha256=sha(source),
    candidate_sha256=sha(candidate),max_slope_locations=locations,limits='Descriptive saved-source geometry only.'),indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status=result['status'],locations=locations),indent=2))
