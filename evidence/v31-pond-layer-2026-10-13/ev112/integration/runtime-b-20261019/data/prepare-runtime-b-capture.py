from pathlib import Path
import hashlib
O=Path(__file__).parent
src=O/'capture-runtime-probe-ae.py';s=src.read_text();dest=O/'capture-runtime-probe-runtime-b.py';assert not dest.exists()
pairs=[("O/'deploy.json'","O/'deploy-runtime-b.json'"),("deploy['forest_tag']=='ae' and deploy['offline_status']=='PASS'","deploy['terrain_revision']=='runtime-b' and deploy['offline_status']=='PASS_AFFECTED_CONSUMERS_WITH_INHERITED_BASELINE'"),("O/'build-review-closure-ae.json'","O/'build-review-closure-runtime-b.json'"),("O/'probe-c/points.csv'","O/'probe-runtime-b/points.csv'"),("O/'probe-c/points.json'","O/'probe-runtime-b/points.json'")]
for a,b in pairs:
 assert a in s,a;s=s.replace(a,b)
anchor="assert sha(review['raw_review'])==review['raw_review_sha256']"
assert anchor in s
s=s.replace(anchor,anchor+"\nassert review['ready_for_server_probe'] is True and review['review_round']==2\nassert review['deploy_sha256']==sha(O/'deploy-runtime-b.json')\nassert all(sha(p)==h for p,h in deploy['probe_binding'].items())")
dest.write_text(s)
print(dest,hashlib.sha256(dest.read_bytes()).hexdigest())
