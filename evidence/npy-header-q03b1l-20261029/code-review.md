**Verdict: SOUND-with-fixes.** The inspector does what the bounded contract asks: it consumes exactly prefix plus header, never reads payload, maps every listed negative fixture to its literal code, and applies the NumPy cap check before the header request. One error-code misattribution needs fixing. Nothing else blocks.

**Bug (must fix): invalid schema dtype is reported as NPY_DTYPE, not MEMBER_SCHEMA.**
At `saved_scene_npy_header_q03b1l.py:111`, `_dtype(schema["dtype"])` runs before any byte is read. Any rejection there raises NPY_DTYPE, which the contract reserves for the file's header. The adjudication text states that mistyped schema goes to MEMBER_SCHEMA. Repro, no stream needed:

```python
m.inspect_header(Spy(base), len(base), {"dtype": "|O", "shape": [2]})
# raises HeaderError NPY_DTYPE; contract precedence says MEMBER_SCHEMA
m.inspect_header(Spy(base), len(base), {"dtype": [("a", "<f8", (2,))], "shape": [1]})
# same misattribution
```

Fix: wrap lines 109 to 111 so a HeaderError from `_dtype` on the schema is re-raised as MEMBER_SCHEMA. The oracle has no fixture for this path, so the test suite does not catch it. Add one negative case to keep the closed table honest, which means also adding the key to the external contract table, since the test asserts set equality at line 146.

**Verified correct against the fixtures and contract:**

- Read loop at lines 26 to 40 accumulates short reads, treats empty bytes as EOF, maps OSError to source I/O, and routes non-bytes or over-long chunks to INTERNAL_ERROR. Spy with short=1 and short=7 exercises accumulation on a 16384-byte header.
- HEADER_LIMIT fires at line 122 before the header read. The oversize test checks request sequence [6, 2, width], which the code produces.
- Bool exclusion is real: `type(x) is not int` rejects True for both member_bytes and shape entries.
- Product guard at lines 140 to 147 divides before multiplying, so no overflow and no large allocation. Zero-dimension and scalar fixtures give 0 and 8 bytes as expected.
- dtype guard rejects object, big endian, titles, subarray, nested fields, and zero itemsize. The byte-order check also rejects a bare `|f8` spelling via the ambiguous-endian rule. String compare on the descriptor plus np.dtype compare means `<d` versus `<f8` is rejected, which is the strict behavior the contract wants.
- The meta fixture round-trips: descriptor_json uses dtype.descr, which for this unaligned layout yields the same pairs as the schema, and offsets come from the dtype rather than world positions.
- The standard-parser cross-check runs on a BytesIO holding only prefix and header, seeked to 8, using public read_array_header_1_0 and read_array_header_2_0 with max_header_size=16384. Patching that public name in the test is effective because the module resolves it at call time.
- stream_bug and the parser RuntimeError both land in INTERNAL_ERROR with cause preserved, distinct from OSError.
- The attested-length check at line 150 is arithmetic only. The docstring says physical truncation is a later gate, so no over-claim.

**Minor, non-blocking:**

- `_dtype` builds np.dtype twice for structured descriptors, once per field and once whole. Harmless.
- NPY_TRAILING is used both for short header reads and for attested-length mismatch. That matches the oracle table, so leave it, but the detail strings already distinguish them.
- Datetime kinds like `<M8[ns]` pass the dtype guard. Not object, not in any fixture, acceptable under the stated scope.

**Test file:** fixture construction, hash pinning of oracle and contract, and the case-set equality assertion are all correct as written. The only gap is the schema-dtype path above.