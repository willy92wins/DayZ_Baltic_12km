import ast
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch
import numpy as np

MOD = Path(os.environ["Q03B1L_MODULE"])
spec = importlib.util.spec_from_file_location("q03b1l_subject", MOD)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)
raw = Path(os.environ["Q03B1_ORACLE"]).read_bytes()
assert hashlib.sha256(raw).hexdigest() == "79b946237ff06dfc414cb47fbee38063a6eedf66af784a0ea2b769fc7d8e18f9"
O = json.loads(raw)
raw_contract = Path(os.environ["Q03B1A_CONTRACT"]).read_bytes()
assert hashlib.sha256(raw_contract).hexdigest() == "de2afee0c706392d3579e4c036eab5bee0c24767940f23563916aa5df5b34bc3"
C = json.loads(raw_contract)
extension_raw = Path(os.environ["Q03B1L_EXTENSION"]).read_bytes()
assert hashlib.sha256(extension_raw).hexdigest() == "177d117f952139c6e2b6fc7e2e4d432d8831d483f98bf8045563c4546b04cc92"
E = json.loads(extension_raw)
F = {f["id"]: f for f in O["fixtures"]}
S = F["signed"]["schema"]


def blob(dictionary=None, version=1, header_size=None, payload=None):
    text = dictionary if dictionary is not None else F["signed"]["header_dictionary"]
    body = text.encode("latin1")
    size = header_size if header_size is not None else len(body) + 1
    assert size >= len(body) + 1
    header = body + b" " * (size - len(body) - 1) + b"\n"
    prefix = bytes.fromhex(O["npy_prefixes"][f"{version}.0_magic_version_hex"])
    prefix += struct.pack("<H" if version == 1 else "<I", size)
    if payload is None:
        payload = bytes.fromhex(F["signed"]["payload_hex"])
    return prefix + header + payload, len(prefix) + len(header)


class Spy:
    def __init__(self, data, short=None):
        self.data, self.position, self.requests, self.short = data, 0, [], short

    def read(self, n):
        self.requests.append(n)
        actual = min(n, self.short) if self.short else n
        value = self.data[self.position:self.position + actual]
        self.position += len(value)
        return value


class HeaderTests(unittest.TestCase):
    def test_invalid_expected_dtype_before_read(self):
        for case in E["cases"]:
            with self.subTest(dtype=case["dtype"]):
                spy = Spy(b"")
                with self.assertRaises(m.HeaderError) as ctx:
                    m.inspect_header(spy, 16, {"dtype": case["dtype"], "shape": case["shape"]})
                self.assertEqual(ctx.exception.code, case["expected"])
                self.assertEqual(len(spy.requests), case["read_calls"])

    def test_literal_positives_and_standard_payload(self):
        self.assertEqual(np.__version__, "2.5.3")
        for f in F.values():
            for version in [1, 2]:
                with self.subTest(f=f["id"], version=version):
                    expected = bytes.fromhex(f["payload_hex"])
                    data, offset = blob(f["header_dictionary"], version, payload=expected)
                    spy = Spy(data)
                    with patch.object(np.lib.format, "read_array", side_effect=AssertionError("payload")), patch.object(np, "load", side_effect=AssertionError("array")):
                        result = m.inspect_header(spy, len(data), f["schema"])
                    self.assertEqual(spy.position, offset)
                    self.assertEqual(result["payload_offset"], offset)
                    self.assertEqual(result["payload_bytes"], len(expected))
                    self.assertEqual(result["shape"], tuple(f["schema"]["shape"]))
                    descriptor = json.loads(json.dumps(result["descriptor"]))
                    self.assertEqual(descriptor, f["schema"]["dtype"])
                    if f["id"] == "meta":
                        dt = result["dtype"]
                        self.assertEqual(dt.itemsize, 35)
                        self.assertEqual([dt.fields[n][1] for n in dt.names], f["expected_offsets"])
                    array = np.lib.format.read_array(io.BytesIO(data), allow_pickle=False, max_header_size=16384)
                    self.assertEqual(array.tobytes(), expected)
                    if f["id"] == "signed":
                        self.assertTrue(np.signbit(array[0]))
                    if f["id"] == "matrix":
                        self.assertTrue(np.signbit(array[1, 0]))

    def test_boundary_header_size_and_short_reads(self):
        for version in [1, 2]:
            for short in [None, 1, 7]:
                with self.subTest(version=version, short=short):
                    data, offset = blob(version=version, header_size=16384)
                    spy = Spy(data, short)
                    result = m.inspect_header(spy, len(data), S)
                    self.assertEqual(spy.position, offset)
                    self.assertEqual(result["payload_offset"], offset)
                    self.assertEqual(np.lib.format.read_array(io.BytesIO(data), allow_pickle=False, max_header_size=16384).tobytes(), bytes.fromhex(F["signed"]["payload_hex"]))

    def test_oversize_guard_before_header_request(self):
        for version in [1, 2]:
            data, _ = blob(version=version, header_size=16385)
            prefix_len = 10 if version == 1 else 12
            spy = Spy(data[:prefix_len])
            with self.assertRaises(m.HeaderError) as ctx:
                m.inspect_header(spy, len(data), S)
            self.assertEqual(ctx.exception.code, "HEADER_LIMIT")
            self.assertEqual(spy.position, prefix_len)
            self.assertEqual(spy.requests, [6, 2, prefix_len - 8])

    def test_scalar_empty_and_no_physical_payload_claim(self):
        for shape, expected_bytes in [((), 8), ((0, 2000000, 2000000), 0)]:
            text = repr({"descr": "<f8", "fortran_order": False, "shape": shape})
            data, offset = blob(text, payload=b"")
            result = m.inspect_header(Spy(data), offset + expected_bytes, {"dtype": "<f8", "shape": list(shape)})
            self.assertEqual(result["payload_bytes"], expected_bytes)
            self.assertEqual(result["payload_offset"], offset)

    def test_closed_contract_negative_codes(self):
        base, _ = blob()
        dictionary = ast.literal_eval(F["signed"]["header_dictionary"])
        cases = {}
        def add(name, data=base, schema=S, size=None):
            cases[name] = (Spy(data), len(data) if size is None else size, schema)
        add("bad_member_bool", size=True)
        add("bad_member_negative", size=-1)
        add("bad_member_limit", size=134217729)
        add("schema_keys", schema={"dtype": "<f8", "shape": [2], "extra": 0})
        add("schema_bool_shape", schema={"dtype": "<f8", "shape": [True]})
        add("header_eof", data=base[:9])
        add("magic", data=b"XXXXXX" + base[6:])
        add("version3", data=base[:6] + b"\x03\x00" + base[8:])
        add("minor1", data=base[:6] + b"\x01\x01" + base[8:])
        add("header16385", data=blob(header_size=16385)[0])
        add("dictionary", data=blob("not a dictionary")[0])
        add("extra_key", data=blob(repr(dict(dictionary, extra=1)))[0])
        add("fortran", data=blob(repr(dict(dictionary, fortran_order=True)))[0])
        for key, shape in [("shape_bool", (True,)), ("shape_negative", (-1,)), ("shape_mismatch", (1,))]:
            add(key, data=blob(repr(dict(dictionary, shape=shape)))[0])
        add("shape_product", data=blob(repr(dict(dictionary, shape=(2000000, 2000000))))[0], schema={"dtype": "<f8", "shape": [2000000, 2000000]})
        for key, descr in [
            ("dtype_object", "|O"), ("dtype_endian", ">f8"), ("dtype_mismatch", "<i8"),
            ("dtype_field", [("wrong", "<f8")]),
            ("dtype_title", [(("title", "name"), "<f8")]),
            ("dtype_subarray", [("name", "<f8", (2,))])]:
            add(key, data=blob(repr(dict(dictionary, descr=descr)))[0])
        add("trailing", data=base + b"Z")
        class Failing:
            def __init__(self, exc): self.exc = exc
            def read(self, n): raise self.exc
        cases["stream_oserror"] = Failing(OSError("synthetic")), len(base), S
        cases["stream_bug"] = Failing(RuntimeError("synthetic")), len(base), S
        self.assertEqual(set(cases), set(C["cases"]))
        for name, (stream, size, schema) in cases.items():
            with self.subTest(name=name):
                with patch.object(np.lib.format, "read_array", side_effect=AssertionError("payload")):
                    with self.assertRaises(m.HeaderError) as ctx:
                        m.inspect_header(stream, size, schema)
                self.assertEqual(ctx.exception.code, C["cases"][name])

    def test_read_failures_and_unexpected_parser_bug_are_distinct(self):
        base, offset = blob()
        for cut in [0, 5, 6, 7, 8, 9, 10, offset - 1]:
            with self.subTest(cut=cut):
                with self.assertRaises(m.HeaderError) as ctx:
                    m.inspect_header(Spy(base[:cut]), len(base), S)
                self.assertEqual(ctx.exception.code, "NPY_TRAILING")
        with patch.object(np.lib.format, "read_array_header_1_0", side_effect=RuntimeError("internal")):
            with self.assertRaises(m.HeaderError) as ctx:
                m.inspect_header(Spy(base), len(base), S)
            self.assertEqual(ctx.exception.code, "INTERNAL_ERROR")
            self.assertIsInstance(ctx.exception.__cause__, RuntimeError)


if __name__ == "__main__":
    unittest.main(verbosity=2)
