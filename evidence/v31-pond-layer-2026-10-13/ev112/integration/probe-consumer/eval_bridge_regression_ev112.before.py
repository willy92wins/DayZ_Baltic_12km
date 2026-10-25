"""OT5 no-regression consumer against the actual EV110 server probe.

This supplements (never replaces) the strict current bridge/shores evaluator.
Compare identical probe positions and the existing three-decimal step/level
metrics, individual previously wet points and individual sea flags. Wave depth
magnitudes are not compared: they vary with time. Invalid/missing data fails.
Usage: script baseline-points baseline-log current-points current-log out.json
"""
from pathlib import Path
import sys,json,math,hashlib

def load_rows(path,points):
 ids={p['id'] for p in points};rows={};begin=[];end=[]
 if len(ids)!=len(points):raise ValueError('duplicate point ids')
 for line in Path(path).read_text(encoding='utf-8').splitlines():
  a=line.split(';')
  if a[0]=='BEGIN':begin.append(int(a[1]))
  elif a[0]=='END':end.append(int(a[1]))
  elif a[0]=='P':
   if len(a)!=9:raise ValueError('invalid row width')
   k=int(a[1])
   if k not in ids or k in rows:raise ValueError('unknown or duplicate row')
   if a[3] not in ('true','false') or a[4] not in ('true','false'):raise ValueError('invalid water flags')
   v=dict(ground=float(a[2]),sea=a[3]=='true',pond=a[4]=='true',surface=float(a[5]),depth=float(a[6]),roadY=float(a[7]),objects=int(a[8]))
   if not all(math.isfinite(v[n]) for n in ('ground','surface','depth','roadY')) or v['objects']<0:raise ValueError('non-finite or invalid row')
   rows[k]=v
 if begin!=[len(points)] or end!=[len(points)] or set(rows)!=ids:raise ValueError('incomplete probe framing or ids')
 return rows

def judge(bp,br,cp,cr):
 key=lambda p:(p['site'],p['kind'],p['s'])
 old={key(p):p for p in bp};new={key(p):p for p in cp}
 if len(old)!=len(bp) or len(new)!=len(cp) or old.keys()!=new.keys():raise ValueError('probe sampling changed; comparison is not valid')
 if any(abs(old[k][v]-new[k][v])>1e-6 for k in old for v in ('x','z')):raise ValueError('probe positions changed')
 sites={};fail=[]
 for site in sorted({p['site'] for p in cp}):
  keys=[k for k in new if k[0]==site];road=sorted([k for k in keys if k[1]=='road'],key=lambda k:k[2]);under=[k for k in keys if k[1]=='under']
  if len(road)<2 or not under:raise ValueError('empty bridge metrics')
  def metrics(points,rows):
   step=max(abs(rows[points[a]['id']]['roadY']-rows[points[b]['id']]['roadY'])/abs(a[2]-b[2]) for a,b in zip(road,road[1:]))
   wet=[k for k in under if rows[points[k]['id']]['depth']>0]
   if not wet:raise ValueError('no wet surface samples')
   err=max(abs(rows[points[k]['id']]['surface']-points[k]['level']) for k in wet)
   return dict(max_step_per_m=round(step,3),under_level_err=round(err,3),wet=len(wet),under=len(under))
  b=metrics(old,br);c=metrics(new,cr);why=[]
  if c['max_step_per_m']>b['max_step_per_m']:why.append('road step worsened')
  if c['under_level_err']>b['under_level_err']:why.append('water level error worsened')
  new_dry=[new[k]['id'] for k in under if br[old[k]['id']]['depth']>0 and cr[new[k]['id']]['depth']<=0]
  new_sea=[new[k]['id'] for k in under if not br[old[k]['id']]['sea'] and cr[new[k]['id']]['sea']]
  if new_dry:why.append('previously wet under-bridge points became dry')
  if new_sea:why.append('new sea flag under bridge')
  sites[site]=dict(baseline=b,current=c,new_dry=new_dry,new_sea=new_sea,failures=why)
  if why:fail.append(site)
 return dict(status='PASS' if not fail else 'FAIL',failed_sites=fail,sites=sites,scope='No regression against actual EV110; strict current wetness/traversability and other families must also pass.')

def main():
 a=list(map(Path,sys.argv[1:6]));bp,bl,cp,cl,out=a
 try:
  b=json.loads(bp.read_text());c=json.loads(cp.read_text());r=judge(b,load_rows(bl,b),c,load_rows(cl,c))
 except (ValueError,KeyError,TypeError,IndexError,ZeroDivisionError) as e:r=dict(status='FAIL',invalid_input=str(e))
 r['inputs']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in a[:4]};r['tool_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();out.write_bytes((json.dumps(r,indent=2)+'\n').encode());print(r['status'],r.get('failed_sites',r.get('invalid_input')),flush=True);return int(r['status']!='PASS')
if __name__=='__main__':sys.exit(main())
