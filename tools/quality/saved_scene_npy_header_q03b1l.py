"""Bounded NPY header inspection, Q03B1L. Does not read/attest array payload.

The caller supplies an exact, separately attested member_bytes and owns archive
reservations. No archive, path, global budget or scene semantics are validated.
"""
import ast
import io
import struct
import numpy as np

HEADER_CAP = 16384
MEMBER_CAP = 128 * 1024 * 1024
DIM_CAP = 2_000_000


class HeaderError(Exception):
    def __init__(self, code, detail=""):
        self.code = code
        super().__init__(code + (": " + detail if detail else ""))


def _fail(code, detail=""):
    raise HeaderError(code, detail)


def _read_exact(stream, n):
    """Only this operation translates an OS read error into source I/O."""
    out = bytearray()
    while len(out) < n:
        remaining = n - len(out)
        try:
            chunk = stream.read(remaining)
        except OSError as exc:
            raise HeaderError("INCONCLUSIVE_SOURCE_IO") from exc
        if type(chunk) is not bytes or len(chunk) > remaining:
            _fail("INTERNAL_ERROR", "stream read contract")
        if not chunk:
            _fail("NPY_TRAILING", "short header")
        out.extend(chunk)
    return bytes(out)


def _shape(value, container, code):
    if type(value) is not container or len(value) > 3:
        _fail(code)
    if any(type(n) is not int or not 0 <= n <= DIM_CAP for n in value):
        _fail(code)
    return tuple(value)


def _canonical(descr):
    """Closed plain or flat structured descriptor; never truncate a format."""
    if type(descr) is str:
        if not descr or len(descr) > HEADER_CAP:
            _fail("NPY_DTYPE")
        return descr
    if type(descr) is not list or not descr or len(descr) > HEADER_CAP:
        _fail("NPY_DTYPE")
    result = []
    names = set()
    for field in descr:
        if type(field) not in (tuple, list) or len(field) != 2:
            _fail("NPY_DTYPE", "title/subarray/field shape")
        name, fmt = field
        if (type(name) is not str or not name or name in names
                or type(fmt) is not str):
            _fail("NPY_DTYPE", "field name or nested descriptor")
        names.add(name)
        result.append([name, fmt])
    return result


def _dtype(descr):
    canonical = _canonical(descr)
    forms = [canonical] if type(canonical) is str else [v[1] for v in canonical]
    for form in forms:
        try:
            scalar = np.dtype(form)
        except (TypeError, ValueError, OverflowError) as exc:
            raise HeaderError("NPY_DTYPE") from exc
        if (scalar.hasobject or scalar.subdtype is not None
                or scalar.fields is not None or scalar.itemsize <= 0):
            _fail("NPY_DTYPE")
        # Require the literal endian spelling as well as NumPy's normalized type.
        if not form or form[0] not in ("<", "|") or scalar.byteorder == ">":
            _fail("NPY_DTYPE", "explicit little endian required")
        if scalar.itemsize > 1 and form[0] == "|" and scalar.kind not in ("S", "V"):
            _fail("NPY_DTYPE", "ambiguous endian")
    try:
        dt = np.dtype(canonical if type(canonical) is str
                      else [tuple(v) for v in canonical])
    except (TypeError, ValueError, OverflowError) as exc:
        raise HeaderError("NPY_DTYPE") from exc
    return canonical, dt


def descriptor_json(dtype):
    """Full JSON-compatible dtype description (field formats remain strings)."""
    if dtype.fields is None:
        return dtype.str
    return [list(field) for field in dtype.descr]


def _inspect(stream, member_bytes, schema):
    if (type(member_bytes) is not int or not 0 <= member_bytes <= MEMBER_CAP
            or type(schema) is not dict or set(schema) != {"dtype", "shape"}):
        _fail("MEMBER_SCHEMA")
    expected_shape = _shape(schema["shape"], list, "MEMBER_SCHEMA")
    if type(schema["dtype"]) not in (str, list):
        _fail("MEMBER_SCHEMA")
    try:
        expected_descr, expected_dtype = _dtype(schema["dtype"])
    except HeaderError as exc:
        if exc.code != "NPY_DTYPE":
            raise
        raise HeaderError("MEMBER_SCHEMA", "invalid expected dtype") from exc

    magic = _read_exact(stream, 6)
    if magic != b"\x93NUMPY":
        _fail("NPY_MAGIC")
    version = _read_exact(stream, 2)
    if version not in (b"\x01\x00", b"\x02\x00"):
        _fail("NPY_VERSION")
    width = 2 if version[0] == 1 else 4
    length_bytes = _read_exact(stream, width)
    length = struct.unpack("<H" if width == 2 else "<I", length_bytes)[0]
    if length > HEADER_CAP:
        _fail("HEADER_LIMIT")
    header = _read_exact(stream, length)
    try:
        dictionary = ast.literal_eval(header.decode("latin1"))
    except (SyntaxError, ValueError, TypeError, RecursionError) as exc:
        raise HeaderError("MEMBER_SCHEMA", "header dictionary") from exc
    if type(dictionary) is not dict or set(dictionary) != {"descr", "shape", "fortran_order"}:
        _fail("MEMBER_SCHEMA")
    if dictionary["fortran_order"] is not False:
        _fail("NPY_ORDER")
    shape = _shape(dictionary["shape"], tuple, "NPY_SHAPE")
    if shape != expected_shape:
        _fail("NPY_SHAPE", "schema mismatch")
    actual_descr, dt = _dtype(dictionary["descr"])
    if actual_descr != expected_descr or dt != expected_dtype:
        _fail("NPY_DTYPE", "schema mismatch")

    count = 0 if 0 in shape else 1
    if count:
        for n in shape:
            if count > MEMBER_CAP // n:
                _fail("NPY_SHAPE", "element count")
            count *= n
    if count > MEMBER_CAP // dt.itemsize:
        _fail("NPY_SHAPE", "payload bytes")
    payload_bytes = count * dt.itemsize
    offset = 8 + width + length
    if offset + payload_bytes != member_bytes:
        _fail("NPY_TRAILING", "attested member length mismatch")

    # Public NumPy header reader. This bounded copy contains NO payload.
    bounded = io.BytesIO(magic + version + length_bytes + header)
    bounded.seek(8)
    parser = (np.lib.format.read_array_header_1_0 if width == 2
              else np.lib.format.read_array_header_2_0)
    try:
        parsed_shape, fortran, parsed_dtype = parser(bounded, max_header_size=HEADER_CAP)
    except (ValueError, TypeError, OverflowError) as exc:
        raise HeaderError("NPY_DTYPE", "standard header parser") from exc
    if (parsed_shape != shape or fortran is not False or parsed_dtype != dt
            or descriptor_json(parsed_dtype) != descriptor_json(dt)):
        _fail("NPY_DTYPE", "standard parser mismatch")
    return {"dtype": parsed_dtype, "descriptor": descriptor_json(parsed_dtype),
            "shape": shape, "payload_offset": offset, "payload_bytes": payload_bytes}


def inspect_header(stream, member_bytes, schema):
    """Consume only prefix/header, leave stream at payload, return metadata.

    member_bytes is an attestation from the caller, not measured by this function.
    Physical payload truncation and byte identity require a later caller gate.
    """
    try:
        return _inspect(stream, member_bytes, schema)
    except HeaderError:
        raise
    except Exception as exc:
        raise HeaderError("INTERNAL_ERROR", type(exc).__name__) from exc
