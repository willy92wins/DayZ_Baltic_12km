"""Synthetic-validated NPZ session. Logical reservations are not RSS bounds."""
from contextlib import contextmanager
from pathlib import Path
import hashlib
import io
import os
import stat
import struct
import types
import zipfile
import zlib
import numpy as np

CAPS = {"stored": 16777216, "archive": 134217728, "total": 262434599, "members": 35}
HEADER_SHA = "051436d9d41e50e4a74aee22f91ee7f0b81d284a82a10246df77949910df7434"


class ArchiveError(Exception):
    def __init__(self, code, detail=""):
        self.code = code
        super().__init__(code + (": " + detail if detail else ""))


def fail(code, detail=""):
    raise ArchiveError(code, detail)


def _load_header(path):
    try:
        with open(path, "rb") as stream:
            data = stream.read(65537)
    except OSError as exc:
        raise ArchiveError("INCONCLUSIVE_SOURCE_IO", "header dependency") from exc
    if len(data) > 65536 or hashlib.sha256(data).hexdigest() != HEADER_SHA:
        fail("MEMBER_SCHEMA", "header dependency hash")
    module = types.ModuleType("_q03b2_pinned_header")
    exec(compile(data, str(path), "exec"), module.__dict__)
    return module


header = _load_header(Path(__file__).with_name("saved_scene_npy_header_q03b1l.py"))


def _identity(s):
    return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns


def _check_path(path):
    for entry in [path, *path.parents]:
        s = os.lstat(entry)
        if stat.S_ISLNK(s.st_mode) or getattr(s, "st_file_attributes", 0) & 0x400:
            fail("REPARSE")
    return os.lstat(path)


def _snapshot(path, session):
    if not isinstance(path, (str, Path)):
        fail("MEMBER_SCHEMA", "path type")
    path = Path(path)
    if not path.is_absolute() or ".." in path.parts:
        fail("MEMBER_SCHEMA", "absolute non-traversing path required")
    try:
        before = _check_path(path)
        if not stat.S_ISREG(before.st_mode):
            fail("MEMBER_SCHEMA", "regular file required")
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(fd, "rb") as f:
            first = os.fstat(f.fileno())
            if _identity(first) != _identity(before):
                fail("INCONCLUSIVE_SOURCE_CHANGED")
            n = first.st_size
            if not 0 < n <= session.limits["stored"]:
                fail("STORED_CAP")
            session.live_stored = n  # Logical reservation precedes snapshot read.
            data = f.read(n)
            session.cumulative_stored_actual_bytes_read += len(data)
            after = os.fstat(f.fileno())
            final = _check_path(path)
            if len(data) != n or not (_identity(first) == _identity(after) == _identity(final)):
                fail("INCONCLUSIVE_SOURCE_CHANGED")
        return data, hashlib.sha256(data).hexdigest()
    except OSError as exc:
        raise ArchiveError("INCONCLUSIVE_SOURCE_IO") from exc


def _name(raw):
    if raw.endswith(b"/"):
        fail("ZIP_DIRECTORY")
    if (not raw or any(x < 32 or x >= 127 for x in raw)
            or b"/" in raw or b"\\" in raw or b":" in raw or raw in (b".", b"..")):
        fail("ZIP_PATH")
    name = raw.decode("ascii")
    if not name.endswith(".npy"):
        fail("MEMBER_SCHEMA")
    return name


def _flags(flags, method):
    if flags & (1 | 64):
        fail("ZIP_ENCRYPTED")
    if method not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
        fail("ZIP_COMPRESSION")
    allowed = 0x800 | (6 if method == zipfile.ZIP_DEFLATED else 0)
    if flags & ~allowed:
        fail("ZIP_LAYOUT_UNSUPPORTED", "flag mask")


def _central(data, schemas, limits):
    """Bounded raw-directory preguard. No ZipFile/ZipInfo created here."""
    if type(schemas) is not dict or not 1 <= len(schemas) <= limits["members"]:
        fail("MEMBER_SCHEMA")
    for key in schemas:
        if type(key) is not str or not key.isascii():
            fail("MEMBER_SCHEMA")
        try:
            _name(key.encode("ascii"))
        except ArchiveError as exc:
            raise ArchiveError("MEMBER_SCHEMA", "schema name") from exc
    end = None
    for pos in range(len(data) - 22, max(-1, len(data) - 65558), -1):
        if data[pos:pos + 4] != b"PK\x05\x06":
            continue
        e = struct.unpack_from("<4s4H2IH", data, pos)
        if pos + 22 + e[7] == len(data):
            end = pos
            break
    if end is None:
        fail("ZIP_TRUNCATED", "EOCD")
    if e[1] or e[2] or e[3] == 0xffff or e[4] == 0xffff or e[5] == 0xffffffff or e[6] == 0xffffffff:
        fail("ZIP_LAYOUT_UNSUPPORTED", "disk/ZIP64 EOCD")
    if end >= 20 and data[end - 20:end - 16] == b"PK\x06\x07":
        fail("ZIP_LAYOUT_UNSUPPORTED", "ZIP64 locator")
    if e[3] != e[4] or e[6] + e[5] != end:
        fail("ZIP_TRUNCATED", "central bounds/counts")
    if not 1 <= e[4] <= limits["members"]:
        fail("MEMBER_SCHEMA", "member count")
    cursor = e[6]
    rows, names, expanded = [], set(), 0
    while cursor < end:
        if len(rows) >= limits["members"]:
            fail("MEMBER_SCHEMA", "actual member count")
        if end - cursor < 46:
            fail("ZIP_TRUNCATED", "central header")
        c = struct.unpack_from("<4s6H3I5H2I", data, cursor)
        if c[0] != b"PK\x01\x02":
            fail("ZIP_TRUNCATED", "central signature")
        stop = cursor + 46 + c[10] + c[11] + c[12]
        if stop > end:
            fail("ZIP_TRUNCATED", "central extent")
        if c[8] == 0xffffffff or c[9] == 0xffffffff or c[16] == 0xffffffff or c[13]:
            fail("ZIP_LAYOUT_UNSUPPORTED", "central ZIP64/disk")
        if c[11]:
            fail("ZIP_LAYOUT_UNSUPPORTED", "central extra outside tested subset")
        raw_name = data[cursor + 46:cursor + 46 + c[10]]
        name = _name(raw_name)
        if name in names:
            fail("ZIP_DUPLICATE")
        names.add(name)
        if name not in schemas:
            fail("MEMBER_SCHEMA", "unexpected member")
        _flags(c[3], c[4])
        if c[9] <= 0 or c[9] > limits["archive"] - expanded:
            fail("ARCHIVE_CAP")
        expanded += c[9]
        rows.append({"name": name, "raw": raw_name, "flags": c[3], "method": c[4],
                     "crc": c[7], "compressed": c[8], "expanded": c[9], "offset": c[16]})
        cursor = stop
    if len(rows) != e[4] or names != set(schemas):
        fail("ZIP_TRUNCATED" if len(rows) != e[4] else "MEMBER_SCHEMA")
    cursor = 0
    for row in sorted(rows, key=lambda r: r["offset"]):
        off = row["offset"]
        if off != cursor:
            fail("ZIP_LAYOUT_UNSUPPORTED", "local gap/overlap/concat")
        if off + 30 > e[6]:
            fail("ZIP_TRUNCATED")
        h = struct.unpack_from("<4s5H3I2H", data, off)
        start = off + 30 + h[9] + h[10]
        stop = start + row["compressed"]
        if h[0] != b"PK\x03\x04" or stop > e[6]:
            fail("ZIP_TRUNCATED", "local range")
        if data[off + 30:off + 30 + h[9]] != row["raw"] or h[2] != row["flags"] or h[3] != row["method"] or h[6] != row["crc"]:
            fail("ZIP_TRUNCATED", "local/central mismatch")
        extra = data[off + 30 + h[9]:start]
        if h[7] == 0xffffffff or h[8] == 0xffffffff:
            if h[7] != 0xffffffff or h[8] != 0xffffffff or len(extra) != 20 or extra[:4] != b"\x01\x00\x10\x00":
                fail("ZIP_LAYOUT_UNSUPPORTED", "local ZIP64 layout")
            usize, csize = struct.unpack_from("<QQ", extra, 4)
            if (usize, csize) != (row["expanded"], row["compressed"]):
                fail("ZIP_TRUNCATED", "local ZIP64 values")
        elif extra:
            fail("ZIP_LAYOUT_UNSUPPORTED", "local extra")
        elif (h[8], h[7]) != (row["expanded"], row["compressed"]):
            fail("ZIP_TRUNCATED", "local sizes")
        cursor = stop
    if cursor != e[6]:
        fail("ZIP_LAYOUT_UNSUPPORTED", "data/central gap")
    return rows, expanded


class _PayloadReader:
    def __init__(self, source, payload_offset):
        self.source, self.offset, self.position = source, payload_offset, 0
        self.digest, self.length = hashlib.sha256(), 0

    def read(self, n):
        data = self.source.read(n)
        skip = max(0, min(len(data), self.offset - self.position))
        self.digest.update(memoryview(data)[skip:])
        self.length += len(data) - skip
        self.position += len(data)
        return data


class Session:
    def __init__(self, **limits):
        if set(limits) - set(CAPS):
            fail("MEMBER_SCHEMA", "limit keys")
        self.limits = dict(CAPS, **limits)
        if any(type(v) is not int or not 0 < v <= CAPS[k] for k, v in self.limits.items()):
            fail("MEMBER_SCHEMA", "limit values")
        self.active = False
        self.live_stored = self.live_expanded = 0
        self.cumulative_stored_actual_bytes_read = 0
        self.cumulative_expanded_reserved = 0

    def _prepare(self, path, schemas):
        try:
            data, digest = _snapshot(path, self)
            rows, expanded = _central(data, schemas, self.limits)
            if expanded > self.limits["total"] - self.cumulative_expanded_reserved:
                fail("TOTAL_CAP")
            self.live_expanded = expanded
            self.cumulative_expanded_reserved += expanded
            with zipfile.ZipFile(io.BytesIO(data), "r") as archive:
                infos = archive.infolist()
                if len(infos) != len(rows):
                    fail("ZIP_TRUNCATED")
                for info, row in zip(infos, rows, strict=True):
                    if (info.filename, info.flag_bits, info.compress_type, info.CRC, info.compress_size, info.file_size, info.header_offset) != (row["name"], row["flags"], row["method"], row["crc"], row["compressed"], row["expanded"], row["offset"]):
                        fail("ZIP_TRUNCATED", "standard metadata mismatch")
                heads = {}
                for row in rows:
                    with archive.open(row["name"], "r") as member:
                        heads[row["name"]] = header.inspect_header(member, row["expanded"], schemas[row["name"]])
                arrays, payloads = {}, {}
                for row in rows:
                    name = row["name"]
                    with archive.open(name, "r") as member:
                        reader = _PayloadReader(member, heads[name]["payload_offset"])
                        try:
                            array = np.lib.format.read_array(reader, allow_pickle=False, max_header_size=16384)
                        except ValueError as exc:
                            raise ArchiveError("NPY_TRAILING", "array read") from exc
                        if reader.read(1) != b"" or reader.position != row["expanded"]:
                            fail("NPY_TRAILING", "decoded extent")
                    expected = heads[name]["payload_bytes"]
                    array_hash = hashlib.sha256(memoryview(array).cast("B") if array.nbytes else b"").hexdigest()
                    if reader.length != expected or array.nbytes != expected or array_hash != reader.digest.hexdigest():
                        fail("NPY_TRAILING", "payload/array byte mismatch")
                    array.flags.writeable = False
                    arrays[name] = array
                    payloads[name] = {"sha256": array_hash, "bytes": expected}
            return {"arrays": arrays, "payloads": payloads, "source_sha256": digest,
                    "status": "ARCHIVE_SESSION_FIXTURE_VERIFIED_ONLY", "closed": False}
        except ArchiveError:
            raise
        except header.HeaderError:
            raise
        except (zipfile.BadZipFile, EOFError, zlib.error) as exc:
            raise ArchiveError("ZIP_TRUNCATED") from exc
        except Exception as exc:
            raise ArchiveError("INTERNAL_ERROR", type(exc).__name__) from exc

    @contextmanager
    def open(self, path, schemas):
        if self.active:
            fail("MEMBER_SCHEMA", "session already active")
        self.active = True
        result = None
        try:
            result = self._prepare(path, schemas)
            yield result
        finally:
            if result is not None:
                result["arrays"].clear()
                result["closed"] = True
            self.live_stored = self.live_expanded = 0
            self.active = False
