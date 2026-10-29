"""Shared bounded I/O and digest primitives for Q03B.

Only this module is shared by producer and consumer. It contains no
semantic checks, no META/instance/coverage guards and no report builder.
"""
from __future__ import annotations
import ast, hashlib, io, json, os, stat, struct, zipfile
from pathlib import Path
import numpy as np
MAX_HEADER = 16384
MAGIC = b"\x93NUMPY"
REPARSE_FLAG = 0x400

class Reject(Exception):
    status = "REJECTED"
    def __init__(self, code, message):
        super().__init__(message); self.code = code; self.message = message
class Inconclusive(Exception):
    status = "INCONCLUSIVE"
    def __init__(self, code, message):
        super().__init__(message); self.code = code; self.message = message

def sha256_bytes(data): return hashlib.sha256(data).hexdigest()
def is_int(v): return isinstance(v, int) and not isinstance(v, bool)
def require(cond, code, msg):
    if not cond: raise Reject(code, msg)
def req_int(v, code, what):
    require(is_int(v), code, f"{what} must be int, not bool/other"); return v
def req_str(v, code, what):
    require(isinstance(v, str), code, f"{what} must be str"); return v
def req_bool(v, code, what):
    require(isinstance(v, bool), code, f"{what} must be bool"); return v
def req_keys(obj, allowed, code, what, optional=()):
    require(isinstance(obj, dict), code, f"{what} must be object")
    keys = set(obj)
    require(not (keys - set(allowed) - set(optional)), code, f"{what} unknown keys {sorted(keys-set(allowed)-set(optional))}")
    require(not (set(allowed) - keys), code, f"{what} missing keys {sorted(set(allowed)-keys)}")
    return obj

def _identity(st):
    return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns)

def read_snapshot(path, cap, code="INCONCLUSIVE_SOURCE_IO"):
    p = Path(path)
    try:
        st1 = os.lstat(p)
        attrs = getattr(st1, "st_file_attributes", 0)
        if stat.S_ISLNK(st1.st_mode) or p.is_symlink() or (attrs & REPARSE_FLAG):
            raise Reject("REJECTED_REPARSE", f"reparse/symlink rejected: {p}")
        require(stat.S_ISREG(st1.st_mode), code, f"not a regular file: {p}")
        require(st1.st_size <= cap, "REJECTED_SIZE_CAP", f"file exceeds cap: {p}")
        chunks = []; total = 0
        with p.open("rb") as fh:
            fst1 = os.fstat(fh.fileno())
            require(_identity(fst1) == _identity(st1), "INCONCLUSIVE_SOURCE_CHANGED", f"path/handle identity mismatch before read: {p}")
            while True:
                b = fh.read(1048576)
                if not b: break
                chunks.append(b); total += len(b)
                if total > cap: raise Reject("REJECTED_SIZE_CAP", f"file exceeds cap: {p}")
            fst2 = os.fstat(fh.fileno())
        data = b"".join(chunks)
        st2 = os.lstat(p)
        attrs2 = getattr(st2, "st_file_attributes", 0)
        if stat.S_ISLNK(st2.st_mode) or (attrs2 & REPARSE_FLAG):
            raise Reject("REJECTED_REPARSE", f"reparse/symlink rejected: {p}")
        require(_identity(st1) == _identity(fst2) == _identity(st2), "INCONCLUSIVE_SOURCE_CHANGED", f"file changed while reading: {p}")
        require(len(data) == st1.st_size, "INCONCLUSIVE_SOURCE_CHANGED", f"short read: {p}")
        return data
    except (Reject, Inconclusive): raise
    except OSError as e: raise Inconclusive(code, f"{type(e).__name__}: {e}") from e

def check_pin(data, pin, what):
    # Accept a full array entry at this I/O boundary, but validate only its
    # projected sub-pin {path,sha256,bytes}; unknown keys still reject.
    req_keys(pin, {"path", "sha256", "bytes"}, "REJECTED_PIN_SCHEMA", what, optional=("relative", "kind", "expanded_bound"))
    req_str(pin["path"], "REJECTED_PIN_SCHEMA", what + ".path")
    req_int(pin["bytes"], "REJECTED_PIN_SCHEMA", what + ".bytes")
    req_str(pin["sha256"], "REJECTED_PIN_SCHEMA", what + ".sha256")
    require(len(pin["sha256"]) == 64, "REJECTED_PIN_SCHEMA", what + ".sha256 length")
    require(len(data) == pin["bytes"], "REJECTED_PIN_BYTES", f"{what} byte count mismatch")
    require(sha256_bytes(data) == pin["sha256"], "REJECTED_PIN_SHA", f"{what} sha mismatch")

def _no_dup(pairs):
    out = {}
    for k, v in pairs:
        if k in out: raise Reject("REJECTED_JSON_DUPLICATE_KEY", f"duplicate JSON key {k!r}")
        out[k] = v
    return out
def _bad_const(x): raise Reject("REJECTED_JSON_CONSTANT", f"JSON constant {x}")
def parse_json(data, what):
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=_no_dup, parse_constant=_bad_const)
    except Reject: raise
    except Exception as e: raise Reject("REJECTED_JSON_PARSE", f"{what}: {type(e).__name__}: {e}") from e
def load_pinned_json(path, pin, cap):
    data = read_snapshot(path, cap); check_pin(data, pin, str(path)); return parse_json(data, str(path)), data
def contract_bytes(contract_path, external_sha):
    require(isinstance(external_sha, str) and len(external_sha) == 64, "REJECTED_CONTRACT_SHA", "external contract SHA required")
    data = read_snapshot(contract_path, 33554432)
    require(sha256_bytes(data) == external_sha.lower(), "REJECTED_CONTRACT_SHA", "contract SHA mismatch")
    return data

def _parse_header_bytes(hdr_bytes, what):
    try: hdr = ast.literal_eval(hdr_bytes.decode("latin1").strip())
    except Exception as e: raise Reject("REJECTED_NPY_HEADER", f"{what}: {e}") from e
    require(isinstance(hdr, dict) and set(hdr) == {"descr", "fortran_order", "shape"}, "REJECTED_NPY_HEADER", what)
    return hdr
def _dtype_shape(hdr, limits, what):
    require(hdr["fortran_order"] is False, "REJECTED_NPY_FORTRAN", what)
    try: dtype = np.dtype(hdr["descr"])
    except Exception as e: raise Reject("REJECTED_NPY_DTYPE", f"{what}: {e}") from e
    require(not dtype.hasobject, "REJECTED_NPY_OBJECT", what)
    require(dtype.str[0] != ">", "REJECTED_NPY_DTYPE", f"{what} big-endian dtype {dtype.str}")
    if dtype.fields:
        for _nm, (fmt, *_rest) in dtype.fields.items():
            require(np.dtype(fmt).str[0] != ">", "REJECTED_NPY_DTYPE", f"{what} big-endian field")
    shape = hdr["shape"]
    max_dim = int(limits.get("max_dimension", 2000000)); max_dims = int(limits.get("max_dimensions", 3))
    require(isinstance(shape, tuple) and len(shape) <= max_dims, "REJECTED_NPY_SHAPE", what)
    require(all(is_int(x) and 0 <= x <= max_dim for x in shape), "REJECTED_NPY_SHAPE", what)
    count = 1
    for x in shape: count *= x
    return dtype, tuple(int(x) for x in shape), count
def descr_json(dtype):
    if dtype.fields: return [[str(n), str(f[0])] for n, f in dtype.descr]
    return dtype.str

def parse_npy_header(blob, what, limits=None):
    limits = limits or {}
    require(len(blob) >= 10, "REJECTED_NPY_SHORT", what)
    require(blob[:6] == MAGIC, "REJECTED_NPY_MAGIC", what)
    major, minor = blob[6], blob[7]
    require(major in (1, 2), "REJECTED_NPY_VERSION", f"{what} NPY version {major}.{minor} rejected")
    if major == 1: hlen = struct.unpack("<H", blob[8:10])[0]; off = 10
    else:
        require(len(blob) >= 12, "REJECTED_NPY_SHORT", what)
        hlen = struct.unpack("<I", blob[8:12])[0]; off = 12
    require(hlen <= MAX_HEADER, "REJECTED_NPY_HEADER_SIZE", f"{what} header {hlen} > 16384 before allocation")
    require(off + hlen <= len(blob), "REJECTED_NPY_SHORT", what)
    hdr = _parse_header_bytes(blob[off:off+hlen], what)
    dtype, shape, count = _dtype_shape(hdr, limits, what)
    require(off + hlen + count * dtype.itemsize == len(blob), "REJECTED_NPY_TRAILING", f"{what} expected bytes != actual")
    return dtype, shape, hlen

def load_npz(data, expected_members, limits, what, expanded_bound=None):
    limits = limits or {}
    stored_cap = int(limits.get("npz_stored_bytes", 16777216))
    archive_cap = int(limits.get("archive_expanded_bytes", 134217728))
    require(len(data) <= stored_cap, "REJECTED_NPZ_STORED_CAP", what)
    try: zf = zipfile.ZipFile(io.BytesIO(data))
    except Exception as e: raise Reject("REJECTED_ZIP_OPEN", f"{what}: {type(e).__name__}") from e
    infos = zf.infolist(); names = [i.filename for i in infos]
    require(len(names) == len(set(names)), "REJECTED_ZIP_DUPLICATE_MEMBER", what)
    require(all(not n.endswith("/") and not i.is_dir() for n, i in zip(names, infos)), "REJECTED_ZIP_DIRECTORY", what)
    require(all("\\" not in n and not n.startswith("/") and ".." not in n.split("/") and ":" not in n for n in names), "REJECTED_ZIP_PATH", what)
    require(all(i.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED) for i in infos), "REJECTED_ZIP_COMPRESSION", what)
    require(all(not (i.flag_bits & 0x1) for i in infos), "REJECTED_ZIP_ENCRYPTED", what)
    require(len(names) <= int(limits.get("zip_members", 35)), "REJECTED_ZIP_MEMBER_CAP", what)
    if expected_members is not None:
        want_zip = {str(m) + ".npy" for m in expected_members}
        require(set(names) == want_zip, "REJECTED_ZIP_MEMBERS", f"{what} members {sorted(names)} != {sorted(want_zip)}")
    # Preflight every ZipInfo size before reading any payload.
    total = 0
    for info in infos:
        require(info.file_size <= archive_cap, "REJECTED_ZIP_EXPANDED_CAP", what)
        total += int(info.file_size)
    require(total <= archive_cap, "REJECTED_ZIP_EXPANDED_CAP", what)
    if expanded_bound is not None:
        require(total <= int(expanded_bound), "REJECTED_ZIP_EXPANDED_CAP", f"{what} expanded {total} > bound {expanded_bound}")
    # Pass 1: bounded MAGIC/version/header-length/header inspection for all
    # members before any array construction (no np.load anywhere).
    specs = []
    for info in infos:
        w = f"{what}/{info.filename}"
        try:
            with zf.open(info, "r") as fh:
                prefix = fh.read(10)
                require(len(prefix) >= 10, "REJECTED_NPY_SHORT", w)
                require(prefix[:6] == MAGIC, "REJECTED_NPY_MAGIC", w)
                major, minor = prefix[6], prefix[7]
                require(major in (1, 2), "REJECTED_NPY_VERSION", f"{w} NPY version {major}.{minor} rejected")
                if major == 1: hlen = struct.unpack("<H", prefix[8:10])[0]; off = 10
                else:
                    extra = fh.read(2); require(len(extra) == 2, "REJECTED_NPY_SHORT", w)
                    hlen = struct.unpack("<I", extra)[0]; off = 12
                require(hlen <= MAX_HEADER, "REJECTED_NPY_HEADER_SIZE", f"{w} header {hlen} > 16384 before allocation")
                hdr_bytes = fh.read(hlen)
                require(len(hdr_bytes) == hlen, "REJECTED_NPY_SHORT", w)
        except (Reject, Inconclusive): raise
        except Exception as e: raise Reject("REJECTED_ZIP_SIZE", f"{w}: {type(e).__name__}: {e}") from e
        hdr = _parse_header_bytes(hdr_bytes, w)
        dtype, shape, count = _dtype_shape(hdr, limits, w)
        expected_total = off + hlen + count * dtype.itemsize
        if int(info.file_size) < expected_total: raise Reject("REJECTED_ZIP_SIZE", f"{w} decompressed larger than declared/header size")
        require(int(info.file_size) == expected_total, "REJECTED_NPY_TRAILING", f"{w} expected bytes != actual, trailing/short data")
        specs.append((info, dtype, shape, count, hlen, off))
    # Pass 2: bounded payload reads; an extra decompressed byte is ZIP_SIZE.
    arrays = {}; meta = []
    for info, dtype, shape, count, hlen, off in specs:
        w = f"{what}/{info.filename}"; payload_len = count * dtype.itemsize
        try:
            with zf.open(info, "r") as fh:
                fh.read(off + hlen)
                payload = fh.read(payload_len)
                require(len(payload) == payload_len, "REJECTED_ZIP_SIZE", w)
                extra = fh.read(1)
                require(extra == b"", "REJECTED_ZIP_SIZE", f"{w} decompressed larger than header-declared size")
        except (Reject, Inconclusive): raise
        except Exception as e: raise Reject("REJECTED_ZIP_SIZE", f"{w}: {type(e).__name__}: {e}") from e
        arr = np.frombuffer(payload, dtype=dtype, count=count).reshape(shape).copy()
        require(not arr.dtype.hasobject, "REJECTED_NPY_OBJECT", info.filename)
        bare = info.filename[:-4] if info.filename.endswith(".npy") else info.filename
        arrays[bare] = arr
        meta.append({"name": bare, "dtype": descr_json(arr.dtype), "shape": [int(x) for x in arr.shape], "order": "C", "data_sha256": sha256_bytes(arr.tobytes(order="C")), "header_bytes": int(hlen), "itemsize": int(arr.dtype.itemsize)})
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
