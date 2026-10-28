# B3C: complete saved-binary census and exact numerical witness

Status: **FEASIBILITY_ONLY**, no model authored or compiled. B3B remains
REJECTED_BINARY. Original 47 FAIL / 21 uncertain and all map acceptance stay open.

Both control and candidate: 1520/1520 components, 9120 points, 12160 faces;
zero noncomparables and complete oriented topology. Local predicted float32
coordinates match actual saved ODOL vertex bytes exactly everywhere. Historical
3514 and fresh control0fcc have equal semantic content under the pinned reader.
The control has zero world discrepancies. The candidate has two Y differences:
base8007/component1335 and roof8455/component1410, each one world ULP
4.76837158203125e-7m, affecting eight oriented faces. The second was beyond
R1's rejected prefix;185 further components are now censused. These WORLD
coordinates are two instrument calculations, not measured engine coordinates;
local raw-byte correspondence is the empirical compiler comparison.

The bounded solver examined9123 top values across36 pairs, domains33..1074,
and checked18246 top/base frame triples against independent rational IEEE754
round-to-nearest/even. Its JSON witness changes17 Y values (nine components),
maximum2.9802322387695312e-8m. All36 MLOD pair thicknesses are exactly180/512;
plane/base max error2.7824641812834727e-8m remains below1e-6. X/Z, other LODs,
source/predicted bounding boxes, fixed centre/pose and original controls stay
unchanged. Closure/convexity and full overlay pass existing limits±0.02m/0.01m.
1520 bed and1520 roof triangles,18842 overlay pairs, no missing/excess area;
height error range[-0.00075529737,+0.00017500189]m. This proves numerical
feasibility under fixed frames only, not a future compiler centre or game physics.

## Correction to previous thickness wording

Direct rational subtraction of saved coordinates confirms d130 has36/36 exact
pairs in the selected domain; c769 has20 exact and16 nonexact (maximum error
1.4901161193847656e-8m). The old exact guard was on author INPUT. The saved-file
consumer allowed1e-6 for candidate thickness. Describing all36 c769 output pairs
as exact was wrong. See thickness-addendum.json with all72 source/candidate pair
records and source anchors. Historical receipts stay intact. B3C enforces actual
exact MLOD thickness in the witness; it has not changed any old verdict.

## Validation and limits

Fable5.1 native independent plan181.25s and code275.156s, adjudicated.26tests pass:
manual IEEE ties/negatives/exponents/subnormals/signedzero, missing/ambiguous
mapping, winding, complete denominator, discarded-domain oracle mutation,
contract-only thickness filter, explicit control gate, and nontrivial12-prism
movement with real overlay. Private suite0.285s,process1.036s.
Census4.750s plus feasibility3.484s; peak resident238592000bytes (<2GiB).
Input pins externally inherited from R1 are distinguished from current
instrument hashes merely recorded; all are checked for stability afterward.

No P3D/PBO/native asset is published here. No package201, DayZ, lease or deployment.
No repeat of B3C or its reviews. Next unit needs a reviewed author/independent
saved-file consumer plan; future binary comparison and native run remain gated.
Nav8 historic607PASS only; water reference, RAM, nine visual regressions and C1
human review remain open. Expanded council is still queued after prior work.
