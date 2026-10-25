"""Prepare scripts, without creating a mission or running DayZ."""
from pathlib import Path
import ast
import hashlib
import json
import re

D=Path(__file__).parent
B=D.parent.parent/'v30-mixed-bank-incremental-fixed-20261010'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
old_terrain='0a18c5623885eed274cfe7d296e02aba290ed491b835d317213fc7876b2fc45b'
base_terrain='f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'
new_terrain='8e239f8e2815b61a920421af1dfbb1b64f353ab4978d633eb39fe74f04946d1b'
old_snap='5e14a189d288fa4725c7343831bd973357c4b3a5ef4e8ee217f2fb14148239c3'
base_snap='c0effbbcf0200bd916a691e94d44546bc573dc30a7c275b8049a8ad64b2863a2'
native_source=B/'verify_native.py'
assert sha(native_source)=='675daae3bc1fa5cfa7feecf211132000e91e56e281e86349f1b8f78947da8771'
assert sha(B/'native-snapshot.log')==base_snap

def simultaneous(text,replacements):
    regex=re.compile('|'.join(re.escape(k) for k in sorted(replacements,key=len,reverse=True)))
    return regex.sub(lambda m:replacements[m.group()],text)

common={
    'EV82':'EV87','EV80':'EV82','ev82':'ev87','ev80':'ev82',
    'E:/DayZ-Baltic-Build/v30-mixed-bank-constrained-20261010':str(B).replace('\\','/'),
    old_terrain:base_terrain,old_snap:base_snap,
    'BALTIC_INCREMENTALBANK_FULLWATER_V1':'BALTIC_STRICTBANK_FULLWATER_V1',
    'incrementalbank':'strictbank',
}
native=simultaneous(native_source.read_text(),common)
ast.parse(native)
target=D/'verify_native.py'
assert not target.exists()
target.write_text(native,encoding='utf-8',newline='\n')

prepare_source=B/'prepare_probe.py'
mapping={**common,
    'E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010':str(D).replace('\\','/'),
    base_terrain:new_terrain,
    'BalticIncrementalBankFullWaterV1':'BalticStrictBankFullWaterV1',
    'BalticIncrementalBankFullWaterMission':'BalticStrictBankFullWaterMission',
    '@DayZ_Baltic_IncrementalBankPreviewV1':'@DayZ_Baltic_StrictBankPreviewV1',
    'BALTIC_MIXEDBANK_FULLWATER_V1':'BALTIC_INCREMENTALBANK_FULLWATER_V1',
    'BalticMixedBankFullWaterMission':'BalticIncrementalBankFullWaterMission',
    'baltic_mixedbank_fullwater_v1':'baltic_incrementalbank_fullwater_v1',
    '675daae3bc1fa5cfa7feecf211132000e91e56e281e86349f1b8f78947da8771':sha(target),
    "R / 'review-luna' / 'report.json'":"R.parent / 'selective' / 'selective-review.json'",
    "'PASS_EV82_CONSUMER'":"'PASS_INCREMENTAL_NONREGRESSION'",
}
prepare=simultaneous(prepare_source.read_text(),mapping)
old="    assert report.get('candidate_sha256') == EXPECTED_TERRAIN_SHA, 'consumer did not verify exact EV87 terrain'"
assert prepare.count(old)==1
prepare=prepare.replace(old,"    anchor=json.loads((R/'build-inputs.json').read_text())\n    assert anchor['inputs'][str(CONSUMER_REPORT)]==sha(CONSUMER_REPORT)\n    assert report['inputs'][str(R.parent/'selective/candidate-terrain.npz')]==EXPECTED_TERRAIN_SHA\n    for path,digest in anchor['inputs'].items():\n        assert sha(path)==digest, f'build input drift: {path}'")
ast.parse(prepare)
target_prepare=D/'prepare_probe.py'
assert not target_prepare.exists()
target_prepare.write_text(prepare,encoding='utf-8',newline='\n')
receipt={'status':'ADAPTER_SCRIPTS_PREPARED_NOT_RUN','source':{str(native_source):sha(native_source),str(prepare_source):sha(prepare_source)},
         'output':{str(target):sha(target),str(target_prepare):sha(target_prepare)},
         'limits':'No mission created; no native run; parser and thresholds retained from B.'}
(D/'native-adapter-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
