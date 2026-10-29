"""Terrain triangle clipping and successive subtraction of selected water unions."""
from pathlib import Path
import sys,math
sys.path.insert(0,str(Path(__file__).parent))
import terrain_water_io_q03c2r1 as S
I,F=S.I,S.F
P=S.geometry('selected_water_producer_q03c1.py')
def remainder_bounds(q,nofoot,uncovered,regarea):
 I.need(q.cmp(nofoot,F(0))>=0 and q.cmp(uncovered,nofoot)>=0 and q.cmp(regarea,uncovered)>=0,'INTERNAL_ERROR','water remainders')

def measure(row,prepared,grid,limits=None):
 q=S.Budget(limits);key=row['key'];I.key_ok(key);I.validate_face(row['triangle'])
 I.need(all(0<=v[0]<=grid.top and 0<=v[2]<=grid.top for v in row['triangle']),'GEOMETRY','outside source grid')
 try:
  q.reserve(5,24);bed,by,det=P.projection(row['triangle'],q)
  if det==0:return S.record(key,q,'DEGENERATE_PROJECTION')
  bp=P.affine(bed,by,q);total=P.area(bed,q);active=[];water_contacts=[];box=P.bbox(row['triangle'])
  for w,bbox in prepared.rows:
   if bbox[0]>box[2] or box[0]>bbox[2] or bbox[1]>box[3] or box[1]>bbox[3]:continue
   q.hold(len(active)+len(water_contacts)+1,len(active)*3+3);q.reserve(6,24)
   t,y,d=P.projection(w['triangle'],q)
   if d==0:return S.record(key,q,'INCONCLUSIVE_GEOMETRY',detail='DEGENERATE_WATER_AABB_CANDIDATE')
   common=P.intersection(bed,t,q)
   if P.area(common,q)==0:
    if common:q.reserve(1,0);water_contacts.append(w['key'])
    continue
   wp=P.affine(t,y,q);delta=tuple(q.sub(a,b) for a,b in zip(wp,bp));q.reserve(1,3);active.append((t,delta))
  xmin=min(x for x,z in bed);xmax=max(x for x,z in bed);zmin=min(z for x,z in bed);zmax=max(z for x,z in bed);step=F(grid.step);top=F(grid.top)
  c0=max(0,math.floor(q.div(xmin,step))-1);c1=min(grid.n-2,math.floor(q.div(xmax,step)))
  r0=max(0,math.floor(q.div(q.sub(top,zmax),step))-1);r1=min(grid.n-2,math.floor(q.div(q.sub(top,zmin),step)))
  cellcount=(c1-c0+1)*(r1-r0+1);I.need(cellcount<=1024,'RESOURCE_INCONCLUSIVE','terrain cells');areas=[F(0)]*9;parts=[];contacts=[];covered=F(0)
  def hold():q.hold(cellcount+len(active)+len(parts)+len(contacts)+len(water_contacts)+2,len(active)*3+3)
  for r in range(r0,r1+1):
   for c in range(c0,c1+1):
    hold();q.reserve(8,36)
    vertices=[[grid.step*(c+dc),float(grid.h[r+dr,c+dc]),grid.top-grid.step*(r+dr)] for dr,dc in ((0,0),(0,1),(1,0),(1,1))]
    for ti,indices in enumerate(((0,1,3),(0,2,3))):
     t,hy,hd=P.projection([vertices[i] for i in indices],q);common=P.intersection(bed,t,q);ar=P.area(common,q)
     if not ar:
      if common:hold();q.reserve(1,0);contacts.append([r,c,ti])
      continue
     hp=P.affine(t,hy,q);delta=tuple(q.sub(a,b) for a,b in zip(bp,hp));values=[P.value(delta,v,q) for v in common];lo=hi=values[0]
     for v in values[1:]:
      if q.cmp(v,lo)<0:lo=v
      if q.cmp(v,hi)>0:hi=v
     hold();q.reserve(1,0);parts.append({'cell':[r,c,ti],'area':I.pack(ar),'min_B_H':I.pack(lo),'max_B_H':I.pack(hi)});covered=q.add(covered,ar)
     hold();q.reserve(4,4*len(common)+12)
     regions=[(1,common)] if all(x==0 for x in delta) else [(0,P.clip(common,delta,q)),(2,P.clip(common,delta,q,False))]
     for slot,region in regions:
      regarea=P.area(region,q)
      if regarea==0:continue
      foot=[region];cover=[region];region_hold=sum(len(v) for _,v in regions)+len(common)+12
      for wt,wd in active:
       outer=(len(regions)+len(foot)+len(cover)+3,region_hold+sum(map(len,foot))+sum(map(len,cover)))
       part=P.intersection(region,wt,q,outer)
       if P.area(part,q)==0:continue
       foot=P.subtract(foot,part,q,(len(cover)+len(regions)+3,sum(map(len,cover))+region_hold))
       above=P.clip(part,wd,q,held=(len(foot)+len(cover)+len(regions)+3,sum(map(len,foot))+sum(map(len,cover))+region_hold))
       cover=P.subtract(cover,above,q,(len(foot)+len(regions)+4,sum(map(len,foot))+region_hold+len(part)))
      uncovered=q.sum(P.area(v,q) for v in cover);nofoot=q.sum(P.area(v,q) for v in foot)
      remainder_bounds(q,nofoot,uncovered,regarea)
      values=(q.sub(regarea,uncovered),q.sub(uncovered,nofoot),nofoot)
      for k,v in enumerate(values):areas[slot*3+k]=q.add(areas[slot*3+k],v)
      foot=[];cover=[];part=[];above=[]
     regions=[];common=[]
  I.need(q.cmp(covered,total)==0 and q.cmp(q.sum(areas),total)==0,'INTERNAL_ERROR','terrain partition')
  return S.record(key,q,'DEFINED',[I.pack(a) for a in areas],parts,contacts,water_contacts,water_marginal=[I.pack(q.sum(areas[k::3])) for k in range(3)])
 except I.Rejected as e:
  if e.code=='RESOURCE_INCONCLUSIVE':return S.record(key,q,e.code,detail=str(e))
  raise
def main():
 a=S.arguments();c,old,m=S.config(a.contract,a.sha);beds,waters,grid,inventory,marginals=S.data(c,old,m,a);prepared=P.Prepared(waters);out=I.Output(a.out,c['limits']['output']);out.write('header.json',S.header(a.sha,inventory,len(beds),len(waters),bool(a.fixture)));states={}
 for i,bed in enumerate(beds):
  row=measure(bed,prepared,grid);S.semantic(row);S.check_marginal(row,None if marginals is None else marginals[i]);out.terminal(i,row);states[row['status']]=states.get(row['status'],0)+1
 full=states.get('DEFINED',0)==len(beds)
 out.write('manifest.json',{'status':'MEASURED_SOURCE_TERRAIN_SELECTED_WATER_ONLY' if full else 'VERIFIED_PARTIAL_SOURCE_PARTITION','terminals':len(beds),'states':states,'contract_sha256':a.sha,'fixture':bool(a.fixture),'terrain_source_evaluated':full,'claims':dict(S.CLAIMS)})
if __name__=='__main__':I.main_guard(main)
