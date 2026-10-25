"""Float32-lattice MILP candidate generator with exact Fraction post-validation.

This module is intentionally tested only on small synthetic cases.  The real
121-variable instance is not solved here.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
import time
from typing import Iterable

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix


class ModelError(ValueError):
    pass


class NoCanonicalOptimum(RuntimeError):
    pass


def F32(v) -> np.float32:
    return np.float32(v)


def frac_f32(v) -> Fraction:
    return Fraction.from_float(float(np.float32(v)))


def f32_from_bits(bits: int) -> np.float32:
    return np.asarray([bits], dtype=np.uint32).view(np.float32)[0]


def bits_f32(v) -> int:
    return int(np.asarray([np.float32(v)], dtype=np.float32).view(np.uint32)[0])


def ulp_for_exponent_field(exp: int) -> Fraction:
    if exp == 0:
        return Fraction(1, 1 << 149)
    if exp >= 255:
        raise ModelError("non-finite float32 binade is unsupported")
    power = exp - 150
    return Fraction(1 << power, 1) if power >= 0 else Fraction(1, 1 << (-power))


def common_quantum(lo: np.ndarray, hi: np.ndarray) -> Fraction:
    exps = []
    for value in np.concatenate((np.asarray(lo, np.float32), np.asarray(hi, np.float32))):
        x = float(value)
        if not math.isfinite(x) or x <= 0:
            raise ModelError("this terrain model requires positive finite float32 heights")
        exps.append((bits_f32(value) >> 23) & 0xFF)
    q = min(ulp_for_exponent_field(e) for e in exps)
    return q


def _as_fraction(value):
    if isinstance(value, Fraction):
        return value
    if isinstance(value, (int, np.integer)):
        return Fraction(int(value))
    x = float(value)
    if math.isinf(x):
        return x
    if not math.isfinite(x):
        raise ModelError("NaN row bound")
    return Fraction.from_float(x)


def _ceil_binary64(value: Fraction) -> float:
    out = float(value)
    if Fraction.from_float(out) < value:
        out = math.nextafter(out, math.inf)
    return out


def _floor_binary64(value: Fraction) -> float:
    out = float(value)
    if Fraction.from_float(out) > value:
        out = math.nextafter(out, -math.inf)
    return out


def conservative_float_row(coefficients, lower, upper, variable_bounds):
    """Return a float64 row whose feasible set is a subset of the exact row.

    Coefficient/RHS conversion error is bounded over the declared variable box.
    Rows with a rounded coefficient on an unbounded variable are rejected.
    This makes a candidate sound after exact gates, at the cost of possible
    false infeasibility. It does not certify exact optimality.
    """
    exact_coeff = {int(i): _as_fraction(v) for i, v in coefficients.items() if v != 0}
    float_coeff = {i: float(v) for i, v in exact_coeff.items()}
    error = Fraction(0)
    for i, exact in exact_coeff.items():
        rounded = Fraction.from_float(float_coeff[i])
        delta = abs(exact - rounded)
        if not delta:
            continue
        lo, hi = variable_bounds[i]
        if not math.isfinite(float(lo)) or not math.isfinite(float(hi)):
            raise ModelError("cannot conservatively round a coefficient on an unbounded variable")
        max_abs = max(abs(Fraction.from_float(float(lo))), abs(Fraction.from_float(float(hi))))
        error += delta * max_abs
    lb_exact = _as_fraction(lower)
    ub_exact = _as_fraction(upper)
    lb_out = -math.inf if isinstance(lb_exact, float) and lb_exact == -math.inf else _ceil_binary64(lb_exact + error)
    ub_out = math.inf if isinstance(ub_exact, float) and ub_exact == math.inf else _floor_binary64(ub_exact - error)
    if lb_out > ub_out:
        raise ModelError("conservative float64 rounding empties a linear row")
    return float_coeff, lb_out, ub_out, str(error)


@dataclass(frozen=True)
class BinSegment:
    exponent_field: int
    first_bits: int
    last_bits: int
    first_m: int
    stride_m: int
    count: int


def decompose_f32_interval(lo, hi, baseline, quantum: Fraction) -> tuple[BinSegment, ...]:
    lo = np.float32(lo); hi = np.float32(hi); baseline = np.float32(baseline)
    if not (np.isfinite(lo) and np.isfinite(hi) and np.isfinite(baseline)):
        raise ModelError("non-finite interval or baseline")
    if not (0 < lo <= baseline <= hi):
        raise ModelError("baseline must lie inside positive inward float32 bounds")
    lb, hb = bits_f32(lo), bits_f32(hi)
    le, he = (lb >> 23) & 0xFF, (hb >> 23) & 0xFF
    base = frac_f32(baseline)
    segments = []
    for exp in range(le, he + 1):
        if exp >= 255:
            raise ModelError("infinite/NaN exponent interval")
        exp_start = exp << 23
        exp_end = ((exp + 1) << 23) - 1
        first = max(lb, exp_start)
        last = min(hb, exp_end)
        if first > last:
            continue
        ulp = ulp_for_exponent_field(exp)
        stride = ulp / quantum
        if stride.denominator != 1 or stride <= 0:
            raise ModelError("common quantum does not divide an exponent-bin ULP")
        first_m = (frac_f32(f32_from_bits(first)) - base) / quantum
        last_m = (frac_f32(f32_from_bits(last)) - base) / quantum
        if first_m.denominator != 1 or last_m.denominator != 1:
            raise ModelError("float32 endpoint is not on the common integer lattice")
        stride_i = int(stride)
        count = last - first + 1
        if int(last_m - first_m) != stride_i * (count - 1):
            raise ModelError("binade segment is not an exact arithmetic progression")
        segments.append(BinSegment(exp, first, last, int(first_m), stride_i, count))
    if not segments:
        raise ModelError("empty float32 interval")
    if sum(s.count for s in segments) != hb - lb + 1:
        raise ModelError("binade decomposition omitted representable float32 values")
    return tuple(segments)


@dataclass(frozen=True)
class Crossing:
    a_rc: tuple[int, int]
    b_rc: tuple[int, int]
    level_a: Fraction
    level_b: Fraction
    dry_endpoint: int
    t_lower: Fraction
    t_upper: Fraction
    source: str = "crossing"


@dataclass(frozen=True)
class Sign:
    rc: tuple[int, int]
    level: Fraction
    sign: int
    baseline: np.float32 | None = None
    source: str = "sign"


@dataclass
class VarExpr:
    constant: int
    terms: dict[int, int]
    segments: tuple[BinSegment, ...]


class LatticeMILP:
    """Finite float32 domain represented as integer offsets from exact B."""

    def __init__(self, base_grid, variables_rc, lo, hi, x64,
                 crossings: Iterable[Crossing] = (), signs: Iterable[Sign] = (),
                 d8_witnesses: Iterable[tuple[tuple[int, int], tuple[int, int]]] = (),
                 fixed_indices: Iterable[int] = ()):
        self.base = np.asarray(base_grid, dtype=np.float32).copy()
        self.variables_rc = tuple(tuple(map(int, rc)) for rc in np.asarray(variables_rc))
        self.lo = np.asarray(lo, dtype=np.float32).copy()
        self.hi = np.asarray(hi, dtype=np.float32).copy()
        self.x64 = np.asarray(x64, dtype=np.float64).copy()
        n = len(self.variables_rc)
        self.crossings = tuple(crossings)
        self.signs = tuple(signs)
        self.d8_witnesses = tuple(d8_witnesses)
        if self.base.ndim != 2 or self.lo.shape != (n,) or self.hi.shape != (n,) or self.x64.shape != (n,):
            raise ModelError("base/bounds/objective shapes do not match variable list")
        if len(set(self.variables_rc)) != n:
            raise ModelError("duplicate variable coordinate")
        if not np.all(np.isfinite(self.x64)):
            raise ModelError("non-finite x64 objective target")
        if any(r < 0 or c < 0 or r >= self.base.shape[0] or c >= self.base.shape[1] for r, c in self.variables_rc):
            raise ModelError("variable outside baseline context")
        for spec in self.signs:
            r, c = map(int, spec.rc)
            if not (0 <= r < self.base.shape[0] and 0 <= c < self.base.shape[1]):
                raise ModelError(f"sign coordinate outside baseline context: {spec.rc}")
        for spec in self.crossings:
            for rc in (spec.a_rc, spec.b_rc):
                r, c = map(int, rc)
                if not (0 <= r < self.base.shape[0] and 0 <= c < self.base.shape[1]):
                    raise ModelError(f"crossing coordinate outside baseline context: {rc}")
            if spec.t_lower > spec.t_upper:
                raise ModelError("crossing interval is reversed")
        for center, witness in self.d8_witnesses:
            for rc in (center, witness):
                r, c = map(int, rc)
                if not (0 <= r < self.base.shape[0] and 0 <= c < self.base.shape[1]):
                    raise ModelError(f"D8 coordinate outside baseline context: {rc}")
        self.var_by_rc = {rc: i for i, rc in enumerate(self.variables_rc)}
        self.baseline = np.asarray([self.base[rc] for rc in self.variables_rc], dtype=np.float32)
        self.quantum = common_quantum(self.lo, self.hi)
        self.fixed = frozenset(map(int, fixed_indices))
        if any(i < 0 or i >= n for i in self.fixed):
            raise ModelError("fixed index outside variables")

        self.var_lb: list[float] = []
        self.var_ub: list[float] = []
        self.integrality: list[int] = []
        self.objective: list[float] = []
        self.var_names: list[str] = []
        self.rows: list[tuple[dict[int, Fraction], object, object, str]] = []
        self.exprs: list[VarExpr] = []
        self.t_indices: dict[int, int] = {}
        self._build_domains()
        self._build_sign_rows()
        self._build_crossing_rows()
        self._build_d8_rows()
        self._build_l1_objective()

    def _new_var(self, name: str, lb: float, ub: float, integer: bool, cost: float = 0.0) -> int:
        i = len(self.var_lb)
        self.var_lb.append(float(lb)); self.var_ub.append(float(ub))
        self.integrality.append(1 if integer else 0)
        self.objective.append(float(cost)); self.var_names.append(name)
        return i

    def _add_row(self, coeffs: dict[int, Fraction | int], lb, ub, name: str):
        co = {int(i): (v if isinstance(v, Fraction) else Fraction(int(v))) for i, v in coeffs.items() if v != 0}
        self.rows.append((co, lb, ub, name))

    def _add_ge(self, coeffs: dict[int, Fraction | int], rhs: Fraction | int, name: str):
        self._add_row(coeffs, rhs, math.inf, name)

    def _add_le(self, coeffs: dict[int, Fraction | int], rhs: Fraction | int, name: str):
        self._add_row(coeffs, -math.inf, rhs, name)

    def _add_eq(self, coeffs: dict[int, Fraction | int], rhs: Fraction | int, name: str):
        self._add_row(coeffs, rhs, rhs, name)

    def _build_domains(self):
        q = self.quantum
        for i, rc in enumerate(self.variables_rc):
            b = self.baseline[i]
            if not (self.lo[i] <= b <= self.hi[i]):
                raise ModelError(f"baseline outside inward bounds at variable {i}")
            bq = (frac_f32(b) / q)
            loq = frac_f32(self.lo[i]) / q
            hiq = frac_f32(self.hi[i]) / q
            if any(v.denominator != 1 for v in (bq, loq, hiq)):
                raise ModelError("B/lo/hi not exactly aligned to common quantum")
            segs = decompose_f32_interval(self.lo[i], self.hi[i], b, q)
            if i in self.fixed:
                self.exprs.append(VarExpr(0, {}, segs))
                continue
            if len(segs) == 1:
                seg = segs[0]
                k = self._new_var(f"k_{i}_e{seg.exponent_field}", 0, seg.count - 1, True)
                self.exprs.append(VarExpr(seg.first_m, {k: seg.stride_m}, segs))
            else:
                terms: dict[int, int] = {}
                z_indices = []
                for j, seg in enumerate(segs):
                    z = self._new_var(f"z_{i}_e{seg.exponent_field}", 0, 1, True)
                    k = self._new_var(f"k_{i}_e{seg.exponent_field}", 0, seg.count - 1, True)
                    z_indices.append(z)
                    terms[z] = seg.first_m
                    terms[k] = seg.stride_m
                    self._add_le({k: 1, z: -(seg.count - 1)}, 0, f"bin_gate_hi:{i}:{j}")
                self._add_eq({z: 1 for z in z_indices}, 1, f"one_binade:{i}")
                self.exprs.append(VarExpr(0, terms, segs))

    def _expr_for_rc(self, rc):
        rc = tuple(map(int, rc))
        i = self.var_by_rc.get(rc)
        if i is None:
            if not (0 <= rc[0] < self.base.shape[0] and 0 <= rc[1] < self.base.shape[1]):
                raise ModelError(f"constraint endpoint outside baseline context: {rc}")
            return VarExpr(0, {}, ())
        return self.exprs[i]

    @staticmethod
    def _merge_expr_row(row: dict[int, Fraction], expr: VarExpr, factor: Fraction):
        for j, value in expr.terms.items():
            row[j] = row.get(j, Fraction(0)) + factor * value
        return factor * expr.constant

    def _build_sign_rows(self):
        for si, spec in enumerate(self.signs):
            if spec.sign not in (-1, 0, 1):
                raise ModelError(f"invalid sign {spec.sign}")
            rc = tuple(map(int, spec.rc))
            idx = self.var_by_rc.get(rc)
            b = frac_f32(self.base[rc]) if idx is None else frac_f32(self.baseline[idx])
            if spec.sign == 0:
                if spec.baseline is None:
                    raise ModelError("baseline-contact sign lacks its exact float32 pin")
                target = frac_f32(spec.baseline)
                if idx is None:
                    if b != target:
                        raise ModelError(f"fixed contact sign fails at {rc}")
                else:
                    delta = (target - b) / self.quantum
                    if delta.denominator != 1:
                        raise ModelError("contact pin is off common lattice")
                    expr = self.exprs[idx]
                    row = {j: Fraction(v) for j, v in expr.terms.items()}
                    self._add_eq(row, int(delta) - expr.constant, f"sign_contact:{si}")
                continue
            if idx is None:
                ok = (b > spec.level) if spec.sign > 0 else (b < spec.level)
                if not ok:
                    raise ModelError(f"fixed sign row fails: {spec.source}")
                continue
            threshold = np.float32(float(spec.level))
            direction = np.float32(np.inf if spec.sign > 0 else -np.inf)
            for _ in range(8):
                f = frac_f32(threshold)
                if (spec.sign > 0 and f > spec.level) or (spec.sign < 0 and f < spec.level):
                    break
                threshold = np.nextafter(threshold, direction, dtype=np.float32)
            else:
                raise ModelError("could not find strict float32 sign threshold")
            delta = (frac_f32(threshold) - b) / self.quantum
            if delta.denominator != 1:
                raise ModelError("strict sign threshold is off common lattice")
            expr = self.exprs[idx]
            row = {j: Fraction(v) for j, v in expr.terms.items()}
            if spec.sign > 0:
                self._add_ge(row, int(delta) - expr.constant, f"sign_above:{si}")
            else:
                self._add_le(row, int(delta) - expr.constant, f"sign_below:{si}")

    def _build_crossing_rows(self):
        q = self.quantum
        for ci, spec in enumerate(self.crossings):
            if spec.dry_endpoint not in (0, 1):
                raise ModelError("dry_endpoint must be 0 or 1")
            endpoints = [spec.a_rc, spec.b_rc]
            levels = [spec.level_a, spec.level_b]
            di = spec.dry_endpoint; wi = 1 - di
            dry_rc, wet_rc = endpoints[di], endpoints[wi]
            dry_level, wet_level = levels[di], levels[wi]
            bd = frac_f32(self.base[dry_rc]); bw = frac_f32(self.base[wet_rc])
            ed = self._expr_for_rc(dry_rc); ew = self._expr_for_rc(wet_rc)
            self._add_strict_sign(dry_rc, dry_level, +1, f"cross_dry:{ci}")
            self._add_strict_sign(wet_rc, wet_level, -1, f"cross_wet:{ci}")
            for side, t, cd, cw in (
                ("lower", spec.t_lower, 1 - spec.t_lower, spec.t_lower),
                ("upper", spec.t_upper, -(1 - spec.t_upper), -spec.t_upper),
            ):
                const = (cd * (bd - dry_level) + cw * (bw - wet_level)) / q
                row: dict[int, Fraction] = {}
                const += self._merge_expr_row(row, ed, cd)
                const += self._merge_expr_row(row, ew, cw)
                # All shoreline rows are scaled to the common ULP quantum. The
                # source coefficients stay Fraction until the final HiGHS float64 boundary.
                self._add_ge(row, -const, f"cross:{ci}:{spec.source}:{side}:ulp")

    def _add_strict_sign(self, rc, level: Fraction, sign: int, name: str):
        rc = tuple(map(int, rc))
        idx = self.var_by_rc.get(rc)
        if idx is None:
            value = frac_f32(self.base[rc])
            if not ((sign > 0 and value > level) or (sign < 0 and value < level)):
                raise ModelError(f"fixed crossing endpoint does not have strict sign: {name}")
            return
        b = frac_f32(self.baseline[idx])
        threshold = np.float32(float(level))
        direction = np.float32(np.inf if sign > 0 else -np.inf)
        for _ in range(8):
            value = frac_f32(threshold)
            if (sign > 0 and value > level) or (sign < 0 and value < level):
                break
            threshold = np.nextafter(threshold, direction, dtype=np.float32)
        else:
            raise ModelError(f"could not find strict crossing threshold: {name}")
        delta = (frac_f32(threshold) - b) / self.quantum
        if delta.denominator != 1:
            raise ModelError(f"strict crossing threshold off common lattice: {name}")
        expr = self.exprs[idx]
        row = {j: Fraction(v) for j, v in expr.terms.items()}
        if sign > 0:
            self._add_ge(row, int(delta) - expr.constant, name)
        else:
            self._add_le(row, int(delta) - expr.constant, name)

    def _build_d8_rows(self):
        q = self.quantum
        for di, (center_rc, witness_rc) in enumerate(self.d8_witnesses):
            ec = self._expr_for_rc(center_rc); ew = self._expr_for_rc(witness_rc)
            bc = frac_f32(self.base[center_rc]); bw = frac_f32(self.base[witness_rc])
            row: dict[int, Fraction] = {}
            const = (bc - bw) / q
            const += self._merge_expr_row(row, ec, Fraction(1))
            const += self._merge_expr_row(row, ew, Fraction(-1))
            if const.denominator != 1:
                raise ModelError("D8 row is not integer in common ULP units")
            self._add_ge(row, -const, f"d8:{di}")

    def _build_l1_objective(self):
        q = self.quantum
        self.l1_constant = Fraction(0)
        for i, expr in enumerate(self.exprs):
            b = frac_f32(self.baseline[i])
            target = (Fraction.from_float(float(self.x64[i])) - b) / q
            if not expr.terms:
                self.l1_constant += abs(Fraction(expr.constant) - target)
                continue
            t = self._new_var(f"abs_l1_{i}", 0.0, math.inf, False, 1.0)
            self.t_indices[i] = t
            # t >= m-target; t >= target-m
            row1 = {t: Fraction(1)}
            row2 = {t: Fraction(1)}
            for j, v in expr.terms.items():
                row1[j] = row1.get(j, Fraction(0)) - v
                row2[j] = row2.get(j, Fraction(0)) + v
            self._add_ge(row1, Fraction(expr.constant) - target, f"l1_pos:{i}")
            self._add_ge(row2, target - Fraction(expr.constant), f"l1_neg:{i}")

    def matrix(self, extra_rows=()):
        rows = [*self.rows, *extra_rows]
        rr=[]; cc=[]; vv=[]; lb=[]; ub=[]; names=[]
        for ri,(coeff,lo,hi,name) in enumerate(rows):
            safe_coeff, safe_lo, safe_hi, _rounding_error = conservative_float_row(
                coeff, lo, hi, tuple(zip(self.var_lb, self.var_ub)))
            for j,fv in safe_coeff.items():
                if not math.isfinite(fv):
                    raise ModelError(f"non-finite linear coefficient in {name}")
                rr.append(ri); cc.append(j); vv.append(fv)
            lb.append(safe_lo); ub.append(safe_hi); names.append(name)
        A=coo_matrix((vv,(rr,cc)),shape=(len(rows),len(self.var_lb))).tocsr()
        return A,np.asarray(lb,float),np.asarray(ub,float),names

    def _run(self, objective, extra_rows, deadline, remaining_nodes):
        A,lb,ub,_=self.matrix(extra_rows)
        remaining = deadline - time.monotonic()
        if remaining <= 0 or remaining_nodes <= 0:
            raise NoCanonicalOptimum("global time/node budget exhausted before MILP call")
        return milp(np.asarray(objective,float),integrality=np.asarray(self.integrality,np.int32),
                    bounds=Bounds(np.asarray(self.var_lb,float),np.asarray(self.var_ub,float)),
                    constraints=LinearConstraint(A,lb,ub),
                    options={"time_limit":remaining,"node_limit":remaining_nodes,
                             "mip_rel_gap":0.0,"presolve":True,"disp":False})

    def _decode_m(self, result):
        if result.x is None:
            raise NoCanonicalOptimum("MILP produced no incumbent")
        vals=np.asarray(result.x,float)
        m=[]
        for expr in self.exprs:
            v=Fraction(expr.constant)
            for j,c in expr.terms.items():
                rounded=int(round(vals[j]))
                if abs(vals[j]-rounded)>1e-5:
                    raise NoCanonicalOptimum("integer auxiliary is not integral in returned incumbent")
                v += c*rounded
            if v.denominator != 1:
                raise ModelError("decoded lattice offset is not integer")
            m.append(int(v))
        return np.asarray(m,dtype=np.int64)

    def decode_f32(self, m):
        out=self.base.copy()
        for i,(rc,mi) in enumerate(zip(self.variables_rc,m)):
            value=frac_f32(self.baseline[i])+self.quantum*int(mi)
            f=np.float32(float(value))
            if frac_f32(f)!=value:
                raise NoCanonicalOptimum("integer model decoded to a non-representable float32 value")
            out[rc]=f
        return out

    def exact_l1_units(self,m):
        return sum((abs(Fraction(int(mi))-(Fraction.from_float(float(self.x64[i]))-
                   frac_f32(self.baseline[i]))/self.quantum) for i,mi in enumerate(m)),Fraction(0))

    def solve_canonical(self, time_limit=60.0, node_limit=1_000_000):
        """Primary L1 solve, then row-major lex tie-break under an exact-cost row.

        The full budget covers both stages. Any timeout, non-optimal status, or
        unrepresentable equality aborts without returning a candidate.
        """
        deadline=time.monotonic()+float(time_limit); nodes_left=int(node_limit); nodes_used=0
        primary=self._run(self.objective,(),deadline,nodes_left)
        if time.monotonic() > deadline:
            raise NoCanonicalOptimum("global time budget expired during primary MILP")
        if primary.status != 0 or primary.x is None or getattr(primary,"mip_gap",None) not in (0,0.0):
            raise NoCanonicalOptimum(f"primary MILP not proven optimal: status={primary.status}, gap={getattr(primary,'mip_gap',None)}")
        nodes_used += int(getattr(primary,"mip_node_count",0) or 0); nodes_left -= int(getattr(primary,"mip_node_count",0) or 0)
        m=self._decode_m(primary); exact_cost=self.exact_l1_units(m)
        # Verify the primary objective returned by HiGHS is the exact L1 value
        # in ULP units. The equality is only used when binary64 can encode it exactly.
        if Fraction.from_float(float(exact_cost)) != exact_cost:
            raise NoCanonicalOptimum("exact L1 optimum cannot be represented exactly by the MILP tie row")
        cost_coeff={j:Fraction(1) for j in self.t_indices.values()}
        cost_rhs=exact_cost-self.l1_constant
        if cost_rhs < 0:
            raise NoCanonicalOptimum("exact primary cost is below fixed-node objective")
        if Fraction.from_float(float(cost_rhs)) != cost_rhs:
            raise NoCanonicalOptimum("variable L1 tie row is not exactly representable in binary64")
        tie_rows=[]
        if cost_coeff:
            v=float(cost_rhs)
            self._add_extra_eq = (cost_coeff,v,v,"exact_l1_optimum")
            tie_rows.append(self._add_extra_eq)
        previous=[]
        # Skip variables with no decision expression; otherwise fix the smallest
        # row-major lattice offset among exactly equal L1 optima.
        for i,expr in enumerate(self.exprs):
            if not expr.terms:
                continue
            objective=[0.0]*len(self.var_lb)
            for j,c in expr.terms.items(): objective[j]=float(c)
            result=self._run(objective,tuple(tie_rows+previous),deadline,nodes_left)
            if time.monotonic() > deadline:
                raise NoCanonicalOptimum(f"global time budget expired during lex tie stage {i}")
            if result.status != 0 or result.x is None or getattr(result,"mip_gap",None) not in (0,0.0):
                raise NoCanonicalOptimum(f"lex tie stage {i} incomplete: status={result.status}")
            used=int(getattr(result,"mip_node_count",0) or 0); nodes_used+=used; nodes_left-=used
            m_now=self._decode_m(result)
            if self.exact_l1_units(m_now)!=exact_cost:
                raise NoCanonicalOptimum("lex tie stage changed exact primary L1 objective")
            previous.append(({j:Fraction(c) for j,c in expr.terms.items()},
                             float(m_now[i]-expr.constant),float(m_now[i]-expr.constant),f"lex_fix:{i}"))
            m=m_now
        grid=self.decode_f32(m)
        if time.monotonic() > deadline:
            raise NoCanonicalOptimum("global time budget expired before candidate return")
        gates=self.exact_gates(grid)
        if not all(gates.values()):
            raise NoCanonicalOptimum(f"decoded float32 incumbent failed exact gates: {gates}")
        return {"grid":grid,"m":m,"exact_l1_units":str(exact_cost),"primary":primary,
                "nodes_used":nodes_used,"remaining_seconds":max(0.0,deadline-time.monotonic()),
                "exact_gates":gates}

    def exact_gates(self, grid):
        grid=np.asarray(grid,dtype=np.float32)
        result={"shape":grid.shape==self.base.shape,"fixed":True,"bounds":True,"signs":True,"crossings":True,"d8":True}
        for i,rc in enumerate(self.variables_rc):
            if i in self.fixed and bits_f32(grid[rc])!=bits_f32(self.baseline[i]): result["fixed"]=False
            if not (self.lo[i]<=grid[rc]<=self.hi[i]): result["bounds"]=False
        for spec in self.signs:
            h=frac_f32(grid[spec.rc])
            if spec.sign>0 and not h>spec.level: result["signs"]=False
            elif spec.sign<0 and not h<spec.level: result["signs"]=False
            elif spec.sign==0 and (spec.baseline is None or bits_f32(grid[spec.rc])!=bits_f32(spec.baseline)):
                result["signs"]=False
        for spec in self.crossings:
            ha=frac_f32(grid[spec.a_rc]); hb=frac_f32(grid[spec.b_rc])
            da=ha-spec.level_a; db=hb-spec.level_b
            if da*db>=0:
                result["crossings"]=False; continue
            t=da/(da-db)
            oriented=t if spec.dry_endpoint==0 else 1-t
            if not (spec.t_lower<=oriented<=spec.t_upper): result["crossings"]=False
        for center,witness in self.d8_witnesses:
            if frac_f32(grid[center])<frac_f32(grid[witness]): result["d8"]=False
        return result


def exact_integer_row(coefficients: dict[int, Fraction], rhs: Fraction):
    """Scale an exact rational row to primitive integers, or refuse >2**53."""
    den=math.lcm(*(v.denominator for v in coefficients.values()),rhs.denominator)
    values={i:int(v*den) for i,v in coefficients.items()}
    r=int(rhs*den)
    g=0
    for v in (*values.values(),r): g=math.gcd(g,abs(v))
    if g: values={i:v//g for i,v in values.items()}; r//=g
    if max((abs(v).bit_length() for v in (*values.values(),r)),default=0)>53:
        raise ModelError("primitive exact integer row exceeds binary64 exact-integer range")
    return values,r
