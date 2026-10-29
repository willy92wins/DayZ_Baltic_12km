import hashlib, importlib.util, json, os, sys, tempfile, types, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MOD_PATH = ROOT / "tools" / "quality" / "road_source_stability_ev112.py"
HELPER_PATH = ROOT / "tools" / "quality" / "road_build_discovery_ev112.py"
spec = importlib.util.spec_from_file_location("road_source_stability_ev112", MOD_PATH)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def sha(b): return hashlib.sha256(b).hexdigest()
def write(p, b): p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b); return p

MODELS = ["dz/structures/roads/parts/asf1_25.p3d","dz/structures/roads/parts/asf2_25.p3d","dz/structures/roads/parts/asf1_10 100.p3d"]
REFS = ["dz/structures/roads/parts/data/asf1_dashedline.rvmat","dz/structures/roads/parts/data/asf1_dashedline_ca.paa","dz/structures/roads/parts/data/asf2_dashedline.rvmat","dz/structures/roads/parts/data/asf2_dashedline_ca.paa"]
EXT = "dz/surfaces/data/roadway/asphalt_ext.paa"
CONTENTS = {}
for i, n in enumerate(MODELS): CONTENTS[n] = b"ODOL" + bytes([65+i])*64
for i, n in enumerate(REFS): CONTENTS[n] = ("class Cfg { texture = %d; };\n" % i).encode() * 4

def clone_stat(s, ctime_delta=0, ino_delta=0, attrs=None):
    return types.SimpleNamespace(st_dev=s.st_dev, st_ino=s.st_ino+ino_delta, st_size=s.st_size, st_mtime=s.st_mtime, st_ctime=s.st_ctime, st_mtime_ns=getattr(s,"st_mtime_ns",int(s.st_mtime*1e9)), st_ctime_ns=getattr(s,"st_ctime_ns",int(s.st_ctime*1e9))+ctime_delta, st_mode=s.st_mode, st_file_attributes=(getattr(s,"st_file_attributes",0) or 0) if attrs is None else attrs, st_reparse_tag=getattr(s,"st_reparse_tag",0) or 0)

class World:
    pass

def build_world(base):
    w = World(); w.base = Path(base); w.root = w.base / "DayZ Projects"; w.root_str = str(w.root)
    w.helper_sha = sha(HELPER_PATH.read_bytes())
    mod.EXPECTED_HELPER_SHA256 = w.helper_sha
    helper_spec = importlib.util.spec_from_file_location("_test_helper", HELPER_PATH); hm = importlib.util.module_from_spec(helper_spec); helper_spec.loader.exec_module(hm); w.helper_mod = hm
    for n, data in CONTENTS.items(): write(w.root.joinpath(*n.split("/")), data)
    w.catalog_models = write(w.base/"catalog"/"models.jsonl", b"{}\n"); w.catalog_entries = write(w.base/"catalog"/"entries.json", b"[]\n")
    w.old_contract_path = w.base/"old"/"contract.json"
    old = {"build_root":w.root_str,"build_alias":"P:/","catalog_models":str(w.catalog_models),"catalog_entries":str(w.catalog_entries)}
    write(w.old_contract_path, json.dumps(old, sort_keys=True).encode())
    w.old_sha = sha(w.old_contract_path.read_bytes())
    models=[]; refs=[]
    for n in MODELS: models.append({"model":n,"entry":n.split("parts/",1)[1],"catalog_sha256":sha(CONTENTS[n]),"pbo_sha256":sha(CONTENTS[n]),"catalog_status":"READ_STRICT","pbo_status":"MATCH","build_status":"SOURCE_UNSTABLE","build":{"normalized":n,"path":os.path.join(w.root_str,*n.split("/")),"status":"SOURCE_UNSTABLE","format":"UNKNOWN","prefix16":None,"sha256":None,"size":None,"stable":False}})
    for n in REFS: refs.append({"normalized":n,"entry":n.split("parts/",1)[1],"expected_sha256":sha(CONTENTS[n]),"pbo_sha256":sha(CONTENTS[n]),"status":"SOURCE_UNSTABLE","build":{"normalized":n,"path":os.path.join(w.root_str,*n.split("/")),"status":"SOURCE_UNSTABLE","format":"UNKNOWN","prefix16":None,"sha256":None,"size":None,"stable":False}})
    refs.append({"normalized":EXT,"status":"UNRESOLVED_EXTERNAL","raws":[EXT.replace("/", chr(92))]})
    w.report_path = w.base/"r0"/"report.json"
    report = {"schema":"road-build-discovery.v1","contract_sha256":w.old_sha,"tool_sha256":w.helper_sha,"build_alias":{"alias":"P:/","root":w.root_str},"models":models,"references":refs,"build_ready":False}
    write(w.report_path, json.dumps(report, sort_keys=True).encode()); w.report_sha = sha(w.report_path.read_bytes())
    w.manifest_path = w.base/"r0"/"manifest.json"
    manifest = {"schema":"road-build-discovery.v1.manifest","report_sha256":w.report_sha,"contract_sha256":w.old_sha,"tool_sha256":w.helper_sha,"integrity_scope":"manifest_hashes_only_not_semantic_acceptance"}
    write(w.manifest_path, json.dumps(manifest, sort_keys=True).encode()); w.manifest_sha = sha(w.manifest_path.read_bytes())
    pins = {str(w.report_path):w.report_sha,str(w.manifest_path):w.manifest_sha,str(w.old_contract_path):w.old_sha,str(HELPER_PATH):w.helper_sha,str(w.catalog_models):sha(w.catalog_models.read_bytes()),str(w.catalog_entries):sha(w.catalog_entries.read_bytes())}
    files=[]
    for n in MODELS: files.append({"kind":"model","name":n,"path":os.path.join(w.root_str,*n.split("/")),"reference_sha256":sha(CONTENTS[n]),"reference_format":"UNKNOWN"})
    for n in REFS: files.append({"kind":"reference","name":n,"path":os.path.join(w.root_str,*n.split("/")),"reference_sha256":sha(CONTENTS[n]),"reference_format":"UNKNOWN"})
    w.contract = {"schema":"road-build-source-stability.v1","r0_report":str(w.report_path),"r0_manifest":str(w.manifest_path),"r0_contract":str(w.old_contract_path),"helper":str(HELPER_PATH),"pins":pins,"alias":"P:/","root":w.root_str,"files":files,"external_references":[EXT],"seconds":30,"max_bytes":268435456}
    w.contract_path = w.base/"contract.json"; write(w.contract_path, json.dumps(w.contract, sort_keys=True).encode()); w.contract_sha = sha(w.contract_path.read_bytes())
    w.query = lambda alias, h=w.helper_mod, r=w.root_str: h.expected_mapping(r)
    w.out = w.base/"out"
    return w

@unittest.skipUnless(HELPER_PATH.exists(), "actual pinned helper not present")
class StabilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.w = build_world(Path(self.tmp.name))
    def tearDown(self): self.tmp.cleanup()
    def runw(self, **kw):
        kw.setdefault("query_dos_device_fn", self.w.query)
        return mod.run_stability(str(self.w.contract_path), self.w.contract_sha, str(self.w.out), **kw)
    def rewrite_contract(self):
        write(self.w.contract_path, json.dumps(self.w.contract, sort_keys=True).encode()); self.w.contract_sha = sha(self.w.contract_path.read_bytes())
    def test_stable_control_exact_statuses(self):
        r = self.runw(); self.assertEqual(r["source_stability"],"STABLE_CAPTURE"); self.assertEqual(r["status"],"DISCOVERY_ONLY"); self.assertEqual(r["overall"],"DISCOVERY_ONLY"); self.assertFalse(r["build_ready"]); self.assertTrue(all(f["reference_status"]=="MATCH" for f in r["files"])); self.assertEqual(r["files"][0]["format"],"ODOL")
    def test_external_not_promoted_never_inputs_match(self):
        r = self.runw(); self.assertNotEqual(r.get("aggregate"),"INPUTS_MATCH"); self.assertEqual(r["external_references"],[{"normalized":EXT,"status":"UNRESOLVED_EXTERNAL"}]); self.assertTrue(r["incomplete_coverage"])
    def test_ctime_differs_path_vs_handle_but_stable_each_api(self):
        prov={"stat":lambda p: clone_stat(os.stat(p), ctime_delta=111000),"lstat":lambda p: clone_stat(os.lstat(p), ctime_delta=111000),"fstat":lambda fd: clone_stat(os.fstat(fd), ctime_delta=222000)}
        r=self.runw(providers=prov); self.assertEqual(r["source_stability"],"STABLE_CAPTURE")
    def test_byte_change_between_reads_mtime_restored(self):
        target = self.w.root.joinpath(*MODELS[0].split("/")); orig = target.read_bytes(); st0 = target.stat()
        class Changing:
            def __init__(s, f): s.f=f; s.seeks=0
            def __enter__(s): return s
            def __exit__(s,*a): return s.f.__exit__(*a)
            def fileno(s): return s.f.fileno()
            def read(s,n=-1): return s.f.read(n)
            def seek(s,o,w=0):
                s.seeks+=1
                if s.seeks==2:
                    target.write_bytes(bytes([orig[0]^1])+orig[1:]); os.utime(target, ns=(st0.st_atime_ns, st0.st_mtime_ns))
                return s.f.seek(o,w)
        prov={"open":lambda p,m: Changing(open(p,m)) if str(p)==str(target) else open(p,m)}
        r=self.runw(providers=prov); self.assertEqual(r["source_stability"],"INCONCLUSIVE_SOURCE_STABILITY"); f=[x for x in r["files"] if x["name"]==MODELS[0]][0]; self.assertFalse(dict((p["name"],p["value"]) for p in f["predicates"])["read1_sha256_eq_read2_sha256"])
    def test_changed_file_id(self):
        calls={"n":0}
        def fake_fstat(fd):
            calls["n"]+=1; s=os.fstat(fd); return clone_stat(s, ino_delta=999) if calls["n"]>1 else s
        r=self.runw(providers={"fstat":fake_fstat}); self.assertEqual(r["source_stability"],"INCONCLUSIVE_SOURCE_STABILITY")
    def test_ancestor_change(self):
        dz = str(self.w.root/"dz"); calls={"n":0}
        def fake_lstat(p):
            s=os.lstat(p)
            if str(p)==dz:
                calls["n"]+=1
                if calls["n"]>1: return clone_stat(s, ino_delta=777)
            return s
        r=self.runw(providers={"lstat":fake_lstat}); self.assertEqual(r["source_stability"],"INCONCLUSIVE_SOURCE_STABILITY")
    def test_reparse_blocked_before_open(self):
        target = str(self.w.root.joinpath(*MODELS[0].split("/"))); opened=[]
        def fake_lstat(p):
            s=os.lstat(p); return clone_stat(s, attrs=0x400) if str(p)==target else s
        snap = mod.capture_file(self.w.contract["files"][0], helper={"stat_tuple":self.w.helper_mod.stat_tuple,"ident_tuple":self.w.helper_mod.ident_tuple,"is_link":self.w.helper_mod.is_link,"expected_mapping":self.w.helper_mod.expected_mapping,"win_norm":self.w.helper_mod.win_norm,"detect_format":self.w.helper_mod.detect_format}, root=self.w.root_str, alias="P:/", query_fn=self.w.query, check_deadline=lambda: None, progress=lambda s: None, providers={"lstat":fake_lstat,"open":lambda p,m: opened.append(p) or open(p,m)})
        self.assertEqual(snap["status"],"UNRESOLVED_LINK"); self.assertEqual(opened,[])
    def test_bad_pin_r0_no_report(self):
        self.w.report_path.write_bytes(b"tampered")
        with self.assertRaises(ValueError): self.runw()
        self.assertFalse((self.w.out/"report.json").exists()); self.assertTrue((self.w.out/"partial.json").exists())
    def test_omit_duplicate_extra_contract_files(self):
        for mutate in ("omit","dup","extra"):
            with self.subTest(mutate=mutate):
                w2 = build_world(Path(self.tmp.name)/mutate)
                if mutate=="omit": w2.contract["files"]=w2.contract["files"][:-1]
                elif mutate=="dup": w2.contract["files"]=w2.contract["files"]+[dict(w2.contract["files"][0])]
                else: w2.contract["files"]=w2.contract["files"]+[{"kind":"reference","name":"dz/extra.paa","path":os.path.join(w2.root_str,"dz","extra.paa"),"reference_sha256":sha(b"x"),"reference_format":"UNKNOWN"}]
                write(w2.contract_path, json.dumps(w2.contract, sort_keys=True).encode()); cs=sha(w2.contract_path.read_bytes())
                with self.assertRaises(ValueError): mod.run_stability(str(w2.contract_path), cs, str(w2.base/"out2"), query_dos_device_fn=w2.query)
    def test_forward_slash_root_canonical_paths_and_wrong_root_rejected(self):
        root_fwd = self.w.root_str.replace(chr(92), "/")
        files = [dict(f) for f in self.w.contract["files"]]
        report = {"models":[{"model":f["name"],"catalog_sha256":f["reference_sha256"],"pbo_sha256":f["reference_sha256"],"build":{"normalized":f["name"],"path":f["path"]}} for f in files if f["kind"]=="model"],"references":[{"normalized":f["name"],"expected_sha256":f["reference_sha256"],"pbo_sha256":f["reference_sha256"],"build":{"normalized":f["name"],"path":f["path"]}} for f in files if f["kind"]=="reference"]+[{"normalized":EXT}]}
        contract = dict(self.w.contract); contract["root"] = root_fwd; contract["files"] = [dict(f) for f in files]
        exp = mod.derive_expected_files(report, contract)
        self.assertEqual([e["path"] for e in exp], [f["path"] for f in files])
        self.assertEqual(contract["root"], root_fwd); self.assertEqual(self.w.contract["root"], self.w.root_str)
        sibling = dict(contract); sibling["root"] = root_fwd.rsplit("/", 1)[0] + "/DayZ Projects Sibling"; sibling["files"] = [dict(f) for f in files]
        with self.assertRaises(ValueError): mod.derive_expected_files(report, sibling)
        noncanon = dict(contract); bad_files = [dict(f) for f in files]; bad_files[0] = dict(bad_files[0]); bad_files[0]["path"] = root_fwd + "/" + bad_files[0]["name"]; noncanon["files"] = bad_files
        with self.assertRaises(ValueError): mod.derive_expected_files(report, noncanon)
    def test_pinned_bytes_changed_in_parse_window_not_parsed(self):
        import builtins, io
        from unittest import mock
        real_open = builtins.open; target = str(self.w.report_path); calls = {"n":0}
        def fake_open(file, mode="r", *a, **kw):
            if str(file) == target and mode == "rb":
                calls["n"] += 1
                if calls["n"] == 2: return io.BytesIO(b'{"unparsed_sentinel":')
            return real_open(file, mode, *a, **kw)
        with mock.patch("builtins.open", side_effect=fake_open):
            with self.assertRaises(ValueError) as cm: self.runw()
        self.assertIn("pinned_bytes_changed_before_parse", str(cm.exception)); self.assertNotIn("invalid_json", str(cm.exception))
    def test_contract_bounds_seconds_and_max_bytes(self):
        for key, val in (("seconds", 31), ("seconds", 30.0001), ("max_bytes", 268435457)):
            with self.subTest(key=key, val=val):
                bad = dict(self.w.contract); bad[key] = val; p = write(self.w.base/("badbound_%s_%s.json" % (key, val)), json.dumps(bad).encode())
                with self.assertRaises(ValueError): mod.run_stability(str(p), sha(p.read_bytes()), str(self.w.base/("outbound_%s_%s" % (key, val))), query_dos_device_fn=self.w.query)
    def test_deadline_checked_per_streaming_chunk(self):
        class Slow:
            def __init__(s, f): s.f = f
            def __enter__(s): return s
            def __exit__(s, *a): return s.f.__exit__(*a)
            def fileno(s): return s.f.fileno()
            def seek(s, o, w=0): return s.f.seek(o, w)
            def read(s, n=-1): return s.f.read(1)
        helper = {k: getattr(self.w.helper_mod, k) for k in ("stat_tuple", "ident_tuple", "is_link", "expected_mapping", "win_norm", "detect_format")}
        calls = {"n":0}; seen = []
        def deadline():
            calls["n"] += 1
            if calls["n"] >= 5: raise mod.CaptureDeadline("chunk_deadline")
        with self.assertRaises(TimeoutError):
            mod.capture_file(self.w.contract["files"][0], helper=helper, root=self.w.root_str, alias="P:/", query_fn=self.w.query, check_deadline=deadline, progress=lambda s: seen.append(s), providers={"open": lambda p, m: Slow(open(p, m))})
        self.assertTrue(seen); self.assertNotIn("read1", seen[-1])
    def test_unreadable_ancestor_blocks_before_open(self):
        dz = str(self.w.root/"dz"); opened = []
        def fake_lstat(p):
            if str(p) == dz: raise PermissionError("ancestor_unreadable_sentinel")
            return os.lstat(p)
        helper = {k: getattr(self.w.helper_mod, k) for k in ("stat_tuple", "ident_tuple", "is_link", "expected_mapping", "win_norm", "detect_format")}
        snap = mod.capture_file(self.w.contract["files"][0], helper=helper, root=self.w.root_str, alias="P:/", query_fn=self.w.query, check_deadline=lambda: None, progress=lambda s: None, providers={"lstat": fake_lstat, "open": lambda p, m: opened.append(p) or open(p, m)})
        self.assertEqual(snap["status"], "UNREADABLE"); self.assertEqual(opened, []); self.assertTrue(any("ancestor_unreadable_sentinel" in e["error"] for e in snap["errors"]))
    def test_mapping_literal_bytes_from_hex_and_double_prefix(self):
        h=self.w.helper_mod; exp=h.expected_mapping(self.w.root_str)
        raw_utf16 = exp.encode("utf-16-le") + b"\x00\x00" + "historical".encode("utf-16-le") + b"\x00\x00"
        ok, first, _ = mod.mapping_current(bytes.fromhex(raw_utf16.hex()), self.w.root_str, {"expected_mapping":h.expected_mapping,"win_norm":h.win_norm}); self.assertTrue(ok); self.assertEqual(first, exp)
        ok2, _, _ = mod.mapping_current(chr(92)+exp, self.w.root_str, {"expected_mapping":h.expected_mapping,"win_norm":h.win_norm}); self.assertFalse(ok2)
    def test_missing_file_exact_inconclusive(self):
        os.unlink(self.w.root.joinpath(*REFS[0].split("/"))); r=self.runw(); self.assertEqual(r["source_stability"],"INCONCLUSIVE_SOURCE_STABILITY"); self.assertEqual(r["status"],"DISCOVERY_ONLY"); f=[x for x in r["files"] if x["name"]==REFS[0]][0]; self.assertEqual(f["status"],"MISSING")
    def test_early_eof_size_guard(self):
        target = str(self.w.root.joinpath(*MODELS[1].split("/")))
        class Short:
            def __init__(s,f): s.f=f; s.done=False
            def __enter__(s): return s
            def __exit__(s,*a): return s.f.__exit__(*a)
            def fileno(s): return s.f.fileno()
            def seek(s,o,w=0): s.done=False; return s.f.seek(o,w)
            def read(s,n=-1):
                if s.done: return b""
                s.done=True; return s.f.read(3)
        prov={"open":lambda p,m: Short(open(p,m)) if str(p)==target else open(p,m)}
        r=self.runw(providers=prov); self.assertEqual(r["source_stability"],"INCONCLUSIVE_SOURCE_STABILITY"); f=[x for x in r["files"] if x["name"]==MODELS[1]][0]; self.assertFalse(dict((p["name"],p["value"]) for p in f["predicates"])["read1_count_eq_fstat_before_size"])
    def test_timeout_partial_and_inconclusive_report(self):
        class Clock:
            def __init__(s): s.t=0.0
            def __call__(s): s.t+=100.0; return s.t
        r=self.runw(monotonic=Clock()); self.assertEqual(r["source_stability"],"INCONCLUSIVE_SOURCE_STABILITY"); self.assertEqual(r["status"],"DISCOVERY_ONLY"); self.assertTrue((self.w.out/"partial.json").exists())
    def test_contract_hash_checked_before_json_and_bool_rejected(self):
        with self.assertRaises(ValueError): mod.run_stability(str(self.w.contract_path), sha(b"wrong"), str(self.w.base/"outbad"), query_dos_device_fn=self.w.query)
        bad=dict(self.w.contract); bad["seconds"]=True; p=write(self.w.base/"bad.json", json.dumps(bad).encode())
        with self.assertRaises(ValueError): mod.run_stability(str(p), sha(p.read_bytes()), str(self.w.base/"outbad2"), query_dos_device_fn=self.w.query)

    def test_timeout_never_claims_reverified_inputs(self):
        class Clock:
            def __init__(s): s.t=0
            def __call__(s): s.t+=100; return s.t
        r=self.runw(monotonic=Clock())
        self.assertEqual(r["r0_unchanged"], "NOT_VERIFIED")
    def test_os_read_timeout_is_not_budget_timeout(self):
        def timeout_open(path, mode): raise TimeoutError("os_read_timeout_sentinel")
        r=self.runw(providers={"open":timeout_open})
        self.assertEqual(r["source_stability"], "INCONCLUSIVE_SOURCE_STABILITY")
        self.assertTrue(all(f["status"]=="UNREADABLE" for f in r["files"]))
        self.assertTrue(all(f["errors"][0]["error"]=="os_read_timeout_sentinel" for f in r["files"]))
        self.assertTrue(r["r0_unchanged"])
    def test_drive_relative_name_rejected(self):
        import copy
        c=copy.deepcopy(self.w.contract); c["files"][0]["name"]="C:foo.p3d"
        with self.assertRaisesRegex(ValueError,"bad_relative_name"): mod.validate_contract(c)
    def test_report_distinguishes_helper_from_new_producer(self):
        r=self.runw()
        self.assertEqual(r["helper_sha256"],self.w.helper_sha)
        self.assertEqual(r["r0_tool_sha256"],self.w.helper_sha)
        self.assertNotIn("tool_sha256",r)
        self.assertEqual(r["format_sample_bytes"],16)

if __name__ == "__main__": unittest.main()
