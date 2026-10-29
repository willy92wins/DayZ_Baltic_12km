import ast, hashlib, io, json, struct, sys, time, unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'quality'))
import road_installed_material_probe_ev112 as probe

def sha(b): return hashlib.sha256(b).hexdigest()
def pack(prefix, entries):
    out = bytearray(); payload = bytearray()
    for name, mime, data in entries: out += name.encode() + b'\x00' + struct.pack('<5I', mime, 0, 0, 0, len(data))
    if prefix is not None: out += b'\x00' + struct.pack('<5I', 0x56657273, 0, 0, 0, 0) + b'prefix\x00' + prefix.encode() + b'\x00' + b'\x00'
    out += b'\x00' + struct.pack('<5I', 0, 0, 0, 0, 0)
    for name, mime, data in entries: payload += data
    return bytes(out + payload)
HELPER = "import struct\nBSL=chr(92)\ndef require(c,m):\n if not bool(c): raise ValueError(m)\ndef exact(f,n):\n r=f.read(n); require(len(r)==n,'truncated_pbo'); return r\ndef string(f):\n r=bytearray()\n for _ in range(4096):\n  c=exact(f,1)\n  if c==bytes(1): return r.decode('utf-8')\n  r.extend(c)\n raise ValueError('unbounded_pbo_string')\ndef unsafe_raw(raw):\n if not isinstance(raw,str) or raw=='': return True\n if raw.strip()!=raw: return True\n q=raw.replace(BSL,'/')\n if ':' in q: return True\n if q.startswith('/'): return True\n parts=q.split('/')\n if any(p in ('','.','..') for p in parts): return True\n return False\ndef pbo_table(f,length):\n entries,properties,seen=[],{},set()\n while True:\n  name=string(f); mime,original,reserved,timestamp,size=struct.unpack('<5I',exact(f,20))\n  if not name:\n   if mime==0x56657273:\n    while True:\n     k=string(f)\n     if not k: break\n     require(k not in properties,'duplicate_property'); properties[k]=string(f)\n    continue\n   require(not any((mime,original,reserved,timestamp,size)),'invalid_pbo_sentinel'); break\n  require(not unsafe_raw(name),'unsafe_pbo_path')\n  key=name.replace(BSL,'/').lower()\n  require(key not in seen,'duplicate_pbo_path'); seen.add(key)\n  entries.append(dict(name=key,mime=mime,size=size)); require(len(entries)<=100000,'pbo_entry_budget')\n off=f.tell()\n for e in entries:\n  e['offset']=off; off+=e['size']; require(off<=length,'truncated_pbo_payload')\n return properties,entries\n"
SEL = [('model', 'dz/structures/roads/parts/asf1_25.p3d', 'parts/asf1_25.p3d', b'P3D-ONE'), ('model', 'dz/structures/roads/parts/asf2_25.p3d', 'parts/asf2_25.p3d', b'P3D-TWO'), ('model', 'dz/structures/roads/parts/asf1_10 100.p3d', 'parts/asf1_10 100.p3d', b'P3D-THREE'), ('material', 'dz/structures/roads/parts/data/asf1_dashedline.rvmat', 'parts/data/asf1_dashedline.rvmat', None), ('texture', 'dz/structures/roads/parts/data/asf1_dashedline_ca.paa', 'parts/data/asf1_dashedline_ca.paa', b'PAA-ONE'), ('material', 'dz/structures/roads/parts/data/asf2_dashedline.rvmat', 'parts/data/asf2_dashedline.rvmat', None), ('texture', 'dz/structures/roads/parts/data/asf2_dashedline_ca.paa', 'parts/data/asf2_dashedline_ca.paa', b'PAA-TWO')]
EXT = 'dz/surfaces/data/roadway/asphalt_ext.paa'
def ok_conv(original, decoded, receipt, timeout, max_bytes):
    Path(receipt).mkdir(parents=True, exist_ok=True); Path(decoded).write_bytes(b'DECODED-TEXT'); return {'rc': 0, 'reason': None}
class FakeRunner:
    def __init__(self, mode='ok'): self.mode = mode; self.calls = 0
    def run(self, job):
        self.calls += 1; receipt = Path(job['out']); receipt.mkdir(parents=True, exist_ok=True); decoded = Path(job['command'][3]); decoded.parent.mkdir(parents=True, exist_ok=True); decoded.write_bytes(b'DECODED-TEXT')
        stdout = b'stdout-bytes'; stderr = b'stderr-bytes'; (receipt / 'stdout.bin').write_bytes(stdout); (receipt / 'stderr.bin').write_bytes(stderr)
        if self.mode == 'missing': return {'rc': 0, 'reason': None, 'stdout_sha256': sha(stdout), 'stderr_sha256': sha(stderr)}
        birth = 'birth-1'; (receipt / 'running.json').write_text(json.dumps({'pid': 4321, 'birth': birth})); completion = {'rc': 0, 'reason': None, 'identities': {'4321': 'birth-2' if self.mode == 'badbirth' else birth}, 'stdout_sha256': sha(stdout), 'stderr_sha256': sha(stderr)}; (receipt / 'completion.json').write_text(json.dumps(completion))
        return {'rc': 0, 'reason': None, 'stdout_sha256': sha(stdout), 'stderr_sha256': sha(stderr)}
class ProbeTests(unittest.TestCase):
    def build(self, root, *, mat=b'class A {};', surfaces=None, bliss=None, roads_entries=None, roads_mime=None, limits=None, duplicate_models=False, entry_sha_bad=False, tamper_selected=False, only_lod3=False, catalog_alias=False, r0_model_alias=False, entries_wrap=False, drop_roads_entry=False, drop_catalog_entry=False):
        tmp = Path(root); tmp.mkdir(parents=True, exist_ok=True); mats = [mat, mat]; content = {}; selected = []; cat_entries = []; rentries = []; mi = 0
        for kind, vp, entry, blob in SEL:
            data = mats[mi] if kind == 'material' else blob
            if kind == 'material': mi += 1
            content[vp] = data; selected.append({'kind': kind, 'virtual_path': vp, 'entry': entry, 'sha256': sha(data)})
            esha = '0' * 64 if (entry_sha_bad and entry == SEL[0][2]) else sha(data)
            mime = (roads_mime or {}).get(entry, 0); cat_entries.append({'name': entry, 'normalized_name': entry, 'category': kind, 'size': len(data), 'mime': mime, 'sha256': esha}); rentries.append((entry, mime, data))
        if roads_entries is not None: rentries = roads_entries
        if drop_roads_entry: rentries = [r for r in rentries if r[0] != SEL[0][2]]
        if drop_catalog_entry: cat_entries = cat_entries[:-1]
        roads = pack('DZ\\structures\\roads', rentries); roads_p = tmp / 'roads.pbo'; roads_p.write_bytes(roads)
        if surfaces is None: surfaces = ('DZ\\surfaces', [('data/roadway/asphalt_ext.paa', 0, b'EXT-DATA')])
        if bliss is None: bliss = ('DZ\\surfaces', [])
        sp = tmp / 'surfaces.pbo'; sp.write_bytes(pack(surfaces[0], surfaces[1])); bp = tmp / 'bliss.pbo'; bp.write_bytes(pack(bliss[0], bliss[1]))
        refs_vp = [s[1] for s in SEL if s[0] != 'model'] + [EXT]; lods = [{'index': 3 if only_lod3 else 0, 'textures': [s[1] for s in SEL if s[0] == 'texture'] + [EXT], 'materials': [s[1] for s in SEL if s[0] == 'material'], 'sections': []}]
        rows = [{'name': vp if catalog_alias else entry, 'sha256': sha(content[vp]), 'status': 'READ_STRICT', 'measurement': {'lods': lods}} for kind, vp, entry, blob in SEL[:3]]
        if duplicate_models: rows.append(dict(rows[0]))
        models_p = tmp / 'models.jsonl'; models_p.write_text(''.join(json.dumps(r) + '\n' for r in rows))
        entries_p = tmp / 'entries.json'; entries_p.write_text(json.dumps({'entries': cat_entries} if entries_wrap else cat_entries))
        helper = tmp / 'helper.py'; helper.write_text(HELPER); helper_sha = sha(helper.read_bytes())
        r0c = tmp / 'r0contract.json'; r0c.write_text(json.dumps({'schema': 'road-build-discovery.v1.contract'})); r0c_sha = sha(r0c.read_bytes())
        def builddoc(vp, entry, data): return {'format': 'UNKNOWN', 'normalized': vp, 'path': 'C:\\x\\' + vp, 'prefix16': None, 'sha256': None, 'size': None, 'stable': False, 'status': 'SOURCE_UNSTABLE'}
        models_doc = []
        for kind, vp, entry, blob in SEL[:3]: models_doc.append({'build': builddoc(vp, entry, content[vp]), 'build_status': 'SOURCE_UNSTABLE', 'catalog_sha256': sha(content[vp]), 'catalog_status': 'READ_STRICT', 'entry': entry, 'model': entry if r0_model_alias else vp, 'pbo_sha256': sha(content[vp]), 'pbo_status': 'MATCH'})
        refs_doc = []
        for kind, vp, entry, blob in SEL[3:]: refs_doc.append({'build': builddoc(vp, entry, content[vp]), 'entry': entry, 'expected_sha256': sha(content[vp]), 'lod_indexes': [0], 'models': [SEL[0][1]], 'normalized': vp, 'pbo_sha256': sha(content[vp]), 'raws': [vp.replace('/', chr(92))], 'status': 'SOURCE_UNSTABLE'})
        refs_doc.append({'lod_indexes': [3], 'models': [s[1] for s in SEL[:3]], 'normalized': EXT, 'raws': [EXT.replace('/', chr(92))], 'status': 'UNRESOLVED_EXTERNAL'})
        report_p = tmp / 'r0report.json'; report_p.write_text(json.dumps({'schema': 'road-build-discovery.v1.report', 'contract_sha256': r0c_sha, 'tool_sha256': helper_sha, 'models': models_doc, 'references': refs_doc}))
        manifest_p = tmp / 'r0manifest.json'; manifest_p.write_text(json.dumps({'contract_sha256': r0c_sha, 'integrity_scope': 'manifest_hashes_only_not_semantic_acceptance', 'report_sha256': sha(report_p.read_bytes()), 'schema': 'road-build-discovery.v1.manifest', 'tool_sha256': helper_sha}))
        b4contract = sha(b'b4a1-contract-v1')
        b4_p = tmp / 'b4report.json'; b4_p.write_text(json.dumps({'schema': 'road-build-source-stability.v1', 'contract_sha256': b4contract, 'helper_sha256': helper_sha, 'build_ready': False, 'overall': 'DISCOVERY_ONLY', 'r0_contract_sha256': r0c_sha, 'r0_manifest_sha256': sha(manifest_p.read_bytes()), 'r0_report_sha256': sha(report_p.read_bytes()), 'r0_tool_sha256': helper_sha}))
        appr_p = tmp / 'approval.json'; appr_p.write_text(json.dumps({'status': 'REVIEWED_FOR_ONE_CAPTURE', 'tool_sha256': sha(b'b4a1-tool'), 'contract_sha256': b4contract}))
        runner = tmp / 'runner.py'; runner.write_text('# pinned fake runner, not imported with injected converter\n'); cfg = tmp / 'CfgConvert.exe'; cfg.write_bytes(b'FAKEEXE')
        psroot = tmp / 'psroot'; (psroot / 'psutil').mkdir(parents=True); (psroot / 'psutil' / '__init__.py').write_text('# ps\n')
        sources = {'r0_report': str(report_p), 'r0_manifest': str(manifest_p), 'r0_contract': str(r0c), 'b4a1_report': str(b4_p), 'b4a1_approval': str(appr_p), 'catalog_models': str(models_p), 'catalog_entries': str(entries_p)}
        pins = {p: sha(Path(p).read_bytes()) for p in list(sources.values()) + [str(helper), str(runner), str(cfg), str(psroot / 'psutil' / '__init__.py')]}
        use_selected = [dict(s) for s in selected]
        if tamper_selected: use_selected[0] = dict(use_selected[0]); use_selected[0]['sha256'] = '1' * 64
        contract = {'schema': 'ROAD_INSTALLED_MATERIAL_PROBE_V1', 'sources': sources, 'pins': pins, 'helper': str(helper), 'runner': str(runner), 'psutil_root': str(psroot), 'cfgconvert': str(cfg), 'pbos': {'roads': {'path': str(roads_p), 'sha256': sha(roads), 'bytes': len(roads), 'prefix': 'DZ\\structures\\roads'}, 'surfaces': {'path': str(sp), 'bytes': sp.stat().st_size}, 'surfaces_bliss': {'path': str(bp), 'bytes': bp.stat().st_size}}, 'selected': use_selected, 'external': [EXT], 'limits': limits or {'seconds': 120, 'rss_bytes': 536870912, 'conversion_seconds': 30, 'conversions': 2, 'resource_bytes': 16777216, 'total_output_bytes': 67108864}}
        cp = tmp / 'contract.json'; data = json.dumps(contract).encode(); cp.write_bytes(data)
        return cp, sha(data), tmp
    def run_case(self, name='a', **kw):
        import tempfile; td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup); root = Path(td.name) / name; converter = kw.pop('converter', None); factory = kw.pop('converter_factory', None); cp, h, fixture = self.build(root, **kw); out = fixture / 'out'
        if converter is not None: r = probe.run_discovery(cp, h, out, converter=converter)
        elif factory is not None: r = probe.run_discovery(cp, h, out, converter_factory=factory)
        else: r = probe.run_discovery(cp, h, out)
        return r, out, fixture, cp, h
    def build_only(self, name='a', **kw):
        import tempfile; td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup); return self.build(Path(td.name) / name, **kw)
    def test_positive_end_to_end_and_consume(self):
        r, out, fixture, cp, h = self.run_case(); self.assertEqual(r['status'], 'INITIAL_DISCOVERY_ONLY'); self.assertFalse(r['build_ready']); self.assertEqual(r['dependency_closure'], 'NOT_EVALUATED'); self.assertEqual(len([a for a in r['assets'] if a['provider'] == 'roads']), 7); self.assertEqual(r['external'][0]['status'], 'RESOLVED'); self.assertIn(EXT, r['all_lod_refs']); m = probe.consume_saved_manifest(out, sha((out / 'manifest.json').read_bytes()), h); self.assertFalse(m['references_closed'])
    def test_helper_ast_require_and_immutable_same_fixture(self):
        cp, h, fixture = self.build_only(); helper = fixture / 'helper.py'; before = sha(helper.read_bytes()); tree = ast.parse(helper.read_text()); names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}; self.assertIn('require', names); pins = json.loads(cp.read_text())['pins']; fn = probe.load_helper_pbo_table(str(helper), pins); self.assertIn('require', fn.__globals__); props, entries = fn(io.BytesIO(pack('DZ\\x', [('a/b.paa', 0, b'XY')])), 9999); self.assertEqual(props.get('prefix'), 'DZ\\x'); r = probe.run_discovery(cp, h, fixture / 'out'); self.assertEqual(sha(helper.read_bytes()), before)
    def test_pin_changed_before_parse(self):
        cp, h, fixture = self.build_only(); (fixture / 'r0report.json').write_text('not json')
        with self.assertRaises(Exception) as cm: probe.run_discovery(cp, h, fixture / 'out')
        self.assertIn('pin_changed_before_parse', str(cm.exception))
    def test_contract_sha_mismatch_no_out_created(self):
        cp, h, fixture = self.build_only()
        with self.assertRaises(Exception): probe.run_discovery(cp, '0' * 64, fixture / 'out')
        self.assertFalse((fixture / 'out').exists())
    def test_existing_output_refused_no_write(self):
        cp, h, fixture = self.build_only(); out = fixture / 'out'; out.mkdir(); (out / 'sentinel.txt').write_text('keep')
        with self.assertRaises(Exception): probe.run_discovery(cp, h, out)
        self.assertEqual((out / 'sentinel.txt').read_text(), 'keep'); self.assertFalse((out / 'report.json').exists())
    def test_selected_binding_tamper_fails(self):
        cp, h, fixture = self.build_only(tamper_selected=True)
        with self.assertRaises(Exception): probe.run_discovery(cp, h, fixture / 'out')
    def test_missing_prefix_inconclusive_not_resolved(self):
        r, out, fixture, cp, h = self.run_case(surfaces=(None, [('data/roadway/asphalt_ext.paa', 0, b'X')])); self.assertTrue(r['external'][0]['status'].startswith('INCONCLUSIVE')); self.assertEqual(r['status'], 'INCONCLUSIVE_INITIAL_DISCOVERY')
    def test_wrong_basename_not_resolved_when_prefixes_known(self):
        r, out, fixture, cp, h = self.run_case(surfaces=('DZ\\surfaces', [('data/other/asphalt_ext.paa', 0, b'X')])); self.assertEqual(r['external'][0]['status'], 'UNRESOLVED_EXTERNAL')
    def test_ambiguous_two_providers(self):
        both = ('DZ\\surfaces', [('data/roadway/asphalt_ext.paa', 0, b'X')]); r, out, fixture, cp, h = self.run_case(surfaces=both, bliss=both); self.assertEqual(r['external'][0]['status'], 'AMBIGUOUS_PROVIDER')
    def test_traversal_rejected(self):
        entries = [('../evil.paa', 0, b'X')] + [(s[2], 0, b'Y') for s in SEL]
        with self.assertRaises(Exception): self.run_case(roads_entries=entries)
    def test_duplicate_pbo_entry_rejected(self):
        dup = ('DZ\\surfaces', [('data/roadway/asphalt_ext.paa', 0, b'A'), ('data/roadway/asphalt_ext.paa', 0, b'B')])
        with self.assertRaises(Exception): self.run_case(surfaces=dup)
    def test_duplicate_catalog_model_rejected(self):
        with self.assertRaises(Exception): self.run_case(duplicate_models=True)
    def test_external_compression_inconclusive(self):
        r, out, fixture, cp, h = self.run_case(surfaces=('DZ\\surfaces', [('data/roadway/asphalt_ext.paa', 7, b'X')])); self.assertEqual(r['external'][0]['status'], 'INCONCLUSIVE_UNSUPPORTED_COMPRESSION'); self.assertEqual(r['status'], 'INCONCLUSIVE_INITIAL_DISCOVERY')
    def test_selected_compression_inconclusive(self):
        r, out, fixture, cp, h = self.run_case(roads_mime={SEL[4][2]: 3}); self.assertTrue(any(a.get('status') == 'INCONCLUSIVE_UNSUPPORTED_COMPRESSION' for a in r['assets'])); self.assertEqual(r['status'], 'INCONCLUSIVE_INITIAL_DISCOVERY')
    def test_rvmat_text_no_semantic_claim(self):
        r, out, fixture, cp, h = self.run_case(mat=b'class A {};'); self.assertTrue(all(a.get('material_status') == 'TEXT_SAMPLE' for a in r['assets'] if a['kind'] == 'material')); self.assertNotIn('material_semantics', json.dumps(r))
    def test_rvmat_unknown_inconclusive_aggregate(self):
        r, out, fixture, cp, h = self.run_case(mat=b'\xff\xfe\x00\x99'); self.assertTrue(all(a.get('material_status') == 'UNKNOWN' for a in r['assets'] if a['kind'] == 'material')); self.assertEqual(r['status'], 'INCONCLUSIVE_INITIAL_DISCOVERY')
        with self.assertRaises(Exception): probe.consume_saved_manifest(out, sha((out / 'manifest.json').read_bytes()), h)
    def test_rap_converter_ok(self):
        r, out, fixture, cp, h = self.run_case(mat=b'\x00raPxxxx', converter=ok_conv); self.assertTrue(all(a.get('material_status') == 'DECODED_SAMPLE_ONLY' for a in r['assets'] if a['kind'] == 'material'))
    def test_rap_converter_bad_rc(self):
        r, out, fixture, cp, h = self.run_case(mat=b'\x00raPxxxx', converter=lambda *a: {'rc': 3, 'reason': None}); self.assertTrue(all(a.get('material_status') == 'CONVERSION_FAILED' for a in r['assets'] if a['kind'] == 'material'))
    def test_rap_converter_reason_timeout(self):
        r, out, fixture, cp, h = self.run_case(mat=b'\x00raPxxxx', converter=lambda *a: {'rc': 0, 'reason': 'TIMEOUT'}); self.assertTrue(all(a.get('material_status') == 'CONVERSION_TIMEOUT' for a in r['assets'] if a['kind'] == 'material'))
    def test_rap_converter_empty(self):
        r, out, fixture, cp, h = self.run_case(mat=b'\x00raPxxxx', converter=lambda *a: {'rc': 0, 'reason': None}); self.assertTrue(all(a.get('material_status') == 'CONVERSION_EMPTY' for a in r['assets'] if a['kind'] == 'material'))
    def test_converter_mutates_input_detected(self):
        def bad(o, d, receipt, t, m): Path(o).write_bytes(b'CHANGED'); return {'rc': 0, 'reason': None}
        with self.assertRaises(Exception): self.run_case(mat=b'\x00raPxxxx', converter=bad)
    def test_strict_json_limits_and_extra_field(self):
        with self.assertRaises(Exception): probe.strict_loads(b'{\"x\":NaN}')
        cp, h, fixture = self.build_only(limits={'seconds': True, 'rss_bytes': 536870912, 'conversion_seconds': 30, 'conversions': 2, 'resource_bytes': 16777216, 'total_output_bytes': 67108864})
        with self.assertRaises(Exception): probe.run_discovery(cp, h, fixture / 'out')
        cp2, h2, fixture2 = self.build_only('b'); c = json.loads(cp2.read_text()); c['approvals'] = []; data = json.dumps(c).encode(); cp2.write_bytes(data)
        with self.assertRaises(Exception): probe.run_discovery(cp2, sha(data), fixture2 / 'out')
    def test_max_resource_limit(self):
        lim = {'seconds': 120, 'rss_bytes': 536870912, 'conversion_seconds': 30, 'conversions': 2, 'resource_bytes': 4, 'total_output_bytes': 67108864}
        with self.assertRaises(Exception): self.run_case(limits=lim)
    def test_manifest_mutation_zero_and_wrong_contract(self):
        r, out, fixture, cp, h = self.run_case(); p = out / r['assets'][0]['local_path']; p.write_bytes(b'MUTATED!')
        with self.assertRaises(Exception): probe.consume_saved_manifest(out, sha((out / 'manifest.json').read_bytes()), h)
        r2, out2, fixture2, cp2, h2 = self.run_case('b')
        with self.assertRaises(Exception): probe.consume_saved_manifest(out2, sha((out2 / 'manifest.json').read_bytes()), '0' * 64)
        mp = out2 / 'manifest.json'; m = json.loads(mp.read_text()); m['artifacts'] = []; mp.write_text(json.dumps(m))
        with self.assertRaises(Exception): probe.consume_saved_manifest(out2, sha(mp.read_bytes()), h2)
    def test_fake_complete_status_rejected(self):
        r, out, fixture, cp, h = self.run_case(); mp = out / 'manifest.json'; m = json.loads(mp.read_text()); m['status'] = 'DEPENDENCY_SET_CLOSED_CONDITIONAL'; mp.write_text(json.dumps(m))
        with self.assertRaises(Exception): probe.consume_saved_manifest(out, sha(mp.read_bytes()), h)
    def test_pbo_size_range_rejected(self):
        cp, h, fixture = self.build_only(); c = json.loads(cp.read_text()); c['pbos']['roads']['bytes'] += 1; data = json.dumps(c).encode(); cp.write_bytes(data)
        with self.assertRaises(Exception): probe.run_discovery(cp, sha(data), fixture / 'out')
    def test_safe_local_raw_before_norm(self):
        import tempfile; td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup); out = Path(td.name) / 'o'; out.mkdir()
        for bad in ('/../evil', 'a/../b', 'C:/evil', 'a//b', '/abs', 'a:b'):
            with self.assertRaises(Exception): probe._safe_local(out, bad)
    def test_catalog_entry_bad_sha_rejected(self):
        with self.assertRaises(Exception): self.run_case(entry_sha_bad=True)
    def test_scope_shaped_sources_and_wrongful_aliases(self):
        cp, h, fixture = self.build_only(); entries = json.loads((fixture / 'entries.json').read_text()); self.assertIsInstance(entries, list); self.assertEqual([e['name'] for e in entries], [s[2] for s in SEL])
        rows = [json.loads(x) for x in (fixture / 'models.jsonl').read_text().splitlines()]; self.assertEqual([r['name'] for r in rows], [s[2] for s in SEL[:3]]); r0 = json.loads((fixture / 'r0report.json').read_text()); self.assertEqual([m['model'] for m in r0['models']], [s[1] for s in SEL[:3]])
        for kw in ({'catalog_alias': True}, {'r0_model_alias': True}, {'entries_wrap': True}):
            with self.assertRaises(Exception): self.run_case('alias', **kw)
    def test_lod3_only_refs_still_bind(self):
        r, out, fixture, cp, h = self.run_case(only_lod3=True); self.assertEqual(r['status'], 'INITIAL_DISCOVERY_ONLY'); self.assertIn(EXT, r['all_lod_refs'])
    def test_missing_catalog_entry_in_roads_table(self):
        with self.assertRaises(Exception) as cm: self.run_case(drop_roads_entry=True)
        self.assertIn('catalog_entry_table_mismatch', str(cm.exception))
    def test_missing_catalog_entry_rejected(self):
        with self.assertRaises(Exception): self.run_case(drop_catalog_entry=True)
    def test_other_provider_prefix_same_basename_not_resolved(self):
        r, out, fixture, cp, h = self.run_case(surfaces=('DZ\\other', [('data/roadway/asphalt_ext.paa', 0, b'X')])); self.assertEqual(r['external'][0]['status'], 'UNRESOLVED_EXTERNAL')
    def test_total_output_limit_exhaustion(self):
        lim = {'seconds': 120, 'rss_bytes': 536870912, 'conversion_seconds': 30, 'conversions': 2, 'resource_bytes': 16777216, 'total_output_bytes': 10}
        with self.assertRaises(Exception) as cm: self.run_case(limits=lim)
        self.assertIn('total_limit_exceeded', str(cm.exception))
    def test_consume_recomputed_manifest_omitted_asset_and_replaced_artifact(self):
        r, out, fixture, cp, h = self.run_case(); mp = out / 'manifest.json'; m = json.loads(mp.read_text()); omitted = dict(m); omitted['assets'] = m['assets'][:-1]; mp.write_text(json.dumps(omitted))
        with self.assertRaises(Exception): probe.consume_saved_manifest(out, sha(mp.read_bytes()), h)
        r2, out2, fixture2, cp2, h2 = self.run_case('b'); mp2 = out2 / 'manifest.json'; m2 = json.loads(mp2.read_text()); replaced = dict(m2); arts = [dict(a) for a in m2['artifacts']]; arts[0] = dict(arts[1]); replaced['artifacts'] = arts; mp2.write_text(json.dumps(replaced))
        with self.assertRaises(Exception): probe.consume_saved_manifest(out2, sha(mp2.read_bytes()), h2)
    def test_factory_mock_runner_receipts(self):
        cp, h, fixture = self.build_only(); contract = json.loads(cp.read_text()); original = fixture / 'orig.rvmat'; original.write_bytes(b'\x00raPxxxx')
        for mode, should_pass in (('ok', True), ('missing', False), ('badbirth', False)):
            fake = FakeRunner(mode); decoded = fixture / ('decoded_' + mode + '.txt'); receipt = fixture / ('receipt_' + mode)
            with mock.patch.object(probe, '_verify_runner_import', return_value=fake):
                convert = probe._default_converter_factory(contract, time.monotonic() + 60, {})()
                if should_pass:
                    result = convert(original, decoded, receipt, 10, 1024); self.assertEqual(result['stdout_sha256'], sha(b'stdout-bytes')); self.assertEqual(result['stderr_sha256'], sha(b'stderr-bytes')); self.assertEqual(result['receipt_completion_sha256'], sha((receipt / 'completion.json').read_bytes()))
                else:
                    with self.assertRaises(Exception): convert(original, decoded, receipt, 10, 1024)
    def test_factory_reuse_once_and_evidence_consume(self):
        calls = {'n': 0}
        def factory(): calls['n'] += 1; return ok_conv
        r, out, fixture, cp, h = self.run_case(mat=b'\x00raPxxxx', converter_factory=factory); self.assertEqual(calls['n'], 1)
        cp2, h2, fixture2 = self.build_only('evidence'); contract = json.loads(cp2.read_text())
        with mock.patch.object(probe, '_verify_runner_import', return_value=FakeRunner('ok')): convert = probe._default_converter_factory(contract, time.monotonic() + 60, {})()
        r2, out2, fixture3, cp3, h3 = self.run_case('evidence2', mat=b'\x00raPxxxx', converter_factory=lambda: convert); m = json.loads((out2 / 'manifest.json').read_text()); self.assertEqual(len(m['evidence_artifacts']), 8); probe.consume_saved_manifest(out2, sha((out2 / 'manifest.json').read_bytes()), h3)
    def test_verify_runner_import_pin_change_rejects(self):
        cp, h, fixture = self.build_only('runnerpin'); contract = json.loads(cp.read_text()); (fixture / 'runner.py').write_text('# tampered\n')
        with self.assertRaises(Exception) as cm: probe._verify_runner_import(contract)
        self.assertIn('runner_pin_changed', str(cm.exception))
        cp2, h2, fixture2 = self.build_only('pspin'); contract2 = json.loads(cp2.read_text()); (fixture2 / 'psroot' / 'psutil' / '__init__.py').write_text('# tampered\n')
        with self.assertRaises(Exception) as cm2: probe._verify_runner_import(contract2)
        self.assertIn('psutil_pin_changed', str(cm2.exception))
if __name__ == '__main__': unittest.main(verbosity=2)
