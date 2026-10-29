import hashlib
import importlib.util
import json
import os
import shutil
import struct
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parent.parent
SPEC=importlib.util.spec_from_file_location('road_build_discovery_ev112',ROOT/'tools'/'quality'/'road_build_discovery_ev112.py')
tool=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(tool)
B=chr(92)
def sha(b): return hashlib.sha256(b).hexdigest()
def write_pbo(path,entries,prefix):
    out=bytearray(); out.extend(bytes(1)); out.extend(struct.pack('<5I',0x56657273,0,0,0,0)); out.extend(b'prefix'+bytes(1)); out.extend(prefix.encode()+bytes(1)); out.extend(bytes(1))
    for name,mime,payload in entries: out.extend(name.encode()+bytes(1)); out.extend(struct.pack('<5I',mime,0,0,0,len(payload)))
    out.extend(bytes(1)); out.extend(struct.pack('<5I',0,0,0,0,0))
    for name,mime,payload in entries: out.extend(payload)
    Path(path).write_bytes(bytes(out)); return bytes(out)
MODELS=[('parts/asf1_25.p3d','dz/structures/roads/parts/asf1_25.p3d'),('parts/asf2_25.p3d','dz/structures/roads/parts/asf2_25.p3d'),('parts/asf1_10 100.p3d','dz/structures/roads/parts/asf1_10 100.p3d')]
MAT='parts/data/asf_dashedline.rvmat'; TEX='parts/data/asf_dashedline_ca.paa'; EXTRA='parts/data/extra.rvmat'
def make_scenario(tmp,opts=None):
    o=opts or {}; tmp=Path(tmp); build=tmp/'build'; cat=tmp/'catalog'; cat.mkdir(parents=True); (tmp/'pbo').mkdir()
    payloads={e:b'ODOL'+e.encode()+b'-model-data' for e,n in MODELS}; payloads[MAT]=b'class ASF { Shader=1; Pix=1; Vertex=1; };'; payloads[TEX]=struct.pack('<H',0xff01)+b'paa-data'; payloads[EXTRA]=b'class Extra { Shader=1; };'
    rels=[e for e,n in MODELS]+[MAT,TEX]+(([EXTRA] if o.get('extra_ref') else []))
    mime_map=o.get('mime_map') or {}; entries=[]
    for rel in rels: entries.append((rel,mime_map.get(rel,0),payloads[rel]))
    if o.get('duplicate'): entries.append((MODELS[0][0],0,payloads[MODELS[0][0]]))
    if o.get('traversal'): entries.append(('../evil.txt',0,b'x'))
    prefix=o.get('prefix','DZ'+B+'structures'+B+'roads'); pbo=tmp/'pbo'/'structures_roads.pbo'; write_pbo(pbo,entries,prefix)
    def bref(rel): return 'dz/structures/roads/'+rel
    for rel in rels:
        if rel in (o.get('missing_build') or set()): continue
        data=(o.get('build_overrides') or {}).get(rel,payloads[rel]); p=build/bref(rel); p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(data)
    extp=build/'dz'/'surfaces'/'data'/'roadway'/'asphalt_ext.paa'; extp.parent.mkdir(parents=True,exist_ok=True); extp.write_bytes(struct.pack('<H',0xff01)+b'external')
    lines=[]
    for entry,full in MODELS:
        secs=[dict(index=0,material_raw=B.join(['dz','structures','roads','parts','data','asf_dashedline.rvmat']),texture_raw=B.join(['dz','structures','roads','parts','data','asf_dashedline_ca.paa']))]
        geo=dict(index=1,resolution=1.0,role='Geometry',sections=[],textures=[],materials=[B.join(['dz','structures','roads','parts','data','extra.rvmat'])] if o.get('extra_ref') else [])
        lods=[dict(index=0,resolution=0.0,role='Visual',sections=secs,textures=[secs[0]['texture_raw']],materials=[secs[0]['material_raw']]),geo,dict(index=3,resolution=3.0,role='Roadway',sections=[dict(index=0,material_raw='',texture_raw=B.join(['dz','surfaces','data','roadway','asphalt_ext.paa']))],textures=[B.join(['dz','surfaces','data','roadway','asphalt_ext.paa'])],materials=[])]
        lines.append(json.dumps(dict(name=entry,sha256=sha(payloads[entry]),status='READ_STRICT',measurement=dict(lods=lods))))
    models_path=cat/'models.jsonl'; models_path.write_text(chr(10).join(lines)+chr(10),encoding='utf-8')
    entries_list=[dict(name=r,normalized_name=r,size=len(payloads[r]),mime=mime_map.get(r,0),sha256=sha(payloads[r])) for r in rels]
    entries_path=cat/'entries.json'; entries_path.write_text(json.dumps(entries_list),encoding='utf-8')
    receipt=tmp/'receipt.json'; receipt.write_bytes(b'{x:1}'.replace(b'x',b'1'))
    prereq=tmp/'prereq.txt'; prereq.write_bytes(b'prereq')
    stage=tmp/'stage'/'DZ'; stage.mkdir(parents=True)
    pins={str(models_path):sha(models_path.read_bytes()),str(entries_path):sha(entries_path.read_bytes()),str(receipt):sha(receipt.read_bytes())}
    if o.get('pin_bad'): pins[str(receipt)]='0'*64
    contract=dict(schema='road-build-discovery.v1',pbo=dict(path=str(pbo),sha256=sha(pbo.read_bytes()),bytes=pbo.stat().st_size,prefix='DZ'+B+'structures'+B+'roads'),catalog_models=str(models_path),catalog_entries=str(entries_path),pins=pins,models=[dict(name=n,entry=e) for e,n in MODELS],build_alias='P:/',build_root=str(build),prerequisites=[dict(path=str(prereq),sha256=sha(prereq.read_bytes()))],stage_paths=[str(stage)],limits=dict(seconds=60,bytes=1073741824))
    cpath=tmp/'contract.json'; cpath.write_text(json.dumps(contract),encoding='utf-8')
    tool.BUILD_ALIAS_MAP.clear(); tool.BUILD_ALIAS_MAP['P:/']=str(build)
    return SimpleNamespace(tmp=tmp,build=build,contract=cpath,contract_sha=sha(cpath.read_bytes()),out=tmp/'out',pbo=pbo,receipt=receipt,prereq=prereq,payloads=payloads)
def run(s):
    tool.run_discovery(str(s.contract),s.contract_sha,str(s.out)); return json.loads((s.out/'report.json').read_text(encoding='utf-8'))
def statuses(r,kind=None): return [c['status'] for c in r['comparisons'] if kind is None or c['kind']==kind]
class RoadB4ATests(unittest.TestCase):
    def setUp(self): self.td=tempfile.TemporaryDirectory(); self.addCleanup(self.td.cleanup); self.addCleanup(tool.BUILD_ALIAS_MAP.clear)
    def test_allLODextraReference(self):
        s=make_scenario(self.td.name,dict(extra_ref=True)); r=run(s); self.assertIn('dz/structures/roads/parts/data/extra.rvmat',[x['normalized'] for x in r['references']])
    def test_duplicatePBO(self):
        s=make_scenario(self.td.name,dict(duplicate=True)); self.assertRaises(ValueError,tool.run_discovery,str(s.contract),s.contract_sha,str(s.out)); self.assertFalse(s.out.exists())
    def test_traversal(self):
        s=make_scenario(self.td.name,dict(traversal=True)); self.assertRaises(ValueError,tool.run_discovery,str(s.contract),s.contract_sha,str(s.out)); self.assertFalse(s.out.exists())
    def test_linkescape(self):
        s=make_scenario(self.td.name); parts=s.build/'dz'/'structures'/'roads'/'parts'; outside=Path(self.td.name)/'outside'; shutil.copytree(parts,outside); shutil.rmtree(parts)
        try: os.symlink(outside,parts,target_is_directory=True)
        except OSError: self.skipTest('symlink unavailable')
        r=run(s); self.assertIn('UNRESOLVED_LINK',statuses(r)); self.assertNotEqual(r['status'],'INPUTS_MATCH')
    def test_prefixmismatch(self):
        s=make_scenario(self.td.name,dict(prefix='XX'+B+'wrong')); r=run(s); self.assertIn('PREFIX_MISMATCH',statuses(r)); self.assertNotEqual(r['status'],'INPUTS_MATCH')
    def test_missing(self):
        s=make_scenario(self.td.name,dict(missing_build={MODELS[0][0]})); r=run(s); self.assertIn('MISSING',statuses(r)); self.assertEqual(r['status'],'INCONCLUSIVE_DISCOVERY'); self.assertFalse(r['build_ready'])
    def test_externe(self):
        s=make_scenario(self.td.name); r=run(s); ext=[x for x in r['references'] if x['normalized']=='dz/surfaces/data/roadway/asphalt_ext.paa']; self.assertEqual(ext[0]['status'],'UNRESOLVED_EXTERNAL')
    def test_MIME(self):
        s=make_scenario(self.td.name,dict(mime_map={TEX:1})); r=run(s); self.assertIn('UNSUPPORTED_COMPRESSION',statuses(r))
    def test_sameNameDifferentBytes(self):
        s=make_scenario(self.td.name,dict(build_overrides={MODELS[0][0]:b'ODOLdifferent-bytes'})); r=run(s); self.assertIn('DIFFER',statuses(r)); self.assertEqual(r['status'],'INPUTS_DIFFER')
    def test_FORMAT_DIFFERS(self):
        s=make_scenario(self.td.name,dict(build_overrides={MODELS[0][0]:b'MLODdifferent-format'})); r=run(s); self.assertIn('FORMAT_DIFFERS',statuses(r))
    def test_unknown(self):
        s=make_scenario(self.td.name,dict(build_overrides={MODELS[0][0]:bytes([0,1,2,3,4])})); r=run(s); self.assertIn('UNDETERMINED_FORMAT',statuses(r)); self.assertEqual(r['status'],'INCONCLUSIVE_DISCOVERY')
    def test_drift_unknown_precedence(self):
        s=make_scenario(self.td.name,dict(build_overrides={MODELS[0][0]:b'ODOLdifferent-bytes',MODELS[1][0]:bytes([9,8,7])})); r=run(s); self.assertEqual(r['status'],'INPUTS_DIFFER'); self.assertTrue(r['incomplete_coverage'])
    def test_source_mutation(self):
        s=make_scenario(self.td.name); s.receipt.write_bytes(b'mutated'); r=run(s); self.assertIn('DIFFER',statuses(r,'pin')); self.assertNotEqual(r['status'],'INPUTS_MATCH')
    def test_pins_contractchanged(self):
        s=make_scenario(self.td.name,dict(pin_bad=True)); r=run(s); self.assertIn('DIFFER',statuses(r,'pin')); self.assertNotEqual(r['status'],'INPUTS_MATCH')
    def test_reportcorruption(self):
        s=make_scenario(self.td.name); r=run(s); report=json.loads((s.out/'report.json').read_text()); manifest=json.loads((s.out/'manifest.json').read_text()); expected=hashlib.sha256((s.out/'manifest.json').read_bytes()).hexdigest(); self.assertTrue(tool.verify_manifest(report,manifest,expected)); report['status']='INPUTS_MATCH'; self.assertFalse(tool.verify_manifest(report,manifest,expected))
    def test_outputexists(self):
        s=make_scenario(self.td.name); s.out.mkdir(); self.assertRaises(ValueError,tool.run_discovery,str(s.contract),s.contract_sha,str(s.out))
    def test_contract_hash_before_parse(self):
        s=make_scenario(self.td.name); self.assertRaises(ValueError,tool.run_discovery,str(s.contract),'0'*64,str(s.out)); self.assertFalse(s.out.exists())
if __name__=='__main__': unittest.main()
