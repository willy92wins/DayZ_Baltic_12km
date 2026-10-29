import argparse
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shore_serialization_io_ev112 as io

def _totals_add(totals, cls, rec):
    if cls not in totals:
        totals[cls] = {"files": 0, "original_bytes": 0, "encoded_bytes": 0, "decoded_bytes": 0}
    totals[cls]["files"] += 1; totals[cls]["original_bytes"] += rec["original_bytes"]; totals[cls]["encoded_bytes"] += rec["encoded_bytes"]; totals[cls]["decoded_bytes"] += rec["decoded_bytes"]

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--contract", required=True)
    ap.add_argument("--contract-sha", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--receipts", required=True)
    ap.add_argument("--audit", required=True)
    args = ap.parse_args(argv)
    audit_state = None
    out_dir = None
    consumer_path = None
    try:
        contract = io.load_contract(args.contract, args.contract_sha)
        lim = contract["limits"]
        meta = io.load_metadata(contract)
        capture_root = os.path.abspath(contract["capture_root"])
        out_dir = os.path.abspath(args.output_dir)
        io.require(not os.path.exists(out_dir), "REJECTED_INTEGRITY", "output_exists")
        io.require(os.path.normcase(out_dir) != os.path.normcase(capture_root) and not os.path.normcase(out_dir).startswith(os.path.normcase(capture_root) + os.sep), "REJECTED_INTEGRITY", "output_inside_capture")
        preloads = io.preload_and_record()
        io.validate_preloads(preloads)
        os.mkdir(out_dir)
        consumer_path = os.path.join(out_dir, "consumer.json")
        allowed = {}
        for name in io.PIN_NAMES:
            allowed[os.path.abspath(contract["files"][name]["path"])] = "input"
        allowed[os.path.abspath(args.contract)] = "input"
        allowed[os.path.abspath(args.receipts)] = "input"
        allowed[os.path.abspath(args.audit)] = "input"
        allowed[consumer_path] = "output"
        audit_state = io.AuditState(allowed, capture_root=capture_root)
        audit_state.install()
        selftests = io.run_selftests(audit_state, out_dir)
        io.require(selftests.get("hook_installed") is True and selftests.get("forbidden_open_denied") is True and selftests.get("forbidden_import_denied") is True, "REJECTED_INTEGRITY", "selftests")
        receipts_data, receipts_sha, receipts_n = io.read_limited_bytes(args.receipts, lim["all_output_bytes"])
        audit_data, audit_sha, audit_n = io.read_limited_bytes(args.audit, lim["all_output_bytes"])
        io.require(receipts_n + audit_n <= lim["all_output_bytes"], "REJECTED_INTEGRITY", "all_output_input")
        io.require(receipts_data.endswith(b"\n") and len(receipts_data) > 0, "REJECTED_INTEGRITY", "truncated_last_line")
        lines = receipts_data.split(b"\n")
        io.require(lines[-1] == b"", "REJECTED_INTEGRITY", "truncated_last_line")
        lines = lines[:-1]
        io.require(len(lines) >= 1, "REJECTED_INTEGRITY", "receipts_empty")
        records = []
        for raw in lines:
            io.require(raw != b"", "REJECTED_INTEGRITY", "receipt_blank_line")
            records.append(io.parse_json_bytes(raw))
        header = records[0]
        io.exact_keys(header, contract["record_schema"]["header"])
        io.require(header["kind"] == "header" and header["schema"] == contract["schema"], "REJECTED_INTEGRITY", "header")
        io.require(header["contract_sha256"] == contract["_contract_sha256"], "REJECTED_INTEGRITY", "header_contract")
        io.require(header["inventory_sha256"] == contract["files"]["inventory"]["sha256"], "REJECTED_INTEGRITY", "header_inventory")
        io.require(header["classification_sha256"] == contract["files"]["classification"]["sha256"], "REJECTED_INTEGRITY", "header_classification")
        io.require_typed(header["codec"], contract["codec"], "REJECTED_INTEGRITY", "header_codec")
        io.require_typed(header["claims"], contract["claims"], "REJECTED_INTEGRITY", "header_claims")
        startup, terminal = io.parse_audit_ndjson(audit_data, receipts_sha=receipts_sha, receipts_n=receipts_n)
        io.require(startup["contract_sha256"] == contract["_contract_sha256"], "REJECTED_INTEGRITY", "audit_startup_contract_binding")
        io.require(startup["inventory_sha256"] == contract["files"]["inventory"]["sha256"] and startup["classification_sha256"] == contract["files"]["classification"]["sha256"], "REJECTED_INTEGRITY", "audit_startup_pins_binding")
        io.require(not any((r["path"] or "").lower().endswith((".npz", ".wrp", ".pbo")) for r in startup["preloads"]), "REJECTED_INTEGRITY", "audit_preload_no_npz_wrp_pbo")
        inv_by_path = {e["path"]: e for e in meta["inventory"]["files"]}
        cls_by_path = {r["path"]: r["classification"] for r in meta["classification"]["rows"]}
        body = records[1:]
        final = None
        if body and body[-1].get("kind") == "final":
            final = body[-1]; file_records = body[:-1]
        else:
            file_records = body
        for rec in file_records:
            io.require(rec.get("kind") == "file", "REJECTED_INTEGRITY", "record_kind")
        totals = {}
        for idx, rec in enumerate(file_records):
            io.exact_keys(rec, contract["record_schema"]["file"])
            io.require(io.is_int(rec["index"]) and rec["index"] == idx, "REJECTED_INTEGRITY", "noncontiguous_partial")
            io.require(type(rec["path"]) is str and rec["path"] in inv_by_path, "REJECTED_INTEGRITY", "receipt_unknown_path")
            io.require(idx < len(meta["inventory"]["files"]) and rec["path"] == meta["inventory"]["files"][idx]["path"], "REJECTED_INTEGRITY", "receipt_order")
            inv_e = inv_by_path[rec["path"]]
            io.require(rec["classification"] == cls_by_path[rec["path"]], "REJECTED_INTEGRITY", "receipt_classification")
            for k in ("original_bytes", "encoded_bytes", "decoded_bytes", "unused_bytes", "unconsumed_bytes"):
                io.require(io.is_int(rec[k]) and rec[k] >= 0, "REJECTED_INTEGRITY", "receipt_int:" + k)
            io.require(rec["original_bytes"] == inv_e["bytes"], "REJECTED_INTEGRITY", "receipt_original_vs_inventory")
            io.require(rec["decoded_bytes"] == rec["original_bytes"], "REJECTED_INTEGRITY", "receipt_decoded")
            io.require(rec["encoded_bytes"] <= 2 * rec["original_bytes"] + 1024, "REJECTED_INTEGRITY", "receipt_encoded_cap")
            io.require(io.is_sha(rec["original_sha256"]) and rec["original_sha256"] == inv_e["sha256"], "REJECTED_INTEGRITY", "receipt_source_sha")
            io.require(io.is_sha(rec["encoded_sha256"]) and io.is_sha(rec["decoded_sha256"]) and rec["decoded_sha256"] == rec["original_sha256"], "REJECTED_INTEGRITY", "receipt_hashes")
            io.require(rec["eof"] is True and rec["unused_bytes"] == 0 and rec["unconsumed_bytes"] == 0, "REJECTED_INTEGRITY", "receipt_eof")
            io.require(rec["state"] == "EXACT_BYTE_ROUNDTRIP", "REJECTED_INTEGRITY", "receipt_state")
            _totals_add(totals, rec["classification"], rec)
        complete = False
        state_name = "PARTIAL_SERIALIZATION_DIAGNOSTIC"
        if final is not None:
            io.require(terminal is not None, "REJECTED_INTEGRITY", "full_requires_audit_terminal")
            io.exact_keys(final, contract["record_schema"]["final"])
            io.require(final["kind"] == "final", "REJECTED_INTEGRITY", "final_kind")
            io.require(io.is_int(final["complete_files"]) and io.is_int(final["expected_files"]) and type(final["complete"]) is bool, "REJECTED_INTEGRITY", "final_types")
            io.require(final["complete_files"] == len(file_records) and final["expected_files"] == len(meta["inventory"]["files"]), "REJECTED_INTEGRITY", "final_counts")
            io.require(type(final["totals_by_classification"]) is dict, "REJECTED_INTEGRITY", "final_totals_type")
            for cls_name, tv in final["totals_by_classification"].items():
                io.require(type(cls_name) is str and type(tv) is dict and set(tv.keys()) == {"files", "original_bytes", "encoded_bytes", "decoded_bytes"} and all(io.is_int(x) and x >= 0 for x in tv.values()), "REJECTED_INTEGRITY", "final_totals_typed_ints_no_bool")
            io.require_typed(final["totals_by_classification"], totals, "REJECTED_INTEGRITY", "final_totals")
            io.require_typed(final["claims"], contract["claims"], "REJECTED_INTEGRITY", "final_claims")
            io.require(final["reason"] is None, "REJECTED_INTEGRITY", "final_reason")
            io.require(final["complete"] is True and len(file_records) == len(meta["inventory"]["files"]), "REJECTED_INTEGRITY", "no_full_on_partial")
            io.require(final["state"] == "SAVED_SERIALIZATION_FEASIBILITY_ONLY", "REJECTED_INTEGRITY", "final_state")
            io.require(terminal["state"] == final["state"] and terminal["complete_files"] == len(file_records) and terminal["expected_files"] == len(meta["inventory"]["files"]) and terminal["receipts_records"] == len(records), "REJECTED_INTEGRITY", "audit_terminal_final_consistency")
            io.require(terminal["capture_open_allowed"] == len(file_records) and terminal["counters"]["capture_attempts"] == len(file_records), "REJECTED_INTEGRITY", "terminal_capture_count")
            complete = True; state_name = "SAVED_SERIALIZATION_FEASIBILITY_ONLY"
        else:
            # All file records without a final marker remain PARTIAL, including a kill at this boundary.
            io.require(len(file_records) <= len(meta["inventory"]["files"]), "REJECTED_INTEGRITY", "partial_count")
            if terminal is not None:
                io.require(terminal["complete_files"] == len(file_records), "REJECTED_INTEGRITY", "audit_terminal_partial_counts")
        io.require(audit_state.counters["capture_attempts"] == 0, "REJECTED_INTEGRITY", "consumer_capture_access")
        result = {"kind": "consumer", "schema": "q02b4-metadata-consumer.v1", "state": state_name, "complete": complete, "verified_files": len(file_records), "expected_files": len(meta["inventory"]["files"]), "totals_by_classification": totals, "claims": contract["claims"], "contract_sha256": contract["_contract_sha256"], "inventory_sha256": contract["files"]["inventory"]["sha256"], "classification_sha256": contract["files"]["classification"]["sha256"], "receipts_sha256": receipts_sha, "audit_sha256": audit_sha, "scope": "METADATA_ONLY_NO_CAPTURE_NO_CODEC", "audit": {"counters": audit_state.counters, "selftests": selftests, "capture_attempts": audit_state.counters["capture_attempts"], "preloads_count": len(preloads), "producer_audit_record": startup["record"], "producer_audit_terminal": terminal is not None}}
        data = io.dump_json_obj(result) + b"\n"
        io.require(len(data) <= lim["all_output_bytes"], "INCONCLUSIVE_RESOURCE", "consumer_cap")
        with open(consumer_path, "xb") as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        return 0
    except io.Reject as exc:
        try:
            if audit_state is not None and consumer_path and out_dir and os.path.isdir(out_dir) and not os.path.exists(consumer_path):
                bad = {"kind": "consumer", "schema": "q02b4-metadata-consumer.v1", "state": "REJECTED_INTEGRITY", "complete": False, "reason": exc.code, "claims": io.EXPECTED_CLAIMS, "scope": "METADATA_ONLY_NO_CAPTURE_NO_CODEC", "audit": {"counters": audit_state.counters, "capture_attempts": audit_state.counters["capture_attempts"]}}
                with open(consumer_path, "xb") as f:
                    f.write(io.dump_json_obj(bad) + b"\n"); f.flush(); os.fsync(f.fileno())
        except Exception:
            pass
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
