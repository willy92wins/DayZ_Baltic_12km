"""EV93 one-axis crest policy; no terrain authoring or solver execution."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
import hashlib
import math
import re
from typing import Any, Mapping, Sequence

import numpy as np

POLICY_ID = "ev93-crest-one-active-axis-v1"
EXPECTED_PINS = {
    "baseline_sha256": "f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0",
    "policy_plan_sha256": "ba9245134a368870bb4e0090ff36f3c1b91b26b5bc8756d8f0fbf48ddb04ccce",
    "ev92_sha256": "87b5ee5ee95318f1a8026c4a7459aa06d27c9b69db80f34ad25149293d5fc1df",
    "shape_contract_sha256": "8cd9d0fbea03c05e5ae53a31676d79ec2364be83c055213446f6c8599245d533",
}
LEGACY_FOCUS_GATE = "focus_positive_prominence_reduced_25pct_both_axes"
NEW_FOCUS_GATE = "focus_active_axes_reduced_25pct_inactive_axes_zero"
EXPECTED_SOURCE_REASON = (
    "final gate scalar interpolation rule unavailable: "
    "baseline focus is not prominent on both axes"
)
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


class PolicyReject(ValueError):
    """A direction cannot yield a material alpha under this frozen rule."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Provenance:
    queue_id: int
    center_rc: tuple[int, int]
    baseline_sha256: str
    prepared_sha256: str
    result_sha256: str
    solution_sha256: str
    policy_plan_sha256: str
    ev92_sha256: str
    shape_contract_sha256: str
    policy_module_sha256: str
    source_rejection_reason: str

    def validate(self) -> None:
        if isinstance(self.queue_id, bool) or int(self.queue_id) != self.queue_id or self.queue_id < 0:
            raise ValueError("queue_id must be a nonnegative integer")
        if len(self.center_rc) != 2 or any(isinstance(v, bool) or int(v) != v for v in self.center_rc):
            raise ValueError("center_rc must contain exact integer indices")
        values = asdict(self)
        keys = (
            "baseline_sha256", "prepared_sha256", "result_sha256", "solution_sha256",
            "policy_plan_sha256", "ev92_sha256", "shape_contract_sha256", "policy_module_sha256",
        )
        for key in keys:
            value = values[key]
            if not isinstance(value, str) or not _HASH_RE.fullmatch(value.lower()):
                raise ValueError(f"{key} must be a 64-digit SHA-256")
        for key, expected in EXPECTED_PINS.items():
            if values[key] != expected:
                raise ValueError(f"stale or unexpected pinned source: {key}")
        if self.source_rejection_reason != EXPECTED_SOURCE_REASON:
            raise ValueError("source is not the exact EV92 one-axis prominence rejection")


def _f32(value: float | np.float32) -> Fraction:
    return Fraction.from_float(float(np.float32(value)))


def _ratio(x: Fraction) -> dict[str, Any]:
    return {"fraction": f"{x.numerator}/{x.denominator}", "float64": float(x)}


def _sublevel_interval(intercept: Fraction, slope: Fraction) -> tuple[Fraction, Fraction] | None:
    """Closed alpha subset [0,1] where intercept+slope*alpha <= 0."""
    zero, one = Fraction(0), Fraction(1)
    if slope == 0:
        return (zero, one) if intercept <= 0 else None
    crossing = -intercept / slope
    if slope > 0:
        if crossing < 0:
            return None
        return zero, min(one, crossing)
    if crossing > 1:
        return None
    return max(zero, crossing), one


def _component_reaching_one(
    intervals: Sequence[tuple[Fraction, Fraction] | None],
) -> tuple[Fraction, Fraction] | None:
    """Connected component of the interval union that contains alpha=1."""
    merged: list[list[Fraction]] = []
    valid = sorted((x for x in intervals if x is not None), key=lambda x: (x[0], x[1]))
    for lo, hi in valid:
        if not merged or lo > merged[-1][1]:
            merged.append([lo, hi])
        elif hi > merged[-1][1]:
            merged[-1][1] = hi
    for lo, hi in reversed(merged):
        if hi == 1:
            return lo, hi
    return None


def _neighbors(focus: tuple[int, int], axis: str) -> tuple[tuple[int, int], tuple[int, int]]:
    r, c = focus
    if axis == "EW":
        return (r, c - 1), (r, c + 1)
    if axis == "NS":
        return (r - 1, c), (r + 1, c)
    raise ValueError(f"unknown axis {axis!r}")


def _grid_sha(a: np.ndarray) -> str:
    canonical = np.asarray(a, dtype="<f4", order="C")
    return hashlib.sha256(canonical.tobytes(order="C")).hexdigest()


def _grids(base: np.ndarray, direction: np.ndarray, focus_rc: tuple[int, int]):
    b, h = np.asarray(base), np.asarray(direction)
    if b.dtype != np.float32 or h.dtype != np.float32 or b.ndim != 2 or b.shape != h.shape:
        raise ValueError("B and H must be matching float32 2D grids")
    if not np.isfinite(b).all() or not np.isfinite(h).all():
        raise ValueError("B and H must contain finite heights")
    r, c = map(int, focus_rc)
    if r <= 0 or c <= 0 or r >= b.shape[0] - 1 or c >= b.shape[1] - 1:
        raise ValueError("focus needs all four cardinal neighbors")
    return b, h, (r, c)


def _cardinals(values: Sequence[float] | np.ndarray, name: str) -> tuple[Fraction, ...]:
    array = np.asarray(values)
    if array.dtype != np.float32 or array.shape != (5,) or not np.isfinite(array).all():
        raise ValueError(f"{name} must be five finite float32 values ordered center,W,E,N,S")
    return tuple(_f32(x) for x in array)


def _prominence_values(values: tuple[Fraction, ...], axis: str) -> Fraction:
    n1, n2 = (1, 2) if axis == "EW" else (3, 4)
    return max(Fraction(0), values[0] - max(values[n1], values[n2]))


def _axis_tail_values(base: tuple[Fraction, ...], direction: tuple[Fraction, ...], axis: str,
                      target: Fraction) -> tuple[Fraction, Fraction] | None:
    neighbor_ids = (1, 2) if axis == "EW" else (3, 4)
    b_center = base[0]
    h_center = direction[0]
    center_delta = h_center - b_center
    intervals = []
    for index in neighbor_ids:
        b_diff = b_center - base[index]
        neighbor_delta = direction[index] - base[index]
        slope = center_delta - neighbor_delta
        intervals.append(_sublevel_interval(b_diff - target, slope))
    return _component_reaching_one(intervals)


def _derive_from_cardinals(base_values, direction_values, *, alpha_energy, provenance, legacy_rule):
    b = _cardinals(base_values, "baseline cardinals")
    h = _cardinals(direction_values, "direction cardinals")
    if not math.isfinite(float(alpha_energy)) or not 0 < float(alpha_energy) < 1:
        raise PolicyReject("invalid_energy_lower", "EV92 alpha_energy must be in (0,1)")
    prominences = {axis: _prominence_values(b, axis) for axis in ("EW", "NS")}
    active_count = sum(p > 0 for p in prominences.values())
    if active_count == 0:
        raise PolicyReject("no_active_axis", "neither cardinal axis has positive baseline prominence")

    axes: dict[str, Any] = {
        axis: {
            "active": prominences[axis] > 0,
            "prominence_B_m": _ratio(prominences[axis]),
            "maximum_prominence_H_m": _ratio(Fraction(3, 4) * prominences[axis]
                                                if prominences[axis] > 0 else Fraction(0)),
        }
        for axis in ("EW", "NS")
    }

    provenance_map = asdict(provenance)
    if active_count == 2:
        if not isinstance(legacy_rule, Mapping):
            raise PolicyReject("legacy_rule_required", "both-active case requires the original EV92 scalar rule")
        try:
            legacy_alpha = float(legacy_rule["alpha"])
            legacy_energy = float(legacy_rule["energy_lower"])
            focus_bounds = legacy_rule["focus_lower_by_axis"]
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("legacy EV92 rule is missing alpha, energy_lower, or axis focus bounds") from exc
        if not (0 < legacy_alpha < 1 and 0 < legacy_energy < 1):
            raise ValueError("legacy EV92 alpha and energy lower root must be in (0,1)")
        if legacy_energy != float(alpha_energy) or not {"EW", "NS"}.issubset(focus_bounds):
            raise ValueError("legacy EV92 rule does not match supplied energy root/axes")
        result = dict(legacy_rule)
        result.update({
            "policy_id": POLICY_ID, "policy_mode": "legacy_both_axes_bit_exact",
            "provenance": provenance_map, "focus_rc": list(provenance.center_rc),
            "axes": axes, "alpha_energy": float(alpha_energy), "alpha_midpoint": legacy_alpha,
            "baseline_cardinals_sha256": _values_sha(b),
            "direction_cardinals_sha256": _values_sha(h),
            "note": "Both axes active: original EV92 alpha and scalar fields passed through unchanged.",
        })
        return result

    # The affine tail policy is a narrowly scoped replacement for exactly one
    # positive baseline axis. Do not impose its alpha=1 component condition on
    # two-axis cases: those retain the original EV92 scalar rule unchanged.
    tails: dict[str, tuple[Fraction, Fraction]] = {}
    for axis in ("EW", "NS"):
        target = Fraction(3, 4) * prominences[axis] if prominences[axis] > 0 else Fraction(0)
        tail = _axis_tail_values(b, h, axis, target)
        if tail is None:
            raise PolicyReject("no_tail_to_one", f"{axis} constraint has no feasible component reaching alpha=1")
        tails[axis] = tail
        axes[axis]["tail_alpha"] = {"start": _ratio(tail[0]), "end": _ratio(tail[1])}

    alpha_e = Fraction.from_float(float(alpha_energy))
    alpha_start = max(alpha_e, tails["EW"][0], tails["NS"][0])
    if alpha_start >= 1:
        raise PolicyReject("zero_width_tail", "common feasible tail has zero width at alpha=1")
    alpha_fraction = (alpha_start + 1) / 2
    alpha = float(alpha_fraction)
    if not 0 < alpha < 1:
        raise PolicyReject("nonmaterial_alpha", "midpoint is not strictly inside (0,1)")
    return {
        "policy_id": POLICY_ID, "policy_mode": "one_active_axis_affine_tail",
        "provenance": provenance_map, "focus_rc": list(provenance.center_rc), "axes": axes,
        "alpha_energy": float(alpha_energy), "common_tail_start": _ratio(alpha_start),
        "common_tail_end": "1/1", "alpha_midpoint": alpha,
        "alpha_midpoint_fraction": _ratio(alpha_fraction),
        "baseline_cardinals_sha256": _values_sha(b),
        "direction_cardinals_sha256": _values_sha(h),
        "rule": "midpoint of [max(EV92 alpha_energy, EW tail start, NS tail start), 1]",
        "note": "Scalar derivation only; cast float32 and rerun every original local/global gate.",
    }


def _values_sha(values: Sequence[Fraction]) -> str:
    arr = np.asarray([float(x) for x in values], dtype="<f4")
    return hashlib.sha256(arr.tobytes()).hexdigest()


def _grid_cardinals(grid: np.ndarray, focus: tuple[int, int]) -> np.ndarray:
    r, c = focus
    return np.asarray([grid[r, c], grid[r, c - 1], grid[r, c + 1], grid[r - 1, c], grid[r + 1, c]],
                      dtype=np.float32)


def energy_lower_from_moments(moments: Sequence[Fraction]) -> float:
    """EV92 stable lower root from already-computed exact q0/q1/q2 moments."""
    if len(moments) != 3 or any(not isinstance(x, Fraction) for x in moments):
        raise ValueError("moments must be the three exact EV92 Fractions q0/q1/q2")
    q0, q1, q2 = moments
    if not (q0 > 0 and q2 > 0 and q1 < 0 and q0 + q1 + q2 <= Fraction(3, 4) * q0):
        raise PolicyReject("energy_conditions", "EV92 direction misses its pinned energy conditions")
    k0, k1, k2 = map(float, moments)
    discriminant = k1 * k1 - k2 * k0
    if not discriminant > 0:
        raise PolicyReject("energy_discriminant", "EV92 energy polynomial has no positive discriminant")
    lower = (k0 / 2.0) / (-k1 + math.sqrt(discriminant))
    if not math.isfinite(lower) or not 0 < lower < 1:
        raise PolicyReject("energy_lower", "EV92 energy lower root is outside (0,1)")
    return lower


def derive_scalar_rule_from_cardinals(
    base_values: Sequence[float] | np.ndarray,
    direction_values: Sequence[float] | np.ndarray,
    *,
    alpha_energy: float,
    provenance: Provenance,
    legacy_rule: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Local-artifact API with cardinals ordered [center,W,E,N,S], all float32."""
    provenance.validate()
    return _derive_from_cardinals(base_values, direction_values, alpha_energy=alpha_energy,
                                  provenance=provenance, legacy_rule=legacy_rule)


def derive_scalar_rule(
    base: np.ndarray,
    direction: np.ndarray,
    *,
    focus_rc: tuple[int, int],
    alpha_energy: float,
    provenance: Provenance,
    legacy_rule: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Derive alpha while preserving EV92 bit-exact behavior for two active axes.

    alpha_energy must come from the unchanged EV92 exact-moment calculation;
    this helper does not recalculate or relax that energy gate. If both axes
    are active, the caller must provide the exact EV92 legacy rule so its alpha
    and fields pass through unchanged.
    """
    provenance.validate()
    b, h, focus = _grids(base, direction, focus_rc)
    if tuple(focus) != tuple(provenance.center_rc):
        raise ValueError("focus differs from provenance center")
    result = _derive_from_cardinals(_grid_cardinals(b, focus), _grid_cardinals(h, focus),
                                    alpha_energy=alpha_energy, provenance=provenance,
                                    legacy_rule=legacy_rule)
    result["baseline_height_grid_sha256"] = _grid_sha(b)
    result["direction_height_grid_sha256"] = _grid_sha(h)
    return result


def interpolate_float32(base: np.ndarray, direction: np.ndarray, alpha: float) -> np.ndarray:
    """Match the EV92 float64 interpolation operation order and one float32 cast."""
    b, h = np.asarray(base), np.asarray(direction)
    if b.dtype != np.float32 or h.dtype != np.float32 or b.shape != h.shape:
        raise ValueError("B and H must be matching float32 grids")
    if not math.isfinite(float(alpha)) or not 0 < float(alpha) < 1:
        raise ValueError("alpha must be strictly between zero and one")
    return np.asarray(b.astype(np.float64) + float(alpha) * (h.astype(np.float64) - b.astype(np.float64)),
                      dtype=np.float32)


def evaluate_focus_after_cardinals(base_values: Sequence[float] | np.ndarray,
                                   after_values: Sequence[float] | np.ndarray) -> dict[str, Any]:
    """Check the revised predicate on [center,W,E,N,S] float32 post-cast values."""
    b, h = _cardinals(base_values, "baseline cardinals"), _cardinals(after_values, "after cardinals")
    axes: dict[str, Any] = {}
    for axis in ("EW", "NS"):
        p_b, p_h = _prominence_values(b, axis), _prominence_values(h, axis)
        active = p_b > 0
        limit = Fraction(3, 4) * p_b if active else Fraction(0)
        axes[axis] = {
            "active": active,
            "prominence_B_m": _ratio(p_b),
            "prominence_H_m": _ratio(p_h),
            "maximum_allowed_H_m": _ratio(limit),
            "pass": p_h <= limit,
        }
    return {
        "gate": NEW_FOCUS_GATE,
        "pass": all(x["pass"] for x in axes.values()) and any(x["active"] for x in axes.values()),
        "axes": axes,
        "evaluated_values_dtype": "float32",
    }


def evaluate_focus_after(base: np.ndarray, after: np.ndarray, *, focus_rc: tuple[int, int]) -> dict[str, Any]:
    """Grid wrapper for the same post-cast cardinal predicate."""
    b, h, focus = _grids(base, after, focus_rc)
    result = evaluate_focus_after_cardinals(_grid_cardinals(b, focus), _grid_cardinals(h, focus))
    result["focus_rc"] = list(focus)
    result["evaluated_grid_dtype"] = str(h.dtype)
    return result


def replace_focus_gate(shape_report: Mapping[str, Any], focus_report: Mapping[str, Any]) -> dict[str, Any]:
    """Replace only legacy focus gate; preserve all other original shape gates."""
    if not isinstance(shape_report, Mapping) or not isinstance(shape_report.get("gates"), Mapping):
        raise ValueError("shape report must contain gates mapping")
    if LEGACY_FOCUS_GATE not in shape_report["gates"]:
        raise ValueError(f"missing expected legacy gate {LEGACY_FOCUS_GATE}")
    if focus_report.get("gate") != NEW_FOCUS_GATE or not isinstance(focus_report.get("pass"), bool):
        raise ValueError("focus report schema does not match crest policy")
    result = dict(shape_report)
    gates = dict(shape_report["gates"])
    old = gates.pop(LEGACY_FOCUS_GATE)
    gates[NEW_FOCUS_GATE] = focus_report["pass"]
    result["gates"] = gates
    result["superseded_focus_gate"] = {
        "name": LEGACY_FOCUS_GATE, "diagnostic_value": old, "replaced_by": NEW_FOCUS_GATE,
    }
    result["crest_focus_policy"] = dict(focus_report)
    return result
