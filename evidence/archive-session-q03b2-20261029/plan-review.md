## SOUND-with-fixes

Required corrections:

1. **Count-before-`ZipFile`:** Locate EOCD by scanning only the final `22+65535` bytes and accepting the candidate whose comment ends exactly at EOF and whose `cd_offset+cd_size` equals the EOCD offset. Require single-disk fields to be zero. Abort the central-directory walk when record 36 starts, before storing it. Require the walked count to equal both EOCD entry-count fields. Treat `0xFFFF`/`0xFFFFFFFF` count, size, or offset sentinels as `ZIP_LAYOUT_UNSUPPORTED`. After the walk, require the first local header at offset 0 and pairwise-disjoint local, central, and EOCD ranges within the buffer.

2. **Preallocation accounting:** Rename “reserve” to *logical reservation*; it is neither allocation nor an RSS bound. Define testable counters: `live_stored`, `live_expanded`, `cumulative_stored_actual_bytes_read`, and `cumulative_expanded_reserved`. Charge expanded once per attempt at reservation and never refund it, including pre-`ZipFile` failures. Derive `262434599` from schema maxima or replace it with a formula. Reject non-`int`, `bool`, non-positive, or above-hard-cap limits rather than clamping them.

3. **Two-phase memory peak:** Explicitly choose the implementation. Either reopen each member for header inspection and again for `read_array`, charging one transient member plus retained arrays under `sum(file_size)`, or spool all payloads and charge spool plus arrays separately. Do not claim one `sum(file_size)` charge covers simultaneously retained payloads and arrays. The spy must prove no `read_array` call occurs before every header passes.

4. **Identity sequence:** Require: `lstat` ancestors/file, open without following the final symlink where the platform supports it, `fstat` the handle and match the pre-open `lstat`, reserve using the handle size, read exactly that many bytes, then `fstat` again and re-`lstat` path and ancestors, matching `dev/ino/size/mtime_ns`. State that this detects substitution; because parsing uses the retained buffer, post-read substitution does not affect the snapshot.

5. **Local ZIP64 compatibility:** Byte-assert a generated NumPy fixture: local extra field `0x0001` present, payload extents derived from central compressed size, no ZIP64 EOCD/locator. Parse local extras strictly; allow `0x0001` whose values, when present for sentinel local fields, equal central sizes. Reject ZIP64 EOCD/locator records and sentinel-dependent central values as `ZIP_LAYOUT_UNSUPPORTED`, but do not reject a redundant, consistent central `0x0001` extra if the real fixture produces one. Define the allowed flag mask explicitly, including treatment of data-descriptor bit 3; reject name-altering extras.

6. **Digests:** Separate payload SHA-256/length, verified against the external contract, from array `nbytes`, verified against dtype/shape. A payload digest cannot be compared with `memoryview(array)`, which excludes the NPY header and padding. State that payload hashing *detects* header/padding differences; returned arrays do not themselves preserve them.

7. **Missing state rules:** Specify the error for a second concurrent `open`, sequential reuse after exit, relative or drive-relative paths, and sibling-header SHA mismatch before import. Header mismatch and state misuse must fail closed without falling back to another header copy.

8. **Honest scope:** Attach `ARCHIVE_SESSION_FIXTURE_VERIFIED_ONLY` to the result and state that supported local-ZIP64 fixtures prove only the enumerated subset, not NumPy files generally or any historical archive.