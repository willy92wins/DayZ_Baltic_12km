"""Own cell walk, halfplane arrangement, interior point classification."""
from pathlib import Path
import sys,math,itertools
sys.path.insert(0,str(Path(__file__).parent))
import terrain_water_io_q03c2r1 as S
I,F=S.I,S.F
C=S.geometry('selected_water_consumer_q03c1.py')
def measure(row,prepared,grid,limits=None):
 q=S.Budget(limits);key=row['key'];I.key_ok(key);I.validate_face(row['triangle']);top=(grid.n-1)*grid.step
 I.need(all(0<=point[0]<=top and 0<=point[2]<=top for point in row['triangle']),'GEOMETRY','outside source grid')
 try:
  q.reserve(5,24);bed,bp,blines=C.projected(row['triangle'],q)
  if bp is None:return S.record(key,q,'DEGENERATE_PROJECTION')
  xs=[v[0] for v in bed];zs=[v[1] for v in bed];xmin,xmax,zmin,zmax=min(xs),max(xs),min(zs),max(zs);active=[];water_contacts=[]
  for w,wx0,wx1,wz0,wz1 in prepared.rows:
   if wx1<xmin or wx0>xmax or wz1<zmin or wz0>zmax:continue
   q.hold(len(active)+len(water_contacts)+1,len(active)*6+3);q.reserve(6,24)
   pts,wp,lines=C.projected(w['triangle'],q)
   if wp is None:return S.record(key,q,'INCONCLUSIVE_GEOMETRY',detail='DEGENERATE_WATER_AABB_CANDIDATE')
   common=bed
   for line in lines:common=C.half(common,line,q)
   if C.polygon_area(common,q)==0:
    if common:q.reserve(1,0);water_contacts.append(w['key'])
    continue
   delta=tuple(q.sub(a,b) for a,b in zip(wp,bp));q.reserve(1,6);active.append((lines,delta))
  # Independent exact ceil/floor range; no producer candidates or cells used.
  first_col=max(0,math.ceil(q.div(xmin,F(grid.step)))-1);last_col=min(grid.n-2,math.floor(q.div(xmax,F(grid.step))))
  first_row=max(0,math.ceil(q.div(q.sub(F(top),zmax),F(grid.step)))-1);last_row=min(grid.n-2,math.floor(q.div(q.sub(F(top),zmin),F(grid.step))))
  count=(last_col-first_col+1)*(last_row-first_row+1);I.need(count<=1024,'RESOURCE_INCONCLUSIVE','terrain cells');parts=[];contacts=[];areas=[F(0)]*9;terrain_area=F(0)
  def hold(extra=0,vertices=0):q.hold(count+len(active)+len(parts)+len(contacts)+len(water_contacts)+extra+2,len(active)*6+vertices+3)
  for rr in range(first_row,last_row+1):
   for cc in range(first_col,last_col+1):
    hold();q.reserve(8,36)
    west,east=cc*grid.step,(cc+1)*grid.step;north,south=top-rr*grid.step,top-(rr+1)*grid.step
    nw=[west,float(grid.h[rr,cc]),north];ne=[east,float(grid.h[rr,cc+1]),north];sw=[west,float(grid.h[rr+1,cc]),south];se=[east,float(grid.h[rr+1,cc+1]),south]
    for ti,triangle in enumerate(([nw,ne,se],[nw,sw,se])):
     tp,hp,tlines=C.projected(triangle,q);common=bed
     for line in tlines:common=C.half(common,line,q)
     ar=C.polygon_area(common,q)
     if ar==0:
      if common:hold();q.reserve(1,0);contacts.append([rr,cc,ti])
      continue
     delta=tuple(q.sub(a,b) for a,b in zip(bp,hp));vals=[C.evaluate(delta,v,q) for v in common];lo=hi=vals[0]
     for v in vals[1:]:
      if q.cmp(v,lo)<0:lo=v
      if q.cmp(v,hi)>0:hi=v
     hold();q.reserve(1,0);parts.append({'cell':[rr,cc,ti],'area':I.pack(ar),'min_B_H':I.pack(lo),'max_B_H':I.pack(hi)});terrain_area=q.add(terrain_area,ar)
     lineset=set()
     for raw in itertools.chain((delta,),(line for lines,d in active for line in (*lines,d))):
      normalized=C.normalized(raw,q)
      if normalized is not None:
       I.need(len(lineset)+(normalized not in lineset)<=1024,'RESOURCE_INCONCLUSIVE','lines');hold(len(lineset)+1,3*(len(lineset)+1)+len(common));lineset.add(normalized)
     hold(len(lineset)+2,3*len(lineset)+len(common));cells=[common]
     for raw in sorted(lineset):
      line=tuple(F(n) for n in raw);next_cells=[];held_vertices=sum(map(len,cells))
      for cell in cells:
       values=[C.evaluate(line,p,q) for p in cell]
       if not(any(v>0 for v in values) and any(v<0 for v in values)):
        q.reserve(len(cells)+len(next_cells)+1,held_vertices+sum(map(len,next_cells))+len(cell));next_cells.append(cell);continue
       for sign in (1,-1):
        part=C.half(cell,line,q,sign,(len(cells)+len(next_cells),held_vertices+sum(map(len,next_cells))))
        if part and C.polygon_area(part,q)>0:q.reserve(len(cells)+len(next_cells)+1,held_vertices+sum(map(len,next_cells))+len(part));next_cells.append(part)
      cells=next_cells
     q.reserve(len(cells),sum(map(len,cells)))
     for cell in cells:
      mid=tuple(q.div(q.sum(v[k] for v in cell),F(len(cell))) for k in (0,1));difference=C.evaluate(delta,mid,q)
      terrain_slot=0 if difference>0 else 2 if difference<0 else 1;foot=cover=False
      for lines,wd in active:
       if all(C.evaluate(line,mid,q)>=0 for line in lines):
        foot=True
        if C.evaluate(wd,mid,q)>=0:cover=True
      water_slot=0 if cover else 1 if foot else 2;slot=3*terrain_slot+water_slot;areas[slot]=q.add(areas[slot],C.polygon_area(cell,q))
     cells=[];next_cells=[];cell=[];part=[];common=[];lineset=set()
  total=C.polygon_area(bed,q);I.need(q.cmp(terrain_area,total)==0 and q.cmp(q.sum(areas),total)==0,'INTERNAL_ERROR','terrain partition')
  return S.record(key,q,'DEFINED',[I.pack(v) for v in areas],parts,contacts,water_contacts,water_marginal=[I.pack(q.sum(areas[k::3])) for k in range(3)])
 except I.Rejected as e:
  if e.code=='RESOURCE_INCONCLUSIVE':return S.record(key,q,e.code,detail=str(e))
  raise
def verify(rows,beds,waters,grid,marginals):
 I.need(len(rows)<=len(beds),'REPORT');prepared=C.Prepared(waters);verified=unverified=0;states={}
 for i,r in enumerate(rows):
  claim=S.semantic(r);I.need(I.exact(r['key'],beds[i]['key']),'REPORT','key');actual=measure(beds[i],prepared,grid)
  if r['status']=='RESOURCE_INCONCLUSIVE' or actual['status']=='RESOURCE_INCONCLUSIVE':I.need(r['status'] in ('DEFINED','RESOURCE_INCONCLUSIVE'),'REPORT');unverified+=1
  else:
   I.need(I.exact(claim,S.semantic(actual)),'REPORT','joint geometry');verified+=int(r['status']=='DEFINED')
  S.check_marginal(r,None if marginals is None else marginals[i]);S.check_marginal(actual,None if marginals is None else marginals[i]);states[r['status']]=states.get(r['status'],0)+1
 return verified,unverified,states
def main():
 a=S.arguments(True);c,old,m=S.config(a.contract,a.sha);beds,waters,grid,inventory,marginals=S.data(c,old,m,a);header=I.parse(I.read(Path(a.capture)/'header.json',cap=33554432));I.need(I.exact(header,S.header(a.sha,inventory,len(beds),len(waters),bool(a.fixture))),'REPORT','header')
 rows=I.prefix(a.capture,33554432);verified,unverified,states=verify(rows,beds,waters,grid,marginals);manifest=Path(a.capture)/'manifest.json'
 if manifest.exists():
  full=states.get('DEFINED',0)==len(beds);expected={'status':'MEASURED_SOURCE_TERRAIN_SELECTED_WATER_ONLY' if full else 'VERIFIED_PARTIAL_SOURCE_PARTITION','terminals':len(beds),'states':states,'contract_sha256':a.sha,'fixture':bool(a.fixture),'terrain_source_evaluated':full,'claims':dict(S.CLAIMS)};I.need(len(rows)==len(beds) and I.exact(I.parse(I.read(manifest)),expected),'REPORT','manifest')
 full=verified==len(beds) and unverified==0 and manifest.exists();out=I.Output(a.out,33554432);out.write('consumer.json',{'status':'MEASURED_SOURCE_TERRAIN_SELECTED_WATER_ONLY' if full else 'VERIFIED_PARTIAL_SOURCE_PARTITION','contract_sha256':a.sha,'terminals':len(rows),'verified_numeric':verified,'unverified_numeric':unverified,'expected_faces':len(beds),'fixture':bool(a.fixture),'terrain_source_evaluated':full,'claims':dict(S.CLAIMS)})
if __name__=='__main__':I.main_guard(main)
