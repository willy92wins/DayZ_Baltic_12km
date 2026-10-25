# Corrected numeric diagnostics and global operator measurement

No terrain is accepted or promoted by this checkpoint. EV95 remains the latest isolated preview.

The original wet-bank proposal is still unaccepted. The first exact CSR-crossing gate also rejected the baseline by floating-point roundoff, and its metadata indexing was wrong. The old 0-of-3^13 enumeration is therefore not a physical infeasibility proof. Direct rational crossing reconstruction passes all 116 baseline checks and finds 20 candidate incidences on five native edges outside their physical interval, by at most about 1.12 micrometres. A separate bounded conversion unit is required; the original solver call is not repeated.

The frozen sizing run-05 helper rounded bounds outward despite its name. The live helper is corrected and its fixtures pass. Reconstructing the true inward bounds changes 684,315 lower and 185,062 upper variable bounds, but produces zero infeasible nodes, no domain change, and keeps EV95 feasible. Thus operator counts remain valid; the old run-05 bounds must not be used for a solver.

The matrix-free operator is independently compared with the frozen CSR reference. The measurement receipt records the one real-map action/adjoint invocation, including any resource abort. It is not a solve, convergence claim, terrain acceptance or native/render proof. The measurement uses the explicit run_benchmark(review_path, review_sha) API with the separate driver review; the default CLI points to the earlier operator-only review.

BASE 1.0, full-map bank shaping, dynamic water, gray-water rendering and native EV95 validation remain open.
