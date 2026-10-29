"""Independent source walker: planar line arrangement and cell classification."""
import sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import selected_water_io_q03c1 as I
from fractions import Fraction as F
def determinant(a,b,c,d,q):return q.sub(q.mul(a,d),q.mul(b,c))
def polygon_area(v,q):
 if len(v)<3:return F(0)
 terms=[];origin=v[0]
 for i in range(len(v)):
  a=v[i];b=v[(i+1)%len(v)];terms.append(determinant(q.sub(a[0],origin[0]),q.sub(a[1],origin[1]),q.sub(b[0],origin[0]),q.sub(b[1],origin[1]),q))
 return q.div(abs(q.sum(terms)),F(2))
def projected(tri,q):
 xs=[q.val(p[0]) for p in tri];zs=[q.val(p[2]) for p in tri];ys=[q.val(p[1]) for p in tri]
 det=determinant(q.sub(xs[1],xs[0]),q.sub(zs[1],zs[0]),q.sub(xs[2],xs[0]),q.sub(zs[2],zs[0]),q)
 if det==0:return list(zip(xs,zs)),None,[]
 dy1=q.sub(ys[1],ys[0]);dy2=q.sub(ys[2],ys[0]);dx1=q.sub(xs[1],xs[0]);dx2=q.sub(xs[2],xs[0]);dz1=q.sub(zs[1],zs[0]);dz2=q.sub(zs[2],zs[0])
 x=q.div(determinant(dy1,dz1,dy2,dz2,q),det);z=q.div(determinant(dx1,dy1,dx2,dy2,q),det);const=q.sub(ys[0],q.add(q.mul(x,xs[0]),q.mul(z,zs[0])))
 points=list(zip(xs,zs));lines=[]
 for i in range(3):
  j=(i+1)%3;ax=q.sub(zs[i],zs[j]);az=q.sub(xs[j],xs[i]);ac=q.sub(q.mul(xs[i],zs[j]),q.mul(xs[j],zs[i]))
  lines.append((ax,az,ac) if det>0 else (-ax,-az,-ac))
 return points,(x,z,const),lines
def evaluate(l,v,q):return q.add(q.add(q.mul(l[0],v[0]),q.mul(l[1],v[1])),l[2])
def half(v,l,q,sign=1,held=(0,0)):
 q.reserve(held[0]+2,held[1]+3*len(v)+2)
 if not v:return []
 out=[];last=v[-1];a=evaluate(l,last,q);a=a if sign>0 else -a
 for point in v:
  b=evaluate(l,point,q);b=b if sign>0 else -b
  if (a<0<b) or (b<0<a):
   ratio=q.div(a,q.sub(a,b));hit=tuple(q.add(last[k],q.mul(ratio,q.sub(point[k],last[k]))) for k in range(2));out.append(hit)
  if b>=0:out.append(point)
  last=point;a=b
 result=[]
 for p in out:
  if not result or result[-1]!=p:result.append(p)
 if len(result)>1 and result[0]==result[-1]:result.pop()
 return result
def normalized(l,q):
 if l[0]==0 and l[1]==0:return None
 multiple=1
 for a in l:
  d=a.denominator;g=math.gcd(multiple,d);v=multiple//g;q.tick();q.bound(v.bit_length()+d.bit_length());multiple=v*d
 ns=[]
 for a in l:
  scale=multiple//a.denominator;q.tick();q.bound(abs(a.numerator).bit_length()+scale.bit_length());ns.append(a.numerator*scale)
 g=math.gcd(*ns);ns=[n//g for n in ns]
 if next(n for n in ns if n)!=abs(next(n for n in ns if n)):ns=[-n for n in ns]
 return tuple(ns)
class Prepared:
 def __init__(self,waters):
  I.need(len(waters)<=4760,'GEOMETRY');self.rows=[]
  for w in sorted(waters,key=lambda w:(w['key'][0],w['key'][1])):
   I.key_ok(w['key']);I.validate_face(w['triangle']);xs=[p[0] for p in w['triangle']];zs=[p[2] for p in w['triangle']]
   self.rows.append((w,min(xs),max(xs),min(zs),max(zs)))
def measure(row,waters,limits=None):
 q=I.Budget(limits);key=row['key'];I.key_ok(key);I.validate_face(row['triangle'])
 try:
  bed,bplane,blines=projected(row['triangle'],q)
  if bplane is None:return I.result(key,q,'DEGENERATE_PROJECTION')
  x=[p[0] for p in row['triangle']];z=[p[2] for p in row['triangle']];x0,x1,z0,z1=min(x),max(x),min(z),max(z)
  active=[];all_lines=set();pairs=[];contacts=[]
  prepared=waters if isinstance(waters,Prepared) else Prepared(waters)
  for w,wx0,wx1,wz0,wz1 in prepared.rows:
   if wx1<x0 or wx0>x1 or wz1<z0 or wz0>z1:continue
   p,wp,lines=projected(w['triangle'],q)
   if wp is None:return I.result(key,q,'INCONCLUSIVE_GEOMETRY',detail='DEGENERATE_WATER_AABB_CANDIDATE')
   common=bed
   for line in lines:common=half(common,line,q)
   ar=polygon_area(common,q)
   if ar==0:
    if common:contacts.append(w['key'])
    continue
   delta=tuple(q.sub(a,b) for a,b in zip(wp,bplane));values=[evaluate(delta,p,q) for p in common];low=high=values[0]
   for v in values[1:]:
    if q.cmp(v,low)<0:low=v
    if q.cmp(v,high)>0:high=v
   pairs.append({'water':w['key'],'area':I.pack(ar),'min_W_B':I.pack(low),'max_W_B':I.pack(high)})
   active.append((lines,delta))
   for line in (*lines,delta):
    line=normalized(line,q)
    if line is not None:all_lines.add(line)
  cells=[bed]
  for raw in sorted(all_lines):
   line=tuple(F(n) for n in raw);next_cells=[];held_vertices=sum(map(len,cells))
   for cell in cells:
    vals=[evaluate(line,v,q) for v in cell]
    if not (any(v>0 for v in vals) and any(v<0 for v in vals)):
     q.reserve(len(cells)+len(next_cells)+1,held_vertices+sum(map(len,next_cells))+len(cell));next_cells.append(cell);continue
    for sign in (1,-1):
     part=half(cell,line,q,sign,(len(cells)+len(next_cells),held_vertices+sum(map(len,next_cells))))
     if part and polygon_area(part,q)>0:
      q.reserve(len(cells)+len(next_cells)+1,held_vertices+sum(map(len,next_cells))+len(part));next_cells.append(part)
   cells=next_cells
  areas=[F(0),F(0),F(0)]
  for cell in cells:
   center=tuple(q.div(q.sum(v[k] for v in cell),F(len(cell))) for k in (0,1));has_foot=has_cover=False
   for lines,delta in active:
    if all(evaluate(l,center,q)>=0 for l in lines):
     has_foot=True
     if evaluate(delta,center,q)>=0:has_cover=True
   slot=0 if has_cover else 1 if has_foot else 2;areas[slot]=q.add(areas[slot],polygon_area(cell,q))
  I.need(q.sum(areas)==polygon_area(bed,q),'INTERNAL_ERROR','cell partition')
  return I.result(key,q,'DEFINED',[I.pack(a) for a in areas],pairs,contacts)
 except I.Rejected as e:
  if e.code=='RESOURCE_INCONCLUSIVE':return I.result(key,q,'RESOURCE_INCONCLUSIVE',detail=str(e))
  raise
def verify_rows(rows,bed,water):
 I.need(len(rows)<=len(bed),'REPORT');verified=0;unverified=0;states={};prepared=Prepared(water)
 for i,record in enumerate(rows):
  claimed=I.semantic(record);I.need(I.exact(record['key'],bed[i]['key']),'REPORT','key')
  actual=measure(bed[i],prepared)
  if actual['status']=='RESOURCE_INCONCLUSIVE' or record['status']=='RESOURCE_INCONCLUSIVE':
   I.need(record['status'] in ('DEFINED','RESOURCE_INCONCLUSIVE'),'REPORT');unverified+=1
  else:I.need(I.exact(claimed,I.semantic(actual)),'REPORT','geometric mismatch');verified+=int(actual['status']=='DEFINED')
  states[record['status']]=states.get(record['status'],0)+1
 return verified,unverified,states
def main():
 a=I.arguments(True);c,sealed=I.config(a.contract,a.sha);bed,water,inventory=I.data(c,sealed,a)
 header=I.parse(I.read(Path(a.capture)/'header.json',cap=c['limits']['output']))
 expected={'schema':'q03c1-capture-v1','contract_sha256':a.sha,'inventory':inventory,'bed_count':len(bed),'water_count':len(water),'claims':I.CLAIMS}
 I.need(I.exact(header,expected),'REPORT','header')
 rows=I.prefix(a.capture,c['limits']['output']);verified,unverified,states=verify_rows(rows,bed,water)
 manifest=Path(a.capture)/'manifest.json'
 if manifest.exists():
  m=I.parse(I.read(manifest));want={'status':'MEASURED_SELECTED_WATER_OVERLAY_ONLY' if states.get('DEFINED',0)==len(bed) else 'VERIFIED_PARTIAL_OVERLAY','terminals':len(bed),'states':states,'contract_sha256':a.sha,'claims':I.CLAIMS}
  I.need(len(rows)==len(bed) and I.exact(m,want),'REPORT','manifest')
 full=verified==len(bed) and unverified==0 and manifest.exists()
 out=I.Output(a.out,c['limits']['output']);out.write('consumer.json',{'status':'MEASURED_SELECTED_WATER_OVERLAY_ONLY' if full else 'VERIFIED_PARTIAL_OVERLAY','contract_sha256':a.sha,'terminals':len(rows),'verified_numeric':verified,'unverified_numeric':unverified,'expected_faces':len(bed),'claims':I.CLAIMS})
if __name__=='__main__':I.main_guard(main)
