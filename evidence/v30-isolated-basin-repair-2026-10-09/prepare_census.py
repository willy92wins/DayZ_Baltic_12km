from pathlib import Path
B=Path(__file__).parent;R=Path('E:/DayZ-Baltic-Build');old=R/'v30-low-dry-surface-census-20261009';out=B/'risk-census';out.mkdir(exist_ok=False)
code=(old/'census_low_dry.py').read_text()
code=code.replace("SOURCE=R/'v30-native-hinge-finish-20261009/candidate/terrain.npz';PFILE=R/'v30-global-water-risk-20261009/frozen-field-reference/plane.npy';FFILE=R/'v30-frozen-water-stitch-20261009/preserved-field.npy'","SOURCE=B.parent/'candidate/terrain.npz';PFILE=B.parent/'candidate/plane.npy';FFILE=B.parent/'candidate/visible-field.npy'")
code=code.replace('fb36ec4c2203b6c936c8823078250f71082fbf43d9b1ba410049f735f890a0e6','73f4cc82192a6042eee30da3e1aeca90b0c4fb578f0ac9e38e31b3a8852556d2')
begin=code.index(' # The marked dry point');end=code.index(' np.savez_compressed',begin)
code=code[:begin]+''' # The reported point is allowed to leave the low-elevation risk band after repair.
 x,z=2718.4852496,6812.812874;r,c=int((12282-z)//6),int(x//6);aa,bb=x/6-c,(12282-z)/6-r;face=0 if aa>=bb else 1;weights=np.array([1-aa,aa-bb,bb]) if face==0 else np.array([1-bb,bb-aa,aa]);idx=int(lookup[r,c]);hc=np.array([h[r,c],h[r,c+1],h[r+1,c],h[r+1,c+1]])
 target=dict(x=x,z=z,height_m=float(weights@hc[CORNERS[face]]),inside_elevation_risk_band=bool(idx>=0 and np.all(constraints[idx][:,CORNERS[face]]@weights>0)))
'''+code[end:]
code=code.replace("archived_conditional_alerts=dict(total=len(q),inside_low_dry_band=int(matches.sum()),fraction=float(matches.mean())),",'')
code=code.replace(",R/'v30-georeferenced-render-audit-20261009/temporal-analysis.json'",'')
code=code.replace("'Archived image correspondence remains conditional on native projection confirmation.',",'')
(out/'census_low_dry.py').write_text(code)
v=(old/'verify_low_dry.py').read_text().replace("R/'v30-native-hinge-finish-20261009/candidate/terrain.npz'","B.parent/'candidate/terrain.npz'").replace("R/'v30-global-water-risk-20261009/frozen-field-reference/plane.npy'","B.parent/'candidate/plane.npy'").replace("R/'v30-frozen-water-stitch-20261009/preserved-field.npy'","B.parent/'candidate/visible-field.npy'")
(out/'verify_low_dry.py').write_text(v)
