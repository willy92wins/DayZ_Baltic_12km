import copy, hashlib, json, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools' / 'quality'))
import road_content_identity_io_ev112 as io
import road_content_identity_ev112 as producer
import verify_road_content_identity_ev112 as consumer
def sha(b):
    return hashlib.sha256(b).hexdigest()
def jb(obj):
    return (json.dumps(obj, sort_keys=True) + chr(10)).encode()
def fake_sha(tag):
    return sha(('pin:' + tag).encode())
CLAIMS = {'build_ready': False, 'map_repaired': False, 'provider_precedence_current': 'NOT_EVALUATED', 'physical_file_identity': 'NOT_EVALUATED', 'native_resolution': 'NOT_EVALUATED', 'loaded_extractor_image_identity': 'NOT_CERTIFIED'}
def raw_of(c):
    return {'package': c['package'], 'package_sha256': c['package_sha'], 'prefix': c['prefix'], 'entry': c['entry'], 'model_sha256': c['model_sha']}
def mini_case(candidates, hist, hist_state='PROVIDER_RESOLVED', issues=None, name='dz/x/a.p3d', source_instances=1, road_candidates=None):
    issues = issues or []
    pkgs = {}; pins = {}; b2a_models = []
    raws = []
    for c in candidates:
        r = raw_of(c); raws.append(r)
        pkgs[c['package']] = {'path': c['package'], 'sha256': c['package_sha'], 'prefix': c['prefix']}
        pins[c['package']] = c['package_sha']
        b2a_models.append({'name': name, 'sha256': c['model_sha'], 'package': c['package'], 'entry': c['entry']})
    distinct = len({json.dumps(r, sort_keys=True) for r in raws})
    table = [{'name': name, 'aliases': [], 'source_instances': source_instances, 'candidate_instances': source_instances, 'provider': hist, 'state': hist_state}]
    roads_sha = fake_sha('roads'); pbo_path = 'E:/Addons/structures_roads.pbo'
    road_models = road_candidates or []
    parsed = {
        'b2a_models': b2a_models, 'b2a_report': {'packages': list(pkgs.values())}, 'b2a_config': {'package_pins': pins},
        'catalog': [], 'b4a3_contract': {'sources': {'models': {'sha256': fake_sha('road_models')}, 'catalog': {'sha256': fake_sha('road_entries')}, 'source_table': {'sha256': fake_sha('road_source_table')}}},
        'b4a3_summary': {'contract_sha': fake_sha('b4a3_contract'), 'catalog_pins': {'catalog_sha256': fake_sha('road_entries'), 'models_sha256': fake_sha('road_models'), 'source_table_sha256': fake_sha('road_source_table')}, 'pbo': {'path': pbo_path, 'sha256': roads_sha, 'prefix': 'dz/structures/roads'}},
        'road_models': road_models, 'road_entries': [], 'b4b0_contract': {}, 'b4b0_report': {'contract_sha256': fake_sha('b4b0_contract'), 'table': table, 'issues': issues},
        'b4b0_consumer': {'contract_sha256': fake_sha('b4b0_contract')}, 'b4b0_recovery_receipt': {'source_report_sha256': fake_sha('b4b0_report'), 'consumer_sha256': fake_sha('b4b0_consumer')},
        'b2a_correction_receipt': {'unchanged_geometry_artifacts': {'models.json': fake_sha('b2a_models')}}, 'b2a_code_adjudication': {'final_code_sha256': fake_sha('b2a_code')},
        'road_execution_approval': {'pins': {'road_code.py': fake_sha('road_catalog_code')}}, 'road_report': {'pbo_sha256': roads_sha}, 'road_inputs': {pbo_path: roads_sha}, 'road_source_table': {},
    }
    sources = {}
    for sid, p in parsed.items():
        sources[sid] = {'parsed': p, 'sha256': fake_sha(sid), 'bytes': 1, 'path': (sid + '.json')}
    for sid in ('b2a_code', 'road_catalog_code'):
        sources[sid] = {'parsed': None, 'sha256': fake_sha(sid), 'bytes': 1, 'path': ('road_code.py' if sid == 'road_catalog_code' else 'b2a_code.py')}
    sources['oracles'] = {'parsed': {}, 'sha256': fake_sha('oracles'), 'bytes': 1, 'path': 'oracles.json'}
    sources['road_execution_approval']['parsed'] = {'pins': {sources['road_catalog_code']['path']: fake_sha('road_catalog_code')}}
    inputs = [{'source_id': s, 'sha256': sources[s]['sha256'], 'bytes': 1} for s in sorted(sources)]
    hist_null = 1 if hist is None else 0
    contract = {'schema': 'road-b4b1.v1', 'scope': 'SAVED_CONTENT_IDENTITY_ONLY', 'claims': copy.deepcopy(CLAIMS), 'method_binding': {'b2a': {'state': 'METHOD_UNVERIFIED'}, 'road_catalog': {'state': 'METHOD_DECLARED'}}, 'expected': {'references': 1, 'source_instances': source_instances, 'candidate_instances': source_instances, 'candidate_delta_instances': 0, 'single_pinned_content_references': (1 if distinct == 1 else 0), 'multi_provider_references': (1 if distinct >= 2 else 0), 'historical_conflicts': hist_null, 'historical_conflict_instances': (source_instances if hist_null else 0)}}
    return contract, fake_sha('contract'), sources, inputs
C1 = {'package': 'E:/A.pbo', 'package_sha': '1' * 64, 'prefix': 'DZ/X', 'entry': 'A.P3D', 'model_sha': '2' * 64}
C2 = {'package': 'E:' + chr(92) + 'A.pbo', 'package_sha': '1' * 64, 'prefix': 'dz/x', 'entry': 'a.p3d', 'model_sha': '2' * 64}
class TestNormalization(unittest.TestCase):
    def test_oracles_and_kelvin(self):
        self.assertEqual(io.normalize_path_value('/DZ' + chr(92) + 'Structures' + chr(92) + 'Roads/'), 'dz/structures/roads')
        self.assertEqual(io.normalize_path_value('Parts/Asf1_25.P3D'), 'parts/asf1_25.p3d')
        self.assertEqual(io.normalize_path_value('part.p3d '), 'part.p3d ')
        self.assertEqual(consumer._norm('Parts/Asf1_25.P3D'), 'parts/asf1_25.p3d')
        for bad in ['a//b', 'a/../b', 'C:/a', 'a/./b', '', '..', 'á/b', '\u212a/b', 'a' * 4097]:
            with self.assertRaises(io.InvalidError):
                io.normalize_path_value(bad)
            with self.assertRaises(io.InvalidError):
                consumer._norm(bad)
    def test_joins(self):
        self.assertEqual(io.normalize_join('DZ/X/', '/A.P3D'), 'dz/x/a.p3d')
        with self.assertRaises(io.InvalidError):
            io.normalize_join('dz', 'x//a.p3d')
    def test_jsonl_cr_and_blank(self):
        rows = io.parse_jsonl_physical(b'{"name":"a"}\r\n{"name":"b"}\n')
        self.assertEqual([r['name'] for r in rows], ['a', 'b'])
        with self.assertRaises(io.InvalidError):
            io.parse_jsonl_physical(b'{"name":"a"}\n\n{"name":"b"}\n')
    def test_strict_types(self):
        self.assertFalse(io.is_sha256('A' * 64))
        self.assertTrue(io.is_int_exact(1))
        self.assertFalse(io.is_int_exact(True))
        with self.assertRaises(io.InvalidError):
            io.strict_json_loads(b'{"a":1,"a":2}')
class TestProductionGrouping(unittest.TestCase):
    def test_same_content_different_locator_case(self):
        contract, csha, sources, inputs = mini_case([C1, C2], None, 'UNRESOLVED', [{'code': 'PROVIDER_CONFLICT', 'detail': 'multiple distinct providers for dz/x/a.p3d'}])
        rep = producer.build_report(contract, csha, sources, inputs)
        self.assertEqual(rep['table'][0]['state'], 'SAME_PINNED_CONTENT')
        self.assertEqual(len(rep['table'][0]['groups']), 1)
        self.assertEqual(rep['counts']['multi_provider_references'], 1)
        status, worst = consumer.verify(contract, csha, sources, inputs, rep, fake_sha('report'))
        self.assertEqual(status, 'INCONCLUSIVE_METHOD_BINDING')
    def test_single(self):
        contract, csha, sources, inputs = mini_case([C1], raw_of(C1))
        rep = producer.build_report(contract, csha, sources, inputs)
        self.assertEqual(rep['table'][0]['state'], 'SINGLE_PINNED_CONTENT')
    def test_blocked_groups_counted_negative(self):
        # required_negatives: blocked_groups_counted
        bad = dict(C1); bad['model_sha'] = '4' * 64
        contract, csha, sources, inputs = mini_case([C1, bad], None, 'UNRESOLVED', [{'code': 'PROVIDER_CONFLICT', 'detail': 'multiple distinct providers for dz/x/a.p3d'}])
        rep = producer.build_report(contract, csha, sources, inputs)
        self.assertEqual(rep['table'][0]['state'], 'BLOCKED_SHA_CONFLICT')
        self.assertEqual(rep['table'][0]['groups'], [])
        self.assertEqual(rep['table'][0]['observed_keys'], 2)
        forged = copy.deepcopy(rep); forged['counts']['accepted_groups'] = 1
        with self.assertRaises(io.InvalidError):
            consumer.verify(contract, csha, sources, inputs, forged, fake_sha('r'))
    def test_historical_null_missing_and_nonnull_extra(self):
        # historical_rows: null_missing_provider, nonnull_extra_raw
        contract, csha, sources, inputs = mini_case([C1], None, 'UNRESOLVED', [{'code': 'PROVIDER_CONFLICT', 'detail': 'multiple distinct providers for dz/x/a.p3d'}])
        rep = producer.build_report(contract, csha, sources, inputs)
        self.assertEqual(rep['table'][0]['state'], 'MALFORMED')
        self.assertEqual(rep['table'][0]['issues'][0]['code'], 'HISTORY_PROVIDER_MISMATCH')
        contract, csha, sources, inputs = mini_case([C1, C2], raw_of(C1))
        rep = producer.build_report(contract, csha, sources, inputs)
        self.assertEqual(rep['table'][0]['state'], 'MALFORMED')
class TestConsumerNegatives(unittest.TestCase):
    def setUp(self):
        self.contract, self.csha, self.sources, self.inputs = mini_case([C1, C2], None, 'UNRESOLVED', [{'code': 'PROVIDER_CONFLICT', 'detail': 'multiple distinct providers for dz/x/a.p3d'}])
        self.report = producer.build_report(self.contract, self.csha, self.sources, self.inputs)
    def verify_bad(self, mut):
        bad = copy.deepcopy(self.report); mut(bad)
        with self.assertRaises(io.InvalidError):
            consumer.verify(self.contract, self.csha, self.sources, self.inputs, bad, fake_sha('r'))
    def test_omit_provenance(self):
        self.verify_bad(lambda b: b['table'][0].__setitem__('provenances', []))
    def test_forged_pointer(self):
        self.verify_bad(lambda b: b['table'][0]['provenances'][0].__setitem__('pointer', '/999'))
    def test_duplicate_reference_and_changed_instance_count(self):
        self.verify_bad(lambda b: b['table'].append(copy.deepcopy(b['table'][0])))
        self.verify_bad(lambda b: b['table'][0].__setitem__('source_instances', 99))
    def test_bool_in_count_index_mime(self):
        self.verify_bad(lambda b: b['counts'].__setitem__('references', False))
        self.verify_bad(lambda b: b['table'][0]['groups'][0].__setitem__('provenance_indices', [False, True]))
        self.verify_bad(lambda b: b['table'][0].__setitem__('observed_keys', False))
    def test_expected_mismatch_explicit(self):
        bad_contract = copy.deepcopy(self.contract); bad_contract['expected']['references'] = 999
        with self.assertRaises(io.InvalidError) as cm:
            consumer.verify(bad_contract, self.csha, self.sources, self.inputs, self.report, fake_sha('r'))
        self.assertIn('EXPECTED_COUNT_MISMATCH', str(cm.exception))
        with self.assertRaises(io.InvalidError) as cm2:
            producer.build_report(bad_contract, self.csha, self.sources, self.inputs)
        self.assertIn('EXPECTED_COUNT_MISMATCH', str(cm2.exception))
def build_case(tmp):
    tmp = Path(tmp); tmp.mkdir(parents=True, exist_ok=True)
    roads_sha = sha(b'roads-pbo'); pilot_sha = sha(b'pilot-pbo')
    bridges = [('dz/structures/roads/bridges/bridge_metal_25.p3d', 15), ('dz/structures/roads/bridges/bridge_wood_25.p3d', 8), ('dz/structures/roads/bridges/bridge_wood_50.p3d', 4), ('dz/structures/roads/bridges/bridge_wood_50_1.p3d', 1)]
    news = ['dz/structures/roads/parts/asf1_25.p3d', 'dz/structures/roads/parts/asf2_25.p3d', 'dz/structures/roads/parts/asf1_10 100.p3d']
    def model_sha(name):
        return sha(('model:' + name).encode())
    b2a_models = []; table = []; issues = []
    for name, inst in bridges:
        entry = name.split('dz/structures/roads/')[1]
        b2a_models.append({'name': name, 'sha256': model_sha(name), 'package': 'E:' + chr(92) + 'Addons' + chr(92) + 'structures_roads.pbo', 'entry': entry})
        table.append({'name': name, 'aliases': [], 'source_instances': inst, 'candidate_instances': inst, 'provider': None, 'state': 'UNRESOLVED'})
        issues.append({'code': 'PROVIDER_CONFLICT', 'detail': 'multiple distinct providers for ' + name})
    single_name = 'baltic_stream_pilot/cs_1.p3d'
    b2a_models.append({'name': single_name, 'sha256': model_sha(single_name), 'package': 'E:' + chr(92) + 'Addons' + chr(92) + 'baltic_stream_pilot.pbo', 'entry': 'cs_1.p3d'})
    table.append({'name': single_name, 'aliases': [], 'source_instances': 1, 'candidate_instances': 1, 'provider': {'package': 'E:' + chr(92) + 'Addons' + chr(92) + 'baltic_stream_pilot.pbo', 'package_sha256': pilot_sha, 'prefix': 'baltic_stream_pilot', 'entry': 'cs_1.p3d', 'model_sha256': model_sha(single_name)}, 'state': 'PROVIDER_RESOLVED'})
    road_entries = []; road_models = []
    for name, inst in bridges:
        rel = name.split('dz/structures/roads/')[1]
        road_entries.append({'name': rel, 'normalized_name': rel, 'size': 10, 'mime': 0, 'sha256': model_sha(name)})
        road_models.append({'name': rel, 'sha256': model_sha(name), 'status': 'READ_STRICT'})
    for name in news:
        rel = name.split('dz/structures/roads/')[1]
        road_entries.append({'name': rel, 'normalized_name': rel, 'size': 10, 'mime': 0, 'sha256': model_sha(name)})
        road_models.append({'name': rel, 'sha256': model_sha(name), 'status': 'READ_STRICT'})
        table.append({'name': name, 'aliases': [], 'source_instances': 0, 'candidate_instances': 1, 'provider': {'package': 'E:/Addons/structures_roads.pbo', 'package_sha256': roads_sha, 'prefix': 'dz/structures/roads', 'entry': rel, 'model_sha256': model_sha(name)}, 'state': 'NEW_REFERENCE_WITH_B4A3_PIN'})
    files = {}
    def put(key, fname, data):
        p = tmp / fname; p.write_bytes(data); files[key] = {'path': str(p), 'sha256': sha(data), 'bytes': len(data)}; return p
    put('b2a_models', 'b2a_models.json', jb(b2a_models))
    put('b2a_report', 'b2a_report.json', jb({'packages': [{'path': 'E:' + chr(92) + 'Addons' + chr(92) + 'structures_roads.pbo', 'sha256': roads_sha, 'prefix': 'dz/structures/roads'}, {'path': 'E:' + chr(92) + 'Addons' + chr(92) + 'baltic_stream_pilot.pbo', 'sha256': pilot_sha, 'prefix': 'baltic_stream_pilot'}]}))
    put('b2a_config', 'b2a_config.json', jb({'package_pins': {'E:' + chr(92) + 'Addons' + chr(92) + 'structures_roads.pbo': roads_sha, 'E:' + chr(92) + 'Addons' + chr(92) + 'baltic_stream_pilot.pbo': pilot_sha}}))
    put('catalog', 'catalog.json', jb([]))
    rm_data = b''.join((json.dumps(x, sort_keys=True) + chr(10)).encode() for x in road_models)
    put('road_models', 'road_models.jsonl', rm_data)
    put('road_entries', 'road_entries.json', jb(road_entries))
    put('road_source_table', 'road_source_table.json', jb({}))
    b4a3_sources = {'models': {'sha256': files['road_models']['sha256']}, 'catalog': {'sha256': files['road_entries']['sha256']}, 'source_table': {'sha256': files['road_source_table']['sha256']}}
    for name in news:
        b4a3_sources['previous:assets/' + name] = {'sha256': model_sha(name)}
    put('b4a3_contract', 'b4a3_contract.json', jb({'sources': b4a3_sources}))
    put('b4a3_summary', 'b4a3_summary.json', jb({'contract_sha': files['b4a3_contract']['sha256'], 'catalog_pins': {'catalog_sha256': files['road_entries']['sha256'], 'models_sha256': files['road_models']['sha256'], 'source_table_sha256': files['road_source_table']['sha256']}, 'pbo': {'path': 'E:/Addons/structures_roads.pbo', 'sha256': roads_sha, 'prefix': 'dz/structures/roads'}}))
    put('b4b0_contract', 'b4b0_contract.json', jb({'schema': 'road-b4b0.v1'}))
    # deliberately non-alphabetical order to prove original-index pointers: reverse bridges order in file
    table_file = list(reversed(table))
    put('b4b0_report', 'b4b0_report.json', jb({'contract_sha256': files['b4b0_contract']['sha256'], 'table': table_file, 'issues': issues}))
    put('b4b0_consumer', 'b4b0_consumer.json', jb({'contract_sha256': files['b4b0_contract']['sha256']}))
    put('b4b0_recovery_receipt', 'receipt.json', jb({'source_report_sha256': files['b4b0_report']['sha256'], 'consumer_sha256': files['b4b0_consumer']['sha256']}))
    put('b2a_correction_receipt', 'b2a_correction_receipt.json', jb({'unchanged_geometry_artifacts': {'models.json': files['b2a_models']['sha256']}}))
    put('road_report', 'road_report.json', jb({'pbo_sha256': roads_sha}))
    put('road_inputs', 'road_inputs.json', jb({'E:/Addons/structures_roads.pbo': roads_sha}))
    methods = {}
    code_paths = {}
    for key, fname in [('b2a_code', 'b2a_code.py'), ('road_catalog_code', 'road_code.py')]:
        data = ('# sealed ' + key + chr(10)).encode(); p = tmp / fname; p.write_bytes(data); methods[key] = {'path': str(p), 'sha256': sha(data), 'bytes': len(data)}; code_paths[key] = str(p)
    put('b2a_code_adjudication', 'b2a_code_adjudication.json', jb({'final_code_sha256': methods['b2a_code']['sha256']}))
    put('road_execution_approval', 'road_execution_approval.json', jb({'pins': {code_paths['road_catalog_code']: methods['road_catalog_code']['sha256']}}))
    oracles_data = jb({}); op = tmp / 'oracles.json'; op.write_bytes(oracles_data)
    contract = {'schema': 'road-b4b1.v1', 'scope': 'SAVED_CONTENT_IDENTITY_ONLY', 'files': files, 'methods': methods, 'oracles': {'path': str(op), 'sha256': sha(oracles_data), 'bytes': len(oracles_data)}, 'expected': {'references': 8, 'source_instances': 29, 'candidate_instances': 32, 'candidate_delta_instances': 3, 'historical_conflicts': 4, 'historical_conflict_instances': 28, 'single_pinned_content_references': 4, 'multi_provider_references': 4}, 'claims': copy.deepcopy(CLAIMS), 'method_binding': {'b2a': {'state': 'METHOD_UNVERIFIED'}, 'road_catalog': {'state': 'METHOD_DECLARED'}}}
    cdata = jb(contract); cpath = tmp / 'contract.json'; cpath.write_bytes(cdata)
    return cpath, sha(cdata), tmp
def run_cli(args):
    return subprocess.run([sys.executable] + args, capture_output=True, text=True, timeout=30)
class TestCLI(unittest.TestCase):
    def test_producer_consumer_assets_and_negatives(self):
        with tempfile.TemporaryDirectory() as td:
            cpath, csha, tmp = build_case(Path(td) / 'case')
            report = Path(td) / 'report.json'; receipt = Path(td) / 'receipt.json'
            r = run_cli([str(ROOT / 'tools' / 'quality' / 'road_content_identity_ev112.py'), '--contract', str(cpath), '--contract-sha', csha, '--output', str(report)])
            self.assertEqual(r.returncode, 2, r.stderr)
            data = json.loads(report.read_text())
            self.assertEqual(data['status'], 'INCONCLUSIVE_METHOD_BINDING')
            self.assertEqual(data['counts']['single_provider_references'], 4)
            # new assets must be accepted: proves removeprefix asset key in consumer reconstruction
            new_rows = [x for x in data['table'] if x['source_instances'] == 0]
            self.assertEqual(len(new_rows), 3)
            self.assertTrue(all(x['state'] == 'SINGLE_PINNED_CONTENT' for x in new_rows))
            r2 = run_cli([str(ROOT / 'tools' / 'quality' / 'verify_road_content_identity_ev112.py'), '--contract', str(cpath), '--contract-sha', csha, '--report', str(report), '--output', str(receipt)])
            self.assertEqual(r2.returncode, 2, r2.stderr)
            bad = copy.deepcopy(data); bad['counts']['by_state']['MALFORMED'] = False
            badp = Path(td) / 'bad.json'; badp.write_text(json.dumps(bad))
            out2 = Path(td) / 'receipt2.json'
            r3 = run_cli([str(ROOT / 'tools' / 'quality' / 'verify_road_content_identity_ev112.py'), '--contract', str(cpath), '--contract-sha', csha, '--report', str(badp), '--output', str(out2)])
            self.assertEqual(r3.returncode, 1); self.assertFalse(out2.exists())
            out3 = Path(td) / 'no.json'
            r4 = run_cli([str(ROOT / 'tools' / 'quality' / 'road_content_identity_ev112.py'), '--contract', str(cpath), '--contract-sha', csha.upper(), '--output', str(out3)])
            self.assertEqual(r4.returncode, 1); self.assertFalse(out3.exists())
class TestContractCoverage(unittest.TestCase):
    def make(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        cp, sh, _ = build_case(Path(td.name) / 'case')
        return io.load_pinned_bundle(cp, sh)

    def test_frozen_oracles_on_production(self):
        raw = (ROOT / 'tests/fixtures/road_b4b1/oracles-r2.json').read_bytes()
        self.assertEqual(sha(raw), '596c815885ed18ca3e3a244e5e5d8148797f0c7cf212c8d7ac434595b30200b9')
        oracle = json.loads(raw)
        for o in oracle['grouping']:
            with self.subTest(o['id']):
                hist = raw_of(o['input'][0]) if len(o['input']) == 1 else None
                issues = [] if hist else [{'code':'PROVIDER_CONFLICT','detail':'multiple distinct providers for '+o['virtual']}]
                c,h,s,i = mini_case(o['input'],hist,issues=issues,name=o['virtual'])
                if o['id']=='invalid_virtual':c['expected']['single_pinned_content_references']=0
                r = producer.build_report(c,h,s,i)
                # The grouping-only empty oracle is UNRESOLVED. Full R2 history
                # gives MALFORMED first: null history requires >=2 raw providers.
                state='MALFORMED' if o['id']=='missing_package_lookup' else o['state']
                self.assertEqual(r['table'][0]['state'],state)
                self.assertEqual(len(r['table'][0]['groups']),o['groups'])
                consumer.verify(c,h,s,i,r,fake_sha('r'))
        for o in oracle['historical_rows']:
            with self.subTest(o['id']):
                hist = raw_of(o['historical_provider']) if o['historical_provider'] else None
                c,h,s,i = mini_case(o['candidates'],hist,o['historical_state'],o['issues'],o['name'])
                r=producer.build_report(c,h,s,i)
                self.assertEqual(r['table'][0]['state'],o['expected_state'])
                consumer.verify(c,h,s,i,r,fake_sha('r'))

    def test_method_cases_and_missing_method_no_code_promotion(self):
        raw=json.loads((ROOT/'tests/fixtures/road_b4b1/oracles-r2.json').read_bytes())
        for ix,o in enumerate(raw['method_cases']):
            candidates = [C1,C2] if ix==0 else [C1]
            if ix==2:
                other=dict(C2);other.update(package='B.pbo',package_sha='3'*64);candidates=[C1,other]
            hist=raw_of(C1) if len(candidates)==1 else None
            c,h,s,i=mini_case(candidates,hist,issues=[] if hist else [{'code':'PROVIDER_CONFLICT','detail':'multiple distinct providers for dz/x/a.p3d'}])
            c['method_binding']['b2a']['state']=o['states'][0]
            r=producer.build_report(c,h,s,i)
            self.assertEqual((r['status'],r['method_binding_global']),(o['global'],o['method_binding_global']))
            consumer.verify(c,h,s,i,r,fake_sha('r'))
        c,h,s,i=self.make();del c['method_binding']['b2a']['state']
        for fn in (lambda:producer.build_report(c,h,s,i),lambda:consumer.reconstruct(c,s)):
            with self.assertRaisesRegex(io.InvalidError,'method'):fn()

    def test_every_required_receipt_binding_missing_or_changed(self):
        c,h,s,i=self.make()
        changes=[('b4b0_report','contract_sha256'),('b4b0_consumer','contract_sha256'),('b4b0_recovery_receipt','source_report_sha256'),('b4b0_recovery_receipt','consumer_sha256'),('b4a3_summary','contract_sha'),('b4a3_summary','catalog_pins'),('b4a3_contract','sources'),('b2a_code_adjudication','final_code_sha256'),('b2a_correction_receipt','unchanged_geometry_artifacts'),('road_execution_approval','pins'),('road_report','pbo_sha256')]
        for sid,key in changes:
            with self.subTest(sid=sid,key=key):
                bad=copy.deepcopy(s);del bad[sid]['parsed'][key]
                for fn in (lambda:producer.build_report(c,h,bad,i),lambda:consumer.reconstruct(c,bad)):
                    with self.assertRaises(io.InvalidError):fn()
                def changed(value):
                    if type(value)is str and io.is_sha256(value):return 'f'*64 if value!='f'*64 else 'e'*64
                    if type(value)is dict:
                        out=copy.deepcopy(value)
                        for k,v in out.items():
                            try:out[k]=changed(v);return out
                            except ValueError:pass
                    raise ValueError('no SHA leaf')
                bad=copy.deepcopy(s);bad[sid]['parsed'][key]=changed(bad[sid]['parsed'][key])
                for fn in (lambda:producer.build_report(c,h,bad,i),lambda:consumer.reconstruct(c,bad)):
                    with self.assertRaises(io.InvalidError):fn()
        bad=copy.deepcopy(s);bad['b4b0_consumer']['parsed']='an executable path, not a JSON result'
        for fn in (lambda:producer.build_report(c,h,bad,i),lambda:consumer.reconstruct(c,bad)):
            with self.assertRaisesRegex(io.InvalidError,'object'):fn()

    def test_original_pointer_resolves_after_ordering(self):
        c,h,s,i=self.make(); source=s['b4b0_report']['parsed']
        idx=next(j for j,r in enumerate(source['table']) if r['source_instances']==0)
        source['table'][idx]['provider']['entry']='wrong.p3d'
        r=producer.build_report(c,h,s,i)
        row=next(x for x in r['table'] if x['name']==source['table'][idx]['name'])
        self.assertEqual(row['state'],'MALFORMED')
        self.assertEqual(row['issues'][0]['pointer'],'/table/'+str(idx))
        self.assertEqual(io.resolve_pointer(source,row['issues'][0]['pointer'])['name'],row['name'])
        consumer.verify(c,h,s,i,r,fake_sha('r'))

    def test_invalid_history_fails_before_report_and_bad_names_not_silent(self):
        c,h,s,i=self.make()
        for field,value in [('aliases',[False]),('state',None),('provider',{'wrong':'keys'})]:
            bad=copy.deepcopy(s);bad['b4b0_report']['parsed']['table'][0][field]=value
            for fn in (lambda:producer.build_report(c,h,bad,i),lambda:consumer.reconstruct(c,bad)):
                with self.assertRaisesRegex(io.InvalidError,'history|historical_provider'):fn()
        for sid in ('road_models','b2a_models'):
            bad=copy.deepcopy(s);bad[sid]['parsed'][0]['name']='\u212a/../bad.p3d'
            for fn in (lambda:producer.build_report(c,h,bad,i),lambda:consumer.reconstruct(c,bad)):
                with self.assertRaisesRegex(io.InvalidError,sid+'/0: invalid name'):fn()

    def test_road_rejections_record_reasons(self):
        # Counts remain literal when excluding one of two raw candidates: adjust only
        # fixture denominator to the independently known 5 single / 3 multi.
        for field,val,reason in [('mime',1,'mime_nonzero'),('mime',False,'mime_nonzero'),('sha256','4'*64,'model_entry_sha_mismatch')]:
            with self.subTest(field=field,val=val):
                c,h,s,i=self.make();s['road_entries']['parsed'][0][field]=val
                c['expected']['single_pinned_content_references']=5;c['expected']['multi_provider_references']=3
                r=producer.build_report(c,h,s,i)
                row=next(x for x in r['table'] if 'bridge_metal_25' in x['name'])
                self.assertEqual(row['state'],'MALFORMED')
                self.assertEqual(row['rejected_provenances'][0]['reason'],reason)
                consumer.verify(c,h,s,i,r,fake_sha('r'))
        c,h,s,i=self.make();s['road_models']['parsed'][0]['status']='FAILED'
        c['expected']['single_pinned_content_references']=5;c['expected']['multi_provider_references']=3
        r=producer.build_report(c,h,s,i)
        self.assertTrue(any(p['reason']=='road_not_READ_STRICT' for x in r['table'] for p in x['rejected_provenances']))
        consumer.verify(c,h,s,i,r,fake_sha('r'))

    def test_asset_mismatch_and_exact_locator_joins(self):
        c,h,s,i=self.make();key=next(k for k in s['b4a3_contract']['parsed']['sources'] if k.startswith('previous:assets/'))
        s['b4a3_contract']['parsed']['sources'][key]['sha256']='5'*64
        c['expected']['single_pinned_content_references']=3
        r=producer.build_report(c,h,s,i)
        self.assertTrue(any(p['reason']=='previous_asset_sha_mismatch' for x in r['table'] for p in x['rejected_provenances']))
        consumer.verify(c,h,s,i,r,fake_sha('r'))
        c,h,s,i=self.make();s['b2a_models']['parsed'][0]['package']=s['b2a_models']['parsed'][0]['package'].replace(chr(92),'/')
        c['expected']['single_pinned_content_references']=5;c['expected']['multi_provider_references']=3
        r=producer.build_report(c,h,s,i)
        self.assertTrue(any(p['reason']=='missing_package_lookup' for x in r['table'] for p in x['rejected_provenances']))
        consumer.verify(c,h,s,i,r,fake_sha('r'))

    def test_conflict_literal_and_history_comutation(self):
        c,h,s,i=self.make();s['b4b0_report']['parsed']['issues'][0]['detail']+=' changed'
        r=producer.build_report(c,h,s,i)
        self.assertTrue(any(x['state']=='MALFORMED' for x in r['table']))
        consumer.verify(c,h,s,i,r,fake_sha('r'))
        forged=copy.deepcopy(r);row=next(x for x in forged['table'] if x['state']=='MALFORMED')
        row['state']='SAME_PINNED_CONTENT';row['issues']=[];row['historical_issue_pointer']='/issues/0'
        with self.assertRaises(io.InvalidError):consumer.verify(c,h,s,i,forged,fake_sha('r'))

    def test_all_expected_counters_and_types(self):
        c,h,s,i=self.make();r=producer.build_report(c,h,s,i)
        for key in producer.EXPECTED_KEYS:
            bad=copy.deepcopy(c);bad['expected'][key]+=1
            for fn in (lambda:producer.build_report(bad,h,s,i),lambda:consumer.verify(bad,h,s,i,r,fake_sha('r'))):
                with self.assertRaisesRegex(io.InvalidError,'EXPECTED_COUNT_MISMATCH'):fn()
        bad=copy.deepcopy(r);bad['table'][0]['groups'][0]['provenance_indices']=[False]
        with self.assertRaises(io.InvalidError):consumer.verify(c,h,s,i,bad,fake_sha('r'))

    def test_io_caps_before_open_and_reparse_and_no_binary_input(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as td:
            cp,ch,_=build_case(Path(td)/'case');contract=json.loads(cp.read_bytes())
            contract['files']['b2a_models']['bytes']=io.MAX_FILE+1
            cp.write_bytes(jb(contract));ch=sha(cp.read_bytes())
            real=io.stable_read;calls=[]
            def watched(p,*a,**kw):calls.append(str(p));return real(p,*a,**kw)
            with patch.object(io,'stable_read',side_effect=watched):
                with self.assertRaisesRegex(io.InvalidError,'before read'):io.load_pinned_bundle(cp,ch)
            self.assertEqual(calls,[str(cp)])
            out=Path(td)/'too-large.json'
            with self.assertRaisesRegex(io.InvalidError,'before create'):io.write_exclusive(out,b'1234',3)
            self.assertFalse(out.exists())
            with patch.object(io,'MAX_FILE',12):
                with self.assertRaisesRegex(io.InvalidError,'before retain'):io.dump_json({'key':'too much serialized output'})
            with patch.object(io,'_is_reparse',return_value=True):
                with self.assertRaisesRegex(io.InvalidError,'non-reparse'):io.stable_read(cp)
            cp,ch,_=build_case(Path(td)/'case2');allowed=[];realopen=io.os.open
            def guarded(p,*a,**kw):
                self.assertNotIn(Path(p).suffix.lower(),('.wrp','.pbo','.p3d','.paa','.rvmat','.npz'));allowed.append(str(p));return realopen(p,*a,**kw)
            with patch.object(io.os,'open',side_effect=guarded):
                c,h,s,i=io.load_pinned_bundle(cp,ch);r=producer.build_report(c,h,s,i);consumer.verify(c,h,s,i,r,fake_sha('r'))
            self.assertTrue(allowed)

if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    print('tests_run=' + str(result.testsRun))
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun > 0 else 1)
