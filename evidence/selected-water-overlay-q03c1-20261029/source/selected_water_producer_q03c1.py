"""Exact selected-water union by convex subtraction. No consumer geometry."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import selected_water_io_q03c1 as I
from fractions import Fraction as F
def cross(a,b,q):return q.sub(q.mul(a[0],b[1]),q.mul(a[1],b[0]))
def vector(a,b,q):return (q.sub(a[0],b[0]),q.sub(a[1],b[1]))
def area(p,q):
 if len(p)<3:return F(0)
 total=q.sum(cross(vector(p[i],p[0],q),vector(p[i+1],p[0],q),q) for i in range(1,len(p)-1))
 return q.div(abs(total),F(2))
def projection(tri,q):
 p=[(q.val(v[0]),q.val(v[2])) for v in tri];y=[q.val(v[1]) for v in tri]
 d=cross(vector(p[1],p[0],q),vector(p[2],p[0],q),q)
 if d<0:p.reverse();y.reverse()
 return p,y,d
def affine(p,y,q):
 a=vector(p[1],p[0],q);b=vector(p[2],p[0],q);d=cross(a,b,q);u=q.sub(y[1],y[0]);v=q.sub(y[2],y[0])
 sx=q.div(q.sub(q.mul(u,b[1]),q.mul(v,a[1])),d);sz=q.div(q.sub(q.mul(a[0],v),q.mul(b[0],u)),d)
 return sx,sz,q.sub(q.sub(y[0],q.mul(sx,p[0][0])),q.mul(sz,p[0][1]))
def value(line,p,q):return q.add(q.add(q.mul(line[0],p[0]),q.mul(line[1],p[1])),line[2])
def edge(a,b,q):
 dx=q.sub(b[0],a[0]);dz=q.sub(b[1],a[1]);return -dz,dx,q.sub(q.mul(dz,a[0]),q.mul(dx,a[1]))
def clean(p):
 out=[]
 for v in p:
  if not out or v!=out[-1]:out.append(v)
 if len(out)>1 and out[0]==out[-1]:out.pop()
 return out
def clip(p,line,q,positive=True,held=(0,0)):
 q.reserve(held[0]+2,held[1]+3*len(p)+2);out=[]
 if not p:return out
 vals=[value(line,v,q) for v in p]
 if not positive:vals=[-v for v in vals]
 for i,a in enumerate(p):
  j=(i+1)%len(p);va,vb=vals[i],vals[j]
  if va>=0:out.append(a)
  if (va<0<vb) or (vb<0<va):
   t=q.div(va,q.sub(va,vb));out.append(tuple(q.add(a[k],q.mul(q.sub(p[j][k],a[k]),t)) for k in (0,1)))
 return clean(out)
def intersection(p,t,q,held=(0,0)):
 out=p
 for i in range(3):out=clip(out,edge(t[i],t[(i+1)%3],q),q,held=held)
 return out
def subtract(rest,cut,q,outer=(0,0)):
 if not cut or area(cut,q)==0:return rest
 output=[];total_vertices=sum(map(len,rest));remaining=len(rest)
 for part in rest:
  remaining-=1;total_vertices-=len(part);inside=part
  for i,a in enumerate(cut):
   if not inside:break
   held=(outer[0]+remaining+len(output)+2,outer[1]+total_vertices+sum(map(len,output))+len(cut)+len(part))
   l=edge(a,cut[(i+1)%len(cut)],q);out=clip(inside,l,q,False,held)
   # When a line coincides with the whole polygon, only the inside continues.
   if out and area(out,q)>0:
    q.reserve(held[0]+2,held[1]+len(out)+len(inside));output.append(out)
   inside=clip(inside,l,q,True,(held[0]+1,held[1]+len(out)))
  q.reserve(outer[0]+len(output)+remaining+2,outer[1]+sum(map(len,output))+total_vertices+len(cut)+len(part))
 return output
def bbox(t):return (min(v[0] for v in t),min(v[2] for v in t),max(v[0] for v in t),max(v[2] for v in t))
class Prepared:
 def __init__(self,waters):
  I.need(len(waters)<=4760,'GEOMETRY');self.rows=[]
  for w in sorted(waters,key=lambda w:(w['key'][0],w['key'][1])):
   I.key_ok(w['key']);I.validate_face(w['triangle']);self.rows.append((w,bbox(w['triangle'])))
def candidates(tri,waters):
 b=bbox(tri);out=[]
 prepared=waters if isinstance(waters,Prepared) else Prepared(waters)
 for w,a in prepared.rows:
  if a[0]<=b[2] and b[0]<=a[2] and a[1]<=b[3] and b[1]<=a[3]:out.append(w)
 return sorted(out,key=lambda w:(w['key'][0],w['key'][1]))
def measure(row,waters,limits=None):
 q=I.Budget(limits);key=row['key'];I.key_ok(key);I.validate_face(row['triangle'])
 try:
  p,y,d=projection(row['triangle'],q)
  if d==0:return I.result(key,q,'DEGENERATE_PROJECTION')
  plane=affine(p,y,q);foot=[p];cover=[p];total=area(p,q);pair_rows=[];contacts=[]
  for w in candidates(row['triangle'],waters):
   I.key_ok(w['key']);I.validate_face(w['triangle']);t,wy,det=projection(w['triangle'],q)
   if det==0:return I.result(key,q,'INCONCLUSIVE_GEOMETRY',detail='DEGENERATE_WATER_AABB_CANDIDATE')
   part=intersection(p,t,q,(len(foot)+len(cover)+2,sum(map(len,foot))+sum(map(len,cover))+len(p)+len(t)));ar=area(part,q)
   if not ar:
    if part:contacts.append(w['key'])
    continue
   wp=affine(t,wy,q);delta=tuple(q.sub(a,b) for a,b in zip(wp,plane));vals=[value(delta,z,q) for z in part]
   lo=hi=vals[0]
   for v in vals[1:]:
    if q.cmp(v,lo)<0:lo=v
    if q.cmp(v,hi)>0:hi=v
   pair_rows.append({'water':w['key'],'area':I.pack(ar),'min_W_B':I.pack(lo),'max_W_B':I.pack(hi)})
   q.reserve(len(foot)+len(cover)+4,sum(map(len,foot))+sum(map(len,cover))+len(part)+12)
   foot=subtract(foot,part,q,(len(cover)+1,sum(map(len,cover))+len(p)))
   above=clip(part,delta,q,held=(len(foot)+len(cover)+1,sum(map(len,foot))+sum(map(len,cover))+len(p)))
   cover=subtract(cover,above,q,(len(foot)+2,sum(map(len,foot))+len(p)+len(part)))
  uncovered=q.sum(area(v,q) for v in cover);nofoot=q.sum(area(v,q) for v in foot)
  covered=q.sub(total,uncovered);below=q.sub(uncovered,nofoot)
  I.need(nofoot>=0 and q.cmp(nofoot,uncovered)<=0 and q.cmp(uncovered,total)<=0,'INTERNAL_ERROR','remainder bounds')
  return I.result(key,q,'DEFINED',[I.pack(x) for x in (covered,below,nofoot)],pair_rows,contacts)
 except I.Rejected as e:
  if e.code=='RESOURCE_INCONCLUSIVE':return I.result(key,q,'RESOURCE_INCONCLUSIVE',detail=str(e))
  raise
def main():
 a=I.arguments();c,sealed=I.config(a.contract,a.sha);bed,water,inventory=I.data(c,sealed,a);prepared=Prepared(water)
 out=I.Output(a.out,c['limits']['output']);out.write('header.json',{'schema':'q03c1-capture-v1','contract_sha256':a.sha,'inventory':inventory,'bed_count':len(bed),'water_count':len(water),'claims':I.CLAIMS})
 states={}
 for i,row in enumerate(bed):
  r=measure(row,prepared);out.terminal(i,r);states[r['status']]=states.get(r['status'],0)+1
 full=states.get('DEFINED',0)==len(bed)
 out.write('manifest.json',{'status':'MEASURED_SELECTED_WATER_OVERLAY_ONLY' if full else 'VERIFIED_PARTIAL_OVERLAY','terminals':len(bed),'states':states,'contract_sha256':a.sha,'claims':I.CLAIMS})
if __name__=='__main__':I.main_guard(main)
