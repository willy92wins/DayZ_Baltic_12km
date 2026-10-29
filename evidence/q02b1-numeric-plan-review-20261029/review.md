**Verdict: SOUND-with-fixes.** The numeric kernel's core claims hold; three definitions are missing or under-specified and one proof needs its hypothesis stated.

**Verified claims**

- **Root witness.** With m = floor(n·2^96/d) and j = isqrt(m): j² ≤ m ≤ n·2^96/d gives j²d ≤ n·2^96. Since (j+1)² is an integer and floor(x) < (j+1)² implies x < (j+1)², n·2^96 < (j+1)²d. The witness inequality is exactly the one a consumer should recheck. Width 2^-48 holds; exact-equality test j²d == n·2^96 is correct.
- **Prefix width** n·2^-48 is a plain sum of widths. Correct, conditional on n being the real edge count, as stated.
- **Degeneration guard** ensures L_lo > 0: q ≥ 10^-16 gives sqrt(q) ≥ 10^-8, far above 2^-48 ≈ 3.6e-15, so j ≥ 1. Division by L is well defined.
- **Segment selection, t ⊂ [0,1].** Residual [h − S_hi, h − S_lo] is positive because h > S_hi. Upper bound t_hi = (h − S_lo)/L_lo < 1 requires h − S_lo < L_lo, which follows from h < next_lo **only if next_lo is defined as S_lo + L_lo**. The proof is sound under that definition. Any "tighter" prefix construction breaks it. State this as a contract invariant and have the consumer recompute next_lo = S_lo + L_lo itself.
- **Support rules.** 2h ≥ P_hi implies 2h ≥ P_true, so INSUFFICIENT is correct. 2h < P_lo implies supported. Open-side rule with lo ≥ h supported, hi < h insufficient, else uncertain, is correct.
- **Interval algebra.** Product by four endpoint products, square with 0-containing rule, division with strictly positive denominator, all exact over Fraction. Menger curvature 2·cross/(abc) is the correct formula. Containment follows because every true value lies in its interval; rectangles over-approximate and no PASS is claimed. Fine.
- **Resource caps.** Normal coordinates near 12282 m have as_integer_ratio denominators ≤ 2^40. q needs ~200 bits after the shift. Cross products of rational A,B,C land near a few hundred bits. Well under 4096. Only subnormal coordinates (denominator 2^1074) could trip the cap in a product of four, which yields RESOURCE_INCONCLUSIVE, acceptable.

**Essential fixes (missing definitions)**

1. **Cyclic wrap makes station positions intervals.** For a closed chain, A and C sit at h ∓ half-width. When that crosses the seam you add or subtract P, which is an interval, so the query position is no longer an exact rational. The segment-selection predicate is written for an exact h. Counterexample: square seam, perimeter interval [4 − 4·2^-48, 4], station h = 0.5, half-width 1. C position −0.5 + P is an interval straddling the last-edge vertex boundary only if P is inexact, and the current text does not say what to do. Fix: define queries as rational intervals [q_lo, q_hi]; unique segment iff q_lo > prev_hi and q_hi < next_lo; t = (q − S)/L with the same ⊂ [0,1] argument; equality cases become BOUNDARY_UNCERTAIN unless q is a point. Open chains keep exact points, so no change there.

2. **Square root of an interval.** State explicitly: lower bound uses j(s_lo)/2^48, upper uses j(s_hi)+1 over 2^48, or j(s_hi) when the upper witness is exact. Mutant "dropped root witness" cannot be detected unless both witnesses are emitted.

3. **Range of h.** Define h = 0 (first vertex, t = 0), h negative (REJECT), h ≥ total_hi (OUT_OF_RANGE), h ∈ [total_lo, total_hi) inexact (BOUNDARY_UNCERTAIN). Also fix whether the degeneration test is q ≤ threshold or q < threshold; either is defensible, but the mutant suite needs one.

**Minor**

- Deficit lower bound can go negative because |C−A| interval may exceed 2h. No clamp is correct, but tests should assert that and not treat it as a failure.
- "Open final last, t = 1" wording: ensure the last vertex is chosen on the final segment only when the prefix at that vertex is exact and the chain is open; for cyclic, h == exact P should map to vertex 0.

No false numerical claims found. Verifiable with the three definitions added.