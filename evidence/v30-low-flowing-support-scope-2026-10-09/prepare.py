from pathlib import Path
B=Path(__file__).parent;R=B.parent
s=(R/'v30-isolated-basin-scope-20261009/discover.py').read_text()
s=s.replace("R/'v30-native-hinge-finish-20261009/candidate/terrain.npz'","R/'v30-strict-dry-composition-20261009/candidate/terrain.npz'").replace("R/'v30-global-water-risk-20261009/frozen-field-reference/plane.npy'","R/'v30-strict-dry-composition-20261009/candidate/plane.npy'")
old="target={i for i,r in physical.items() if float(r['area_m2'])>=1 and r['has_flowing']=='False' and float(r['below_sea_crest_m2'])>=1}"
assert old in s;s=s.replace(old,"target={95,594,693}")
s=s.replace("eligible=not(engineering.any() or flow or large or (core&other).any())","eligible=not(engineering.any() or large or (core&other).any())")
s=s.replace('READ_ONLY_LEVEL_POLICY_SCOPE_NO_TERRAIN_EDIT','READ_ONLY_FLOWING_SUPPORT_SCOPE_NO_TERRAIN_EDIT').replace("'target_standing_components'","'target_flowing_components'")
(B/'discover.py').write_text(s)
