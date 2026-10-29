"""Synthetic face/route identity kernel. No geometry or scene acceptance."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import math
import os

FACE_KEYS = ("model", "source_model", "face", "section", "lod", "kind", "proxy")
LIMITATIONS = {"face_section_membership": "NOT_SAVED", "kind_semantics": "NOT_EVALUATED",
              "global_proxy_graph": "NOT_EVALUATED", "world_frame_certified": False,
              "exposure_evaluated": False, "map_repaired": False, "engine_proxy_binding": "UNKNOWN"}


class IdentityError(Exception):
    def __init__(self, code, detail=""):
        self.code = code
        super().__init__(code + (": " + detail if detail else ""))


def require(value, code="SCHEMA", detail=""):
    if not value:
        raise IdentityError(code, detail)


def record(value, keys):
    require(type(value) is dict and set(value) == set(keys))


def integer(value, minimum=0):
    require(type(value) is int and minimum <= value <= 2147483647)


def sequence(value, maximum, minimum=0):
    require(type(value) is list and minimum <= len(value) <= maximum)


def string(value):
    require(type(value) is str and len(value) <= 4096)


def number(value):
    require(type(value) in (int, float))
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    require(finite)


def vector(value, length):
    sequence(value, length, length)
    for x in value:
        number(x)


def canonical_name(value):
    string(value)
    require(value and all(32 <= ord(c) < 127 for c in value) and ":" not in value, "NAME")
    result = value.replace("\\", "/").strip("/").lower()
    require(result and all(p not in ("", ".", "..") for p in result.split("/")), "NAME")
    require(result.endswith(".p3d"), "NAME", "no suffix insertion")
    return result


def _route_schema(route, expected=False):
    record(route, ("ordinal", "root_model", "slots", "source_model") if expected else ("root_model", "slots", "source_model"))
    if expected:
        integer(route["ordinal"])
    integer(route["root_model"]); integer(route["source_model"])
    sequence(route["slots"], 16)
    require(bool(route["slots"]), "ROUTE_CONTINUITY", "empty route")
    for pair in route["slots"]:
        sequence(pair, 2, 2)
        integer(pair[0]); integer(pair[1])


def _face_schema(face):
    record(face, FACE_KEYS)
    for key in FACE_KEYS:
        integer(face[key], -1 if key == "proxy" else 0)


def _expected_schema(expected):
    record(expected, ("models", "routes", "faces"))
    sequence(expected["models"], 64, 1)
    sequence(expected["routes"], 64)
    sequence(expected["faces"], 512)
    for model in expected["models"]:
        record(model, ("index", "name", "canonical"))
        integer(model["index"])
        string(model["canonical"])
        require(model["canonical"] == canonical_name(model["name"]))
    for row in expected["routes"]:
        _route_schema(row, expected=True)
    for row in expected["faces"]:
        _face_schema(row)


def _validate(sections, routes, face_records, expected):
    sequence(sections, 64, 1); sequence(routes, 64); sequence(face_records, 512)
    _expected_schema(expected)
    by_index, by_name, lod_maps, model_rows = {}, {}, {}, []
    for model in sections:
        record(model, ("index", "name", "center", "lods", "proxies"))
        index = model["index"]; integer(index)
        require(index not in by_index, "SCHEMA", "duplicate model index")
        name = canonical_name(model["name"])
        require(name not in by_name, "NAME_COLLISION")
        vector(model["center"], 3)
        sequence(model["lods"], 64); sequence(model["proxies"], 64)
        lods = {}
        for lod in model["lods"]:
            record(lod, ("index", "resolution", "faces", "sections"))
            integer(lod["index"]); integer(lod["faces"]); number(lod["resolution"])
            require(lod["index"] not in lods, "SCHEMA", "duplicate LOD")
            sequence(lod["sections"], 256)
            ids, total = set(), 0
            for section in lod["sections"]:
                record(section, ("index", "material_raw", "material", "texture_raw", "texture", "faces"))
                integer(section["index"]); integer(section["faces"])
                require(section["index"] not in ids, "SCHEMA", "duplicate section")
                ids.add(section["index"]); total += section["faces"]
                for key in ("material_raw", "material", "texture_raw", "texture"):
                    string(section[key])
            require(total == lod["faces"], "SCHEMA", "section counts")
            lods[lod["index"]] = (lod["faces"], ids)
        for proxy in model["proxies"]:
            record(proxy, ("model", "matrix"))
            canonical_name(proxy["model"]); vector(proxy["matrix"], 12)
        by_index[index] = model; by_name[name] = index; lod_maps[index] = lods
        model_rows.append({"index": index, "name": model["name"], "canonical": name})
    route_rows = []
    for ordinal, route in enumerate(routes):
        _route_schema(route)
        current, visited = route["root_model"], set()
        require(current in by_index, "ROUTE_CHILD", "unknown root")
        for parent, slot in route["slots"]:
            require(parent == current, "ROUTE_CONTINUITY")
            require(parent not in visited, "ROUTE_CYCLE")
            visited.add(parent)
            proxies = by_index[parent]["proxies"]
            require(slot < len(proxies), "ROUTE_SLOT")
            child_name = canonical_name(proxies[slot]["model"])
            require(child_name in by_name, "ROUTE_CHILD", "literal child not found")
            current = by_name[child_name]
            require(current not in visited, "ROUTE_CYCLE")
        require(current == route["source_model"], "ROUTE_CHILD", "literal final child differs")
        route_rows.append({"ordinal": ordinal, **deepcopy(route)})
    for face in face_records:
        _face_schema(face)
        model, source, kind, proxy = (face[k] for k in ("model", "source_model", "kind", "proxy"))
        require(model in by_index and source in by_index, "FACE_BINDING")
        require(kind in (0, 1, 2), "FACE_KIND")
        if kind in (0, 1):
            require(proxy == -1 and source == model, "FACE_BINDING")
        else:
            require(0 <= proxy < len(routes), "FACE_BINDING")
            route = routes[proxy]
            require(route["root_model"] == model and route["source_model"] == source, "FACE_BINDING")
        require(face["lod"] in lod_maps[source], "FACE_LOD")
        count, section_ids = lod_maps[source][face["lod"]]
        require(face["face"] < count, "FACE_INDEX")
        require(face["section"] in section_ids, "FACE_SECTION")
    model_key = lambda x: (x["index"], x["name"], x["canonical"])
    face_key = lambda x: tuple(x[k] for k in FACE_KEYS)
    require(Counter(map(model_key, model_rows)) == Counter(map(model_key, expected["models"])),
            "EXPECTED_MISMATCH", "models")
    # Route ordinal/order is identity. Full face multisets retain multiplicity.
    require(route_rows == expected["routes"], "EXPECTED_MISMATCH", "routes")
    require(Counter(map(face_key, face_records)) == Counter(map(face_key, expected["faces"])),
            "EXPECTED_MISMATCH", "faces")
    return {"status": "FIXTURE_FACE_ROUTE_IDENTITY_ONLY", "models": deepcopy(model_rows),
            "routes": route_rows, "faces": deepcopy(face_records), "limitations": dict(LIMITATIONS)}


def validate_face_routes(sections, routes, face_records, expected):
    try:
        return _validate(sections, routes, face_records, expected)
    except IdentityError:
        raise
    except Exception as exc:
        raise IdentityError("INTERNAL_ERROR", type(exc).__name__) from exc


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "SCHEMA", "duplicate JSON key")
        result[key] = value
    return result


def _nonfinite(value):
    raise IdentityError("SCHEMA", "nonfinite JSON literal")


def _finite_float(value):
    parsed = float(value)
    require(math.isfinite(parsed), "SCHEMA", "JSON number overflow")
    return parsed


def load_fixture(path, expected_sha256):
    """Synthetic fixture loader; no historical path/handle identity guarantee."""
    require(type(expected_sha256) is str and len(expected_sha256) == 64
            and all(c in "0123456789abcdef" for c in expected_sha256), "SCHEMA")
    try:
        with open(Path(path), "rb") as stream:
            size = os.fstat(stream.fileno()).st_size
            require(0 < size <= 1048576, "FIXTURE_LIMIT")
            data = stream.read(size)
            require(len(data) == size, "FIXTURE_IO")
    except OSError as exc:
        raise IdentityError("FIXTURE_IO") from exc
    require(hashlib.sha256(data).hexdigest() == expected_sha256, "FIXTURE_HASH")
    try:
        return json.loads(data, object_pairs_hook=_pairs, parse_constant=_nonfinite,
                          parse_float=_finite_float)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise IdentityError("SCHEMA", "JSON") from exc
