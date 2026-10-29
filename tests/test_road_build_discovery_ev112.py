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
from unittest import mock
ROOT=Path(__file__).resolve().parent.parent
SPEC=importlib.util.spec_from_file_location('road_build_discovery_ev112',ROOT/'tools'/'quality'/'road_build_discovery_ev112.py')
tool=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(tool)
ORIGINAL_QUERY=tool.query_dos_device
B=chr(92)
def sha(b): return hashlib.sha256(b).hexdigest()
def winmap(root): return B+'??'+B+os.path.normpath(str(root))
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
    payloads={e:b'ODOL'+e.encode()+b'-model-data' for e,n in MODELS}; payloads[MAT]=b'class ASF { Shader=1; Pix=1; Vertex=1; Stage=1; };'; payloads[TEX]=struct.pack('<H',0xff01)+b'paa-data'; payloads[EXTRA]=b'class Extra { Shader=1; };'
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
        matraw='..'+B+'..'+B+'evil.rvmat' if o.get('ref_traversal') else B.join(['dz','structures','roads','parts','data','asf_dashedline.rvmat'])
        secs=[dict(index=0,material_raw=matraw,texture_raw=B.join(['dz','structures','roads','parts','data','asf_dashedline_ca.paa']))]
        geo=dict(index=1,resolution=1.0,role='Geometry',sections=[],textures=[],materials=[B.join(['dz','structures','roads','parts','data','extra.rvmat'])] if o.get('extra_ref') else [])
        lods=[dict(index=0,resolution=0.0,role='Visual',sections=secs,textures=[secs[0]['texture_raw']],materials=[secs[0]['material_raw']]),geo]
        if not o.get('no_external'): lods.append(dict(index=3,resolution=3.0,role='Roadway',sections=[dict(index=0,material_raw='',texture_raw=B.join(['dz','surfaces','data','roadway','asphalt_ext.paa']))],textures=[B.join(['dz','surfaces','data','roadway','asphalt_ext.paa'])],materials=[]))
        lines.append(json.dumps(dict(name=entry,sha256=sha(payloads[entry]),status='READ_STRICT',measurement=dict(lods=lods))))
    models_path=cat/'models.jsonl'; models_path.write_text(chr(10).join(lines)+chr(10),encoding='utf-8')
    entries_path=cat/'entries.json'; entries_path.write_text(json.dumps([dict(name=r,normalized_name=r,category='catalog',size=len(payloads[r]),mime=mime_map.get(r,0),sha256=sha(payloads[r])) for r in rels]),encoding='utf-8')
    receipt=tmp/'receipt.json'; receipt.write_bytes(b'{1:1}')
    prereq=tmp/'prereq.txt'; prereq.write_bytes(b'prereq')
    stage=tmp/'stage'/'DZ'; stage.mkdir(parents=True)
    pins={str(models_path):sha(models_path.read_bytes()),str(entries_path):sha(entries_path.read_bytes()),str(receipt):sha(receipt.read_bytes())}
    if o.get('pin_bad'): pins[str(receipt)]='0'*64
    contract=dict(schema='road-build-discovery.v1',pbo=dict(path=str(pbo),sha256=sha(pbo.read_bytes()),bytes=pbo.stat().st_size,prefix='DZ'+B+'structures'+B+'roads'),catalog_models=str(models_path),catalog_entries=str(entries_path),pins=pins,models=[dict(name=n,entry=e) for e,n in MODELS],build_alias='P:/',build_root=str(build),prerequisites=[dict(path=str(prereq),sha256=sha(prereq.read_bytes()))],stage_paths=[str(stage)],limits=dict(seconds=60,bytes=1073741824))
    cpath=tmp/'contract.json'; cpath.write_text(json.dumps(contract),encoding='utf-8')
    if o.get('root_mapping_mismatch'): tool.query_dos_device=lambda alias: winmap(tmp/'wrongroot')
    elif o.get('query_fails'): tool.query_dos_device=lambda alias: (_ for _ in ()).throw(OSError('query failed'))
    else: tool.query_dos_device=lambda alias,_b=str(build): winmap(_b)
    return SimpleNamespace(tmp=tmp,build=build,contract=cpath,contract_sha=sha(cpath.read_bytes()),out=tmp/'out',pbo=pbo,receipt=receipt,prereq=prereq,payloads=payloads,models_path=models_path,entries_path=entries_path)
def run(s):
    tool.run_discovery(str(s.contract),s.contract_sha,str(s.out)); return json.loads((s.out/'report.json').read_text(encoding='utf-8'))
def statuses(r,kind=None): return [c['status'] for c in r['comparisons'] if kind is None or c['kind']==kind]
def update_contract(s,fn):
    c=json.loads(s.contract.read_text(encoding='utf-8')); fn(c); s.contract.write_text(json.dumps(c),encoding='utf-8'); s.contract_sha=sha(s.contract.read_bytes())
def rewrite_models(s,fn):
    rows=[json.loads(x) for x in s.models_path.read_text(encoding='utf-8').splitlines() if x.strip()]; fn(rows); s.models_path.write_text(chr(10).join(json.dumps(x) for x in rows)+chr(10),encoding='utf-8'); update_contract(s,lambda c: c['pins'].__setitem__(str(s.models_path),sha(s.models_path.read_bytes())))
def rewrite_entries(s,fn):
    rows=json.loads(s.entries_path.read_text(encoding='utf-8')); fn(rows); s.entries_path.write_text(json.dumps(rows),encoding='utf-8'); update_contract(s,lambda c: c['pins'].__setitem__(str(s.entries_path),sha(s.entries_path.read_bytes())))
class RoadB4ATests(unittest.TestCase):
    def setUp(self): self.td=tempfile.TemporaryDirectory(); self.addCleanup(self.td.cleanup); self.addCleanup(setattr,tool,'query_dos_device',ORIGINAL_QUERY)
    def test_allLODextraReference(self):
        s=make_scenario(self.td.name,dict(extra_ref=True)); r=run(s); self.assertIn('dz/structures/roads/parts/data/extra.rvmat',[x['normalized'] for x in r['references']])
    def test_positive_all_match_no_external(self):
        s=make_scenario(self.td.name,dict(no_external=True)); r=run(s); self.assertEqual(r['status'],'INPUTS_MATCH'); self.assertTrue(all(c['status']=='MATCH' for c in r['comparisons'])); self.assertGreater(r['reference_count'],0); self.assertFalse(r['build_ready'])
    def test_duplicatePBO(self):
        s=make_scenario(self.td.name,dict(duplicate=True)); self.assertRaises(ValueError,tool.run_discovery,str(s.contract),s.contract_sha,str(s.out)); self.assertFalse(s.out.exists())
    def test_traversal(self):
        s=make_scenario(self.td.name,dict(traversal=True)); self.assertRaises(ValueError,tool.run_discovery,str(s.contract),s.contract_sha,str(s.out)); self.assertFalse(s.out.exists())
    def test_reference_traversal(self):
        s=make_scenario(self.td.name,dict(ref_traversal=True)); r=run(s); self.assertIn('UNSAFE_PATH',[x['status'] for x in r['references']]); self.assertNotEqual(r['status'],'INPUTS_MATCH')
    def test_linkescape(self):
        s=make_scenario(self.td.name); parts=s.build/'dz'/'structures'/'roads'/'parts'; outside=Path(self.td.name)/'outside'; shutil.copytree(parts,outside); shutil.rmtree(parts)
        try: os.symlink(outside,parts,target_is_directory=True)
        except OSError: self.skipTest('symlink unavailable')
        r=run(s); self.assertIn('UNRESOLVED_LINK',statuses(r)); self.assertNotEqual(r['status'],'INPUTS_MATCH')
    def test_simulated_reparse_no_privilege(self):
        s=make_scenario(self.td.name); parts=str(s.build/'dz'/'structures'/'roads'/'parts'); real_lstat=os.lstat; fake=SimpleNamespace(st_mode=0o40777,st_dev=1,st_ino=999,st_size=0,st_mtime_ns=0,st_ctime_ns=0,st_file_attributes=tool.REPARSE,st_reparse_tag=0xA0000003)
        def fake_lstat(p,*a,**k): return fake if os.path.normpath(str(p))==os.path.normpath(parts) else real_lstat(p,*a,**k)
        with mock.patch.object(tool.os,'lstat',side_effect=fake_lstat), mock.patch.object(tool.os,'readlink',return_value='outside',create=True): r=run(s)
        self.assertIn('UNRESOLVED_LINK',statuses(r)); self.assertNotEqual(r['status'],'INPUTS_MATCH')
    def test_prefixmismatch(self):
        s=make_scenario(self.td.name,dict(prefix='XX'+B+'wrong')); r=run(s); self.assertIn('PREFIX_MISMATCH',statuses(r)); self.assertNotEqual(r['status'],'INPUTS_MATCH')
    def test_missing(self):
        s=make_scenario(self.td.name,dict(missing_build={MODELS[0][0]})); r=run(s); self.assertIn('MISSING',statuses(r)); self.assertEqual(r['status'],'INCONCLUSIVE_DISCOVERY'); self.assertFalse(r['build_ready'])
    def test_externe(self):
        s=make_scenario(self.td.name); r=run(s); ext=[x for x in r['references'] if x['normalized']=='dz/surfaces/data/roadway/asphalt_ext.paa']; self.assertEqual(ext[0]['status'],'UNRESOLVED_EXTERNAL'); self.assertEqual(r['status'],'INCONCLUSIVE_DISCOVERY')
    def test_MIME(self):
        s=make_scenario(self.td.name,dict(mime_map={TEX:1})); r=run(s); self.assertIn('UNSUPPORTED_COMPRESSION',statuses(r)); self.assertEqual(r['status'],'INCONCLUSIVE_DISCOVERY')
    def test_sameNameDifferentBytes(self):
        s=make_scenario(self.td.name,dict(build_overrides={MODELS[0][0]:b'ODOLdifferent-bytes'})); r=run(s); self.assertIn('DIFFER',statuses(r)); self.assertEqual(r['status'],'INPUTS_DIFFER')
    def test_FORMAT_DIFFERS_aggregate_inconclusive(self):
        s=make_scenario(self.td.name,dict(build_overrides={MODELS[0][0]:b'MLODdifferent-format'})); r=run(s); self.assertIn('FORMAT_DIFFERS',statuses(r)); self.assertEqual(r['status'],'INCONCLUSIVE_DISCOVERY')
    def test_RAP_and_text_rejection(self):
        self.assertEqual(tool.detect_format('x.rvmat',b'\x00raP'+bytes(8)+b'Stage'), 'RVMAT_RAP')
        self.assertEqual(tool.detect_format('x.rvmat',b'class A { Stage=1; };'),'RVMAT_TEXT')
        self.assertEqual(tool.detect_format('x.rvmat',b'class A { Stage=1; };\x00junk'),'UNKNOWN')
        self.assertEqual(tool.detect_format('x.rvmat',b'Stage \x01 binary'),'UNKNOWN')
        s=make_scenario(self.td.name,dict(build_overrides={MAT:b'\x00raP'+bytes(8)+b'Stage'})); r=run(s); self.assertIn('FORMAT_DIFFERS',statuses(r)); self.assertEqual(r['status'],'INCONCLUSIVE_DISCOVERY')
    def test_unknown(self):
        s=make_scenario(self.td.name,dict(build_overrides={MODELS[0][0]:bytes([0,1,2,3,4])})); r=run(s); self.assertIn('UNDETERMINED_FORMAT',statuses(r)); self.assertEqual(r['status'],'INCONCLUSIVE_DISCOVERY')
    def test_drift_unknown_precedence(self):
        s=make_scenario(self.td.name,dict(build_overrides={MODELS[0][0]:b'ODOLdifferent-bytes',MODELS[1][0]:bytes([9,8,7])})); r=run(s); self.assertEqual(r['status'],'INPUTS_DIFFER'); self.assertTrue(r['incomplete_coverage'])
    def test_source_mutation_aborts_no_output(self):
        s=make_scenario(self.td.name); s.receipt.write_bytes(b'mutated'); self.assertRaises(ValueError,tool.run_discovery,str(s.contract),s.contract_sha,str(s.out)); self.assertFalse(s.out.exists())
    def test_pins_contractchanged_aborts_no_output(self):
        s=make_scenario(self.td.name,dict(pin_bad=True)); self.assertRaises(ValueError,tool.run_discovery,str(s.contract),s.contract_sha,str(s.out)); self.assertFalse(s.out.exists())
    def test_absent_catalog_pin_aborts(self):
        s=make_scenario(self.td.name); update_contract(s,lambda c: c['pins'].pop(str(s.models_path))); self.assertRaises(ValueError,tool.run_discovery,str(s.contract),s.contract_sha,str(s.out)); self.assertFalse(s.out.exists())
    def test_missing_contract_field_aborts(self):
        s=make_scenario(self.td.name); update_contract(s,lambda c: c.pop('stage_paths')); self.assertRaises(ValueError,tool.run_discovery,str(s.contract),s.contract_sha,str(s.out)); self.assertFalse(s.out.exists())
    def test_model_name_prefix_entry_mismatch_aborts(self):
        s=make_scenario(self.td.name); update_contract(s,lambda c: c['models'][0].__setitem__('name','dz/structures/roads/parts/wrong.p3d')); self.assertRaises(ValueError,tool.run_discovery,str(s.contract),s.contract_sha,str(s.out)); self.assertFalse(s.out.exists())
    def test_zero_and_missing_lods_inconclusive(self):
        for mode in ('zero','missing'):
            with self.subTest(mode=mode):
                td=tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup); s=make_scenario(td.name)
                def fn(rows):
                    if mode=='zero': rows[0]['measurement']['lods']=[]
                    else: rows[0]['measurement'].pop('lods',None)
                rewrite_models(s,fn); r=run(s); self.assertIn('UNREADABLE',statuses(r,'model_lods')); self.assertEqual(r['status'],'INCONCLUSIVE_DISCOVERY')
    def test_missing_lod_fields_inconclusive(self):
        s=make_scenario(self.td.name)
        def fn(rows): rows[0]['measurement']['lods'][0].pop('materials')
        rewrite_models(s,fn); r=run(s); self.assertIn('UNREADABLE',statuses(r,'model_lods')); self.assertNotEqual(r['status'],'INPUTS_MATCH')
    def test_entry_normalized_wrong_aborts(self):
        s=make_scenario(self.td.name); rewrite_entries(s,lambda rows: rows[0].__setitem__('normalized_name','parts/wrong.p3d')); self.assertRaises(ValueError,tool.run_discovery,str(s.contract),s.contract_sha,str(s.out)); self.assertFalse(s.out.exists())
    def test_pbo_length_mismatch_aborts(self):
        s=make_scenario(self.td.name); update_contract(s,lambda c: c['pbo'].__setitem__('bytes',c['pbo']['bytes']+1)); self.assertRaises(ValueError,tool.run_discovery,str(s.contract),s.contract_sha,str(s.out)); self.assertFalse(s.out.exists())
    def test_catalog_changed_between_capture_and_parse_final_rehash(self):
        s=make_scenario(self.td.name); orig=tool.observe_file; state={'done':False}
        def wrapped(path,expected=None,read_data=False,max_bytes=None):
            r=orig(path,expected,read_data,max_bytes)
            if str(path)==str(s.models_path) and read_data and not state['done']: state['done']=True; s.models_path.write_bytes(s.models_path.read_bytes()+b' ')
            return r
        with mock.patch.object(tool,'observe_file',side_effect=wrapped): self.assertRaises(ValueError,tool.run_discovery,str(s.contract),s.contract_sha,str(s.out))
        self.assertFalse(s.out.exists())
    def test_root_mapping_mismatch_unresolved(self):
        s=make_scenario(self.td.name,dict(root_mapping_mismatch=True)); r=run(s); self.assertIn('UNRESOLVED_LINK',statuses(r,'build_alias')); self.assertEqual(r['status'],'INCONCLUSIVE_DISCOVERY'); self.assertFalse(r['build_alias']['trusted'])
    def test_query_failure_unresolved(self):
        s=make_scenario(self.td.name,dict(query_fails=True)); r=run(s); self.assertIn('UNRESOLVED_LINK',statuses(r)); self.assertNotEqual(r['status'],'INPUTS_MATCH')
    def test_reportcorruption_manifest_is_integrity_only(self):
        s=make_scenario(self.td.name); r=run(s); report=json.loads((s.out/'report.json').read_text()); manifest=json.loads((s.out/'manifest.json').read_text()); expected=hashlib.sha256((s.out/'manifest.json').read_bytes()).hexdigest(); self.assertTrue(tool.verify_manifest(report,manifest,expected)); self.assertIn('manifest_integrity_is_not_semantic_acceptance',report['limitations']); report['status']='INPUTS_MATCH'; self.assertFalse(tool.verify_manifest(report,manifest,expected))
    def test_expected_mapping_literal_golden(self):
        self.assertEqual(tool.expected_mapping(r'C:\sample'),bytes.fromhex('5c3f3f5c433a5c73616d706c65').decode())
        self.assertFalse(tool.expected_mapping(r'C:\sample').startswith(B+B))
    def test_double_prefix_mapping_not_trusted(self):
        s=make_scenario(self.td.name,dict(no_external=True)); tool.query_dos_device=lambda alias,_b=str(s.build): B+B+'??'+B+os.path.normpath(_b); r=run(s); self.assertIn('UNRESOLVED_LINK',statuses(r,'build_alias')); self.assertFalse(r['build_alias']['trusted']); self.assertEqual(r['status'],'INCONCLUSIVE_DISCOVERY')
    def test_entry_category_malformed_aborts(self):
        s=make_scenario(self.td.name); rewrite_entries(s,lambda rows: rows[0].__setitem__('category',123)); self.assertRaises(ValueError,tool.run_discovery,str(s.contract),s.contract_sha,str(s.out)); self.assertFalse(s.out.exists())
    def test_entry_unexpected_key_aborts(self):
        s=make_scenario(self.td.name); rewrite_entries(s,lambda rows: rows[0].__setitem__('unexpected',1)); self.assertRaises(ValueError,tool.run_discovery,str(s.contract),s.contract_sha,str(s.out)); self.assertFalse(s.out.exists())
    def test_missing_prerequisite_inconclusive(self):
        s=make_scenario(self.td.name,dict(no_external=True)); update_contract(s,lambda c: c['prerequisites'].__setitem__(0,dict(path=str(s.tmp/'missing-prereq.txt'),sha256=sha(b'x')))); r=run(s); self.assertIn('MISSING',statuses(r,'prerequisite')); self.assertEqual(r['status'],'INCONCLUSIVE_DISCOVERY'); self.assertFalse(r['build_ready'])
    def test_null_prerequisite_sha_inconclusive(self):
        s=make_scenario(self.td.name,dict(no_external=True)); update_contract(s,lambda c: c['prerequisites'][0].__setitem__('sha256',None)); r=run(s); self.assertIn('UNPINNED',statuses(r,'prerequisite')); self.assertEqual(r['status'],'INCONCLUSIVE_DISCOVERY'); self.assertFalse(r['build_ready'])
    def test_differing_prerequisite_sha_inputs_differ(self):
        s=make_scenario(self.td.name,dict(no_external=True)); update_contract(s,lambda c: c['prerequisites'][0].__setitem__('sha256',sha(b'other'))); r=run(s); self.assertIn('DIFFER',statuses(r,'prerequisite')); self.assertEqual(r['status'],'INPUTS_DIFFER')
    def test_unapproved_reparse_blocked_regardless_of_tag(self):
        self.assertTrue(tool.is_link(SimpleNamespace(st_mode=0,st_file_attributes=1024,st_reparse_tag=0)))
        self.assertTrue(tool.is_link(SimpleNamespace(st_mode=0,st_file_attributes=1024,st_reparse_tag=0x9000001A)))
        self.assertFalse(tool.is_link(SimpleNamespace(st_mode=0,st_file_attributes=0,st_reparse_tag=0)))
    def test_outputexists(self):
        s=make_scenario(self.td.name); s.out.mkdir(); self.assertRaises(ValueError,tool.run_discovery,str(s.contract),s.contract_sha,str(s.out))
    def test_contract_hash_before_parse(self):
        s=make_scenario(self.td.name); self.assertRaises(ValueError,tool.run_discovery,str(s.contract),'0'*64,str(s.out)); self.assertFalse(s.out.exists())
if __name__=='__main__': unittest.main()
