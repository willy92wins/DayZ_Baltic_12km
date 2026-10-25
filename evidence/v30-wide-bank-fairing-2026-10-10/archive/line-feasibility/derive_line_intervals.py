from __future__ import annotations
import hashlib, json, math
from pathlib import Path
import numpy as np

ROOT=Path(r'E:/DayZ-Baltic-Build')
PILOT=ROOT/'v30-wide-bank-fairing-pilot-20261010'
B_PATH=ROOT/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
Q_PATH=PILOT/'candidate-terrain.npz'
PLAN=PILOT/'plan.md'
RECEIPT=PILOT/'authoring.json'
PREFLIGHT=PILOT/'author/preflight/preflight.json'
OUT=PILOT/'line-feasibility/line-intervals.json'
R,C=840,370
CORE=(R-6,R+7,C-6,C+7)
TAU=0.024040603637695314

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()

def npz_height(p):
 with np.load(p,allow_pickle=False) as z:return np.asarray(z['heights'],dtype=np.float64)

def add_root(bp, a0, da, target=0.0):
 # a0 + alpha*da == target
 if da==0.0:return
 x=(target-a0)/da
 if 0.0<x<1.0:bp.add(float(x))

def line_breakpoints(B,Q):
 d=Q-B;bp={0.0,1.0};r0,r1,c0,c1=CORE
 # All cardinal edge order changes touching the core, including border-to-collar
 # edges used by strict extrema and row/column prominences.
 edge_set=set()
 for r in range(r0,r1):
  for c in range(c0,c1):
   for rr,cc in ((r,c-1),(r,c+1),(r-1,c),(r+1,c)):
    if 0<=rr<B.shape[0] and 0<=cc<B.shape[1]:
     edge_set.add(tuple(sorted(((r,c),(rr,cc)))))
 for u,v in edge_set:
  add_root(bp,float(B[u]-B[v]),float(d[u]-d[v]))
 # 2x2 span threshold events: span<=tau iff every pair differs by at most tau.
 for r in range(r0,r1-1):
  for c in range(c0,c1-1):
   bvals=[float(B[r,c]),float(B[r,c+1]),float(B[r+1,c]),float(B[r+1,c+1])]
   if max(bvals)-min(bvals)<=TAU:continue
   nodes=((r,c),(r,c+1),(r+1,c),(r+1,c+1))
   for i in range(4):
    for j in range(i+1,4):
     u,v=nodes[i],nodes[j]
     v0=float(B[u]-B[v]);dv=float(d[u]-d[v])
     add_root(bp,v0,dv,TAU);add_root(bp,v0,dv,-TAU)
 # Focus prominence gates and no-new-depression breakpoints.
 for dr,dc in ((0,-1),(0,1),( -1,0),(1,0)):
  a=(R,C);n=(R+dr,C+dc)
  diff0=float(B[a]-B[n]);diffd=float(d[a]-d[n])
  add_root(bp,diff0,diffd,0.0)
  if dr==0:
   bprom=max(0.0,float(B[a]-max(B[R,C-1],B[R,C+1])))
  else:
   bprom=max(0.0,float(B[a]-max(B[R-1,C],B[R+1,C])))
  add_root(bp,diff0,diffd,0.75*bprom)
 # Row/column peak prominence gates. Candidate peak prominence can exceed its
 # frozen line maximum only after both adjacent differences exceed that maximum.
 for r in range(r0,r1):
  peak=max([min(float(B[r,c]-B[r,c-1]),float(B[r,c]-B[r,c+1]))
            for c in range(c0+1,c1-1) if B[r,c]>B[r,c-1] and B[r,c]>B[r,c+1]]+[0.0])
  for c in range(c0+1,c1-1):
   for cc in (c-1,c+1):add_root(bp,float(B[r,c]-B[r,cc]),float(d[r,c]-d[r,cc]),peak)
 for c in range(c0,c1):
  peak=max([min(float(B[r,c]-B[r-1,c]),float(B[r,c]-B[r+1,c]))
            for r in range(r0+1,r1-1) if B[r,c]>B[r-1,c] and B[r,c]>B[r+1,c]]+[0.0])
  for r in range(r0+1,r1-1):
   for rr in (r-1,r+1):add_root(bp,float(B[r,c]-B[rr,c]),float(d[r,c]-d[rr,c]),peak)
 # One-to-one extrema matching: an H extremum can match only same-kind B extrema
 # within Chebyshev radius 1, and its prominence must not exceed that B prominence.
 b_ext=axial_extrema(B,CORE)
 for r in range(r0,r1):
  for c in range(c0,c1):
   ns=((r,c-1),(r,c+1),(r-1,c),(r+1,c))
   for kind in ('max','min'):
    matches=[e['prominence'] for e in b_ext if e['kind']==kind and max(abs(e['row']-r),abs(e['col']-c))<=1]
    for threshold in matches:
     for rr,cc in ns:
      if kind=='max':a0=float(B[r,c]-B[rr,cc]);da=float(d[r,c]-d[rr,cc])
      else:a0=float(B[rr,cc]-B[r,c]);da=float(d[rr,cc]-d[r,c])
      add_root(bp,a0,da,threshold)
 return sorted(bp)

def axial_extrema(h,window):
 r0,r1,c0,c1=window;out=[]
 for r in range(max(1,r0),min(h.shape[0]-1,r1)):
  for c in range(max(1,c0),min(h.shape[1]-1,c1)):
   v=float(h[r,c]);n=(float(h[r,c-1]),float(h[r,c+1]),float(h[r-1,c]),float(h[r+1,c]))
   if v>max(n):out.append({'row':r,'col':c,'kind':'max','prominence':v-max(n)})
   elif v<min(n):out.append({'row':r,'col':c,'kind':'min','prominence':min(n)-v})
 return out

def match_extrema(b,h,window,radius=1):
 be=axial_extrema(b,window);he=axial_extrema(h,window);adj=[]
 for x in he:
  adj.append([i for i,y in enumerate(be) if x['kind']==y['kind'] and
   max(abs(x['row']-y['row']),abs(x['col']-y['col']))<=radius and y['prominence']>=x['prominence']])
 owner={}
 def augment(i,seen):
  for j in adj[i]:
   if j in seen:continue
   seen.add(j)
   if j not in owner or augment(owner[j],seen):owner[j]=i;return True
  return False
 matched=sum(augment(i,set()) for i in sorted(range(len(he)),key=lambda k:(len(adj[k]),he[k]['row'],he[k]['col'])))
 return {'pass':matched==len(he),'B_count':len(be),'H_count':len(he),'matched':matched,
  'unmatched_H':[he[i] for i in range(len(he)) if i not in set(owner.values())]}

def rowcol_prom(B,h,window):
 r0,r1,c0,c1=window;rp=[];hp=[];cp=[];hc=[]
 for r in range(r0,r1):
  rp.append(max([min(float(B[r,c]-B[r,c-1]),float(B[r,c]-B[r,c+1])) for c in range(c0+1,c1-1)
    if B[r,c]>B[r,c-1] and B[r,c]>B[r,c+1]]+[0.0]))
  hp.append(max([min(float(h[r,c]-h[r,c-1]),float(h[r,c]-h[r,c+1])) for c in range(c0+1,c1-1)
    if h[r,c]>h[r,c-1] and h[r,c]>h[r,c+1]]+[0.0]))
 for c in range(c0,c1):
  cp.append(max([min(float(B[r,c]-B[r-1,c]),float(B[r,c]-B[r+1,c])) for r in range(r0+1,r1-1)
    if B[r,c]>B[r-1,c] and B[r,c]>B[r+1,c]]+[0.0]))
  hc.append(max([min(float(h[r,c]-h[r-1,c]),float(h[r,c]-h[r+1,c])) for r in range(r0+1,r1-1)
    if h[r,c]>h[r-1,c] and h[r,c]>h[r+1,c]]+[0.0]))
 return {'rows_nonworse':bool(np.all(np.asarray(hp)<=np.asarray(rp)+1e-12)),
  'columns_nonworse':bool(np.all(np.asarray(hc)<=np.asarray(cp)+1e-12)),
  'max_row_excess_m':float(np.max(np.asarray(hp)-np.asarray(rp))),
  'max_column_excess_m':float(np.max(np.asarray(hc)-np.asarray(cp))),
  'row_excesses_m':(np.asarray(hp)-np.asarray(rp)).tolist(),
  'column_excesses_m':(np.asarray(hc)-np.asarray(cp)).tolist()}

def focus_values(B,h):
 ans={};r,c=R,C
 for axis,ns in [('east_west',((r,c-1),(r,c+1))),('north_south',((r-1,c),(r+1,c)))]:
  bp=max(0.0,float(B[r,c]-max(B[ns[0]],B[ns[1]])))
  hp=max(0.0,float(h[r,c]-max(h[ns[0]],h[ns[1]])))
  depression=bool(h[r,c]<min(h[ns[0]],h[ns[1]]))
  ans[axis]={'B_prominence_m':bp,'Halpha_prominence_m':hp,'required_max_m':0.75*bp,
   'reduction_fraction':None if bp<=0 else float(1-hp/bp),'new_strict_minimum':depression,
   'pass':bool(bp>0 and hp<=0.75*bp and not depression)}
 return ans

def gate_set(B,H):
 r0,r1,c0,c1=CORE
 focus=focus_values(B,H)
 spans=[];newflats=[]
 for r in range(r0,r1-1):
  for c in range(c0,c1-1):
   sb=float(np.ptp(B[r:r+2,c:c+2]));sh=float(np.ptp(H[r:r+2,c:c+2]))
   spans.append({'rc':[r,c],'B':sb,'H':sh})
   if sb>TAU and sh<=TAU:newflats.append([r,c])
 extrema=match_extrema(B,H,CORE)
 rc=rowcol_prom(B,H,CORE)
 return {'focus':focus,'focus_pass':all(x['pass'] for x in focus.values()),
  'new_nearflat_count':len(newflats),'new_nearflat_examples':newflats[:12],
  'nearflat_pass':len(newflats)==0,'extrema':extrema,'extrema_pass':extrema['pass'],
  'rowcol':rc,'rowcol_pass':rc['rows_nonworse'] and rc['columns_nonworse']}

def alpha_components(points,open_segments,point_ok):
 # Exact union of passing open segments and passing breakpoint singletons.
 pieces=[]
 for i,x in enumerate(points):
  if point_ok[i]:
   pieces.append({'lo':x,'hi':x,'lo_closed':True,'hi_closed':True,'point':True})
  if i<len(points)-1 and open_segments[i]:
   pieces.append({'lo':x,'hi':points[i+1],'lo_closed':False,'hi_closed':False,'point':False})
 pieces.sort(key=lambda q:(q['lo'],q['hi']))
 merged=[]
 for x in pieces:
  if not merged:merged.append(x);continue
  z=merged[-1]
  if x['lo']<z['hi'] or (x['lo']==z['hi'] and (z['hi_closed'] or x['lo_closed'])):
   if x['lo']==z['lo']:z['lo_closed']=z['lo_closed'] or x['lo_closed']
   if x['hi']>z['hi']:z['hi']=x['hi'];z['hi_closed']=x['hi_closed']
   elif x['hi']==z['hi']:z['hi_closed']=z['hi_closed'] or x['hi_closed']
   z['point']=z['point'] and x['point']
  else:merged.append(x.copy())
 return merged

def main():
 plan_sha=sha(PLAN); expected_plan='50a94dac1a15580c6299426678399ca80caf49835ba98a79946ded688a8a47ad'
 q_sha=sha(Q_PATH);expected_q='cce4cd0c2f71355c6d8a110804b52570644e496055ada9ef17d07b4cb60c455c'
 b_sha=sha(B_PATH);expected_b='f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'
 if (plan_sha,q_sha,b_sha)!=(expected_plan,expected_q,expected_b):raise AssertionError('frozen B/Q/plan identity mismatch')
 b=npz_height(B_PATH);q=npz_height(Q_PATH);d=q-b
 points=line_breakpoints(b,q);n=len(points)
 segment_gates=[];point_gates=[]
 for lo,hi in zip(points[:-1],points[1:]):
  a=(lo+hi)/2.0
  segment_gates.append(gate_set(b,b+a*d))
 for a in points:point_gates.append(gate_set(b,b+a*d))
 gate_names=('focus_pass','nearflat_pass','extrema_pass','rowcol_pass')
 pass_segments={}
 for gate in gate_names:
  ok=[bool(seg[gate]) for seg in segment_gates]
  pk=[bool(pt[gate]) for pt in point_gates]
  pass_segments[gate]=alpha_components(points,ok,pk)
 # Correct combined components using per-gate booleans, with all gate truth constant inside each cell.
 segok=[all(s[g] for g in gate_names) for s in segment_gates]
 ptok=[all(p[g] for g in gate_names) for p in point_gates]
 merged=alpha_components(points,segok,ptok)
 # Gate behavior at alpha endpoints and diagnostic extrema.
 h0=b;h1=q
 endpoint={'alpha0':gate_set(b,h0),'alpha1':gate_set(b,h1)}
 all_pass_intervals=merged
 limiting={}
 for i,s in enumerate(segment_gates):
  if any(not s[g] for g in gate_names):
   key=','.join(g for g in gate_names if not s[g]);limiting[key]=limiting.get(key,0)+1
 # Raw focal values and how alpha1 Q changed 2D rows/columns.
 out={'status':'COMPLETE_ANALYTIC_LINE_DECOMPOSITION','scope':'Float64 line segment between frozen B and rejected frozen Q; shape gates only; no new solve or candidate.',
  'inputs':{str(p):sha(p) for p in (Path(__file__),PLAN,B_PATH,Q_PATH,PILOT/'authoring.json',PREFLIGHT)},
  'pins':{'B_sha256':b_sha,'Q_rejected_sha256':q_sha,'plan_sha256':plan_sha,'tau_flat_m':TAU,
   'core_rc_halfopen':list(CORE),'nearflat_count_B_from_preflight':8},
  'method':{'breakpoint_count_unique':n,'critical_breakpoints':points,'interval_labeling':'Each open segment is classified at its analytic interior point after all order/threshold roots are enumerated; root points are checked separately. This is a piecewise-linear arrangement, not a sampled alpha grid.',
   'breakpoint_families':['cardinal height equalities for strict extrema','2x2 pairwise height differences at +/-tau','focus differences at 0 and 75% B prominence','row/column neighbor differences at each B line-peak prominence','candidate axial prominence differences at matching B-extremum prominence thresholds']},
  'endpoint_gates':endpoint,'line_components_satisfying_all_shape_gates':all_pass_intervals,
  'gate_components':pass_segments,'limiting_gate_combinations_by_open_segment':limiting,
  'positive_width_feasible_intervals':[x for x in all_pass_intervals if x['hi']>x['lo']],
  'notes':['Near-flat uses the frozen 0.024040603637695314 m threshold, testing only core 13x13 2x2 windows that were above threshold in B.','Focus prominence is computed independently as max(0,center-max(axis neighbors)); focus may not become a strict minimum in either cardinal pair.','Extrema matching follows the plan: strict 4-neighbour extrema, same kind, Chebyshev radius 1, one-to-one, B prominence >= interpolated prominence.','Row/column prominence gate checks every core row and column maximum strict-peak prominence against the same B row/column.','No water, crossing, slope/angle, corridor, energy, float32 quantization, or visual/engine gate is evaluated; passing this line test is not acceptance of any alpha or terrain.']}
 OUT.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'status':out['status'],'breakpoints':n,'alpha1':{k:endpoint['alpha1'][k] for k in ('focus_pass','nearflat_pass','extrema_pass','rowcol_pass')},
  'combined':all_pass_intervals,'positive_width_intervals':out['positive_width_feasible_intervals'],'limiting':limiting,'output_sha256':sha(OUT)},indent=2))
if __name__=='__main__':main()
