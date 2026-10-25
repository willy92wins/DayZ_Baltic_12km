from pathlib import Path
B=Path(__file__).parent;R=B.parent;OLD=R/'v30-exact-dry-support-20261009'
code=(OLD/'author.py').read_text().replace('v30-strict-dry-composition-20261009/candidate','v30-exact-dry-support-20261009/candidate')
old="target=np.load(R/'v30-strict-dry-floor-20261009/constraints.npz')['target']&(original<1.79999)\nassert int(target.sum())==2197 and not (target&fixed).any()"
new="target=scope['editable']&~fixed&(original<1.79999)\nassert int(target.sum())==164 and not (target&fixed).any()"
assert old in code;code=code.replace(old,new).replace('7bcfae7662acf3f83ff0f52434a3d9c3f1e8af745574b2fdc3ad689db123a990','682d5553480e779cda1874725dd6a8a5a3615c356b65c546c77342f251857244')
assert 'maximum=original+.4' in code;code=code.replace('maximum=original+.4',"maximum=np.maximum(original,np.load(R/'v30-strict-dry-composition-20261009/candidate/terrain.npz')['heights'].astype(float)+.4)")
(B/'author.py').write_text(code)
code=(OLD/'verify.py').read_text().replace('v30-strict-dry-composition-20261009/candidate','v30-exact-dry-support-20261009/candidate')
needle="gates['no_lowering']=bool(np.all(v>=h-1e-6))";assert needle in code
code=code.replace(needle,needle+"\n    original=np.load(B.parent/'v30-strict-dry-composition-20261009/candidate/terrain.npz')['heights']\n    gates['cumulative_uplift_ev61']=bool(np.all(v<=original.astype(float)+.400001))")
(B/'verify.py').write_text(code)
print('EV71_PREPARED_164_TARGETS')
