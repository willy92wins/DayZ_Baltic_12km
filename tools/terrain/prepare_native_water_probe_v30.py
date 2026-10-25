"""Split one asymmetric instance from a prepared native water import.

The native editor must demonstrate its origin/centre convention before the
remaining batch is imported. No project binary is modified here.
"""
from pathlib import Path
import argparse
import hashlib
import json

import numpy as np
from wrp0wzd import read


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--preparation',type=Path,required=True)
    ap.add_argument('--world',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();assert not a.out.exists()
    prep=json.loads(a.preparation.read_text())
    assert sha(a.world)==prep['staged_world_sha256']
    csv=Path(prep['csv']);assert sha(csv)==prep['csv_sha256']
    lines=csv.read_text().splitlines()
    objects=[o for o in read(a.world)['objects'] if o['name'].startswith('baltic_water_v30\\')]
    assert len(objects)==len(lines)==prep['objects']
    bymodel={m['file']:m for m in prep['sources']}
    score=[np.linalg.norm(bymodel[o['name']]['center']) for o in objects]
    index=int(np.argmax(score));obj=objects[index];model=bymodel[obj['name']]
    assert score[index]>10 and all(abs(v)>1 for v in (model['center'][0],model['center'][2]))
    assert lines[index].split(';')[0]=='"'+model['template']+'"'
    a.out.mkdir(parents=True)
    probe=a.out/'01_water_probe_absolute.txt'
    remainder=a.out/'02_water_remaining_absolute.txt'
    probe.write_text(lines[index]+'\n',encoding='ascii',newline='\n')
    remaining=[line for i,line in enumerate(lines) if i!=index]
    remainder.write_text('\n'.join(remaining)+'\n',encoding='ascii',newline='\n')
    assert len(remaining)+1==len(lines)
    result=dict(status='PREPARED_NATIVE_ORIGIN_CONSUMER_PENDING',world_sha256=sha(a.world),
        original_csv_sha256=sha(csv),probe_index=index,probe_model=obj['name'],template=model['template'],
        wrp_matrix=obj['matrix'],raw_bbox_center=model['center'],centre_offset_m=float(score[index]),
        source_model_sha256=model['sha256'],probe_sha256=sha(probe),remaining_sha256=sha(remainder),
        total_instances=len(lines),remaining_instances=len(remaining),
        procedure=['Load the complete prepared template library once; import only 01 as absolute elevation in a new layer.',
                   'Export a fresh WRP and compare the one new model and matrix, before bulk import.',
                   'If exact, import 02 in that layer. Do not also import the complete CSV.',
                   'Old water layer must eventually be removed from the isolated project; merely hiding it may still export it.',
                   'All nine bridge records, terrain and surface need their separate final export comparison.'])
    (a.out/'probe.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
