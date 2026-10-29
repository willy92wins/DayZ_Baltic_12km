"""Shared bounded I/O and digest primitives for Q03B.

Only this module is shared by producer and consumer. It contains no
semantic checks, no META/instance/coverage guards and no report builder.
"""
from __future__ import annotations
import ast, hashlib, io, json, os, struct, zipfile
from pathlib import Path
import numpy as np

MAX_HEADER = 16384
MAGIC = b"\x93NUMPY"

class Reject(Exception):
    status = "REJECTED"
    def __init__(self, code, message):
        super().__init__(message); self.code = code; self.message = message
class Inconclusive(Exception):
    status = "INCONCLUSIVE"
    def __init__(self, code, message):
        super().__init__(message); self.code = code; self.message = message

def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()
def is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)
def require(cond, code, msg):
    if not cond: raise Reject(code, msg)
def req_int(v, code, what):
    require(is_int(v), code, f"{what} must be int, not bool/other")
    return v
def req_str(v, code, what):
    require(isinstance(v, str), code, f"{what} must be str")
    return v
def req_bool(v, code, what):
    require(isinstance(v, bool), code, f"{what} must be bool")
    return v
def req_keys(obj, allowed, code, what, optional=()):
    require(isinstance(obj, dict), code, f"{what} must be object")
    keys = set(obj)
    require(not (keys - set(allowed) - set(optional)), code, f"{what} unknown keys {sorted(keys-set(allowed)-set(optional))}")
    require(not (set(allowed) - keys), code, f"{what} missing keys {sorted(set(allowed)-keys)}")
    return obj

def read_snapshot(path, cap, code="INCONCLUSIVE_SOURCE_IO"):
    p = Path(path)
    try:
        if p.is_symlink(): raise Reject("REJECTED_REPARSE", f"reparse/symlink rejected: {p}")
        st1 = p.stat()
        require(st1.st_size <= cap, "REJECTED_SIZE_CAP", f"file exceeds cap: {p}")
        chunks = []
        with p.open("rb") as fh:
            while True:
                b = fh.read(1048576)
                if not b: break
                chunks.append(b)
                if sum(len(x) for x in chunks) > cap: raise Reject("REJECTED_SIZE_CAP", f"file exceeds cap: {p}")
        data = b"".join(chunks)
        st2 = p.stat()
        require((st1.st_size, st1.st_mtime_ns, st1.st_ino) == (st2.st_size, st2.st_mtime_ns, st2.st_ino), "INCONCLUSIVE_SOURCE_CHANGED", f"file changed while reading: {p}")
        return data
    except (Reject, Inconclusive): raise
    except OSError as e: raise Inconclusive(code, f"{type(e).__name__}: {e}") from e

def check_pin(data, pin, what):
    req_keys(pin, {"path", "sha256", "bytes"}, "REJECTED_PIN_SCHEMA", what)
    req_int(pin["bytes"], "REJECTED_PIN_SCHEMA", what + ".bytes")
    req_str(pin["sha256"], "REJECTED_PIN_SCHEMA", what + ".sha256")
    require(len(data) == pin["bytes"], "REJECTED_PIN_BYTES", f"{what} byte count mismatch")
    require(sha256_bytes(data) == pin["sha256"], "REJECTED_PIN_SHA", f"{what} sha mismatch")

def _no_dup(pairs):
    out = {}
    for k, v in pairs:
        if k in out: raise Reject("REJECTED_JSON_DUPLICATE_KEY", f"duplicate JSON key {k!r}")
        out[k] = v
    return out
def parse_json(data, what):
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=_no_dup, parse_constant=lambda x: (_ for _ in ()).throw(Reject("REJECTED_JSON_CONSTANT", what)))
    except Reject: raise
    except Exception as e: raise Reject("REJECTED_JSON_PARSE", f"{what}: {type(e).__name__}: {e}") from e
def load_pinned_json(path, pin, cap):
    data = read_snapshot(path, cap)
    check_pin(data, pin, str(path))
    return parse_json(data, str(path)), data

def contract_bytes(contract_path, external_sha):
    require(isinstance(external_sha, str) and len(external_sha) == 64, "REJECTED_CONTRACT_SHA", "external contract SHA required")
    data = read_snapshot(contract_path, 33554432)
    require(sha256_bytes(data) == external_sha.lower(), "REJECTED_CONTRACT_SHA", "contract SHA mismatch")
    return data

def parse_npy_header(blob, what):
    require(len(blob) >= 10, "REJECTED_NPY_SHORT", what)
    require(blob[:6] == MAGIC, "REJECTED_NPY_MAGIC", what)
    major, minor = blob[6], blob[7]
    require(major in (1, 2), "REJECTED_NPY_VERSION", f"{what} NPY version {major}.{minor} rejected")
    if major == 1:
        hlen = struct.unpack("<H", blob[8:10])[0]; off = 10
    else:
        require(len(blob) >= 12, "REJECTED_NPY_SHORT", what)
        hlen = struct.unpack("<I", blob[8:12])[0]; off = 12
    require(hlen <= MAX_HEADER, "REJECTED_NPY_HEADER_SIZE", f"{what} header {hlen} > 16384 before allocation")
    require(off + hlen <= len(blob), "REJECTED_NPY_SHORT", what)
    try: hdr = ast.literal_eval(blob[off:off+hlen].decode("latin1").strip())
    except Exception as e: raise Reject("REJECTED_NPY_HEADER", f"{what}: {e}") from e
    require(isinstance(hdr, dict) and set(hdr) == {"descr", "fortran_order", "shape"}, "REJECTED_NPY_HEADER", what)
    require(hdr["fortran_order"] is False, "REJECTED_NPY_FORTRAN", what)
    try: dtype = np.dtype(hdr["descr"])
    except Exception as e: raise Reject("REJECTED_NPY_DTYPE", f"{what}: {e}") from e
    require(not dtype.hasobject, "REJECTED_NPY_OBJECT", what)
    shape = hdr["shape"]
    require(isinstance(shape, tuple) and len(shape) <= 3, "REJECTED_NPY_SHAPE", what)
    require(all(is_int(x) and 0 <= x <= 2000000 for x in shape), "REJECTED_NPY_SHAPE", what)
    count = 1
    for x in shape: count *= x
    require(off + hlen + count * dtype.itemsize == len(blob), "REJECTED_NPY_TRAILING", f"{what} expected bytes != actual, trailing/short data")
    return dtype, shape, hlen

def load_npz(data, expected_members, limits, what):
    require(len(data) <= limits.get("npz_stored_bytes", 16777216), "REJECTED_NPZ_STORED_CAP", what)
    try: zf = zipfile.ZipFile(io.BytesIO(data))
    except Exception as e: raise Reject("REJECTED_ZIP_OPEN", f"{what}: {type(e).__name__}") from e
    infos = zf.infolist()
    names = [i.filename for i in infos]
    require(len(names) == len(set(names)), "REJECTED_ZIP_DUPLICATE_MEMBER", what)
    require(all(not n.endswith("/") and not i.is_dir() for n, i in zip(names, infos)), "REJECTED_ZIP_DIRECTORY", what)
    require(all("\\" not in n and not n.startswith("/") and ".." not in n.split("/") and ":" not in n for n in names), "REJECTED_ZIP_PATH", what)
    require(all(i.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED) for i in infos), "REJECTED_ZIP_COMPRESSION", what)
    require(all(not (i.flag_bits & 0x1) for i in infos), "REJECTED_ZIP_ENCRYPTED", what)
    require(len(names) <= limits.get("zip_members", 35), "REJECTED_ZIP_MEMBER_CAP", what)
    if expected_members is not None:
        require(set(names) == set(expected_members), "REJECTED_ZIP_MEMBERS", f"{what} members {sorted(names)} != {sorted(expected_members)}")
    total = 0; arrays = {}; meta = []
    for info in infos:
        require(info.file_size <= limits.get("archive_expanded_bytes", 134217728), "REJECTED_ZIP_EXPANDED_CAP", what)
        total += info.file_size
        try: blob = zf.read(info.filename)
        except Exception as e: raise Inconclusive("INCONCLUSIVE_SOURCE_IO", f"{what}/{info.filename}: {type(e).__name__}") from e
        require(len(blob) == info.file_size, "REJECTED_ZIP_SIZE", what)
        dtype, shape, hlen = parse_npy_header(blob, f"{what}/{info.filename}")
        try: arr = np.load(io.BytesIO(blob), allow_pickle=False, max_header_size=MAX_HEADER)
        except Exception as e: raise Reject("REJECTED_NPY_LOAD", f"{what}/{info.filename}: {type(e).__name__}") from e
        require(not arr.dtype.hasobject, "REJECTED_NPY_OBJECT", info.filename)
        require(arr.shape == tuple(shape) and arr.dtype == dtype, "REJECTED_NPY_LOAD", info.filename)
        require(arr.flags["C_CONTIGUOUS"] or arr.size == 0, "REJECTED_NPY_FORTRAN", info.filename)
        raw = arr.tobytes(order="C")
        arrays[info.filename[:-4] if info.filename.endswith(".npy") else info.filename] = arr
        meta.append({"name": arrays and (info.filename[:-4] if info.filename.endswith(".npy") else info.filename), "dtype": arr.dtype.descr if arr.dtype.fields else str(arr.dtype), "shape": [int(x) for x in arr.shape], "order": "C", "data_sha256": sha256_bytes(raw), "header_bytes": int(hlen), "itemsize": int(arr.dtype.itemsize)})
    require(total <= limits.get("archive_expanded_bytes", 134217728), "REJECTED_ZIP_EXPANDED_CAP", what)
    meta.sort(key=lambda x: x["name"])
    return arrays, meta

def new_output(path):
    p = Path(path)
    try: p.mkdir(parents=True, exist_ok=False)
    except FileExistsError as e: raise Reject("REJECTED_OUTPUT_EXISTS", f"output exists: {p}") from e
    except OSError as e: raise Inconclusive("INCONCLUSIVE_SOURCE_IO", f"{type(e).__name__}: {e}") from e
    return p
def atomic_write_json(outdir, name, obj):
    raw = (json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    require(len(raw) <= 33554432, "REJECTED_OUTPUT_CAP", name)
    tmp = Path(outdir) / (name + ".tmp")
    with tmp.open("xb") as fh: fh.write(raw); fh.flush(); os.fsync(fh.fileno())
    os.replace(tmp, Path(outdir) / name)
    return raw
def failure_obj(exc):
    return {"schema": "q03b-failure-v1", "status": getattr(exc, "status", "REJECTED"), "code": getattr(exc, "code", "REJECTED_INTERNAL"), "error_type": type(exc).__name__, "message": str(exc)}
