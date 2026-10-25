"""All 33 approved dry-bed cells must carry the final renderer's pixels.

Selection is from the approved dam contract, not the patch's manifest or vertex
marks. Reference uses the standard renderer directly with the bound final
footprint, without the patch/compositor. G5 separately binds these PNGs to PBO
bytes through ImageToPAA. This is composition coverage, not independent proof
of the renderer's colour model.
"""
import sys,json,subprocess
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).parent))
import gate_lib as G
from surface_scope_b import binding

def main():
 d=binding();e=d['explicit_native_cells'];cells=np.load(e['path']);tiles=G.tiles_touched(cells,False)
 f=G.OUT/'fp-ev112-c/footprint.npz';plane=np.load(f)['plane'];out=G.GATES/'g6-dam-reference';out.mkdir(parents=True,exist_ok=False)
 np.save(out/'plane.npy',plane)
 cmd=[G.PY,'-I',str(G.TOOLS/'build_surface_v30.py'),G.target_terrain(),str(out/'render'),'--tiles',';'.join(f'{a},{b}' for a,b in tiles),'--workers','2',*G.FLAGS,'--water-plane',str(out/'plane.npy'),'--water-plane-sha256',G.sha(out/'plane.npy'),'--road-off-lowered',G.EV95_TERRAIN,'--forest-clearings',d['clearings']['path'],'--forest-clearings-sha256',d['clearings']['sha256']]
 r=subprocess.run(cmd,capture_output=True,text=True);(out/'render.log').write_text(r.stdout+r.stderr);assert r.returncode==0
 ev95=G.Pbo(G.EV95_PBO);m=G.manifest();recs={tuple(v['tile']):v for v in m['records']};rows=[];negative=False;seen=np.zeros_like(cells)
 for a,b in tiles:
  domain=G.tile_domain(cells,a,b);X,Z=G.tile_xz(a,b);rr,cc=G.cell_of(X,Z);seen[rr[domain],cc[domain]]=True
  for prefix,stem in G.stems(a,b).items():
   ref=G.load_png(out/'render/layers'/f'{stem}.png');rec=recs.get((a,b));shipped=ev95.read(G.layer_entry(stem));base=G.load_png(G.source_png(stem,shipped))
   actual=G.load_png(G.PATCH/'layers'/f'{stem}.png') if rec and rec['layers'][prefix]['changed_px'] else base
   wrong=int(((actual!=ref).any(-1)&domain).sum());old_wrong=int(((base!=ref).any(-1)&domain).sum())
   if not negative:
    broken=actual.copy();i,j=np.argwhere(domain)[0];broken[i,j,0]^=1
    negative=bool(((broken!=ref).any(-1)&domain).any())
   rows.append(dict(tile=[a,b],layer=prefix,domain_pixels=int(domain.sum()),wrong_pixels=wrong,unpatched_wrong_pixels=old_wrong,in_manifest=rec is not None))
 ok=not(cells&~seen).any() and all(v['wrong_pixels']==0 and v['in_manifest'] for v in rows) and negative
 G.verdict('G6_dry_dam_bed',ok,dict(cells=int(cells.sum()),covered_cells=int((cells&seen).sum()),negative_corrupt_pixel_rejected=negative,reference_command=cmd,rows=rows,scope=__doc__))
 sys.exit(0 if ok else 1)

if __name__=='__main__':main()
