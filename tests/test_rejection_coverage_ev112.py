import ast
import copy
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
FB = "evidence/visual-tour-20261027/feedback.json"
KIT = "evidence/visual-tour-20261027/kit118-feedback.json"
C65 = "evidence/visual-tour-20261027/continuous65-feedback.json"
R49 = "evidence/visual-tour-20261027/road49-feedback.json"
CROSS = "evidence/visual-tour-20261027/additional-crossing-feedback.json"
RELIEF = "evidence/visual-tour-20261027/relief-east-feedback.json"
FOREST = "evidence/visual-tour-20261027/forest-feedback.json"
C0 = "evidence/visual-tour-20261027/causeway-c0-feedback.json"
TOUR = "evidence/visual-tour-20261027/tour-ended-20261028.json"
OBS = "evidence/native-shore-census-20261028/observations.json"
CTX = "evidence/road-water-census-20261028/contexts.json"
SUMM = "evidence/closed-perimeter-q02a-20261029/summary.json"
IDS = ["NARVA-VIS-01", "NARVA-VIS-02", "NARVA-VIS-03", "KIT118-VIS-01", "KIT118-VIS-02", "CONT65-VIS-01", "ROAD49-RIVER-VIS-01", "CROSSING-VIS-01", "RELIEF-EAST-VIS-01"]
WORLD = "f0e0e6b99da08b48f62ee47fa72b8905a5c9843bee4a30cefa18f517ddb1f603"
PILOT = "3d9550bfb3f27e3916b14579990c240c4aaf4d779e628658ec572cb2c806a2b6"
WATER = "97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43"
MOD = "@DayZ_Baltic_EV112_Kit7Nav8Load1"
POSITIONS = [[2391, 6941], [2391, 6941], [2391, 6941], [8253, 9038], [8253, 9038], [5162, 5865], [5295.7, 5999.9], [4789.51465, 5516.52197], [11790, 2400]]
DOMAINS = ["native_candidate", "road_model_not_evaluated", "native_or_model_unresolved", "model_not_evaluated", "model_road_not_evaluated", "model_not_evaluated", "unknown", "road_model_not_evaluated", "native_candidate"]
STATE_FOR = {"native_candidate": "CONTEXT_ONLY_UNCONFIRMED", "road_model_not_evaluated": "NOT_EVALUATED", "native_or_model_unresolved": "CONTEXT_ONLY_UNCONFIRMED", "model_not_evaluated": "NOT_EVALUATED", "model_road_not_evaluated": "NOT_EVALUATED", "unknown": "NOT_EVALUATED"}

def load_mod(name, rel):
    spec = importlib.util.spec_from_file_location(name, BASE / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

producer = load_mod("producer_ev112", "tools/quality/rejection_coverage_ev112.py")
consumer = load_mod("consumer_ev112", "tools/quality/verify_rejection_coverage_ev112.py")

def sources():
    obs_text = ["L ground", "Bridge misaligned", "Bank edges", "Beds protrude", "Bed overlaps road", "Bed protrudes again", "River zigzags", "Road split by river", "Shore inlets"]
    fb_findings = [{"id": IDS[i], "status": "OPEN", "observed": obs_text[i]} for i in range(3)]
    fb_findings[1]["bridge"] = {"id": IDS[1]}
    return {
        FB: {"status": "VISUAL_REJECTED_BY_USER", "mod": MOD, "world_sha256": WORLD, "pilot_sha256": PILOT, "water_sha256": WATER, "findings": fb_findings, "exact_defect_world_coordinates": "NOT_MEASURED", "dry_bank_candidate_in_game": False, "screens": [{"file": "a.png", "sha256": "d" * 64, "kept_local": True}], "annotated_image": "not archived"},
        KIT: {"status": "VISUAL_REJECTED_BY_USER", "build_identity_reference": "feedback.json", "findings": [{"id": IDS[3 + i], "status": "OPEN", "observed": obs_text[3 + i]} for i in range(2)], "position_scope": "Tour stop", "dry_bank_candidate_in_game": False},
        C65: {"status": "VISUAL_REJECTED_BY_USER", "build_identity_reference": "feedback.json", "findings": [{"id": IDS[5], "status": "OPEN", "observed": obs_text[5]}], "position_scope": "Tour stop", "dry_bank_candidate_in_game": False},
        R49: {"build_identity_reference": "feedback.json", "river_findings": [{"id": IDS[6], "status": "VISUAL_REJECTED_BY_USER", "observed": obs_text[6], "exact_defect_coordinates": "NOT_MEASURED", "river_source_id": None}], "road": {"status": "LOCAL_VISUAL_OK_WITH_PAVING_PENDING", "paving": "PENDING", "driving": "NOT_TESTED", "global_road_acceptance": False, "bug_005_closed": False}, "dry_bank_candidate_in_game": False},
        CROSS: {"id": IDS[7], "status": "USER_REJECTED_ROAD_INTERRUPTED_BY_RIVER", "build_identity_reference": "feedback.json", "user_follow_up": obs_text[7], "coordinates_scope": "At crossing", "native_evidence": {"count_total": 108, "returned_entities": 80, "bridge_detected_in_returned_subset": False, "absence_proven": False}},
        RELIEF: {"id": IDS[8], "status": "VISUAL_REJECTED_BY_USER", "build_identity_reference": "feedback.json", "observed": obs_text[8], "localization": {"limitation": "view relative", "exact_defect_coordinates": None}, "existing_screening_candidate": {"matched_to_user_feature": False}, "dry_bank_candidate_in_game": False, "user_screenshot": {"local_archive": "x.png", "sha256": "e" * 64, "bytes": 10, "image_size_px": [2, 2], "source": "user", "published": False}},
        FOREST: {"status": "LOCAL_VISUAL_OK", "global_forest_acceptance": False, "performance": "NOT_MEASURED"},
        C0: {"status": "LOCAL_VISUAL_OK", "driving": "NOT_TESTED", "global_causeway_acceptance": False, "global_shore_acceptance": False},
        TOUR: {"local_visual_ok": ["forest-dense", "causeway-c0"], "road49": "LOCAL_VISUAL_OK_WITH_PAVING_PENDING_NO_DRIVING_TEST", "c1_verdict": "NOT_REVIEWED", "visual_acceptance": "NOT_GRANTED", "defect_observations": 9},
        OBS: [{"observation": IDS[i], "domain": DOMAINS[i], "association": "UNCONFIRMED_CONTEXT_ONLY", "approximate_review_position": list(POSITIONS[i])} for i in range(9)],
        CTX: {"narva": {"association": "UNCONFIRMED_CONTEXT_ONLY", "point": [2391.0, 6941.0]}},
        SUMM: {"status": "DIAGNOSTIC_ONLY", "input_sha256": "f" * 64, "full_report_sha256": "1" * 64, "summary": {"chain_count": 3}},
    }

class Env:
    pass

def build_env(root):
    src = sources()
    hashes = {}
    for path, obj in src.items():
        p = root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        p.write_bytes(data)
        hashes[path] = hashlib.sha256(data).hexdigest()
    def B(path, ptr, lit):
        return {"path": path, "sha256": hashes[path], "pointer": ptr, "expected_literal": copy.deepcopy(lit)}
    spec = [
        (FB, "/findings/0/observed", ["terrain", "visual_models", "water"]), (FB, "/findings/1/observed", ["road_models", "road_corridor", "approaches", "water"]), (FB, "/findings/2/observed", ["terrain", "visual_models", "water"]),
        (KIT, "/findings/0/observed", ["riverbed_models", "terrain", "water"]), (KIT, "/findings/1/observed", ["riverbed_models", "road_corridor", "approaches", "water"]), (C65, "/findings/0/observed", ["riverbed_models", "terrain", "water"]),
        (R49, "/river_findings/0/observed", ["terrain", "visual_models", "water"]), (CROSS, "/user_follow_up", ["road_corridor", "road_models", "approaches", "water"]), (RELIEF, "/observed", ["terrain", "visual_models", "water"]),
    ]
    cases = []
    for i, cid in enumerate(IDS):
        if i < 3:
            primary = [B(FB, f"/findings/{i}/id", cid), B(FB, f"/findings/{i}/status", "OPEN"), B(FB, "/status", "VISUAL_REJECTED_BY_USER")]
        elif i < 5:
            primary = [B(KIT, f"/findings/{i-3}/id", cid), B(KIT, f"/findings/{i-3}/status", "OPEN"), B(KIT, "/status", "VISUAL_REJECTED_BY_USER")]
        elif i == 5:
            primary = [B(C65, "/findings/0/id", cid), B(C65, "/findings/0/status", "OPEN"), B(C65, "/status", "VISUAL_REJECTED_BY_USER")]
        elif i == 6:
            primary = [B(R49, "/river_findings/0/id", cid), B(R49, "/river_findings/0/status", "VISUAL_REJECTED_BY_USER"), B(R49, "/river_findings/0/river_source_id", None)]
        elif i == 7:
            primary = [B(CROSS, "/id", cid), B(CROSS, "/status", "USER_REJECTED_ROAD_INTERRUPTED_BY_RIVER")]
        else:
            primary = [B(RELIEF, "/id", cid), B(RELIEF, "/status", "VISUAL_REJECTED_BY_USER")]
        path_obs, ptr_obs, layers = spec[i]
        val = src[path_obs]
        for tok in ptr_obs.strip("/").split("/"):
            val = val[int(tok)] if isinstance(val, list) else val[tok]
        bindings = primary + [B(path_obs, ptr_obs, val)]
        ev = [{"state": STATE_FOR[DOMAINS[i]], "bindings": [B(OBS, f"/{i}/observation", cid), B(OBS, f"/{i}/domain", DOMAINS[i]), B(OBS, f"/{i}/association", "UNCONFIRMED_CONTEXT_ONLY"), B(OBS, f"/{i}/approximate_review_position", POSITIONS[i])], "limitation": "context only"}]
        if i == 7:
            ev.append({"state": "CONTEXT_ONLY_UNCONFIRMED", "bindings": [B(CROSS, "/native_evidence/count_total", 108), B(CROSS, "/native_evidence/returned_entities", 80), B(CROSS, "/native_evidence/bridge_detected_in_returned_subset", False), B(CROSS, "/native_evidence/absence_proven", False)], "limitation": "subset only"})
        cases.append({"id": cid, "human_verdict": "OPEN_REJECTED", "source_bindings": bindings, "scope": val, "location_status": "UNCONFIRMED_CONTEXT_ONLY", "required_layers": layers, "automatic_evidence": ev})
    contract = {
        "schema": "rejection-coverage-contract.v1", "status": "OPEN_HUMAN_REJECTIONS", "case_count": 9, "resolved_count": 0, "c1_verdict": "NOT_REVIEWED", "visual_acceptance": "NOT_GRANTED",
        "observed_build": {"mod": MOD, "world_sha256": WORLD, "pilot_sha256": PILOT, "water_sha256": WATER},
        "build_bindings": [B(FB, "/mod", MOD), B(FB, "/world_sha256", WORLD), B(FB, "/pilot_sha256", PILOT), B(FB, "/water_sha256", WATER)],
        "cases": cases,
        "scope_controls": [
            {"id": "forest-dense", "status": "LOCAL_VISUAL_OK", "source_bindings": [B(FOREST, "/status", "LOCAL_VISUAL_OK"), B(FOREST, "/global_forest_acceptance", False), B(FOREST, "/performance", "NOT_MEASURED"), B(TOUR, "/local_visual_ok", ["forest-dense", "causeway-c0"])], "limitation": "local only"},
            {"id": "causeway-c0", "status": "LOCAL_VISUAL_OK", "source_bindings": [B(C0, "/status", "LOCAL_VISUAL_OK"), B(C0, "/driving", "NOT_TESTED"), B(C0, "/global_causeway_acceptance", False), B(C0, "/global_shore_acceptance", False), B(TOUR, "/local_visual_ok", ["forest-dense", "causeway-c0"])], "limitation": "local only"},
            {"id": "road-49", "status": "LOCAL_VISUAL_OK_WITH_PAVING_PENDING_NO_DRIVING_TEST", "source_bindings": [B(R49, "/road/status", "LOCAL_VISUAL_OK_WITH_PAVING_PENDING"), B(R49, "/road/paving", "PENDING"), B(R49, "/road/driving", "NOT_TESTED"), B(R49, "/road/global_road_acceptance", False), B(R49, "/road/bug_005_closed", False), B(TOUR, "/road49", "LOCAL_VISUAL_OK_WITH_PAVING_PENDING_NO_DRIVING_TEST")], "limitation": "road only, not river"},
            {"id": "causeway-c1", "status": "NOT_REVIEWED", "source_bindings": [B(TOUR, "/c1_verdict", "NOT_REVIEWED"), B(TOUR, "/visual_acceptance", "NOT_GRANTED"), B(TOUR, "/defect_observations", 9)], "limitation": "not reviewed"},
        ],
        "references": [
            {"kind": "REFERENCE_ONLY", "bindings": [B(FB, "/screens", src[FB]["screens"]), B(FB, "/annotated_image", "not archived"), B(RELIEF, "/user_screenshot", src[RELIEF]["user_screenshot"])], "limitation": "metadata only"},
            {"kind": "DIAGNOSTIC_ONLY", "bindings": [B(SUMM, "/status", "DIAGNOSTIC_ONLY"), B(SUMM, "/input_sha256", "f" * 64), B(SUMM, "/full_report_sha256", "1" * 64), B(SUMM, "/summary", {"chain_count": 3})], "limitation": "diagnostic only"},
        ],
        "domain_states": dict(STATE_FOR),
        "source_pins": {},
    }
    contract["cases"][0]["automatic_evidence"].append({"state": "CONTEXT_ONLY_UNCONFIRMED", "bindings": [B(CTX, "/narva/association", "UNCONFIRMED_CONTEXT_ONLY"), B(CTX, "/narva/point", [2391.0, 6941.0])], "limitation": "nearby only"})
    used = set()
    def collect(o):
        if isinstance(o, dict):
            if set(o) == {"path", "sha256", "pointer", "expected_literal"}:
                used.add(o["path"])
            else:
                for v in o.values():
                    collect(v)
        elif isinstance(o, list):
            for v in o:
                collect(v)
    collect(contract)
    contract["source_pins"] = {p: hashes[p] for p in sorted(used)}
    env = Env()
    env.root = root
    env.contract = contract
    env.contract_path = root / "contract.json"
    cdata = json.dumps(contract, ensure_ascii=False, indent=2).encode("utf-8")
    env.contract_path.write_bytes(cdata)
    env.contract_sha = hashlib.sha256(cdata).hexdigest()
    env.ledger = copy.deepcopy(contract)
    env.ledger["schema"] = "rejection-coverage-ledger.v1"
    env.ledger["contract_sha256"] = env.contract_sha
    env.ledger_path = root / "ledger.json"
    env.ledger_path.write_bytes(json.dumps(env.ledger, ensure_ascii=False, indent=2).encode("utf-8"))
    return env

def run_consumer(env, contract_path=None, sha=None, ledger_path=None):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = consumer.main(["--root", str(env.root), "--contract", str(contract_path or env.contract_path), "--contract-sha256", sha or env.contract_sha, "--ledger", str(ledger_path or env.ledger_path)])
    return code, out.getvalue(), err.getvalue()

def write_both(env, contract=None, ledger=None):
    if contract is not None:
        data = json.dumps(contract, ensure_ascii=False, indent=2).encode("utf-8")
        env.contract_path.write_bytes(data)
        env.contract_sha = hashlib.sha256(data).hexdigest()
        env.contract = contract
    if ledger is not None:
        if contract is not None:
            ledger["contract_sha256"] = env.contract_sha
        env.ledger_path.write_bytes(json.dumps(ledger, ensure_ascii=False, indent=2).encode("utf-8"))
        env.ledger = ledger

def repin(env, contract, ledger):
    def walk(o):
        if isinstance(o, dict):
            if set(o) == {"path", "sha256", "pointer", "expected_literal"}:
                o["sha256"] = hashlib.sha256((env.root / o["path"]).read_bytes()).hexdigest()
            else:
                for v in o.values():
                    walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(contract)
    walk(ledger)
    pins = {}
    def collect(o):
        if isinstance(o, dict):
            if set(o) == {"path", "sha256", "pointer", "expected_literal"}:
                pins[o["path"]] = o["sha256"]
            else:
                for v in o.values():
                    collect(v)
        elif isinstance(o, list):
            for v in o:
                collect(v)
    collect(contract)
    contract["source_pins"] = {k: pins[k] for k in sorted(pins)}
    ledger["source_pins"] = copy.deepcopy(contract["source_pins"])
    write_both(env, contract, ledger)

def set_expected(doc, pointer_suffix, value, path=None):
    def walk(o):
        hit = False
        if isinstance(o, dict):
            if set(o) == {"path", "sha256", "pointer", "expected_literal"} and o["pointer"].endswith(pointer_suffix) and (path is None or o["path"] == path):
                o["expected_literal"] = value
                return True
            for v in o.values():
                hit = walk(v) or hit
            return hit
        if isinstance(o, list):
            for v in o:
                hit = walk(v) or hit
            return hit
        return False
    return walk(doc)

class TestCoverage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = build_env(Path(self.tmp.name))
    def tearDown(self):
        self.tmp.cleanup()
    def assertReject(self, code):
        self.assertNotEqual(code, 0)
    def mutate_both(self, fn, prep=None):
        if prep is not None:
            prep()
        con = copy.deepcopy(self.env.contract)
        led = copy.deepcopy(self.env.ledger)
        fn(con)
        fn(led)
        repin(self.env, con, led)
        code, _, _ = run_consumer(self.env)
        self.assertReject(code)
    def test_positive_consumer_manual_ledger_and_no_images(self):
        self.assertFalse(list(self.env.root.rglob("*.png")))
        code, out, _ = run_consumer(self.env)
        self.assertEqual(code, 0, out)
        self.assertIn("VERIFIED_OPEN_HUMAN_REJECTIONS", out)
    def test_producer_matches_manual_and_output_reuse(self):
        outp = self.env.root / "produced.json"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = producer.main(["--root", str(self.env.root), "--contract", str(self.env.contract_path), "--contract-sha256", self.env.contract_sha, "--output", str(outp)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(outp.read_bytes()), self.env.ledger)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            code2 = producer.main(["--root", str(self.env.root), "--contract", str(self.env.contract_path), "--contract-sha256", self.env.contract_sha, "--output", str(outp)])
        self.assertNotEqual(code2, 0)
    def test_consumer_independence_ast(self):
        text = (BASE / "tools/quality/verify_rejection_coverage_ev112.py").read_text(encoding="utf-8")
        self.assertNotIn("rejection_coverage_ev112", text)
        tree = ast.parse(text)
        imported = []
        names = set()
        attrs = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.append(node.module or "")
            elif isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.Attribute):
                attrs.add(node.attr)
        self.assertFalse(any("rejection_coverage" in m for m in imported))
        self.assertFalse(names & {"exec", "eval", "__import__"})
        self.assertFalse(attrs & {"import_module", "spec_from_file_location"})
        self.assertNotIn("importlib", imported)
    def mutate_ledger(self, fn):
        led = copy.deepcopy(self.env.ledger)
        fn(led)
        self.env.ledger_path.write_bytes(json.dumps(led, ensure_ascii=False).encode("utf-8"))
        code, _, _ = run_consumer(self.env)
        self.assertReject(code)
    def test_missing_duplicate_swapped_ids_ledger(self):
        self.mutate_ledger(lambda l: l["cases"].pop())
    def test_two_beds_collapse(self):
        def f(l):
            del l["cases"][5]
            l["case_count"] = 8
        self.mutate_ledger(f)
    def test_unknown_field_and_required_missing_and_boolint_ledger(self):
        self.mutate_ledger(lambda l: l.__setitem__("extra", 1))
        self.tearDown(); self.setUp()
        self.mutate_ledger(lambda l: l.pop("case_count"))
        self.tearDown(); self.setUp()
        self.mutate_ledger(lambda l: l.__setitem__("resolved_count", False))
    def test_co_absence_true(self):
        def prep():
            p = self.env.root / CROSS
            obj = json.loads(p.read_bytes())
            obj["native_evidence"]["absence_proven"] = True
            p.write_bytes(json.dumps(obj).encode())
        def fn(d):
            self.assertTrue(set_expected(d, "/absence_proven", True))
        self.mutate_both(fn, prep)
    def test_co_river_source_filled(self):
        def prep():
            p = self.env.root / R49
            obj = json.loads(p.read_bytes())
            obj["river_findings"][0]["river_source_id"] = "RIVER-1"
            p.write_bytes(json.dumps(obj).encode())
        def fn(d):
            self.assertTrue(set_expected(d, "/river_source_id", "RIVER-1"))
        self.mutate_both(fn, prep)
    def test_co_c1_promotion(self):
        self.mutate_both(lambda d: d["scope_controls"][3].__setitem__("status", "LOCAL_VISUAL_OK"))
    def test_co_ids_swapped_and_duplicated(self):
        def swap(d):
            d["cases"][0]["id"], d["cases"][1]["id"] = d["cases"][1]["id"], d["cases"][0]["id"]
        self.mutate_both(swap)
        self.tearDown(); self.setUp()
        self.mutate_both(lambda d: d["cases"].__setitem__(1, copy.deepcopy(d["cases"][0])))
    def test_co_not_detected_and_pass_states(self):
        self.mutate_both(lambda d: d["cases"][0]["automatic_evidence"][0].__setitem__("state", "NOT_DETECTED"))
        self.tearDown(); self.setUp()
        self.mutate_both(lambda d: d["cases"][0]["automatic_evidence"][0].__setitem__("state", "PASS"))
    def test_co_resolved_one_and_boolint(self):
        self.mutate_both(lambda d: d.__setitem__("resolved_count", 1))
        self.tearDown(); self.setUp()
        self.mutate_both(lambda d: d.__setitem__("resolved_count", True))
    def test_co_wrong_observed_build(self):
        def prep():
            p = self.env.root / FB
            obj = json.loads(p.read_bytes())
            obj["mod"] = "@OtherBuild"
            p.write_bytes(json.dumps(obj).encode())
        def fn(d):
            d["observed_build"]["mod"] = "@OtherBuild"
            self.assertTrue(set_expected(d, "/mod", "@OtherBuild", FB))
        self.mutate_both(fn, prep)
    def test_co_missing_native_group(self):
        self.mutate_both(lambda d: d["cases"][0]["automatic_evidence"].pop(0))
    def test_co_wrong_census_row(self):
        def fn(d):
            census = d["cases"][0]["automatic_evidence"][0]
            census["state"] = "NOT_EVALUATED"
            values = {"/3/observation": IDS[3], "/3/domain": "model_not_evaluated", "/3/association": "UNCONFIRMED_CONTEXT_ONLY", "/3/approximate_review_position": [8253, 9038]}
            for b in census["bindings"]:
                b["pointer"] = "/3" + b["pointer"][2:]
                b["expected_literal"] = copy.deepcopy(values[b["pointer"]])
        self.mutate_both(fn)
    def test_co_dropped_tour_binding(self):
        def fn(d):
            road = d["scope_controls"][2]
            road["source_bindings"] = [b for b in road["source_bindings"] if b["pointer"] != "/road49"]
        self.mutate_both(fn)
    def test_co_scope_open_string(self):
        self.mutate_both(lambda d: d["cases"][0].__setitem__("scope", "OPEN"))
    def test_co_association_and_global_repinned(self):
        def prep():
            p = self.env.root / OBS
            obj = json.loads(p.read_bytes())
            obj[0]["association"] = "CONFIRMED"
            p.write_bytes(json.dumps(obj).encode())
        def fn(d):
            for b in d["cases"][0]["automatic_evidence"][0]["bindings"]:
                if b["pointer"].endswith("/association"):
                    b["expected_literal"] = "CONFIRMED"
        self.mutate_both(fn, prep)
    def test_source_hash_mismatch_missing_and_oversize(self):
        p = self.env.root / FB
        p.write_bytes(p.read_bytes() + b" ")
        code, _, _ = run_consumer(self.env)
        self.assertReject(code)
        self.tearDown(); self.setUp()
        (self.env.root / KIT).unlink()
        code, _, _ = run_consumer(self.env)
        self.assertReject(code)
        self.tearDown(); self.setUp()
        (self.env.root / FB).write_bytes(b"x" * (producer.MAX_BYTES + 1))
        code, _, _ = run_consumer(self.env)
        self.assertReject(code)
    def test_nan_duplicate_json_and_wrong_sha_cli(self):
        self.env.ledger_path.write_bytes(b'{"schema": NaN}')
        code, _, _ = run_consumer(self.env)
        self.assertReject(code)
        self.env.ledger_path.write_bytes(b'{"a": 1, "a": 2}')
        code, _, _ = run_consumer(self.env)
        self.assertReject(code)
        code, _, _ = run_consumer(self.env, sha="0" * 64)
        self.assertReject(code)
        with self.assertRaises(ValueError):
            consumer.strict_loads(b'{"x": Infinity}')
        self.assertFalse(consumer.deep_equal(True, 1))
        self.assertFalse(producer.deep_equal(1, 1.0))
    def test_nested_bridge_id_exists_and_primary_guard(self):
        src = json.loads((self.env.root / FB).read_bytes())
        self.assertEqual(src["findings"][1]["bridge"]["id"], IDS[1])
        con = copy.deepcopy(self.env.contract); led = copy.deepcopy(self.env.ledger)
        for doc in (con, led):
            doc["cases"][1]["source_bindings"][0]["pointer"] = "/findings/1/bridge/id"
        repin(self.env, con, led)
        code, _, _ = run_consumer(self.env)
        self.assertReject(code)
    def test_repinned_fixed_status(self):
        con = copy.deepcopy(self.env.contract); led = copy.deepcopy(self.env.ledger)
        con["status"] = led["status"] = "FIXED"
        write_both(self.env, con, led)
        code, _, _ = run_consumer(self.env)
        self.assertReject(code)
    def test_pointer_extra_binding_reaches_resolver(self):
        for ptr in ("/findings/01/id", "/findings/0/id~2"):
            def fn(d, ptr=ptr):
                d["cases"][0]["source_bindings"].append({"path": FB, "sha256": "0" * 64, "pointer": ptr, "expected_literal": "x"})
            self.mutate_both(fn)
            self.tearDown(); self.setUp()
    def test_resolver_direct_escaped_and_invalid(self):
        doc = {"a/b": {"x~y": 42}, "findings": [{"id": "z"}]}
        self.assertEqual(consumer.resolve_pointer(doc, "/a~1b/x~0y"), 42)
        self.assertEqual(producer.resolve_pointer(doc, "/a~1b/x~0y"), 42)
        for bad in ("/findings/01/id", "/findings/0/id~2"):
            with self.assertRaises(ValueError):
                consumer.resolve_pointer(doc, bad)
            with self.assertRaises(ValueError):
                producer.resolve_pointer(doc, bad)
    def test_path_traversal_binding(self):
        def fn(d):
            d["cases"][0]["source_bindings"][0]["path"] = "../escape.json"
        con = copy.deepcopy(self.env.contract); led = copy.deepcopy(self.env.ledger)
        fn(con); fn(led)
        write_both(self.env, con, led)
        code, _, _ = run_consumer(self.env)
        self.assertReject(code)
    def test_symlink_escape_if_available(self):
        outside = Path(self.tmp.name) / "outside-secret.json"
        outside.write_bytes(b'{"id": "x"}')
        link = self.env.root / "evil-link.json"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("symlink unavailable")
        digest = hashlib.sha256(outside.read_bytes()).hexdigest()
        crafted = {"source_pins": {"evil-link.json": digest}, "build_bindings": [{"path": "evil-link.json", "sha256": digest, "pointer": "/id", "expected_literal": "x"}], "cases": [], "scope_controls": [], "references": []}
        with self.assertRaises(ValueError):
            consumer.verify_sources(self.env.root, crafted)
        with self.assertRaises(ValueError):
            producer.verify_sources(self.env.root, crafted)

if __name__ == "__main__":
    unittest.main()
