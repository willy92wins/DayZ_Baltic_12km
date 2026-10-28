# B3D code adjudication — delivered Fable5.1 native135.25s

Capsule delivered complete FIN_REVISION, assistant/result identity confirmed,
no tools or denials, original three source hashes unchanged during review.
SOUND-with-fixes; one grouped mechanical correction before production author.
1 ACCEPTED. Actual dict-before conversion raises TypeError; old catch would
label it REJECTED_MLOD. failure_status now only pure ValueError=>REJECTED;
TypeError/IndexError/AttributeError/MemoryError/struct.error/Inconclusive etc
=>INCONCLUSIVE. Named regression exercises malformed witness and classification.
2 ACCEPTED. save_checked writes exclusive candidate.p3d.tmp, then rechecks
all inputs/contract before rename. Failure fixture leaves only pending bytes;
success promotes once, existing destination is refused. A final report is still
required downstream; rename alone is never acceptance.
3 HARDENING ACCEPTED, rationale corrected: float32(1+1e-7) DOES change from1;
there was no demonstrated failure for +/-1 as claimed. nextafter plus byte-change
assertion now makes the intended mutation explicit for any finite normal.
4 ACCEPTED as fixed production postcondition: incident_faces=incident_normals=50
in author and consumer CLIs, matching independent source-domain discovery.
5 BACKLOG, not new blocking claim without repro. Eight CLI tests now exercise
malformed/missing contract, counts/schema, missing/changed pins, self-consistent
fake prior and output reuse, both actual entrypoints. Remaining branch-specific
mutants named by reviewer remain unproven coverage; no claim of exhaustive suite.

No new opinion round. Helpers outside capsule remain source-verified primitives
and tested against saved-file positives/negatives; reviewer did not certify them.
No tolerance or label changed. Final suite/CLI results must be green before
single author60s/2GiB then independent consumer180s/2GiB. No build/native.
