"""Merge owned, disjoint EV112 visual layers on their exact common base.
No additive guesses or silent last-writer wins. Used before bury and staging.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('build');ap.add_argument('pilot');ap.add_argument('global_relief');ap.add_argument('narva');ap.add_argument('out');a=ap.parse_args()
    B=Path(a.build);P=Path(a.pilot);G=Path(a.global_relief);N=Path(a.narva);out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
    tp=B/'water-fix-b/terrain.npz';assert sha(tp)=='07054c46ebf2861bc905fe2d68fb3b734d7b8e9ad1d538c73a7ee745edd56d62'
    z=np.load(tp);arrays={k:z[k] for k in z.files};H0=arrays['heights'];H=H0.copy();occupied=np.zeros_like(H,bool);reports=[]
    for role,folder,report_name,mask in [('global',G,'report.json','v31_relief_general'),('pilot',P,'author-report.json','v31_continuous_pilot'),('narva',N,'layer-report.json','v31_narva_seaward')]:
        report=json.loads((folder/report_name).read_text());t=folder/'terrain.npz'
        assert report['terrain_input_sha256']==sha(tp)
        assert report['terrain_sha256']==sha(t)
        if role!='pilot':assert report['status']=='OFFLINE_PASS'
        zz=np.load(t);h=zz['heights'];changed=h!=H0
        assert not (changed&occupied).any(), ('layer overlap',role,int((changed&occupied).sum()))
        H[changed]=h[changed];occupied|=changed;arrays[mask]=changed
        reports.append(dict(role=role,path=str(t),sha256=sha(t),vertices=int(changed.sum())))
    guard=json.loads((G/'report.json').read_text())['pilot_terrain'];assert guard and guard['sha256']==sha(guard['path'])
    # The global pass protects the pilot's spatial domain, independent of
    # height refinements wholly inside that same already frozen domain.
    guarded_mask=np.load(guard['path'])['heights']!=H0
    assert np.array_equal(guarded_mask,np.load(P/'terrain.npz')['heights']!=H0)
    arrays['heights']=H;np.savez_compressed(out/'terrain.npz',**arrays)
    for filename in ('cover.npy','envelope.npy'):(out/filename).write_bytes((P/filename).read_bytes())
    result=dict(status='MERGED_DISJOINT',input_sha256=sha(tp),layers=reports,terrain_sha256=sha(out/'terrain.npz'),
                changed_vertices=int(occupied.sum()),limitation='Merge proof only; geometry, footprint, forest and engine gates remain separate.')
    (out/'merge-report.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
