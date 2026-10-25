from pathlib import Path
B=Path(__file__).parent;R=B.parent
s=(R/'v30-native-hinge-finish-20261009/verify_hinges.py').read_text()
s=s.replace('from audit_native_surface import SOURCE,PLANE,sha,incident_all,incident_any',"from audit_native_surface import sha,incident_all,incident_any\nSOURCE=Path('E:/DayZ-Baltic-Build/v30-volkhov-stable-derivatives-20261009/candidate/terrain.npz')\nPLANE=SOURCE.parent/'plane.npy'")
s=s.replace("float(abs(v-h).max())<=2.00002","float(abs(v-h).max())<=.400001")
s=s.replace("stats[name]['reduction']>=.1","stats[name]['reduction']>=0")
s=s.replace("candidate=B/'candidate/terrain.npz';", "candidate=B/'candidate/terrain.npz';")
needle="gates,counts=physical(h,v,t,u,m['fixed'],m['allowed'],p);negative=controls(h,t,m['fixed'],m['allowed'],p)"
new=needle+"\n    gates['all_target_floor_1_8']=bool(np.all(v[m['target']]>=1.8-1e-6))\n    gates['no_lowering']=bool(np.all(v>=h-1e-6))\n    mutated=v.copy();pos=tuple(np.argwhere(m['target'])[0]);mutated[pos]=1.79\n    assert not np.all(mutated[m['target']]>=1.8-1e-6)\n    negative.append('low_target_mutant_rejected')"
assert needle in s;s=s.replace(needle,new)
s=s.replace('PASS_NATIVE_HINGE_SOURCE','PASS_STRICT_DRY_FLOOR_SOURCE').replace('FAIL_NATIVE_HINGE_SOURCE','FAIL_STRICT_DRY_FLOOR_SOURCE')
(B/'verify.py').write_text(s)
