# Road object pilot author (offline, source-only). Independent WRP reader/writer.
import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

SCHEMA = "road-object-pilot.v1"
STATUS_IN = "SOURCE_RECIPE_ONLY"
STATUS_OUT = "CANDIDATE_SOURCE_OFFLINE"
MAX_SOURCE_BYTES = 512 * 1024 * 1024
UINT32_MAX = 4294967295
_TOP_KEYS = {"schema", "source_path", "source_sha256", "source_bytes", "object_count", "max_id", "prefix_bytes", "prefix_sha256", "terminator_hex", "objects", "pins", "status"}
_OBJ_KEYS = {"name", "raw_name_hex", "id", "matrix12"}
_HEX = set("0123456789abcdef")
_EXPECTED_PREFIX = b"dz\\structures\\roads\\"


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _sha_ok(v):
    return isinstance(v, str) and len(v) == 64 and all(c in _HEX for c in v)


def _parse_int(text):
    if text == "-0":
        raise ValueError("JSON integer -0 is forbidden")
    return int(text)


def _pack_matrix(matrix):
    if not isinstance(matrix, list) or len(matrix) != 12:
        raise ValueError("matrix12 must be a list of 12")
    parts = []
    for v in matrix:
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ValueError("matrix12 values must be finite numbers")
        try:
            fv = float(v)
        except Exception:
            raise ValueError("matrix12 values must be finite numbers")
        if not math.isfinite(fv):
            raise ValueError("matrix12 values must be finite numbers")
        try:
            packed = struct.pack("<f", fv)
        except Exception:
            raise ValueError("matrix12 cannot be packed as f32")
        unpacked = struct.unpack("<f", packed)[0]
        if unpacked != fv or (fv == 0.0 and math.copysign(1.0, unpacked) != math.copysign(1.0, fv)):
            raise ValueError("matrix12 value is not exactly representable as float32")
        parts.append(packed)
    return b"".join(parts)


def _validate_name(name, raw):
    if not isinstance(name, str) or not name:
        raise ValueError("object name must be a non-empty string")
    try:
        decoded = raw.decode("ascii")
    except Exception:
        raise ValueError("raw name is not ASCII")
    if name != decoded:
        raise ValueError("object name does not match raw_name_hex")
    if b"\x00" in raw:
        raise ValueError("raw name contains NUL")
    if any(b < 0x20 or b > 0x7E for b in raw):
        raise ValueError("raw name is not printable ASCII")
    if raw != raw.lower():
        raise ValueError("raw name must be lowercase")
    if b"/" in raw:
        raise ValueError("raw name must not contain slash")
    if not raw.startswith(_EXPECTED_PREFIX):
        raise ValueError("raw name must start with expected prefix dz\\structures\\roads\\")
    if b":" in raw:
        raise ValueError("raw name must not be absolute")
    parts = raw.split(b"\\")
    if any(p in (b"", b".", b"..") for p in parts):
        raise ValueError("raw name contains empty, dot or parent component")


def _validate_contract(contract):
    if not isinstance(contract, dict):
        raise ValueError("contract must be an object")
    if set(contract.keys()) != _TOP_KEYS:
        raise ValueError("contract keys must match schema exactly")
    if contract["schema"] != SCHEMA:
        raise ValueError("bad schema")
    if contract["status"] != STATUS_IN:
        raise ValueError("bad contract status")
    if not isinstance(contract["source_path"], str) or not contract["source_path"]:
        raise ValueError("source_path must be a non-empty string")
    if not _sha_ok(contract["source_sha256"]) or not _sha_ok(contract["prefix_sha256"]):
        raise ValueError("bad sha256 in contract")
    if not _is_int(contract["source_bytes"]) or contract["source_bytes"] < 56 or contract["source_bytes"] > MAX_SOURCE_BYTES:
        raise ValueError("bad source_bytes")
    if not _is_int(contract["object_count"]) or contract["object_count"] < 0:
        raise ValueError("bad object_count")
    if not _is_int(contract["max_id"]) or contract["max_id"] < 0 or contract["max_id"] > UINT32_MAX:
        raise ValueError("bad max_id")
    if contract["object_count"] == 0 and contract["max_id"] != 0:
        raise ValueError("max_id must be 0 for empty source")
    if contract["object_count"] > 0 and contract["max_id"] == 0:
        raise ValueError("max_id must be positive for non-empty source")
    if not _is_int(contract["prefix_bytes"]) or contract["prefix_bytes"] != contract["source_bytes"] - 56:
        raise ValueError("prefix_bytes must be source_bytes-56")
    if not isinstance(contract["terminator_hex"], str):
        raise ValueError("bad terminator_hex")
    try:
        terminator = bytes.fromhex(contract["terminator_hex"])
    except Exception:
        raise ValueError("bad terminator_hex")
    if len(terminator) != 56 or contract["terminator_hex"].lower() != terminator.hex():
        raise ValueError("terminator must be exactly 56 bytes hex")
    term_id, term_len = struct.unpack_from("<II", terminator, 48)
    if term_len != 0:
        raise ValueError("terminator length must be 0")
    pins = contract["pins"]
    if not isinstance(pins, dict) or any(not isinstance(k, str) or not k or not _sha_ok(v) for k, v in pins.items()):
        raise ValueError("pins must be dict of path to sha256")
    objects = contract["objects"]
    if not isinstance(objects, list) or len(objects) != 3:
        raise ValueError("objects must be a list of exactly 3")
    raw_names = []
    packed = []
    ids = []
    for idx, obj in enumerate(objects):
        if not isinstance(obj, dict) or set(obj.keys()) != _OBJ_KEYS:
            raise ValueError("object keys must match schema exactly")
        expected = contract["max_id"] + 1 + idx
        if expected > UINT32_MAX:
            raise ValueError("object id overflow uint32")
        if not _is_int(obj["id"]) or obj["id"] < 1 or obj["id"] > UINT32_MAX:
            raise ValueError("object id must be int in 1..uint32")
        if obj["id"] != expected:
            raise ValueError("object ids must be max_id+1, max_id+2, max_id+3")
        if obj["id"] == term_id:
            raise ValueError("object id collides with terminator id")
        if not isinstance(obj["raw_name_hex"], str):
            raise ValueError("bad raw_name_hex")
        try:
            raw = bytes.fromhex(obj["raw_name_hex"])
        except Exception:
            raise ValueError("bad raw_name_hex")
        if not raw or len(raw) > 512 or obj["raw_name_hex"].lower() != raw.hex():
            raise ValueError("bad raw_name_hex length or form")
        _validate_name(obj["name"], raw)
        packed.append(_pack_matrix(obj["matrix12"]))
        raw_names.append(raw)
        ids.append(obj["id"])
    if len(set(ids)) != 3:
        raise ValueError("duplicate object id in contract")
    return {"raw_names": raw_names, "packed": packed, "ids": ids, "terminator": terminator, "term_id": term_id}


def _parse_prefix(data):
    if len(data) < 24:
        raise ValueError("truncated WRP header")
    view = memoryview(data)
    magic, tx, tz, nx, nz, cell = struct.unpack_from("<4s4If", view, 0)
    if magic != b"0WZD":
        raise ValueError("bad WRP magic")
    if tx <= 0 or tz <= 0 or nx <= 0 or nz <= 0:
        raise ValueError("WRP dimensions must be positive")
    if not math.isfinite(cell) or cell <= 0:
        raise ValueError("WRP cell size must be positive finite")
    offset = 24
    heights_end = offset + nx * nz * 4
    if heights_end > len(data):
        raise ValueError("truncated heights")
    offset = heights_end
    mats_end = offset + tx * tz * 2
    if mats_end > len(data):
        raise ValueError("truncated material indices")
    offset = mats_end
    if offset + 4 > len(data):
        raise ValueError("truncated material count")
    count = struct.unpack_from("<I", view, offset)[0]
    offset += 4
    if count > (len(data) - offset) // 4:
        raise ValueError("material count out of file bounds")
    for _ in range(count):
        while True:
            if offset + 4 > len(data):
                raise ValueError("truncated material entry")
            length = struct.unpack_from("<I", view, offset)[0]
            offset += 4
            if length == 0:
                break
            if offset + length > len(data):
                raise ValueError("material bytes out of file bounds")
            offset += length
    return offset


def _parse_census(data):
    objects_start = _parse_prefix(data)
    offset = objects_start
    view = memoryview(data)
    ids = set()
    count = 0
    max_id = 0
    while True:
        if offset + 56 > len(data):
            raise ValueError("truncated object or terminator")
        ident, length = struct.unpack_from("<II", view, offset + 48)
        if length == 0:
            if offset + 56 != len(data):
                raise ValueError("terminator not at EOF")
            terminator = bytes(view[offset:offset + 56])
            term_offset = offset
            break
        if ident == 0:
            raise ValueError("object id must be positive")
        if ident in ids:
            raise ValueError("duplicate object id in WRP")
        ids.add(ident)
        count += 1
        if ident > max_id:
            max_id = ident
        name_start = offset + 56
        if name_start + length > len(data):
            raise ValueError("object name out of file bounds")
        offset = name_start + length
    return {"objects_start": objects_start, "term_offset": term_offset, "count": count, "max_id": max_id, "ids": ids, "terminator": terminator}


def _check_candidate(source, candidate, contract, info):
    prefix = contract["prefix_bytes"]
    if len(candidate) < prefix + 56:
        raise ValueError("candidate too short")
    if memoryview(candidate)[:prefix] != memoryview(source)[:prefix]:
        raise ValueError("candidate prefix differs from source")
    offset = prefix
    view = memoryview(candidate)
    for i in range(3):
        if offset + 56 > len(candidate):
            raise ValueError("truncated added record")
        if bytes(view[offset:offset + 48]) != info["packed"][i]:
            raise ValueError("added record matrix differs bit-exactly")
        ident, length = struct.unpack_from("<II", view, offset + 48)
        if ident != info["ids"][i]:
            raise ValueError("added record id differs")
        if length != len(info["raw_names"][i]):
            raise ValueError("added record name length differs")
        start = offset + 56
        if start + length > len(candidate):
            raise ValueError("added record name truncated")
        if bytes(view[start:start + length]) != info["raw_names"][i]:
            raise ValueError("added record raw name differs")
        offset = start + length
    if offset + 56 != len(candidate):
        raise ValueError("candidate terminator not at EOF")
    if bytes(view[offset:offset + 56]) != info["terminator"]:
        raise ValueError("candidate terminator differs")
    census = _parse_census(candidate)
    if census["count"] != contract["object_count"] + 3:
        raise ValueError("candidate object count mismatch")
    if census["max_id"] != info["ids"][-1]:
        raise ValueError("candidate max id mismatch")
    if not set(info["ids"]).issubset(census["ids"]):
        raise ValueError("candidate missing added ids")


def author_bytes(source, contract):
    if isinstance(source, (bytearray, memoryview)):
        data = bytes(source)
    elif isinstance(source, bytes):
        data = source
    else:
        raise ValueError("source must be bytes")
    if len(data) > MAX_SOURCE_BYTES:
        raise ValueError("source exceeds 512 MiB")
    info = _validate_contract(contract)
    if len(data) != contract["source_bytes"]:
        raise ValueError("source size mismatch")
    if hashlib.sha256(memoryview(data)).hexdigest() != contract["source_sha256"]:
        raise ValueError("source sha256 mismatch")
    prefix = contract["prefix_bytes"]
    if hashlib.sha256(memoryview(data)[:prefix]).hexdigest() != contract["prefix_sha256"]:
        raise ValueError("prefix sha256 mismatch")
    census = _parse_census(data)
    if census["term_offset"] != prefix:
        raise ValueError("prefix is not all bytes before terminator")
    if census["count"] != contract["object_count"]:
        raise ValueError("source object count mismatch")
    if census["max_id"] != contract["max_id"]:
        raise ValueError("source max id mismatch")
    if census["terminator"] != info["terminator"]:
        raise ValueError("source terminator mismatch")
    if info["term_id"] in census["ids"]:
        raise ValueError("terminator id collides with existing object")
    if any(i in census["ids"] for i in info["ids"]):
        raise ValueError("added id already present")
    records = b"".join(info["packed"][i] + struct.pack("<II", info["ids"][i], len(info["raw_names"][i])) + info["raw_names"][i] for i in range(3))
    candidate = b"".join((memoryview(data)[:prefix], records, info["terminator"]))
    _check_candidate(data, candidate, contract, info)
    return candidate


def _no_dup(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError("duplicate JSON key: " + k)
        out[k] = v
    return out


def _bad_const(v):
    raise ValueError("invalid JSON constant: " + v)


def _load_contract(path, expected_sha):
    if not isinstance(expected_sha, str) or len(expected_sha) != 64:
        raise ValueError("bad contract sha256 argument")
    try:
        int(expected_sha, 16)
    except Exception:
        raise ValueError("bad contract sha256 argument")
    raw = Path(path).read_bytes()
    if hashlib.sha256(memoryview(raw)).hexdigest() != expected_sha.lower():
        raise ValueError("contract sha256 mismatch")
    try:
        contract = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_dup, parse_constant=_bad_const, parse_int=_parse_int)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(str(exc))
    _validate_contract(contract)
    return contract


def _resolve(p, base):
    q = Path(p).expanduser()
    if q.is_absolute():
        return q
    return base / q


def _verify_pins(contract, base):
    pins = contract["pins"]
    if not pins:
        raise ValueError("pins are required in CLI mode")
    for pin_path, expected in pins.items():
        target = _resolve(pin_path, base)
        if not target.is_file():
            raise ValueError("pin file missing: " + pin_path)
        if hashlib.sha256(memoryview(target.read_bytes())).hexdigest() != expected:
            raise ValueError("pin sha256 mismatch: " + pin_path)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True)
    parser.add_argument("--contract-sha256", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        contract_path = Path(args.contract)
        contract = _load_contract(contract_path, args.contract_sha256)
        _verify_pins(contract, contract_path.parent)
        output = Path(args.output)
        if output.exists():
            raise ValueError("output directory must be new")
        source_path = _resolve(contract["source_path"], contract_path.parent)
        if not source_path.is_file():
            raise ValueError("source file missing")
        if source_path.stat().st_size > MAX_SOURCE_BYTES:
            raise ValueError("source exceeds 512 MiB")
        if source_path.stat().st_size != contract["source_bytes"]:
            raise ValueError("source size mismatch before read")
        source = source_path.read_bytes()
        if len(source) > MAX_SOURCE_BYTES:
            raise ValueError("source exceeds 512 MiB")
        candidate = author_bytes(source, contract)
        info = _validate_contract(contract)
        output.mkdir(parents=False, exist_ok=False)
        pending = output / "pending.wrp"
        final = output / "candidate.wrp"
        pending.write_bytes(candidate)
        if pending.stat().st_size != len(candidate):
            raise ValueError("candidate size mismatch before reread")
        reread = pending.read_bytes()
        if reread != candidate:
            raise ValueError("pending reread differs from authored candidate")
        _check_candidate(source, reread, contract, info)
        pending.replace(final)
        report = {"status": STATUS_OUT, "ok": True, "candidate_path": str(final), "candidate_sha256": hashlib.sha256(memoryview(candidate)).hexdigest(), "candidate_bytes": len(candidate), "source_sha256": hashlib.sha256(memoryview(source)).hexdigest(), "source_bytes": len(source), "object_count": contract["object_count"], "candidate_object_count": contract["object_count"] + 3, "added_count": 3, "added_ids": info["ids"], "max_id": contract["max_id"], "candidate_max_id": info["ids"][-1], "prefix_sha256": contract["prefix_sha256"]}
        print(json.dumps(report, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "REJECTED", "ok": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
