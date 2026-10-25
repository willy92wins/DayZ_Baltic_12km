#!/usr/bin/env python
"""Independent consumer for the EV93 static compiled-water face-range index.

This reads only the finished index and frozen B inputs. It does not import
authoring code or any solver. In production it imports the pinned builder only
to exercise the shipped query API; source-face enumeration and range/exposure
oracles are independently reconstructed here. --fixtures-only exercises those
oracles without loading production data.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math, sys
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

ROOT = Path(r"E:/DayZ-Baltic-Build")
EV93 = ROOT / "v30-global-bank-extension-20261010"
EV87 = ROOT / "v30-global-strict-bank-relief-20261010"
EV79 = ROOT / "v30-narva-dry-bank-relief-20261010"
B = ROOT / "v30-mixed-bank-incremental-fixed-20261010"
EV90 = ROOT / "v30-wide-bank-fairing-pilot-20261010"
WORKSPACE = Path(r"C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290")
MODEL_DIR = ROOT / "v30-native-terminal-finish-20261009/package/water/temp/baltic_water_v30"
BOUNDS = ROOT / "v30-low-water-components-20261009/compiled-instance-bounds.json"
WRP = B / "package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp"
DEPLOY = B / "deploy.json"
P_FIELD = EV79 / "candidate/plane.npy"
F_FIELD = EV79 / "candidate/visible-field.npy"
PLAN = EV93 / "plan.md"
EV87_SOURCE = EV87 / "review-independent/verify_ev87.py"
EV90_SOURCE = EV90 / "next-method-preflight/ev90_preflight.py"
BUILD_SOURCE = EV93 / "ev93-face-index/build_face_index.py"
N, CELL, Z0 = 2048, 6.0, 12282.0
TRIS = ((0, 1, 3), (0, 2, 3))
# Frozen identities from the live EV90 source and B deploy contract.
PINS = {
    "plan_sha256": "ccc018a9e1cc8a51b075a91905b1cbe7d3cdaf72040e51992f2ac55db8ad7e82",
    "ev87_source_sha256": "964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27",
    "ev90_source_sha256": "5892e917335ca2d8caa427f04f48ba8acbd8e16a5e1b400be596d5dd636afb7f",
    "builder_source_sha256": "d1d3d1106bfdff7fd63f201ae042fdbd181bce92a96dddf1afc3182f694d288e",
    "terrain_sha256": "f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0",
    "P_sha256": "768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0",
    "F_sha256": "f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c",
    "wrp_source_sha256": "3071395e2d1830f1c5c28bd84346761b5c517710e9d5f1f4ac19cd3fc1eff1f6",
    "world_pbo_sha256": "b11c825b6c14ecc5649ac668b40c7dc6c9f52c64c26ddfa748983c04b340c36c",
    "water_pbo_sha256": "3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14",
    "bounds_sha256": "863e9539203e59fe77b9c7d4949da3a69b4991249941e15b887b60ff9e81ee62",
    "compiled_oprw_sha256": "3b12b21d554c6ab75d76c43b5ba902c9a1d49a26516bdd14b16f1a6048ba2539",
}
SCHEMA = "ev93.face-range-index.v1"
ARRAY_DTYPES = {
    "kind": np.dtype("uint8"), "object_id": np.dtype("int32"),
    "model_id": np.dtype("uint32"), "face_id": np.dtype("uint32"),
    "xyz": np.dtype("float64"), "plane_y_xz": np.dtype("float64"),
    "area_xz": np.dtype("float64"), "cell_range_rc": np.dtype("int32"),
    "degenerate": np.dtype("uint8"),
}

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def json_sha(value) -> str:
    b = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(b).hexdigest()

def expected_closed_range(xyz):
    """Conservative inclusive cell range for a closed XZ triangle bbox."""
    q = np.asarray(xyz, dtype=np.float64)
    if q.shape != (3, 3) or not np.isfinite(q).all():
        raise ValueError("xyz must be a finite (3,3) array in X,Y,Z order")
    xmin, xmax = float(q[:, 0].min()), float(q[:, 0].max())
    zmin, zmax = float(q[:, 2].min()), float(q[:, 2].max())
    # Closed cell rectangles: exact grid-line contact includes both neighbors.
    c0 = math.ceil(xmin / CELL) - 1
    c1 = math.floor(xmax / CELL)
    r0 = math.ceil((Z0 - zmax) / CELL) - 1
    r1 = math.floor((Z0 - zmin) / CELL)
    c0, c1 = max(0, c0), min(N - 2, c1)
    r0, r1 = max(0, r0), min(N - 2, r1)
    if c0 > c1 or r0 > r1:
        return np.asarray([-1, -1, -1, -1], dtype=np.int32)  # explicit off-map sentinel
    return np.asarray([r0, r1, c0, c1], dtype=np.int32)

def ranges_intersect_cell(rng, cell):
    r0, r1, c0, c1 = map(int, rng)
    r, c = map(int, cell)
    return r0 <= r <= r1 and c0 <= c <= c1

def direct_bbox_touches(xyz, cell):
    r, c = map(int, cell)
    x0, x1 = c * CELL, (c + 1) * CELL
    z1, z0 = Z0 - r * CELL, Z0 - (r + 1) * CELL
    q = np.asarray(xyz, dtype=np.float64)
    return (q[:, 0].max() >= x0 and q[:, 0].min() <= x1 and
            q[:, 2].max() >= z0 and q[:, 2].min() <= z1)

def query_rows(arrays, cell):
    return np.flatnonzero(
        (arrays["cell_range_rc"][:, 0] <= cell[0]) &
        (arrays["cell_range_rc"][:, 1] >= cell[0]) &
        (arrays["cell_range_rc"][:, 2] <= cell[1]) &
        (arrays["cell_range_rc"][:, 3] >= cell[1])
    )

def _cell_xy(r, c):
    return np.asarray([[c*CELL,Z0-r*CELL],[(c+1)*CELL,Z0-r*CELL],
                       [c*CELL,Z0-(r+1)*CELL],[(c+1)*CELL,Z0-(r+1)*CELL]], dtype=np.float64)

def _corner_values(h, r, c):
    return np.asarray([h[r,c],h[r,c+1],h[r+1,c],h[r+1,c+1]], dtype=np.float64)

def _affine(xy, values):
    return np.linalg.solve(np.column_stack((xy[:,0], xy[:,1], np.ones(3))),
                           np.asarray(values, dtype=np.float64))

def _clip_polygon(xyz, signed):
    poly = [(np.asarray(xy, dtype=np.float64), float(d)) for xy,d in zip(xyz,signed)]
    out = []
    for i,(a,da) in enumerate(poly):
        b,db = poly[(i+1) % len(poly)]
        ina, inb = da > 0.0, db > 0.0
        if ina: out.append(a)
        if ina != inb:
            den = da-db
            if abs(den)>1e-15: out.append(a+(b-a)*(da/den))
    if len(out)<3: return Polygon()
    p = Polygon(np.asarray(out))
    return p if p.is_valid and p.area>1e-12 else p.buffer(0)

def _face_exposure(xyz, plane, h, cell):
    """Independent implementation of EV87 face∩native-triangle clipping."""
    r,c = cell
    cellxy = _cell_xy(r,c); gh = _corner_values(h,r,c)
    xy = np.asarray(xyz,dtype=np.float64)[:,[0,2]]
    face = Polygon(xy)
    if face.area <= 1e-12: return Polygon()
    plane = np.asarray(plane,dtype=np.float64)
    result=[]
    for tri in TRIS:
        ids=np.asarray(tri,dtype=np.int64)
        native=Polygon(cellxy[ids])
        overlap=face.intersection(native)
        if overlap.is_empty: continue
        ground=_affine(cellxy[ids],gh[ids])
        # Face and ground are both affine over their triangle.
        points=[]
        geoms=list(overlap.geoms) if hasattr(overlap,"geoms") else [overlap]
        for geom in geoms:
            if geom.is_empty or geom.area<=1e-12: continue
            coords=np.asarray(geom.exterior.coords[:-1],dtype=np.float64)
            face_y=coords @ plane[:2] + plane[2]
            ground_y=coords @ ground[:2] + ground[2]
            clipped=_clip_polygon(coords,face_y-ground_y)
            if not clipped.is_empty: points.append(clipped)
        if points: result.extend(points)
    return unary_union(result) if result else Polygon()

def _load_manifest(manifest_path):
    manifest_path=Path(manifest_path)
    m=json.loads(manifest_path.read_text(encoding="utf-8"))
    if m.get("schema") != SCHEMA or m.get("status") != "COMPLETE":
        raise AssertionError("index manifest schema/status is not complete EV93 v1")
    for k,v in PINS.items():
        # Source paths/hashes are pinned separately; base identity names are schema-defined.
        if k in ("plan_sha256","ev87_source_sha256","ev90_source_sha256","builder_source_sha256"):
            actual = {"plan_sha256":m.get("plan_sha256"),
                      "ev87_source_sha256":m.get("ev87_source",{}).get("sha256"),
                      "ev90_source_sha256":m.get("ev90_source",{}).get("sha256"),
                      "builder_source_sha256":m.get("builder_source",{}).get("sha256")}[k]
        elif k in ("P_sha256","F_sha256"):
            continue # checked by exact file path in input_hashes below
        else: actual=m.get("base_identity",{}).get(k)
        if actual != v: raise AssertionError(f"manifest pin mismatch {k}: {actual!r}")
    if len(m.get("models",[]))==0: raise AssertionError("manifest has no model table")
    model_ids=[int(x["model_id"]) for x in m["models"]]
    if model_ids != sorted(set(model_ids)): raise AssertionError("model_id table must be sorted and unique")
    basenames=[str(x["basename"]) for x in m["models"]]
    if basenames!=sorted(basenames) or model_ids!=list(range(len(model_ids))):
        raise AssertionError("model IDs must enumerate sorted basenames from zero")
    if str(Path(m.get("builder_source",{}).get("path","")).resolve()).casefold()!=str(BUILD_SOURCE.resolve()).casefold():
        raise AssertionError("builder source path is not the frozen EV93 source")
    return manifest_path,m

def _load_shards(manifest_path,m):
    chunks={k:[] for k in ARRAY_DTYPES}
    total=0
    for shard in m.get("shards",[]):
        p=(manifest_path.parent / shard["path"]).resolve()
        try:p.relative_to(manifest_path.parent.resolve())
        except ValueError:raise AssertionError(f"shard escapes index run directory: {p}")
        if sha(p)!=shard["sha256"]: raise AssertionError(f"shard hash mismatch: {p}")
        with np.load(p,allow_pickle=False) as z:
            if set(z.files)!=set(ARRAY_DTYPES): raise AssertionError("unexpected shard array names")
            arrays={k:z[k] for k in ARRAY_DTYPES}
        n=int(shard["records"])
        if any(a.shape[0]!=n for a in arrays.values()): raise AssertionError("shard row-count mismatch")
        for k,a in arrays.items():
            if a.dtype!=ARRAY_DTYPES[k]: raise AssertionError(f"{k} dtype mismatch: {a.dtype}")
        if arrays["xyz"].shape!=(n,3,3) or arrays["plane_y_xz"].shape!=(n,3) or arrays["cell_range_rc"].shape!=(n,4):
            raise AssertionError("face-index array shape mismatch")
        if not np.isfinite(arrays["xyz"]).all() or not np.isfinite(arrays["plane_y_xz"]).all() or not np.isfinite(arrays["area_xz"]).all():
            raise AssertionError("nonfinite indexed geometry")
        for k in chunks: chunks[k].append(arrays[k])
        total+=n
    if total!=int(m.get("counts",{}).get("faces",-1)): raise AssertionError("manifest face total mismatch")
    arrays={k:(np.concatenate(v,axis=0) if v else np.empty((0,),dtype=ARRAY_DTYPES[k])) for k,v in chunks.items()}
    return arrays

def run_fixtures():
    cases=[]
    # A broad triangle overlaps many cells; range querying must find all touched cells.
    broad=np.asarray([[5.0,0.0,Z0-2.0],[23.0,1.0,Z0-3.0],[7.0,2.0,Z0-23.0]])
    rng=expected_closed_range(broad)
    touched=[(r,c) for r in range(int(rng[0]),int(rng[1])+1)
             for c in range(int(rng[2]),int(rng[3])+1) if direct_bbox_touches(broad,(r,c))]
    if len(touched)<6 or any(not ranges_intersect_cell(rng,cell) for cell in touched):
        raise AssertionError("broad multi-cell range fixture failed")
    cases.append("large_triangle_conservative_range:PASS")
    # Exact grid-line contact at X=6 includes columns 0 and 1.
    boundary=np.asarray([[6.0,0.0,Z0-1.0],[6.0,0.0,Z0-5.0],[9.0,0.0,Z0-3.0]])
    br=expected_closed_range(boundary)
    if br[2:4].tolist()!=[0,1]: raise AssertionError(f"exact X boundary fixture failed: {br.tolist()}")
    cases.append("closed_grid_boundary:PASS")
    # NW-SE split independently checked against an inclined native surface.
    corners=np.asarray([0.0,0.0,0.0,6.0])
    xy=_cell_xy(0,0)
    a=_affine(xy[np.asarray(TRIS[0])],corners[np.asarray(TRIS[0])])
    b=_affine(xy[np.asarray(TRIS[1])],corners[np.asarray(TRIS[1])])
    if abs(float((np.asarray([[6.0,Z0-3.0]])@a[:2]+a[2])[0])-3.0)>1e-12:
        raise AssertionError("NW-SE triangle 0 fixture failed")
    if abs(float((np.asarray([[3.0,Z0-6.0]])@b[:2]+b[2])[0])-3.0)>1e-12:
        raise AssertionError("NW-SE triangle 1 fixture failed")
    cases.append("native_NW_SE_triangles:PASS")
    # Empty/off-map triangle has an explicit inverted empty sentinel.
    outside=np.asarray([[-10.0,0.0,Z0-10.0],[-8.0,0.0,Z0-10.0],[-9.0,0.0,Z0-12.0]])
    if expected_closed_range(outside).tolist()!=[-1,-1,-1,-1]:
        raise AssertionError("empty range sentinel fixture failed")
    cases.append("empty_outside_map:PASS")
    # Degenerate triangle remains a record but must not contribute exposure.
    deg=np.asarray([[12.0,1.0,Z0-12.0],[18.0,1.0,Z0-12.0],[24.0,1.0,Z0-12.0]])
    poly=Polygon(deg[:,[0,2]])
    if poly.area!=0.0: raise AssertionError("degenerate XZ fixture failed")
    if not _face_exposure(deg,[0,0,1],np.zeros((N,N),dtype=np.float32),(2,2)).is_empty:
        raise AssertionError("degenerate exposure fixture failed")
    cases.append("degenerate_face_retained_but_no_exposure:PASS")
    # Negative: a query accelerated by a missing/incorrect range must lose a real touch.
    bad=rng.copy(); bad[1]=bad[0]; bad[3]=bad[2]
    if ranges_intersect_cell(bad,touched[-1]):
        raise AssertionError("negative omitted-range fixture did not reject")
    cases.append("negative_range_omission_detected:PASS")
    # Positive/negative affine clipping fixtures: flat face above ground is full; below is empty.
    flat=np.asarray([[0.,1.,Z0],[6.,1.,Z0],[0.,1.,Z0-6.]])
    if _face_exposure(flat,[0.,0.,1.],np.zeros((N,N),dtype=np.float32),(0,0)).area<=0:
        raise AssertionError("positive exposed face fixture failed")
    low=flat.copy(); low[:,1]=-1.
    if not _face_exposure(low,[0.,0.,-1.],np.zeros((N,N),dtype=np.float32),(0,0)).is_empty:
        raise AssertionError("negative buried face fixture failed")
    cases.append("exposure_positive_and_buried_negative:PASS")
    return {"status":"PASS","cases":cases,"triangulation":"NW-SE","range_semantics":"closed inclusive"}

def _load_frozen_module(name, path, expected_sha):
    if sha(path) != expected_sha: raise AssertionError(f"frozen source changed: {path}")
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    spec.loader.exec_module(module)
    return module

def _pack_keys(kind, object_id, face_id):
    oid=np.asarray(object_id,dtype=np.uint64);fid=np.asarray(face_id,dtype=np.uint64)
    k=np.asarray(kind,dtype=np.uint64)
    if np.any(oid>0x7fffffff) or np.any(fid>0xffffffff) or np.any(k>1):
        raise AssertionError("face identity out of canonical key range")
    return ((oid*2+k)<<np.uint64(32))|fid

def _lod_refs(model):
    out={}
    for kind,res in ((0,float(np.float32(3e15))),(1,1.0)):
        lods=[x for x in model.lods if x.resolution==res]
        if len(lods)!=1:raise AssertionError(f"nonunique required LOD kind={kind}")
        lod=lods[0]
        vertices=np.asarray([(float(v.x),float(v.y),float(v.z)) for v in lod.vertices],dtype=np.float64)
        faces=[]
        for face in lod.faces:
            ix=face.vertex_indices
            if len(ix)!=3:raise AssertionError("non-triangle compiled ODOL face")
            faces.append(ix)
        out[kind]=(lod,vertices,np.asarray(faces,dtype=np.int64))
    return out

def _input_guard(ev87,ev90,manifest_path,m):
    deploy=json.loads(DEPLOY.read_text(encoding="utf-8")); addon=Path(deploy["mod"])/"Addons"
    world_pbo=addon/"narva_trial.pbo";water_pbo=addon/"baltic_water_v30.pbo"
    expected={str(p.resolve()):h for p,h in {
        B/"candidate/terrain.npz":PINS["terrain_sha256"],P_FIELD:PINS["P_sha256"],F_FIELD:PINS["F_sha256"],
        WRP:PINS["wrp_source_sha256"],
        world_pbo:PINS["world_pbo_sha256"],water_pbo:PINS["water_pbo_sha256"],
        BOUNDS:PINS["bounds_sha256"],PLAN:PINS["plan_sha256"],
        EV87_SOURCE:PINS["ev87_source_sha256"],EV90_SOURCE:PINS["ev90_source_sha256"],
        BUILD_SOURCE:PINS["builder_source_sha256"]}.items()}
    if deploy.get("compiled_wrp_sha256")!=PINS["compiled_oprw_sha256"]:raise AssertionError("deploy OPRW hash pin mismatch")
    pbo=ev87.pbo_guard(DEPLOY,WRP)
    if not all(pbo[k] for k in ("expected_world_exact","expected_water_exact","deployed_oprw_matches_manifest","staged_source_wrp_identity_exact")):
        raise AssertionError(f"EV87 PBO/OPRW linkage failed: {pbo}")
    declared={str(Path(p).resolve()).casefold():h for p,h in m.get("input_hashes",{}).items()}
    for path,expected_hash in ev90.EXPECTED.items():
        if declared.get(str(Path(path).resolve()).casefold())!=expected_hash:
            raise AssertionError(f"manifest omits/re-pins EV90 frozen input {path}")
    expected={p.casefold():h for p,h in expected.items()}
    if not set(expected).issubset(declared):raise AssertionError("manifest input_hashes omit frozen B/source inputs")
    for p,h in declared.items():
        if not Path(p).is_file() or sha(Path(p))!=h:raise AssertionError(f"manifest input changed: {p}")
    for p,h in expected.items():
        if sha(Path(p))!=h:raise AssertionError(f"frozen input hash mismatch: {p}")
    return deploy,world_pbo,water_pbo

def _direct_exposure(ev87,h,cell,records):
    r,c=cell;cellxy=ev87.cell_xy(r,c);gh=ev87.corner_values(h,r,c);out={0:[],1:[]}
    for kind,xyz,plane in records:
        xy=np.asarray(xyz,dtype=np.float64)[:,[0,2]]
        if Polygon(xy).area<=1e-12:continue
        for tri in ev87.TRIS:
            g=ev87.odol_visible_in_native_tri(xy,plane,cellxy,gh,tri)
            if not g.is_empty:out[kind].append(g)
    return {k:(unary_union(v) if v else Polygon()) for k,v in out.items()}

def _production_consume(manifest_path,output_path):
    manifest_path,m=_load_manifest(manifest_path)
    ev87=_load_frozen_module("ev93_pinned_ev87",EV87_SOURCE,PINS["ev87_source_sha256"])
    ev90=_load_frozen_module("ev93_pinned_ev90",EV90_SOURCE,PINS["ev90_source_sha256"])
    deploy,world_pbo,water_pbo=_input_guard(ev87,ev90,manifest_path,m)
    # Full-map bbox selection; compiled_objects still reads only B's staged 0WZD
    # WRP and actual ODOLs. It verifies the pinned 18,024-object inventory.
    wrp,objects,models,model_hashes=ev87.compiled_objects(
        WRP,WORKSPACE,((0,0),(N-2,N-2)),MODEL_DIR,BOUNDS)
    if len(wrp["objects"])!=18033 or len(objects)!=18024:raise AssertionError("WRP/object counts differ")
    model_rows={int(x["model_id"]):x for x in m["models"]}
    if len(model_rows)!=len(m["models"]) or [*model_rows]!=sorted(model_rows):raise AssertionError("model ID table not sorted/unique")
    if len({int(o["id"]) for o,_,_ in objects})!=18024:raise AssertionError("source object IDs duplicate")
    ids=np.asarray(sorted(int(o["id"]) for o,_,_ in objects),dtype="<i4")
    if hashlib.sha256(ids.tobytes()).hexdigest()!=m.get("water_object_ids_sha256"):
        raise AssertionError("water object ID digest mismatch")
    names={str(x["basename"]).lower():x for x in m["models"]}
    if len(names)!=len(model_hashes):raise AssertionError("model inventory cardinality mismatch")
    for basename,hsh in model_hashes.items():
        row=names.get(basename.lower())
        if row is None or row.get("sha256")!=hsh:raise AssertionError(f"ODOL model pin mismatch: {basename}")
        if float(row["physical_resolution"])!=float(np.float32(3e15)) or float(row["visible_resolution"])!=1.0:
            raise AssertionError(f"LOD resolution metadata mismatch: {basename}")
    declared={str(Path(p).resolve()):h for p,h in m["input_hashes"].items()}
    for basename,hsh in model_hashes.items():
        modelpath=(MODEL_DIR/basename).resolve()
        if declared.get(str(modelpath))!=hsh or sha(modelpath)!=hsh:
            raise AssertionError(f"manifest omitted or changed ODOL: {basename}")

    refs={};expected_keys=[];counts={"physical":0,"visible":0};degens={"physical":0,"visible":0}
    object_meta={};model_lods={};model_face_counts={}
    for o,mat,bounds in objects:
        oid=int(o["id"]);name=o["name"].replace("\\","/").split("/")[-1]
        mtx=np.asarray(mat,dtype=np.float64)
        if not np.array_equal(mtx[:9].reshape(3,3),np.eye(3)):raise AssertionError(f"object {oid} is not translation-only")
        modelrow=names.get(name.lower())
        if modelrow is None:raise AssertionError(f"WRP object model absent from face-index table: {name}")
        mid=int(modelrow["model_id"]);object_meta[oid]=(name,mtx[9:12].copy(),np.asarray(bounds,dtype=np.float64))
        if name not in model_lods:model_lods[name]=_lod_refs(models[name])
        lods=model_lods[name]
        for kind,(lod,vertices,faces) in lods.items():
            label="physical" if kind==0 else "visible";n=len(faces);counts[label]+=n
            model_face_counts[name]=(len(lods[0][2]),len(lods[1][2]))
            keys=_pack_keys(np.full(n,kind,dtype=np.uint8),np.full(n,oid,dtype=np.int32),np.arange(n,dtype=np.uint32))
            expected_keys.append(keys)
            # Retain only per-model arrays; source face identity is (object,kind,face_id).
            refs[(oid,kind)]=(mid,mtx[9:12].copy(),vertices,faces,np.asarray(bounds,dtype=np.float64))
            xyzs=vertices[faces]+mtx[9:12]
            ab=xyzs[:,1][:,[0,2]]-xyzs[:,0][:,[0,2]]
            ac=xyzs[:,2][:,[0,2]]-xyzs[:,0][:,[0,2]]
            twice_area=np.abs(ab[:,0]*ac[:,1]-ab[:,1]*ac[:,0])
            degens[label]+=int(np.count_nonzero(twice_area==0.0))
    for name,face_counts in model_face_counts.items():
        row=names[name.lower()]
        if int(row["physical_faces"])!=face_counts[0] or int(row["visible_faces"])!=face_counts[1]:
            raise AssertionError(f"model face count metadata mismatch: {name}")
    source_keys=np.sort(np.concatenate(expected_keys))
    if len(np.unique(source_keys))!=len(source_keys):raise AssertionError("source face identity is not unique")
    if int(m["counts"]["physical"])!=counts["physical"] or int(m["counts"]["visible"])!=counts["visible"]:
        raise AssertionError("index physical/visible counts differ from independent ODOL enumeration")
    if int(m["counts"]["degenerate_physical"])!=degens["physical"] or int(m["counts"]["degenerate_visible"])!=degens["visible"]:
        raise AssertionError("index degeneracy counts differ from raw ODOL enumeration")

    strata=((128,128),(128,1024),(128,1918),(1024,128),(1024,1024),(1024,1918),
            (1918,128),(1918,1024),(1918,1918))
    sample_cells=[(832,362),(832,370),(832,377),(840,362),(840,370),(840,377),
                  (847,362),(847,370),(847,377)]+list(strata)
    sample_records={cell:[] for cell in sample_cells};sample_keys={cell:[] for cell in sample_cells}
    window=(839,841,369,371);window_keys=[];indexed_keys=[];row_total=0
    for shard in m["shards"]:
        sp=(manifest_path.parent/shard["path"]).resolve()
        if sha(sp)!=shard["sha256"]:raise AssertionError(f"shard hash mismatch: {sp}")
        with np.load(sp,allow_pickle=False) as z: arrays={k:z[k] for k in ARRAY_DTYPES}
        n=len(arrays["kind"]);row_total+=n
        if n!=int(shard["records"]):raise AssertionError("shard record count mismatch")
        for key,a in arrays.items():
            if a.dtype!=ARRAY_DTYPES[key]:raise AssertionError(f"wrong dtype for {key}")
        if arrays["xyz"].shape!=(n,3,3) or arrays["plane_y_xz"].shape!=(n,3) or arrays["cell_range_rc"].shape!=(n,4):
            raise AssertionError("index array shape mismatch")
        if not np.isfinite(arrays["xyz"]).all() or not np.isfinite(arrays["plane_y_xz"]).all() or not np.isfinite(arrays["area_xz"]).all():
            raise AssertionError("nonfinite indexed values")
        if np.any(arrays["kind"]>1) or np.any(arrays["degenerate"]>1):raise AssertionError("invalid kind/degenerate enum")
        indexed_keys.append(_pack_keys(arrays["kind"],arrays["object_id"],arrays["face_id"]))
        for i in range(n):
            kind=int(arrays["kind"][i]);oid=int(arrays["object_id"][i]);fid=int(arrays["face_id"][i])
            ref=refs.get((oid,kind))
            if ref is None:raise AssertionError(f"index has unknown object/kind {(oid,kind)}")
            mid,translation,vertices,faces,_=ref
            if int(arrays["model_id"][i])!=mid:raise AssertionError(f"model/object identity mismatch {(oid,kind,fid)}")
            if fid<0 or fid>=len(faces):raise AssertionError(f"face id out of range {(oid,kind,fid)}")
            xyz=vertices[faces[fid]]+translation
            if not np.array_equal(arrays["xyz"][i],xyz):raise AssertionError(f"XYZ differs from source {(oid,kind,fid)}")
            xy=xyz[:,[0,2]]
            area=0.5*abs(float((xy[1,0]-xy[0,0])*(xy[2,1]-xy[0,1])-(xy[1,1]-xy[0,1])*(xy[2,0]-xy[0,0])))
            if abs(float(arrays["area_xz"][i])-area)>1e-12:raise AssertionError(f"area_xz differs {(oid,kind,fid)}")
            if int(arrays["degenerate"][i])!=int(area==0.0):raise AssertionError(f"degenerate classification differs {(oid,kind,fid)}")
            er=expected_closed_range(xyz);rr=np.asarray(arrays["cell_range_rc"][i],dtype=np.int32)
            if er.tolist()==[-1,-1,-1,-1]:
                if rr.tolist()!=er.tolist():raise AssertionError(f"offmap sentinel differs {(oid,kind,fid)}")
            elif rr[0]>er[0] or rr[1]<er[1] or rr[2]>er[2] or rr[3]<er[3]:
                raise AssertionError(f"range omits source bbox cells {(oid,kind,fid)}")
            plane=np.asarray(arrays["plane_y_xz"][i],dtype=np.float64)
            if area==0.0:
                if np.any(plane!=0.0):raise AssertionError(f"degenerate plane sentinel nonzero {(oid,kind,fid)}")
            else:
                err=float(np.max(np.abs(xyz[:,1]-(xyz[:,0]*plane[0]+xyz[:,2]*plane[1]+plane[2]))))
                if err>1e-8:raise AssertionError(f"plane mismatch {(oid,kind,fid)}: {err}")
        for cell in sample_cells:
            for i in query_rows(arrays,cell):
                sample_records[cell].append((int(arrays["kind"][i]),arrays["xyz"][i].copy(),arrays["plane_y_xz"][i].copy()))
                sample_keys[cell].append(_pack_keys(arrays["kind"][i:i+1],arrays["object_id"][i:i+1],arrays["face_id"][i:i+1])[0])
        ranges=arrays["cell_range_rc"]
        wm=(ranges[:,0]<=window[1])&(ranges[:,1]>=window[0])&(ranges[:,2]<=window[3])&(ranges[:,3]>=window[2])
        window_keys.append(_pack_keys(arrays["kind"][wm],arrays["object_id"][wm],arrays["face_id"][wm]))
    index_keys=np.sort(np.concatenate(indexed_keys))
    if row_total!=len(source_keys) or row_total!=int(m["counts"]["faces"]) or not np.array_equal(index_keys,source_keys):
        raise AssertionError("index has missing, duplicate, or extra source face identities")

    # Exercise the shipped query API, then compare its answers with the independent
    # closed-range scan assembled above. The API is not used as the source oracle.
    builder=_load_frozen_module("ev93_pinned_face_index_api",BUILD_SOURCE,PINS["builder_source_sha256"])
    face_index=builder.FaceRangeIndex(manifest_path.parent)
    api_records={};api_queries={}
    for cell in sample_cells:
        got=face_index.query_cell(*cell)
        api_keys=np.sort(_pack_keys(got["kind"],got["object_id"],got["face_id"]))
        manual=np.sort(np.asarray(sample_keys[cell],dtype=np.uint64))
        if not np.array_equal(api_keys,manual):raise AssertionError(f"query_cell differs from independent ranges at {cell}")
        api_records[cell]=[(int(got["kind"][i]),got["xyz"][i],got["plane_y_xz"][i]) for i in range(len(got["kind"]))]
        api_queries[f"cell:{cell[0]},{cell[1]}"]=int(len(api_keys))
    win=face_index.query_window(*window)
    win_keys=np.sort(_pack_keys(win["kind"],win["object_id"],win["face_id"]))
    manual_win=np.sort(np.concatenate(window_keys))
    if not np.array_equal(win_keys,manual_win):raise AssertionError("query_window differs from independent range scan")
    api_queries["window:839-841,369-371"]=int(len(win_keys))

    h=np.load(B/"candidate/terrain.npz",allow_pickle=False)["heights"].astype(np.float64)
    # Direct raw enumeration per selected spatial cell is independent of the index query.
    exposure={}
    for cell in sample_cells:
        r,c=cell;x0,x1=c*CELL,(c+1)*CELL;z1,z0=Z0-r*CELL,Z0-(r+1)*CELL
        direct=[]
        for (oid,kind),(mid,trans,verts,faces,obj_bounds) in refs.items():
            bx0,bz0,bx1,bz1=map(float,obj_bounds)
            if bx1<x0 or bx0>x1 or bz1<z0 or bz0>z1:continue
            xyzs=verts[faces]+trans
            xmin=xyzs[:,:,0].min(axis=1);xmax=xyzs[:,:,0].max(axis=1)
            zmin=xyzs[:,:,2].min(axis=1);zmax=xyzs[:,:,2].max(axis=1)
            idx=np.flatnonzero((xmax>=x0)&(xmin<=x1)&(zmax>=z0)&(zmin<=z1))
            for fid in idx:
                xyz=xyzs[fid];xy=xyz[:,[0,2]]
                twice=abs(float((xy[1,0]-xy[0,0])*(xy[2,1]-xy[0,1])-(xy[1,1]-xy[0,1])*(xy[2,0]-xy[0,0])))
                if twice==0.0:continue
                plane=np.linalg.solve(np.column_stack((xy[:,0],xy[:,1],np.ones(3))),xyz[:,1])
                direct.append((kind,xyz,plane))
        d=_direct_exposure(ev87,h,cell,direct);q=_direct_exposure(ev87,h,cell,api_records[cell])
        cell_result={}
        for kind,label in ((0,"physical"),(1,"visible")):
            diff=float(d[kind].symmetric_difference(q[kind]).area)
            cell_result[label]={"direct_area_m2":float(d[kind].area),"indexed_area_m2":float(q[kind].area),
                "symmetric_difference_m2":diff,"pass_existing_0_002m2_coverage_tolerance":diff<=0.002}
            if diff>0.002:raise AssertionError(f"indexed exposure differs from direct scan at {cell}/{label}: {diff}")
        exposure[f"{r},{c}"]=cell_result
    # Recheck all manifest inputs after reading index, WRP and ODOLs (TOCTOU guard).
    face_index.reverify()
    for p,hsh in m["input_hashes"].items():
        if sha(Path(p))!=hsh:raise AssertionError(f"source changed while consumer ran: {p}")
    result={"status":"PASS_INDEX_AND_SAMPLED_EXPOSURE","manifest_path":str(manifest_path),
        "manifest_sha256":sha(manifest_path),"source_objects":len(objects),"source_models":len(model_hashes),
        "direct_face_counts":counts,"index_face_count":row_total,"source_degenerate_counts":degens,
        "api_query_counts":api_queries,
        "sampled_cells":exposure,"limits":["static WRP/ODOL identity, inclusive ranges, and sampled geometric exposure",
        "does not verify dynamic water rendering or an in-game visual result"]}
    output_path=Path(output_path);output_path.parent.mkdir(parents=True,exist_ok=True)
    output_path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--fixtures-only",action="store_true")
    ap.add_argument("--manifest",type=Path)
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    if args.fixtures_only:
        result=run_fixtures()
        print(json.dumps(result,indent=2))
        return
    if not args.manifest:
        ap.error("--manifest required unless --fixtures-only")
    if not args.output: ap.error("--output required with --manifest")
    print(json.dumps(_production_consume(args.manifest,args.output),indent=2))

if __name__=="__main__":
    main()

