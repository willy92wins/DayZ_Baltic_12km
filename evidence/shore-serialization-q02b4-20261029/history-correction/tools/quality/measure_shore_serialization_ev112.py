import argparse
import hashlib
import os
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shore_serialization_io_ev112 as io

def _worst_bound(n):
    return n + (n >> 12) + (n >> 14) + (n >> 25) + 13

class Decoder:
    def __init__(self, n, expected_sha):
        self.n = n
        self.expected_sha = expected_sha
        self.dec = zlib.decompressobj(15)
        self.hash = hashlib.sha256()
        self.decoded = 0
    def feed(self, piece, reservation):
        io.require(type(piece) is bytes, "REJECTED_INTEGRITY", "decoder_piece_bytes")
        pending = piece
        while True:
            io.require(reservation >= _worst_bound(self.n) and reservation == 134217728, "INCONCLUSIVE_RESOURCE", "reserve")
            max_len = min(65536, max(1, self.n - self.decoded))
            before_eof = self.dec.eof
            in_len = len(pending)
            try:
                out = self.dec.decompress(pending, max_len)
            except zlib.error:
                raise io.Reject("REJECTED_INTEGRITY", "decoder_corrupt")
            io.require(self.decoded + len(out) <= self.n, "REJECTED_INTEGRITY", "decoder_output_overrun")
            if out:
                self.hash.update(out)
                self.decoded += len(out)
            io.require(not self.dec.unused_data, "REJECTED_INTEGRITY", "decoder_unused_concatenated")
            new_pending = self.dec.unconsumed_tail
            if in_len == 0 and len(out) == 0 and not new_pending:
                break
            progress = (len(new_pending) < in_len) or (len(out) > 0) or ((not before_eof) and self.dec.eof)
            if not progress and new_pending:
                raise io.Reject("REJECTED_INTEGRITY", "decoder_no_progress")
            if not progress and not self.dec.eof and in_len > 0:
                raise io.Reject("REJECTED_INTEGRITY", "decoder_no_progress")
            pending = new_pending
            if not pending:
                break
    def finish(self, reservation):
        io.require(reservation == 134217728, "INCONCLUSIVE_RESOURCE", "reserve")
        try:
            out = self.dec.decompress(b"", 1)
        except zlib.error:
            raise io.Reject("REJECTED_INTEGRITY", "decoder_corrupt")
        io.require(len(out) == 0, "REJECTED_INTEGRITY", "decoder_output_overrun")
        io.require(self.dec.eof, "REJECTED_INTEGRITY", "decoder_truncated_eof")
        io.require(not self.dec.unused_data and not self.dec.unconsumed_tail, "REJECTED_INTEGRITY", "decoder_tail")
        io.require(self.decoded == self.n, "REJECTED_INTEGRITY", "decoder_bytes")
        io.require(self.hash.hexdigest() == self.expected_sha, "REJECTED_INTEGRITY", "decoder_sha")

class RoundTrip:
    def __init__(self, n, expected_sha, reservation=134217728):
        self.n = n
        self.expected_sha = expected_sha
        self.reservation = reservation
        self.enc = zlib.compressobj(1, zlib.DEFLATED, 15, 8, 0)
        self.decoder = Decoder(n, expected_sha)
        self.orig_hash = hashlib.sha256()
        self.enc_hash = hashlib.sha256()
        self.orig = 0
        self.encoded = 0
        self.cap = 2 * n + 1024
    def _reserve(self):
        io.require(self.reservation == 134217728 and self.reservation >= _worst_bound(self.n) + 30769152, "INCONCLUSIVE_RESOURCE", "reserve128")
    def _account_encoded(self, piece):
        io.require(len(piece) <= self.cap - self.encoded, "ENCODING_RESOURCE_INCONCLUSIVE", "encoded_cap_piece")
        io.require(self.encoded + len(piece) <= self.cap, "ENCODING_RESOURCE_INCONCLUSIVE", "encoded_cap")
        if piece:
            self.enc_hash.update(piece)
        self.encoded += len(piece)
    def feed_chunk(self, chunk):
        io.require(self.orig + len(chunk) <= self.n, "REJECTED_INTEGRITY", "source_over")
        self.orig_hash.update(chunk)
        self.orig += len(chunk)
        self._reserve()
        try:
            piece = self.enc.compress(chunk)
        except zlib.error:
            raise io.Reject("REJECTED_INTEGRITY", "encoder")
        self._account_encoded(piece)
        self.decoder.feed(piece, self.reservation)
    def finish(self):
        self._reserve()
        io.require(zlib.Z_FINISH == 4, "REJECTED_INTEGRITY", "zfinish")
        try:
            piece = self.enc.flush(4)
        except zlib.error:
            raise io.Reject("REJECTED_INTEGRITY", "encoder_flush")
        self._account_encoded(piece)
        self.decoder.feed(piece, self.reservation)
        self.decoder.finish(self.reservation)
        io.require(self.orig == self.n, "REJECTED_INTEGRITY", "source_bytes")
        io.require(self.orig_hash.hexdigest() == self.expected_sha, "REJECTED_INTEGRITY", "source_sha")
        io.require(self.decoder.hash.hexdigest() == self.expected_sha, "REJECTED_INTEGRITY", "decoded_sha")
        return {"original_bytes": self.orig, "encoded_bytes": self.encoded, "decoded_bytes": self.decoder.decoded, "original_sha256": self.orig_hash.hexdigest(), "encoded_sha256": self.enc_hash.hexdigest(), "decoded_sha256": self.decoder.hash.hexdigest(), "eof": True, "unused_bytes": 0, "unconsumed_bytes": 0}

def roundtrip_bytes(data, expected_sha=None, cap_n=16777216):
    io.require(type(data) is bytes and len(data) <= cap_n, "INPUT_OUT_OF_CONTRACT", "bytes_cap")
    sha = expected_sha if expected_sha is not None else hashlib.sha256(data).hexdigest()
    rt = RoundTrip(len(data), sha)
    for i in range(0, len(data), 65536):
        rt.feed_chunk(data[i:i + 65536])
    return rt.finish()

def measure_file(path, rel, classification, n, sha, index):
    ap = io.check_file_no_reparse(path)
    st0 = os.stat(ap)
    io.require(st0.st_size <= 16777216, "INPUT_OUT_OF_CONTRACT", "file_cap_before_read")
    io.require(st0.st_size == n, "REJECTED_INTEGRITY", "inventory_size")
    rt = RoundTrip(n, sha)
    with open(ap, "rb") as f:
        fst0 = os.fstat(f.fileno())
        io.require(io.stat_tuple(fst0) == io.stat_tuple(st0), "REJECTED_INTEGRITY", "stat_handle_before")
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            rt.feed_chunk(chunk)
        fst1 = os.fstat(f.fileno())
        io.require(io.stat_tuple(fst1) == io.stat_tuple(st0), "REJECTED_INTEGRITY", "stat_handle_after")
    st1 = os.stat(ap)
    io.require(io.stat_tuple(st1) == io.stat_tuple(st0), "REJECTED_INTEGRITY", "stat_path_after")
    res = rt.finish()
    return {"kind": "file", "index": index, "path": rel, "classification": classification, "original_bytes": res["original_bytes"], "encoded_bytes": res["encoded_bytes"], "decoded_bytes": res["decoded_bytes"], "original_sha256": res["original_sha256"], "encoded_sha256": res["encoded_sha256"], "decoded_sha256": res["decoded_sha256"], "eof": True, "unused_bytes": 0, "unconsumed_bytes": 0, "state": "EXACT_BYTE_ROUNDTRIP"}

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--contract", required=True)
    ap.add_argument("--contract-sha", required=True)
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args(argv)
    audit_state = None
    out_dir = None
    receipts_path = None
    audit_path = None
    receipts_bytes = 0
    audit_bytes_total = 0
    state_name = "REJECTED_INTEGRITY"
    preloads = []
    runtime_checks = {}
    selftests = {}
    try:
        io.require(sys.version_info[:3] == (3, 12, 14) or sys.version.startswith("3.12.14"), "REJECTED_INTEGRITY", "python_version")
        contract = io.load_contract(args.contract, args.contract_sha)
        lim = contract["limits"]
        meta = io.load_metadata(contract)
        io.check_runtime_images(contract)
        runtime_checks = {"python_version": sys.version.startswith("3.12.14"), "zlib_runtime": getattr(zlib, "ZLIB_RUNTIME_VERSION", zlib.ZLIB_VERSION) == "1.3.2", "zlib_compile": zlib.ZLIB_VERSION == "1.3.2", "executable_pin": True, "codec_fixed": io.typed_equal(contract["codec"], io.EXPECTED_CODEC)}
        io.validate_runtime_checks(runtime_checks)
        capture_root = io.check_ancestors_no_reparse(contract["capture_root"])
        io.inventory_walk_check(capture_root, meta["inventory"])
        io.require(meta["inventory"]["total_bytes"] <= lim["total_original"], "INPUT_OUT_OF_CONTRACT", "total_before_read")
        for e in meta["inventory"]["files"]:
            io.require(e["bytes"] <= lim["individual_original"], "INPUT_OUT_OF_CONTRACT", "file_before_read")
        out_dir = os.path.abspath(args.output_dir)
        io.require(not os.path.exists(out_dir), "REJECTED_INTEGRITY", "output_exists")
        io.require(os.path.normcase(out_dir) != os.path.normcase(capture_root) and not os.path.normcase(out_dir).startswith(os.path.normcase(capture_root) + os.sep), "REJECTED_INTEGRITY", "output_inside_capture")
        io.check_ancestors_no_reparse(os.path.dirname(out_dir) or out_dir)
        preloads = io.preload_and_record()
        io.validate_preloads(preloads)
        io.require(not any((r["path"] or "").lower().endswith((".npz", ".wrp", ".pbo")) for r in preloads), "REJECTED_INTEGRITY", "preload_capture_extension")
        os.mkdir(out_dir)
        receipts_path = os.path.join(out_dir, "receipts.ndjson")
        audit_path = os.path.join(out_dir, "audit.json")
        allowed = {}
        for name in io.PIN_NAMES:
            allowed[os.path.abspath(contract["files"][name]["path"])] = "input"
        allowed[os.path.abspath(args.contract)] = "input"
        for e in meta["inventory"]["files"]:
            allowed[os.path.join(capture_root, *e["path"].split("/"))] = "input"
        allowed[receipts_path] = "output"
        allowed[audit_path] = "output"
        audit_state = io.AuditState(allowed, capture_root=capture_root)
        audit_state.install()
        selftests = io.run_selftests(audit_state, out_dir)
        io.require(selftests.get("hook_installed") is True and selftests.get("forbidden_open_denied") is True and selftests.get("forbidden_import_denied") is True, "REJECTED_INTEGRITY", "selftests")
        startup = {"kind": "audit", "schema": "q02b4-audit.v1", "record": "startup", "contract_sha256": contract["_contract_sha256"], "inventory_sha256": contract["files"]["inventory"]["sha256"], "classification_sha256": contract["files"]["classification"]["sha256"], "runtime_checks": runtime_checks, "preloads": preloads, "selftests": selftests, "counters": dict(audit_state.counters), "allowed_path_count": len(audit_state.allowed)}
        startup_bytes = io.dump_json(startup)
        io.require(len(startup_bytes) <= lim["all_output_bytes"], "INCONCLUSIVE_RESOURCE", "audit_startup_cap")
        with open(audit_path, "xb") as af:
            af.write(startup_bytes)
            af.flush(); os.fsync(af.fileno())
        audit_bytes_total = len(startup_bytes)
        cls_by_path = {r["path"]: r["classification"] for r in meta["classification"]["rows"]}
        totals = {}
        header = {"kind": "header", "schema": contract["schema"], "contract_sha256": contract["_contract_sha256"], "inventory_sha256": contract["files"]["inventory"]["sha256"], "classification_sha256": contract["files"]["classification"]["sha256"], "codec": contract["codec"], "claims": contract["claims"]}
        records_done = 0
        receipts_sha_hasher = hashlib.sha256()
        with open(receipts_path, "xb") as out:
            line = io.dump_json(header)
            io.require(receipts_bytes + len(line) + audit_bytes_total <= lim["all_output_bytes"], "INCONCLUSIVE_RESOURCE", "report_cap_before_write")
            out.write(line); receipts_sha_hasher.update(line); receipts_bytes += len(line); out.flush(); os.fsync(out.fileno())
            for idx, e in enumerate(meta["inventory"]["files"]):
                full = os.path.join(capture_root, *e["path"].split("/"))
                rec = measure_file(full, e["path"], cls_by_path[e["path"]], e["bytes"], e["sha256"], idx)
                line = io.dump_json(rec)
                io.require(receipts_bytes + len(line) + audit_bytes_total <= lim["all_output_bytes"], "INCONCLUSIVE_RESOURCE", "report_cap_before_write")
                out.write(line); receipts_sha_hasher.update(line); receipts_bytes += len(line); out.flush(); os.fsync(out.fileno())
                records_done += 1
                c = rec["classification"]
                if c not in totals:
                    totals[c] = {"files": 0, "original_bytes": 0, "encoded_bytes": 0, "decoded_bytes": 0}
                totals[c]["files"] += 1; totals[c]["original_bytes"] += rec["original_bytes"]; totals[c]["encoded_bytes"] += rec["encoded_bytes"]; totals[c]["decoded_bytes"] += rec["decoded_bytes"]
            io.inventory_walk_check(capture_root, meta["inventory"])
            state_name = "SAVED_SERIALIZATION_FEASIBILITY_ONLY"
            final = {"kind": "final", "state": state_name, "complete_files": records_done, "expected_files": len(meta["inventory"]["files"]), "complete": records_done == len(meta["inventory"]["files"]), "totals_by_classification": totals, "reason": None, "claims": contract["claims"]}
            line = io.dump_json(final)
            io.require(receipts_bytes + len(line) + audit_bytes_total <= lim["all_output_bytes"], "INCONCLUSIVE_RESOURCE", "report_cap_before_write")
            out.write(line); receipts_sha_hasher.update(line); receipts_bytes += len(line); out.flush(); os.fsync(out.fileno())
        terminal = {"kind": "audit", "schema": "q02b4-audit.v1", "record": "terminal", "state": state_name, "contract_sha256": contract["_contract_sha256"], "receipts_sha256": receipts_sha_hasher.hexdigest(), "receipts_bytes": receipts_bytes, "receipts_records": records_done + 2, "complete_files": records_done, "expected_files": len(meta["inventory"]["files"]), "counters": dict(audit_state.counters), "capture_open_allowed": audit_state.counters["capture_open_allowed"], "claims": contract["claims"]}
        terminal_bytes = io.dump_json(terminal)
        io.require(receipts_bytes + audit_bytes_total + len(terminal_bytes) <= lim["all_output_bytes"], "INCONCLUSIVE_RESOURCE", "all_output_cap_includes_both_audit_records")
        with open(audit_path, "ab") as af:
            af.write(terminal_bytes); af.flush(); os.fsync(af.fileno())
        return 0
    except io.Reject as exc:
        print(exc.code, file=sys.stderr)
        return 1
    except PermissionError as exc:
        print("REJECTED_INTEGRITY:audit:" + str(exc), file=sys.stderr)
        return 1
    except Exception as exc:
        print("REJECTED_INTEGRITY:" + type(exc).__name__, file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
