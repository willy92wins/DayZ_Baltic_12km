"""Closed synthetic corpus: container producer is stdlib, payload oracles are literal."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import struct
import tempfile
import types
import unittest
from unittest.mock import patch
import warnings
import zipfile
import zlib

ROOT = Path(os.environ["Q03B2_TEST_ROOT"]).resolve()
ROOT.mkdir(parents=True, exist_ok=True)
CONTRACT_BYTES = Path(os.environ["Q03B2_CONTRACT"]).read_bytes()
assert hashlib.sha256(CONTRACT_BYTES).hexdigest() == "72d3011b335005fa69deb498d040c0cebc2e60ceecb136e1a36db91b3a4e07d4"
C = json.loads(CONTRACT_BYTES)
EXT_BYTES = Path(os.environ["Q03B2_EXTENSION"]).read_bytes()
assert hashlib.sha256(EXT_BYTES).hexdigest() == "848c4442258aec59bfa1746a602adf16ab7d3f9f9f8384b0aed3250c14fc3537"
EXT = json.loads(EXT_BYTES)
OB = Path(os.environ["Q03B1_ORACLE"]).read_bytes()
assert hashlib.sha256(OB).hexdigest() == "79b946237ff06dfc414cb47fbee38063a6eedf66af784a0ea2b769fc7d8e18f9"
O = json.loads(OB)["fixtures"]
SPEC = importlib.util.spec_from_file_location("q03b2", os.environ["Q03B2_MODULE"])
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
SIGNED = O[0]


def npy(fixture=SIGNED, version=1):
    text = fixture["header_dictionary"].encode("ascii")
    prefix = 10 if version == 1 else 12
    header = text + b" " * ((-(prefix + len(text) + 1)) % 64) + b"\n"
    return b"\x93NUMPY" + bytes([version, 0]) + struct.pack("<H" if version == 1 else "<I", len(header)) + header + bytes.fromhex(fixture["payload_hex"])


def zipped(entries, method=0):
    target = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(target, "w", compression=method) as z:
            for name, data in entries:
                z.writestr(name, data)
    return target.getvalue()


def changed_stat(s, **changes):
    fields = {k: getattr(s, k) for k in ("st_mode", "st_dev", "st_ino", "st_size", "st_mtime_ns")}
    fields["st_file_attributes"] = getattr(s, "st_file_attributes", 0)
    return types.SimpleNamespace(**dict(fields, **changes))


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.directory = Path(tempfile.mkdtemp(dir=ROOT)).resolve()
        self.schemas = {"v.npy": SIGNED["schema"]}

    def tearDown(self):
        if ROOT not in self.directory.parents:
            raise AssertionError("cleanup outside fixture root")
        shutil.rmtree(self.directory)

    def save(self, data, name="x.npz"):
        p = self.directory / name
        p.write_bytes(data)
        return p

    def reject(self, case, data=None, schemas=None, session=None, preflight=False, path=None):
        p = path if path is not None else self.save(data)
        s = session or M.Session()
        def attempt():
            with s.open(p, self.schemas if schemas is None else schemas):
                self.fail("accepted " + case)
        if preflight:
            with patch.object(M.zipfile, "ZipFile", side_effect=AssertionError("constructor reached")) as spy:
                with self.assertRaises((M.ArchiveError, M.header.HeaderError)) as cm:
                    attempt()
                spy.assert_not_called()
        else:
            with self.assertRaises((M.ArchiveError, M.header.HeaderError)) as cm:
                attempt()
        self.assertEqual(cm.exception.code, C["cases"][case])
        self.assertEqual((s.live_stored, s.live_expanded, s.active), (0, 0, False))
        return s

    def test_literals_versions_compressions_and_release(self):
        for version in (1, 2):
            for method in (0, 8):
                for fixture in O:
                    with self.subTest(version=version, method=method, fixture=fixture["id"]):
                        data = zipped([("v.npy", npy(fixture, version))], method)
                        p = self.save(data)
                        session = M.Session()
                        with session.open(p, {"v.npy": fixture["schema"]}) as result:
                            expected = bytes.fromhex(fixture["payload_hex"])
                            a = result["arrays"]["v.npy"]
                            self.assertEqual(memoryview(a).cast("B").tobytes(), expected)
                            self.assertFalse(a.flags.writeable)
                            self.assertEqual(result["payloads"]["v.npy"], {"bytes": len(expected), "sha256": hashlib.sha256(expected).hexdigest()})
                            self.assertEqual(result["source_sha256"], hashlib.sha256(data).hexdigest())
                            self.assertEqual(session.live_expanded, len(npy(fixture, version)))
                        self.assertTrue(result["closed"])
                        self.assertEqual(result["arrays"], {})
                        self.assertEqual((session.live_stored, session.live_expanded, session.active), (0, 0, False))
                        self.assertEqual(session.cumulative_stored_actual_bytes_read, len(data))

    def test_frozen_numpy_local_zip64(self):
        data = Path(os.environ["Q03B2_NUMPY_FIXTURE"]).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), "3987d5c97667f4be4989b9c345a3dc33b7068cc05d6d252a61212b01a64a81d2")
        with M.Session().open(self.save(data), self.schemas) as result:
            self.assertEqual(memoryview(result["arrays"]["v.npy"]).cast("B").tobytes(), bytes.fromhex(SIGNED["payload_hex"]))

    def test_member_names_and_actual_count_before_constructor(self):
        for case, entries in (
            ("duplicate", [("v.npy", npy()), ("v.npy", npy())]),
            ("directory", [("dir/", npy())]),
            ("traversal", [("../v.npy", npy())]),
            ("unknown", [("w.npy", npy())]),
        ):
            with self.subTest(case=case):
                self.reject(case, zipped(entries), preflight=True)
        data = bytearray(zipped([("v.npy", npy())]))
        c = data.index(b"PK\x01\x02")
        data[c + 46] = 0
        self.reject("nul", data, preflight=True)
        entries = [(f"v{i}.npy", npy()) for i in range(36)]
        data = bytearray(zipped(entries))
        e = data.rindex(b"PK\x05\x06")
        struct.pack_into("<HH", data, e + 8, 35, 35)
        schemas = {f"v{i}.npy": SIGNED["schema"] for i in range(35)}
        self.reject("too_many", data, schemas, preflight=True)

    def test_flags_layout_and_local_header_mutants(self):
        original = zipped([("v.npy", npy())])
        for case in ("encrypted", "bzip2", "descriptor_flag", "eocd64", "trailing", "count_lie", "local_name", "local_method", "local_overlap", "crc"):
            data = bytearray(original)
            c, e = data.index(b"PK\x01\x02"), data.rindex(b"PK\x05\x06")
            if case in ("encrypted", "descriptor_flag"):
                struct.pack_into("<H", data, c + 8, 1 if case == "encrypted" else 8)
            elif case == "bzip2":
                struct.pack_into("<H", data, c + 10, 12)
            elif case == "eocd64":
                struct.pack_into("<H", data, e + 10, 65535)
            elif case == "trailing":
                data += b"x"
            elif case == "count_lie":
                struct.pack_into("<HH", data, e + 8, 2, 2)
            elif case == "local_name":
                data[30] = ord("x")
            elif case == "local_method":
                struct.pack_into("<H", data, 8, 8)
            elif case == "local_overlap":
                struct.pack_into("<I", data, c + 42, 1)
            else:
                struct.pack_into("<I", data, c + 16, 0)
                struct.pack_into("<I", data, 14, 0)
            with self.subTest(case=case):
                self.reject(case, data, preflight=case != "crc")

    def test_caps_exact_boundary_reservations_and_two_phase(self):
        payload, data = npy(), zipped([("v.npy", npy())])
        for case, limits in (("stored_cap", {"stored": len(data)-1}), ("archive_cap", {"archive": len(payload)-1}), ("total_cap", {"total": len(payload)-1})):
            s = self.reject(case, data, session=M.Session(**limits), preflight=True)
            self.assertEqual(s.cumulative_expanded_reserved, 0)
        s = M.Session(stored=len(data), archive=len(payload), total=len(payload))
        with s.open(self.save(data), self.schemas):
            pass
        self.reject("total_cap", data, session=s, preflight=True)
        self.assertEqual(s.cumulative_expanded_reserved, len(payload))
        bad = bytearray(payload)
        bad[6] = 3
        two = zipped([("v.npy", payload), ("w.npy", bad)])
        s = M.Session()
        with patch.object(M.np.lib.format, "read_array", side_effect=AssertionError("array allocated")) as spy:
            self.reject("second_header", two, {"v.npy": SIGNED["schema"], "w.npy": SIGNED["schema"]}, s)
            spy.assert_not_called()
        self.assertEqual(s.cumulative_expanded_reserved, len(payload) * 2)

    def test_snapshot_identity_io_and_reparse(self):
        p = self.save(zipped([("v.npy", npy())]))
        with patch.object(M.os, "open", side_effect=OSError("synthetic")):
            self.reject("source_io", path=p)
        real = M.os.fstat
        for field in ("st_dev", "st_ino", "st_size", "st_mtime_ns"):
            calls = [0]
            def fstat(fd):
                s = real(fd)
                calls[0] += 1
                return changed_stat(s, **{field: getattr(s, field) + 1}) if calls[0] == 2 else s
            with self.subTest(field=field), patch.object(M.os, "fstat", side_effect=fstat):
                self.reject("source_changed", path=p)
        real_lstat = M.os.lstat
        def reparse(path):
            return changed_stat(real_lstat(path), st_file_attributes=0x400)
        with patch.object(M.os, "lstat", side_effect=reparse):
            self.reject("reparse", path=p)

    def test_state_hash_and_internal_errors(self):
        data = zipped([("v.npy", npy())])
        p = self.save(data)
        s = M.Session()
        with s.open(p, self.schemas):
            with self.assertRaises(M.ArchiveError) as cm:
                with s.open(p, self.schemas):
                    pass
            self.assertEqual(cm.exception.code, C["cases"]["state_busy"])
            self.assertTrue(s.active)
        with s.open(p, self.schemas):
            pass
        self.assertEqual(s.cumulative_expanded_reserved, 2 * len(npy()))
        self.reject("relative_path", path="x.npz")
        bad = self.save(b"raise AssertionError('executed')", "bad.py")
        with self.assertRaises(M.ArchiveError) as cm:
            M._load_header(bad)
        self.assertEqual(cm.exception.code, C["cases"]["helper_hash"])
        for limits in ({"stored": True}, {"total": C["caps"]["total"] + 1}, {"other": 1}):
            with self.assertRaises(M.ArchiveError) as cm:
                M.Session(**limits)
            self.assertEqual(cm.exception.code, C["cases"]["invalid_limit"])
        with patch.object(M.np.lib.format, "read_array", side_effect=RuntimeError("bug")):
            self.reject("internal_bug", path=p)
        with self.assertRaisesRegex(RuntimeError, "caller"):
            with s.open(p, self.schemas):
                raise RuntimeError("caller")
        self.assertFalse(s.active)

    def test_real_symlink_when_privileged(self):
        target = self.save(zipped([("v.npy", npy())]))
        link = self.directory / "link.npz"
        try:
            link.symlink_to(target)
        except OSError as exc:
            self.skipTest("Windows symlink privilege unavailable: " + str(exc.winerror))
        self.reject("reparse", path=link)

    def test_physical_decoded_extent_regressions(self):
        payload = npy()
        for method, case in [(0, "stored_hidden"), (8, "deflate_hidden")]:
            data = bytearray(zipped([("v.npy", payload + b"HIDDEN")], method))
            c = data.index(b"PK\x01\x02")
            for pos in (22, c + 24):
                struct.pack_into("<I", data, pos, len(payload))
            for pos in (14, c + 16):
                struct.pack_into("<I", data, pos, zlib.crc32(payload))
            with self.subTest(case=case), self.assertRaises(M.ArchiveError) as cm:
                with M.Session().open(self.save(data), self.schemas):
                    pass
            self.assertEqual(cm.exception.code, EXT["cases"][case])
        original = zipped([("v.npy", payload)], 8)
        c = original.index(b"PK\x01\x02")
        start = 30 + len(b"v.npy")
        for case in ("deflate_no_final", "deflate_unused"):
            compressor = zlib.compressobj(wbits=-15)
            compressed = compressor.compress(payload) + compressor.flush(zlib.Z_SYNC_FLUSH if case == "deflate_no_final" else zlib.Z_FINISH)
            if case == "deflate_unused":
                compressed += b"EXTRA"
            data = bytearray(original[:start] + compressed + original[c:])
            new_c = start + len(compressed)
            e = data.rindex(b"PK\x05\x06")
            struct.pack_into("<I", data, 18, len(compressed))
            struct.pack_into("<I", data, new_c + 20, len(compressed))
            struct.pack_into("<I", data, e + 16, new_c)
            with self.subTest(case=case), self.assertRaises(M.ArchiveError) as cm:
                with M.Session().open(self.save(data), self.schemas):
                    pass
            self.assertEqual(cm.exception.code, EXT["cases"][case])

    def test_wrapped_zip_cause_and_internal_distinction(self):
        p = self.save(zipped([("v.npy", npy())]))
        for cause, case in [(zipfile.BadZipFile("crc"), "header_wrapped_crc"), (RuntimeError("bug"), "header_internal_retained")]:
            def broken(*args):
                try:
                    raise cause
                except Exception as exc:
                    raise M.header.HeaderError("INTERNAL_ERROR") from exc
            with patch.object(M.header, "inspect_header", side_effect=broken), self.assertRaises((M.ArchiveError, M.header.HeaderError)) as cm:
                with M.Session().open(p, self.schemas):
                    pass
            self.assertEqual(cm.exception.code, EXT["cases"][case])


if __name__ == "__main__":
    unittest.main(verbosity=2)
