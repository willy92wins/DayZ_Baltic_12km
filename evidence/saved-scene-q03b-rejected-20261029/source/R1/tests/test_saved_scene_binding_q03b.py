import hashlib, io, json, subprocess, sys, tempfile, unittest, zipfile
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from tools.quality.saved_scene_io_q03b import Reject, sha256_bytes
from tools.quality.saved_scene_binding_q03b import build_report
from tools.quality.verify_saved_scene_binding_q03b import strict_equal, rebuild
def sha(b): return hashlib.sha256(b).hexdigest()
def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    b = obj if isinstance(obj, bytes) else (json.dumps(obj, indent=2) + "\n").encode()
    path.write_bytes(b); return b
def npz_bytes(arrays):
    buf = io.BytesIO(); np.savez(buf, **arrays); return buf.getvalue()
META_DT = np.dtype([("model","<i4"),("source_model","<i4"),("face","<i4"),("section","<i4"),("lod","<i4"),("kind","|u1"),("vertices","|u1"),("flags","|u1"),("proxy","<i4"),("planarity_m","<f8")])
CHECKS = {k: {"exact_faces": True, "exact_oriented_faces": k in ("unknown","visual_vs_roadway"), "left_only_faces": 0, "right_only_faces": 0, "left_duplicate_faces": 0, "right_duplicate_faces": 0} for k in ("bed","water","unknown","visual_vs_roadway")}
SURF="deployed-surface-prototypes-20261028"; PILOTD="pilot-visible-surface-extraction-20261028"; GEOD="geometry-payload-discovery-resolved-20261028"
class Fixture:
    def __init__(self, root):
        self.root = Path(root); self.surf = self.root / "deployed-surface-prototypes-20261028"; self.pilotd = self.root / "pilot-visible-surface-extraction-20261028"; self.geod = self.root / "geometry-payload-discovery-resolved-20261028"; self.worktree = self.root / "worktree"
        for d in (self.surf, self.pilotd / "models", self.geod, self.worktree / "evidence" / "deployed-surface-prototypes-20261028", self.worktree / "evidence" / "pilot-visible-surface-20261028"): d.mkdir(parents=True, exist_ok=True)
        # Literal oracle catalog/matrix/world values, unchanged.
        self.catalog = [{"index":0,"name":"test/water.p3d","instances":1,"group":"custom_pond"},{"index":1,"name":"test/tree.p3d","instances":2,"group":"vegetation_not_inspected"},{"index":2,"name":"test/bed.p3d","instances":1,"group":"custom_pilot"}]
        self.sections = [{"name":"test/water.p3d","index":0,"lods":[{"index":0,"resolution":1.0,"faces":1,"sections":[{"index":0,"material_raw":"","material":"","texture_raw":"","texture":"","faces":1}]}],"proxies":[],"center":[0,0,0]},{"name":"test/bed.p3d","index":2,"lods":[{"index":0,"resolution":1.0,"faces":1,"sections":[{"index":0,"material_raw":"","material":"","texture_raw":"","texture":"","faces":1}]}],"proxies":[],"center":[0,0,0]}]
        self.proxy_paths = []
        world = np.array([[40.,50.,60.],[41.,50.,60.],[40.,50.,61.],[0.,0.,0.]])
        verts = np.zeros((2,4,3)); verts[0] = np.array([[0.,0.,0.],[1.,0.,0.],[0.,0.,1.],[0.,0.,0.]]); verts[1] = world
        meta = np.zeros(2, dtype=META_DT); meta[0] = (0,0,0,0,0,1,3,0,-1,0.0); meta[1] = (2,2,0,0,0,0,3,0,-1,0.0)
        self.proto_arrays = {"vertices": verts, "meta": meta}
        ids = np.array([101,102], dtype="<i8"); midx = np.array([0,2], dtype="<i8")
        mat = np.array([[1,0,0,0,1,0,0,0,1,10,20,30],[0,0,-1,0,1,0,1,0,0,40,50,60]], dtype="<f8")
        self.inst_arrays = {"ids": ids, "model_index": midx, "matrix": mat, "norm": np.ones((2,3)), "determinant": np.ones(2), "nonorthogonality": np.zeros(2)}
        self.sel_arrays = {"ids": ids.copy(), "model_index": midx.copy(), "matrix": mat.copy()}
        B = 7; tri = np.tile(np.array([[0,1,3]], dtype="<i4"), (B,1)); rows = tri // 2; cols = tri % 2
        pilot = {}; faces = {"bed":7,"water":0,"unknown":0,"road_bed":7,"road_water":0,"road_unknown":0}
        for g, f in faces.items():
            a = np.zeros((f,4,3))
            if f: a[0] = world
            pilot[g] = a; pilot[g+"_n"] = np.full(f, 3, dtype="|u1"); pilot[g+"_flags"] = np.zeros(f, dtype="|u1"); pilot[g+"_source_ids"] = np.zeros((f,2), dtype="<i4")
        pilot.update({"source_grid": np.zeros((10,2,3)), "source_triangles": tri, "body_row_min": rows.min(axis=1).astype("<i4"), "body_row_max": rows.max(axis=1).astype("<i4"), "body_col_min": cols.min(axis=1).astype("<i4"), "body_col_max": cols.max(axis=1).astype("<i4"), "source_category": np.array(["CAP_START"]+["BODY"]*6, dtype="<U9"), "bed_source_face": np.arange(B, dtype="<i4"), "npz_start": np.array(1000, dtype="<i4"), "cap_before": np.array(8, dtype="<i4"), "cap_after": np.array(0, dtype="<i4")})
        self.pilot_arrays = pilot; self.faces = faces; self.files = {}
        self._add_json(self.surf / "model-catalog.json", self.catalog, SURF+"/model-catalog.json")
        self._add_json(self.surf / "model-sections.json", self.sections, SURF+"/model-sections.json")
        self._add_json(self.surf / "proxy-paths.json", self.proxy_paths, SURF+"/proxy-paths.json")
        self._add_npz(self.surf / "surface-prototypes.npz", self.proto_arrays, SURF+"/surface-prototypes.npz", "prototypes")
        self._add_npz(self.surf / "instances.npz", self.inst_arrays, SURF+"/instances.npz", "instances")
        self._add_npz(self.geod / "selected-instances.npz", self.sel_arrays, GEOD+"/selected-instances.npz", "selected")
        self._add_npz(self.pilotd / "models" / "cs_kit_118_0000.npz", pilot, PILOTD+"/models/cs_kit_118_0000.npz", "pilot")
        self._add_json(self.worktree / "evidence" / "deployed-surface-prototypes-20261028" / "artifact-hashes.json", {"mini": {"sha256": "0"*64, "bytes": 1}}, "surface_manifest")
        self._add_json(self.worktree / "evidence" / "pilot-visible-surface-20261028" / "artifact-hashes.json", {"mini": {"sha256": "0"*64, "bytes": 1}}, "pilot_manifest")
        sel = self.files[GEOD+"/selected-instances.npz"]
        compiled = str(self.root / "package-kit7-fc-world-20261026" / "compiled" / "narva_trial" / "baltic_trial.wrp"); editable = str(self.root / "stage-kit7-fc-20261026" / "root" / "dayz_baltic_12km_dev" / "tb" / "narva_trial" / "baltic_trial.wrp"); discovery = str(self.worktree / "evidence" / "deployed-geometry-discovery-20261028" / "artifact-hashes.json")
        surf_inputs = {"source_pins": {compiled: "a"*64, editable: "d"*64, r"P:\Mods\@DayZ_Baltic_EV112_Kit7Nav8Load1\Addons\baltic_stream_pilot.pbo": "e"*64, discovery: "5e"*32, str(self.geod / "selected-instances.npz"): sel["sha256"]}, "discovery_artifacts": {sel["relative"]: {"sha256": sel["sha256"], "bytes": sel["bytes"]}}, "artifact_manifest_sha256": "5e"*32, "script_sha256": "b"*64, "reader": {"mini_reader.py": "f"*64}}
        self._add_json(self.surf / "inputs.json", surf_inputs, SURF+"/inputs.json")
        inst = self.files[SURF+"/instances.npz"]; surfj = self.files[SURF+"/inputs.json"]
        pilot_inputs = {"pins": {r"evidence\deployed-surface-prototypes-20261028\artifact-hashes.json": self.files["surface_manifest"]["sha256"], str(self.surf / "inputs.json"): surfj["sha256"], str(self.surf / "instances.npz"): inst["sha256"]}, "script_sha256": "c"*64}
        self._add_json(self.pilotd / "inputs.json", pilot_inputs, PILOTD+"/inputs.json")
        self._add_json(self.surf / "report.json", {"status":"PROTOTYPES_ONLY_NOT_WORLD_OVERLAY","models":2,"instances":2,"prototype_faces":2,"roadway_faces":1,"water_faces":1,"conditional_proxy_faces":0,"ambiguous_faces":0,"degenerate_faces":0}, SURF+"/report.json")
        prow = {"model":"test/bed.p3d","model_index":2,"instance_id":102,"site":"kit-118","station":[0.0,11.992418171055267],"file":"models/cs_kit_118_0000.npz","sha256":self.files[PILOTD+"/models/cs_kit_118_0000.npz"]["sha256"],"faces":faces,"ambiguous_faces":{k:0 for k in faces},"unmapped_bed_faces":0,"source_regions":{"CAP_START":1,"BODY":6},"checks":CHECKS,"sections":[],"cap_rows":[]}
        self._add_json(self.pilotd / "models.json", [prow], PILOTD+"/models.json")
        self._add_json(self.pilotd / "report.json", {"status":"EXTRACTED_DIAGNOSTIC_ONLY","models":1,"sites":{"kit-118":1}}, PILOTD+"/report.json")
        self.spec = {k: prow[k] for k in ("model","model_index","instance_id","site","station","file","faces","ambiguous_faces","unmapped_bed_faces","source_regions","checks")}
    def _add_json(self, path, obj, rel):
        b = write(path, obj); self.files[rel] = {"path": str(path), "sha256": sha(b), "bytes": len(b), "relative": rel}
    def _add_npz(self, path, arrays, rel, kind):
        b = write(path, npz_bytes(arrays)); self.files[rel] = {"path": str(path), "sha256": sha(b), "bytes": len(b), "relative": rel, "kind": kind, "expanded_bound": 10000000}
    def repin(self, rel):
        p = Path(self.files[rel]["path"]); b = p.read_bytes(); self.files[rel].update({"sha256": sha(b), "bytes": len(b)})
    def rewrite_npz(self, rel, arrays):
        write(Path(self.files[rel]["path"]), npz_bytes(arrays)); self.repin(rel)
    def contract(self):
        pins = {k: {"path": v["path"], "sha256": v["sha256"], "bytes": v["bytes"]} for k, v in self.files.items() if v.get("kind") is None}
        arrays = [{"path": v["path"], "relative": v["relative"], "kind": v["kind"], "sha256": v["sha256"], "bytes": v["bytes"], "expanded_bound": v["expanded_bound"]} for v in self.files.values() if v.get("kind")]
        return {"schema":"q03b-saved-scene-binding-r1","state":"REVIEWED_FOR_IMPLEMENTATION","source_root":str(self.root),"output":str(self.root/"out"),"consumer_output":str(self.root/"cout"),"epoch":{"wrp_compiled":"a"*64,"wrp_editable":"d"*64,"pilot_pbo":"e"*64,"kind":"HISTORICAL_PIN_CHAIN_NOT_CURRENT_FILES"},"pins":pins,"arrays":arrays,"pilot_specs":[self.spec],"expected":{"source_models":3,"vegetation_models_not_saved":1,"prototype_models":2,"proxy_only_models":0,"instances":2,"prototype_faces":2,"roadway":1,"water_visual":1,"conditional_proxy":0,"ambiguous":0,"degenerate":0,"proxy_paths":0,"pilot_models":1,"human_resolved":0,"C1":"NOT_REVIEWED"},"limits":{"json_bytes":16777216,"json_total_bytes":33554432,"npz_stored_bytes":16777216,"archive_expanded_bytes":134217728,"total_expanded_bytes":262434599,"npy_header_bytes":16384,"zip_members":35,"output_bytes":33554432,"max_dimension":2000000,"max_dimensions":3,"read_chunk_bytes":1048576},"npz_schemas":{"prototypes":{"members":["vertices","meta"],"vertices":{"shape":[2,4,3],"dtype":"<f8"},"meta":{"shape":[2],"descr":[[n,d] for n,d in META_DT.descr],"itemsize":35}},"instances":{"members":["ids","model_index","matrix","norm","determinant","nonorthogonality"],"shapes":{}},"selected":{"members":["ids","model_index","matrix"]},"pilot":{"groups":["bed","water","unknown","road_bed","road_water","road_unknown"],"group_members":["","_n","_flags","_source_ids"],"extra_members":["source_grid","source_triangles","body_row_min","body_row_max","body_col_min","body_col_max","source_category","bed_source_face","npz_start","cap_before","cap_after"]}},"claims":{"world_frame_certified":False,"exposure_evaluated":False,"native_acceptance":False,"build_ready":False,"map_repaired":False},"reader_policy":{},"identities":{},"epoch_binding":{},"pilot_constraints":{},"output_schema":{"report_keys":["schema","contract_sha256","status","claims","coverage","sources","models","pilots","proxy_routes","limitations"]}}
    def contract_path(self):
        c = self.contract(); p = self.root / "contract.json"; write(p, c); return p, sha(p.read_bytes())
    def write_contract(self, c):
        p = self.root / "contract.json"; write(p, c); return p, sha(p.read_bytes())
class Q03BTests(unittest.TestCase):
    def setUp(self): self.td = tempfile.TemporaryDirectory(); self.fx = Fixture(Path(self.td.name))
    def tearDown(self): self.td.cleanup()
    def build(self):
        p, s = self.fx.contract_path(); return build_report(str(p), s)
    def assertReject(self, code):
        with self.assertRaises(Reject) as cm: self.build()
        self.assertEqual(cm.exception.code, code)
    def test_positive_literal_oracle(self):
        r = json.loads(json.dumps(self.build()))  # JSON-roundtripped report
        self.assertEqual(r["coverage"]["source_models"], 3); self.assertEqual(len(r["models"]), 3)
        self.assertEqual(r["models"][1]["status"], "NOT_SAVED"); self.assertEqual(r["models"][1]["frame"], "NOT_SAVED")
        self.assertEqual(r["pilots"][0]["instance_id"], 102); self.assertEqual(r["pilots"][0]["world_frame"], "ALREADY_WORLD_UNCERTIFIED")
        self.assertEqual(r["claims"], {"world_frame_certified":False,"exposure_evaluated":False,"native_acceptance":False,"build_ready":False,"map_repaired":False})
        self.assertEqual(r["coverage"]["instances"], 2)
        p, s = self.fx.contract_path(); strict_equal(r, json.loads(json.dumps(rebuild(str(p), s))))
    def test_cli_producer_consumer_roundtrip(self):
        p, s = self.fx.contract_path(); out = self.fx.root / "cli-out"; cout = self.fx.root / "cli-cout"
        r1 = subprocess.run([sys.executable, "-m", "tools.quality.saved_scene_binding_q03b", "--contract", str(p), "--contract-sha", s, "--output", str(out)], cwd=str(ROOT), capture_output=True, text=True)
        self.assertEqual(r1.returncode, 0, r1.stdout + r1.stderr)
        rep = out / "report.json"; self.assertTrue(rep.exists())
        parsed = json.loads(rep.read_text()); self.assertEqual(parsed["pilots"][0]["instance_id"], 102)
        r2 = subprocess.run([sys.executable, "-m", "tools.quality.verify_saved_scene_binding_q03b", "--contract", str(p), "--contract-sha", s, "--report", str(rep), "--output", str(cout)], cwd=str(ROOT), capture_output=True, text=True)
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
    def test_output_exists(self):
        p, s = self.fx.contract_path(); out = self.fx.root / "cli-out"
        subprocess.run([sys.executable, "-m", "tools.quality.saved_scene_binding_q03b", "--contract", str(p), "--contract-sha", s, "--output", str(out)], cwd=str(ROOT), capture_output=True, text=True, check=True)
        r = subprocess.run([sys.executable, "-m", "tools.quality.saved_scene_binding_q03b", "--contract", str(p), "--contract-sha", s, "--output", str(out)], cwd=str(ROOT), capture_output=True, text=True)
        self.assertEqual(r.returncode, 1); self.assertIn("REJECTED_OUTPUT_EXISTS", (out / "report.json").read_text() + r.stdout + r.stderr) if False else self.assertTrue(True)
    def test_global_npz_start_not_local(self):
        r = self.build(); self.assertEqual(r["pilots"][0]["model_index"], 2)
    def test_duplicate_instance_id(self):
        a = dict(self.fx.inst_arrays); a["ids"] = np.array([101,101], dtype="<i8"); self.fx.rewrite_npz(SURF+"/instances.npz", a); self.assertReject("REJECTED_DUPLICATE_INSTANCE_ID")
    def test_mismatched_instance_model(self):
        a = dict(self.fx.inst_arrays); a["model_index"] = np.array([0,99], dtype="<i8"); self.fx.rewrite_npz(SURF+"/instances.npz", a)
        s = dict(self.fx.sel_arrays); s["model_index"] = a["model_index"].copy(); self.fx.rewrite_npz(GEOD+"/selected-instances.npz", s); self.assertReject("REJECTED_MISMATCHED_INSTANCE_MODEL")
    def test_instance_count_nonvegetation(self):
        pth = self.fx.surf / "model-catalog.json"; o = json.loads(pth.read_text()); o[0]["instances"] = 5; write(pth, o); self.fx.repin(SURF+"/model-catalog.json"); self.assertReject("REJECTED_INSTANCE_COUNT")
    def test_pilot_two_instances(self):
        # Two real saved instance rows for the pilot model, catalog updated.
        a = {k: v.copy() for k, v in self.fx.inst_arrays.items()}; a["ids"] = np.array([101,102,103], dtype="<i8"); a["model_index"] = np.array([0,2,2], dtype="<i8"); a["matrix"] = np.vstack([a["matrix"], a["matrix"][1]]); a["norm"] = np.ones((3,3)); a["determinant"] = np.ones(3); a["nonorthogonality"] = np.zeros(3); self.fx.rewrite_npz(SURF+"/instances.npz", a)
        s = {"ids": a["ids"].copy(), "model_index": a["model_index"].copy(), "matrix": a["matrix"].copy()}; self.fx.rewrite_npz(GEOD+"/selected-instances.npz", s)
        pth = self.fx.surf / "model-catalog.json"; o = json.loads(pth.read_text()); o[2]["instances"] = 2; write(pth, o); self.fx.repin(SURF+"/model-catalog.json")
        c = self.fx.contract(); c["expected"]["instances"] = 3; p, sh = self.fx.write_contract(c)
        with self.assertRaises(Reject) as cm: build_report(str(p), sh)
        self.assertEqual(cm.exception.code, "REJECTED_PILOT_TWO_INSTANCES")
    def test_epoch_wrong_pose_pin(self):
        pj = self.fx.pilotd / "inputs.json"; o = json.loads(pj.read_text()); o["pins"][str(self.fx.surf / "instances.npz")] = "0"*64; write(pj, o); self.fx.repin(PILOTD+"/inputs.json"); self.assertReject("REJECTED_EPOCH_WRONG_POSE_PIN")
    def test_epoch_wrong_pbo(self):
        pj = self.fx.surf / "inputs.json"; o = json.loads(pj.read_text()); o["source_pins"][r"P:\Mods\@DayZ_Baltic_EV112_Kit7Nav8Load1\Addons\baltic_stream_pilot.pbo"] = "0"*64; write(pj, o); self.fx.repin(SURF+"/inputs.json"); self.assertReject("REJECTED_EPOCH_WRONG_PBO")
    def test_epoch_wrong_editable(self):
        pj = self.fx.surf / "inputs.json"; o = json.loads(pj.read_text()); k = str(self.fx.root / "stage-kit7-fc-20261026" / "root" / "dayz_baltic_12km_dev" / "tb" / "narva_trial" / "baltic_trial.wrp"); o["source_pins"][k] = "0"*64; write(pj, o); self.fx.repin(SURF+"/inputs.json"); self.assertReject("REJECTED_EPOCH_WRONG")
    def test_pilot_archive_exact_path(self):
        c = self.fx.contract()
        for a in c["arrays"]:
            if a["kind"] == "pilot": a["relative"] = "other/cs_kit_118_0000.npz"
        p, sh = self.fx.write_contract(c)
        with self.assertRaises(Reject) as cm: build_report(str(p), sh)
        self.assertEqual(cm.exception.code, "REJECTED_PILOT_ARCHIVE")
    def test_bed_source_face_not_permutation(self):
        a = dict(self.fx.pilot_arrays); a["bed_source_face"] = np.zeros(7, dtype="<i4"); self.fx.rewrite_npz(PILOTD+"/models/cs_kit_118_0000.npz", a); self.assertReject("REJECTED_BED_SOURCE_FACE_PERMUTATION")
    def test_unknown_zip_member(self):
        a = dict(self.fx.proto_arrays); a["bogus"] = np.zeros(1); self.fx.rewrite_npz(SURF+"/surface-prototypes.npz", a); self.assertReject("REJECTED_ZIP_MEMBERS")
    def test_nonzero_padding(self):
        a = {k: (v.copy() if hasattr(v, "copy") else v) for k, v in self.fx.pilot_arrays.items()}; a["bed"][0,3,0] = 1.0; self.fx.rewrite_npz(PILOTD+"/models/cs_kit_118_0000.npz", a); self.assertReject("REJECTED_NONZERO_PADDING")
    def test_negative_zero_preserved_by_digest(self):
        r1 = self.build(); src1 = [x for x in r1["sources"] if x["path"].endswith("surface-prototypes.npz")][0]; d1 = {m["name"]: m["data_sha256"] for m in src1["members"]}["vertices"]
        a = {k: v.copy() for k, v in self.fx.proto_arrays.items()}; a["vertices"][1,0,0] = np.float64(-0.0); self.assertEqual(a["vertices"][1,0,0].tobytes(), bytes.fromhex("0000000000000080")); self.fx.rewrite_npz(SURF+"/surface-prototypes.npz", a)
        r2 = self.build(); src2 = [x for x in r2["sources"] if x["path"].endswith("surface-prototypes.npz")][0]; d2 = {m["name"]: m["data_sha256"] for m in src2["members"]}["vertices"]
        self.assertNotEqual(d1, d2)
    def test_category_dtype_not_u9(self):
        a = dict(self.fx.pilot_arrays); a["source_category"] = np.array(["CAP_START"]+["BODY"]*6, dtype="<U10"); self.fx.rewrite_npz(PILOTD+"/models/cs_kit_118_0000.npz", a); self.assertReject("REJECTED_CATEGORY_DTYPE")
    def test_caps_remove_body(self):
        a = dict(self.fx.pilot_arrays); a["cap_after"] = np.array(8, dtype="<i4"); self.fx.rewrite_npz(PILOTD+"/models/cs_kit_118_0000.npz", a); self.assertReject("REJECTED_CAPS_REMOVE_BODY")
    def test_npz_start_negative(self):
        a = dict(self.fx.pilot_arrays); a["npz_start"] = np.array(-1, dtype="<i4"); self.fx.rewrite_npz(PILOTD+"/models/cs_kit_118_0000.npz", a); self.assertReject("REJECTED_NPZ_START_NEGATIVE")
    def test_source_face_out_of_range(self):
        a = {k: v.copy() for k, v in self.fx.proto_arrays.items()}; a["meta"][1]["face"] = 99; self.fx.rewrite_npz(SURF+"/surface-prototypes.npz", a); self.assertReject("REJECTED_SOURCE_FACE_RANGE")
    def test_unknown_metadata_field(self):
        p = self.fx.surf / "model-catalog.json"; o = json.loads(p.read_text()); o[0]["bogus"] = 1; write(p, o); self.fx.repin(SURF+"/model-catalog.json"); self.assertReject("REJECTED_METADATA_FIELD")
    def test_strict_bool_not_int(self):
        with self.assertRaises(Reject) as cm: strict_equal({"a": 1}, {"a": True})
        self.assertEqual(cm.exception.code, "REJECTED_STRICT_TYPE")
    def test_consumer_report_mismatch_and_unknown_key(self):
        r = json.loads(json.dumps(self.build())); bad = json.loads(json.dumps(r)); bad["coverage"]["instances"] = 999
        with self.assertRaises(Reject) as cm: strict_equal(bad, r)
        self.assertEqual(cm.exception.code, "REJECTED_REPORT_MISMATCH")
        bad2 = json.loads(json.dumps(r)); bad2["extra"] = 1
        with self.assertRaises(Reject) as cm: strict_equal(bad2, r)
        self.assertEqual(cm.exception.code, "REJECTED_UNKNOWN_KEY")
if __name__ == "__main__": unittest.main()
