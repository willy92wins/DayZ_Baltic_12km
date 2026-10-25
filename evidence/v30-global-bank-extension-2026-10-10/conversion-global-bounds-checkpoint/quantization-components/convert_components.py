from __future__ import annotations

import argparse
from collections import deque
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time
from typing import Callable, Iterable

import numpy as np

PILOT = Path(r"E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/G/wet-bank-pilot")
HERE = PILOT / "postsolve-consumer/float32-component-conversion-v1"
PLAN = HERE / "PLAN.md"
TESTS = HERE / "test_components.py"
OLD = PILOT / "postsolve-consumer/float32-neighborhood-v1"
EXECUTOR = OLD / "executor.py"
COMPAT_DIAG = OLD / "real-enumeration-01/compatibility-diagnostic.json"
OUT = HERE / "real-conversion-01"
EXPECTED_EXECUTOR_SHA = "9a0dbffc55e9956209083fe4963e2636b6f0174de1dc150bdfa15f070d48149e"
EXPECTED_COMPAT_DIAG_SHA = "0cb852c2aa3bdd99e7b1dbdfb079df5f9faa65c3db854a3ff1389b25d8b53da7"
STEPS = (-1, 0, 1)
STEP_INDEX = {step: i for i, step in enumerate(STEPS)}
ALL_OPTIONS = 0b111
MAX_SECONDS = 120.0
MAX_PEAK_WS_BYTES = 1_073_741_824
MAX_SEARCH_NODES = 1_000_000


@dataclass(frozen=True)
class UnaryConstraint:
    variable: int
    allowed_mask: int
    kind: str
    source: str
    endpoints_rc: tuple[tuple[int, int], ...] = ()


@dataclass(frozen=True)
class BinaryConstraint:
    a: int
    b: int
    table: tuple[tuple[bool, bool, bool], tuple[bool, bool, bool], tuple[bool, bool, bool]]
    kind: str
    source: str
    endpoints_rc: tuple[tuple[int, int], tuple[int, int]]


class ConversionStop(RuntimeError):
    def __init__(self, status: str, message: str):
        super().__init__(message)
        self.status = status


def check_deadline(deadline: float | None, phase: str):
    if deadline is not None and time.monotonic() >= deadline:
        raise ConversionStop("TIME_LIMIT", f"numeric deadline reached during {phase}")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def sha_map(paths: Iterable[Path]) -> dict[str, str]:
    return {str(Path(p).resolve()): sha256(Path(p)) for p in paths}


def load_executor():
    actual = sha256(EXECUTOR)
    if actual != EXPECTED_EXECUTOR_SHA:
        raise ConversionStop("SOURCE_PIN_MISMATCH", f"frozen executor SHA mismatch: {actual}")
    spec = importlib.util.spec_from_file_location("wet_bank_frozen_executor", EXECUTOR)
    if spec is None or spec.loader is None:
        raise ConversionStop("SOURCE_LOAD_ERROR", "could not load frozen wet-bank executor")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def bit_options(mask: int) -> tuple[int, ...]:
    return tuple(i for i in range(3) if mask & (1 << i))


def mask_of(options: Iterable[int]) -> int:
    result = 0
    for option in options:
        if option not in (0, 1, 2):
            raise ValueError(f"invalid option index {option}")
        result |= 1 << option
    return result


def strict_sign_mask(values, level: Fraction, sign: int, baseline: np.float32 | None = None) -> int:
    """Exact P/F unary sign rule on the binary32 option values."""
    if sign not in (-1, 0, 1):
        raise ValueError("sign must be -1, 0, or +1")
    if sign == 0 and baseline is None:
        raise ValueError("baseline-contact sign requires its frozen float32 value")
    allowed = []
    for i, value in enumerate(values):
        value32 = np.float32(value)
        exact = Fraction.from_float(float(value32))
        if sign > 0 and exact > level:
            allowed.append(i)
        elif sign < 0 and exact < level:
            allowed.append(i)
        elif sign == 0 and value32.view(np.uint32) == np.float32(baseline).view(np.uint32):
            allowed.append(i)
    return mask_of(allowed)


def raw_failure_seeds(unary: Iterable[UnaryConstraint], relations: Iterable[BinaryConstraint], raw_option: int = 1):
    seeds = set()
    failures = []
    for constraint in unary:
        if not (constraint.allowed_mask & (1 << raw_option)):
            seeds.add(constraint.variable)
            failures.append({"kind": constraint.kind, "source": constraint.source,
                             "variables": [constraint.variable], "endpoints_rc": [list(rc) for rc in constraint.endpoints_rc]})
    for relation in relations:
        if not relation.table[raw_option][raw_option]:
            seeds.update((relation.a, relation.b))
            failures.append({"kind": relation.kind, "source": relation.source,
                             "variables": [relation.a, relation.b],
                             "endpoints_rc": [list(rc) for rc in relation.endpoints_rc]})
    return seeds, failures


def all_true(table) -> bool:
    return all(bool(v) for row in table for v in row)


def table_tuple(table):
    rows = tuple(tuple(bool(v) for v in row) for row in table)
    if len(rows) != 3 or any(len(row) != 3 for row in rows):
        raise ValueError("binary relation table must be exactly 3x3")
    return rows


def bound_option_mask(values, lower, upper) -> int:
    return mask_of(i for i, value in enumerate(values) if np.float32(lower) <= np.float32(value) <= np.float32(upper))


def all_gates_pass(gates: dict[str, bool]) -> bool:
    return bool(gates) and all(value is True for value in gates.values())


def require_fixed_constraint(passed: bool, kind: str, source: str):
    if not passed:
        raise ConversionStop("NO_FEASIBLE_FIXED_CONSTRAINT", f"fixed-only {kind} constraint failed: {source}")


def table_from_predicate(predicate: Callable[[int, int], bool]):
    """Materialize the exact nine option pairs for a binary predicate."""
    return table_tuple([[bool(predicate(a, b)) for b in range(3)] for a in range(3)])


def resolve_edge_variables(a_rc, b_rc, variable_by_rc):
    """Resolve a geometric endpoint pair; missing endpoints remain frozen raw."""
    return variable_by_rc.get(tuple(map(int, a_rc))), variable_by_rc.get(tuple(map(int, b_rc)))


def fraction_crossing_pass(ha, hb, level_a: Fraction, level_b: Fraction,
                           dry_endpoint: int, t_lower: Fraction, t_upper: Fraction) -> bool:
    """Independent exact scalar oracle used by fixtures; inputs are quantized float32 values."""
    a = Fraction.from_float(float(np.float32(ha))) - level_a
    b = Fraction.from_float(float(np.float32(hb))) - level_b
    if a * b >= 0:
        return False
    t = a / (a - b)
    dry_t = t if dry_endpoint == 0 else 1 - t
    return t_lower <= dry_t <= t_upper


def relation_allows(relation: BinaryConstraint, x: int, ox: int, y: int, oy: int) -> bool:
    if x == relation.a and y == relation.b:
        return relation.table[ox][oy]
    if x == relation.b and y == relation.a:
        return relation.table[oy][ox]
    raise ValueError("arc endpoints do not match relation")


def propagate(domains: dict[int, int], relations: tuple[BinaryConstraint, ...],
              subset: set[int] | None = None):
    """AC-3 over bitmask domains; returns (domains, contradiction-record)."""
    arcs = deque()
    by_id = {i: rel for i, rel in enumerate(relations)}
    adjacent: dict[int, list[tuple[int, int]]] = {}
    for rid, rel in by_id.items():
        if subset is not None and (rel.a not in subset or rel.b not in subset):
            continue
        adjacent.setdefault(rel.a, []).append((rid, rel.b))
        adjacent.setdefault(rel.b, []).append((rid, rel.a))
        arcs.append((rid, rel.a, rel.b))
        arcs.append((rid, rel.b, rel.a))

    trace = []
    while arcs:
        rid, xi, xj = arcs.popleft()
        rel = by_id[rid]
        old = domains[xi]
        keep = 0
        for ox in bit_options(old):
            if any(relation_allows(rel, xi, ox, xj, oy) for oy in bit_options(domains[xj])):
                keep |= 1 << ox
        if keep == old:
            continue
        domains[xi] = keep
        trace.append({"variable": xi, "against": xj, "relation": rid,
                      "removed_options": [v for v in bit_options(old) if not (keep & (1 << v))],
                      "remaining": list(bit_options(keep))})
        if keep == 0:
            return domains, {"variable": xi, "against": xj, "relation": rid, "trace": trace}
        for rid2, neighbor in adjacent.get(xi, ()):
            if rid2 != rid:
                arcs.append((rid2, neighbor, xi))
    return domains, {"variable": None, "trace": trace}


def components_from_seeds(variable_count: int, relations: tuple[BinaryConstraint, ...], seeds: set[int]):
    adjacency = [set() for _ in range(variable_count)]
    for rel in relations:
        if not all_true(rel.table):
            adjacency[rel.a].add(rel.b)
            adjacency[rel.b].add(rel.a)
    components = []
    assigned = set()
    for seed in sorted(seeds):
        if seed in assigned:
            continue
        stack = [seed]
        found = set()
        while stack:
            value = stack.pop()
            if value in found:
                continue
            found.add(value)
            stack.extend(adjacency[value] - found)
        assigned |= found
        components.append(tuple(sorted(found)))
    return tuple(components), tuple(tuple(sorted(v)) for v in adjacency)


def component_search(component: tuple[int, ...], domains_in: dict[int, int],
                     relations: tuple[BinaryConstraint, ...], options,
                     x64: np.ndarray, deadline: float, budget: dict[str, int], max_nodes: int):
    members = set(component)
    rels = tuple(r for r in relations if r.a in members and r.b in members and not all_true(r.table))
    degree = {v: sum(1 for r in rels if v in (r.a, r.b)) for v in component}
    best_rank = None
    best_choices = None

    def rank(assign):
        choices = [assign[v] for v in component]
        l1 = sum(abs(STEPS[o]) for o in choices)
        d2 = math.fsum((float(options[v][o]) - float(x64[v])) ** 2 for v, o in zip(component, choices))
        lex = tuple(STEPS[o] for o in choices)
        return (l1, d2, lex)

    def lower_rank(doms):
        lb_l1 = sum(min(abs(STEPS[o]) for o in bit_options(doms[v])) for v in component)
        lb_d2 = math.fsum(min((float(options[v][o]) - float(x64[v])) ** 2 for o in bit_options(doms[v]))
                           for v in component)
        lb_lex = tuple(min(STEPS[o] for o in bit_options(doms[v])) for v in component)
        return (lb_l1, lb_d2, lb_lex)

    def dfs(doms):
        nonlocal best_rank, best_choices
        budget["nodes"] += 1
        if budget["nodes"] > max_nodes:
            raise ConversionStop("SEARCH_LIMIT", f"expanded-node cap {max_nodes} reached")
        if time.monotonic() > deadline:
            raise ConversionStop("TIME_LIMIT", f"numeric deadline {MAX_SECONDS}s reached")
        if budget["nodes"] % 512 == 0:
            ws = budget["executor"].memory_peak_ws_bytes()
            budget["peak_ws"] = max(budget["peak_ws"], ws)
            if ws > MAX_PEAK_WS_BYTES:
                raise ConversionStop("MEMORY_LIMIT", f"peak working set {ws} exceeds cap")
        doms, contradiction = propagate(dict(doms), rels, members)
        if contradiction["variable"] is not None:
            return
        if best_rank is not None and lower_rank(doms) >= best_rank:
            return
        undecided = [v for v in component if doms[v].bit_count() > 1]
        if not undecided:
            assign = {v: bit_options(doms[v])[0] for v in component}
            candidate_rank = rank(assign)
            if best_rank is None or candidate_rank < best_rank:
                best_rank, best_choices = candidate_rank, assign
            return
        variable = min(undecided, key=lambda v: (doms[v].bit_count(), -degree[v], v))
        choices = list(bit_options(doms[variable]))
        choices.sort(key=lambda o: (abs(STEPS[o]),
                                    (float(options[variable][o]) - float(x64[variable])) ** 2,
                                    STEPS[o]))
        for option in choices:
            next_domains = dict(doms)
            next_domains[variable] = 1 << option
            dfs(next_domains)

    dfs({v: domains_in[v] for v in component})
    return best_choices, best_rank


def _candidate_grid(ex, raw_grid, options, vars_local, assignments):
    grid = raw_grid.copy()
    for var, option in assignments.items():
        grid[vars_local[var]] = options[var][option]
    return grid


def build_problem(ex, data, deadline: float | None = None):
    vars_rc = np.asarray(data["vars_rc"], dtype=np.int32)
    vars_local = tuple(tuple(map(int, ex.local_rc(rc))) for rc in vars_rc)
    if len(vars_local) != 121 or len(set(vars_local)) != 121:
        raise ConversionStop("DOMAIN_MISMATCH", f"expected 121 unique active nodes, got {len(vars_local)}")
    if [tuple(map(int, rc)) for rc in vars_rc] != sorted(tuple(map(int, rc)) for rc in vars_rc):
        raise ConversionStop("VARIABLE_ORDER_MISMATCH", "prepared variables are not in row-major order required by tie-break")
    var_by_local = {rc: i for i, rc in enumerate(vars_local)}
    raw_grid = np.asarray(data["closed"], dtype=np.float32)
    raw_x = np.asarray(data["raw_x"], dtype=np.float32)
    lo = np.asarray(data["lo"], dtype=np.float32)
    hi = np.asarray(data["hi"], dtype=np.float32)
    x64 = np.asarray(data["x64"], dtype=np.float64)
    if raw_grid.shape != (15, 15) or raw_x.shape != (121,) or lo.shape != (121,) or hi.shape != (121,) or x64.shape != (121,):
        raise ConversionStop("SHAPE_MISMATCH", "pilot context/variable/bound/continuous solution shapes changed")
    if data["G"].shape != (784, 121) or data["k"].shape != (784,) or data["radii"].shape != (392,):
        raise ConversionStop("CONE_POPULATION_MISMATCH", "expected 392 two-axis face cones over the 121-node domain")
    options = ex.build_neighbor_options(raw_x, lo, hi)
    if len(options) != 121 or any(len(row) != 3 for row in options):
        raise ConversionStop("OPTION_SHAPE_MISMATCH", "expected exactly three adjacent float32 choices per variable")

    unary: list[UnaryConstraint] = []
    binary: list[BinaryConstraint] = []
    fixed_failures = []
    domains = {i: ALL_OPTIONS for i in range(121)}
    catalog = {"crossing_records": [], "d8_records": [], "unary": [], "fixed_only": []}
    catalog["variables"] = [{"index": i, "rc": list(map(int, vars_rc[i])), "raw_float32": float(raw_x[i]),
                             "options_float32": [float(v) for v in options[i]],
                             "options_bits_hex": [hex(int(v.view(np.uint32))) for v in options[i]],
                             "lower_float32": float(lo[i]), "upper_float32": float(hi[i])}
                            for i in range(121)]

    def add_unary(var: int, mask: int, kind: str, source: str, endpoints=()):
        mask &= ALL_OPTIONS
        unary.append(UnaryConstraint(var, mask, kind, source, tuple(endpoints)))
        domains[var] &= mask
        catalog["unary"].append({"variable": var, "rc": list(vars_rc[var]), "allowed_options": list(bit_options(mask)),
                                 "kind": kind, "source": source, "endpoints_rc": [list(x) for x in endpoints]})

    # Box options: strict float32 comparisons to the pinned inward float32 bounds.
    for i in range(121):
        check_deadline(deadline, "bound table construction")
        mask = bound_option_mask(options[i], lo[i], hi[i])
        add_unary(i, mask, "inward_float32_bounds", f"variable:{i}", (tuple(map(int, vars_rc[i])),))

    # Independent P/F sign-only samples are unary constraints.
    for si, sign_spec in enumerate(data["sign_specs"]):
        check_deadline(deadline, "P/F sign table construction")
        var = var_by_local.get(tuple(map(int, sign_spec.local_rc)))
        if var is None:
            if not ex.direct_signs_pass(raw_grid, (), (sign_spec,)):
                fixed_failures.append({"kind": "sign_only", "source": si, "rc": list(sign_spec.rc)})
            continue
        mask = strict_sign_mask(options[var], sign_spec.level, sign_spec.sign, sign_spec.baseline)
        add_unary(var, mask, "P_F_sign_only", f"sign_spec:{si}", (tuple(map(int, sign_spec.rc)),))

    # Dry/wet endpoint signs attached to every crossing record are also unary.
    for ci, crossing in enumerate(data["cross_specs"]):
        check_deadline(deadline, "crossing sign table construction")
        for label, global_rc, level, sign in (("dry", crossing.dry_rc, crossing.dry_level, 1),
                                              ("wet", crossing.wet_rc, crossing.wet_level, -1)):
            local = tuple(map(int, ex.local_rc(global_rc)))
            var = var_by_local.get(local)
            if var is None:
                if not ex.direct_signs_pass(raw_grid, (crossing,), ()):
                    fixed_failures.append({"kind": f"crossing_{label}_sign", "source": ci, "rc": list(global_rc)})
                continue
            mask = strict_sign_mask(options[var], level, sign)
            add_unary(var, mask, f"P_F_{label}_sign", f"crossing:{ci}", (tuple(map(int, global_rc)),))

    # Exact scalar crossing interval tables for every pinned P/F edge record.
    for ci, crossing in enumerate(data["cross_specs"]):
        check_deadline(deadline, "P/F crossing table construction")
        a, b = resolve_edge_variables(crossing.local_a, crossing.local_b, var_by_local)
        if a is None and b is None:
            passed = ex.direct_crossings_pass(raw_grid, (crossing,))
            catalog["fixed_only"].append({"kind": "P_F_crossing", "source": ci, "passed": bool(passed),
                                          "endpoints_rc": [list(crossing.edge_rc[0]), list(crossing.edge_rc[1])]})
            if not passed: fixed_failures.append({"kind": "P_F_crossing", "source": ci})
        elif a is not None and b is not None:
            if a == b: raise ConversionStop("INVALID_EDGE", f"crossing record {ci} repeats one variable endpoint")
            table = []
            for oa in range(3):
                row = []
                for ob in range(3):
                    g = raw_grid.copy(); g[vars_local[a]] = options[a][oa]; g[vars_local[b]] = options[b][ob]
                    row.append(bool(ex.direct_crossings_pass(g, (crossing,))))
                table.append(row)
            relation = BinaryConstraint(a, b, table_tuple(table), "P_F_crossing", f"crossing:{ci}",
                                        tuple(tuple(map(int, e)) for e in crossing.edge_rc))
            binary.append(relation)
            catalog["crossing_records"].append(_relation_json(relation))
        else:
            var = a if a is not None else b
            allowed = []
            for option in range(3):
                g = raw_grid.copy(); g[vars_local[var]] = options[var][option]
                if ex.direct_crossings_pass(g, (crossing,)):
                    allowed.append(option)
            add_unary(var, mask_of(allowed), "P_F_crossing_interval", f"crossing:{ci}",
                      tuple(tuple(map(int, e)) for e in crossing.edge_rc))
            catalog["crossing_records"].append({"source": f"crossing:{ci}", "kind": "unary",
                                                 "variable": var, "allowed_options": allowed,
                                                 "endpoints_rc": [list(e) for e in crossing.edge_rc]})

    # Exact 3x3 D8 relations for all 150 witness pairs, with center >= witness.
    if len(data["witnesses"]) != 150:
        raise ConversionStop("D8_POPULATION_MISMATCH", f"expected 150 witnesses, got {len(data['witnesses'])}")
    for wi, witness in enumerate(np.asarray(data["witnesses"], dtype=np.int32)):
        check_deadline(deadline, "D8 table construction")
        cr, cc, wr, wc = map(int, witness)
        center_local, witness_local = (cr, cc), (wr, wc)
        a = var_by_local.get(center_local); b = var_by_local.get(witness_local)
        ends_global = ((cr + ex.ORIGIN[0], cc + ex.ORIGIN[1]), (wr + ex.ORIGIN[0], wc + ex.ORIGIN[1]))
        if a is None and b is None:
            passed = bool(raw_grid[center_local] >= raw_grid[witness_local])
            catalog["fixed_only"].append({"kind": "D8", "source": wi, "passed": passed,
                                          "endpoints_rc": [list(e) for e in ends_global]})
            if not passed: fixed_failures.append({"kind": "D8", "source": wi, "endpoints_rc": [list(e) for e in ends_global]})
        elif a is not None and b is not None:
            if a == b: raise ConversionStop("INVALID_D8_EDGE", f"witness {wi} repeats one variable endpoint")
            table = [[bool(options[a][oa] >= options[b][ob]) for ob in range(3)] for oa in range(3)]
            relation = BinaryConstraint(a, b, table_tuple(table), "D8", f"witness:{wi}", ends_global)
            binary.append(relation); catalog["d8_records"].append(_relation_json(relation))
        else:
            var = a if a is not None else b
            allowed = []
            for option in range(3):
                g = raw_grid.copy(); g[vars_local[var]] = options[var][option]
                if g[center_local] >= g[witness_local]: allowed.append(option)
            add_unary(var, mask_of(allowed), "D8", f"witness:{wi}", ends_global)
            catalog["d8_records"].append({"source": f"witness:{wi}", "kind": "unary", "variable": var,
                                          "allowed_options": allowed, "endpoints_rc": [list(e) for e in ends_global]})

    if len(data["cross_specs"]) != 116:
        raise ConversionStop("CROSSING_POPULATION_MISMATCH", f"expected 116, got {len(data['cross_specs'])}")
    catalog["crossing_record_count"] = len(data["cross_specs"])
    catalog["d8_witness_count"] = len(data["witnesses"])
    catalog["binary_constraint_count"] = len(binary)
    catalog["unary_constraint_count"] = len(unary)
    required_edge = {(864, 1187), (864, 1188)}
    geometric_link = [r for r in binary if r.kind == "P_F_crossing" and set(r.endpoints_rc) == required_edge]
    if not geometric_link:
        raise ConversionStop("REQUIRED_GEOMETRIC_LINK_MISSING", "pinned P/F crossing geometry did not connect (864,1187)-(864,1188)")
    for failure in fixed_failures:
        require_fixed_constraint(False, failure.get("kind", "fixed"), json.dumps(failure, sort_keys=True))
    empty = [i for i, mask in domains.items() if mask == 0]
    if empty:
        raise ConversionStop("NO_FEASIBLE_UNARY_DOMAIN", json.dumps([{"i": i, "rc": list(vars_rc[i])} for i in empty]))

    raw_option = 1
    nontrivial = []
    for relation in binary:
        if not all_true(relation.table): nontrivial.append(relation)
    seeds, raw_violations = raw_failure_seeds(unary, nontrivial, raw_option)
    if not seeds:
        return {"data": data, "executor": ex, "vars_rc": vars_rc, "vars_local": vars_local,
                "options": options, "x64": x64, "domains": domains, "unary": unary,
                "binary": tuple(nontrivial), "catalog": catalog, "raw_violations": [], "seeds": set(),
                "components": (), "adjacency": (), "fixed_failures": []}

    domains, ac3 = propagate(dict(domains), tuple(nontrivial))
    if ac3["variable"] is not None:
        rc = vars_rc[ac3["variable"]]
        raise ConversionStop("NO_FEASIBLE_AC3", f"AC-3 emptied domain at var {ac3['variable']} rc={list(rc)}")
    components, adjacency = components_from_seeds(121, tuple(nontrivial), seeds)
    required_variable = np.flatnonzero(np.all(vars_rc == np.asarray([864, 1188], dtype=np.int32), axis=1))
    if len(required_variable) != 1 or not any(int(required_variable[0]) in component for component in components):
        raise ConversionStop("REQUIRED_COMPONENT_LINK_MISSING", "data-derived failed component does not reach (864,1188)")
    active_nodes = set(v for comp in components for v in comp)
    catalog["raw_violations"] = raw_violations
    catalog["nontrivial_binary_count"] = len(nontrivial)
    catalog["active_components"] = [{"indices": list(comp), "rc": [list(vars_rc[v]) for v in comp]} for comp in components]
    catalog["active_node_count"] = len(active_nodes)
    catalog["raw_seed_indices"] = sorted(seeds)
    catalog["ac3_trace"] = ac3["trace"]
    return {"data": data, "executor": ex, "vars_rc": vars_rc, "vars_local": vars_local,
            "options": options, "x64": x64, "domains": domains, "unary": unary,
            "binary": tuple(nontrivial), "catalog": catalog, "raw_violations": raw_violations,
            "seeds": seeds, "components": components, "adjacency": adjacency,
            "fixed_failures": fixed_failures}


def _relation_json(relation: BinaryConstraint):
    return {"kind": relation.kind, "source": relation.source, "variables": [relation.a, relation.b],
            "endpoints_rc": [list(e) for e in relation.endpoints_rc],
            "allowed_option_pairs": [[i, j] for i in range(3) for j in range(3) if relation.table[i][j]]}


def run_search(problem, max_seconds=MAX_SECONDS, max_nodes=MAX_SEARCH_NODES):
    deadline = time.monotonic() + max_seconds
    budget = {"nodes": 0, "peak_ws": 0, "executor": problem["executor"]}
    assignments = {}
    component_results = []
    for comp in problem["components"]:
        choices, rank = component_search(comp, problem["domains"], problem["binary"], problem["options"],
                                         problem["x64"], deadline, budget, max_nodes)
        if choices is None:
            raise ConversionStop("NO_FEASIBLE_COMPONENT", f"component has no assignment: {comp}")
        assignments.update(choices)
        component_results.append({"indices": list(comp), "rank": [rank[0], rank[1], list(rank[2])],
                                  "options": {str(k): v for k, v in choices.items()}})
    if not problem["components"]:
        assignments = {}
    return assignments, component_results, budget


def validate_assembled(problem, assignments):
    ex, data = problem["executor"], problem["data"]
    candidate = data["closed"].copy()
    for var, option in assignments.items():
        candidate[problem["vars_local"][var]] = problem["options"][var][option]
    x = candidate[tuple((problem["vars_rc"] - np.asarray(ex.ORIGIN)).T)].astype(np.float64)
    box = bool(np.all(x >= data["lo"]) and np.all(x <= data["hi"]))
    signs = bool(ex.direct_signs_pass(candidate, data["cross_specs"], data["sign_specs"]))
    crossings = bool(ex.direct_crossings_pass(candidate, data["cross_specs"]))
    d8 = bool(ex.d8_pass(candidate, data["witnesses"]))
    cones, max_cone_excess = ex.cone_metrics(x, data["G"], data["k"], data["radii"])
    raw_cost = ex.objective_cost(data["A"], data["rhs"], data["raw_x"])
    converted_cost = ex.objective_cost(data["A"], data["rhs"], x)
    baseline_cost = ex.objective_cost(data["A"], data["rhs"], data["x0"])
    energy, allowance = ex.closure_energy_pass(raw_cost, converted_cost, baseline_cost)
    changed = np.argwhere(candidate.view(np.uint32) != data["closed"].view(np.uint32))
    active_rc = {tuple(problem["vars_local"][v]) for comp in problem["components"] for v in comp}
    changed_outside = [list(map(int, rc)) for rc in changed.tolist() if tuple(map(int, rc)) not in active_rc]
    gate = {"121_bounds_exact": box, "all_sign_samples_exact": signs, "all_116_direct_PF_crossings_exact": crossings,
            "all_150_D8_witnesses_exact": d8, "all_392_face_cones_exact": bool(cones),
            "unchanged_outside_active_components": not changed_outside,
            "inherited_objective_energy_and_strict_baseline_improvement": bool(energy)}
    measurements = {"raw_cost": raw_cost, "converted_cost": converted_cost, "baseline_cost": baseline_cost,
                   "closure_allowance": allowance, "max_cone_excess": max_cone_excess,
                   "changed_grid_rc_count": int(len(changed)), "changed_outside_active_components": changed_outside}
    return candidate, gate, measurements


def _load_real_problem(deadline: float):
    if sha256(COMPAT_DIAG) != EXPECTED_COMPAT_DIAG_SHA:
        raise ConversionStop("SOURCE_PIN_MISMATCH", "compatibility certificate pin changed")
    ex = load_executor()
    check_deadline(deadline, "real input load")
    data = ex.load_real_inputs()
    check_deadline(deadline, "pinned input validation")
    baseline_control, raw_control = ex.verify_controls(data)
    if not baseline_control.get("baseline_116_crossings") or not baseline_control.get("baseline_PF_signs"):
        raise ConversionStop("CONTROL_FAILURE", "positive baseline P/F controls failed")
    if raw_control.get("all_116_direct_crossings"):
        raise ConversionStop("CONTROL_FAILURE", "known raw negative crossing control unexpectedly passed")
    if not raw_control.get("PF_signs"):
        raise ConversionStop("CONTROL_FAILURE", "raw control violates sign assumptions; review needed")
    problem = build_problem(ex, data, deadline)
    problem["controls"] = {"baseline": baseline_control, "raw_negative": raw_control}
    return problem


def run_conversion(approved_source_sha: str, approved_plan_sha: str):
    if OUT.exists(): raise ConversionStop("OUTPUT_NOT_FRESH", f"fixed output already exists: {OUT}")
    if sha256(Path(__file__)) != approved_source_sha.lower():
        raise ConversionStop("SOURCE_APPROVAL_MISMATCH", "source SHA differs from reviewed command pin")
    if sha256(PLAN) != approved_plan_sha.lower():
        raise ConversionStop("PLAN_APPROVAL_MISMATCH", "plan SHA differs from reviewed command pin")
    if not TESTS.is_file(): raise ConversionStop("TESTS_MISSING", "fixture source is absent")
    ex = load_executor()
    local_paths = [Path(__file__), PLAN, TESTS, COMPAT_DIAG, *ex.source_paths()]
    readset_start = sha_map(local_paths)
    started = time.monotonic()
    deadline = started + MAX_SECONDS
    peak = ex.memory_peak_ws_bytes()
    status = "ERROR"
    receipt = {"schema": "ev94.wet-bank-component-conversion.v1", "status": status,
               "source_readset_start": readset_start, "source_readset_end": None}
    OUT.mkdir(parents=False, exist_ok=False)
    try:
        problem = _load_real_problem(deadline)
        problem["executor"] = ex
        problem["catalog"]["controls"] = problem["controls"]
        if not problem["components"]:
            raise ConversionStop("NO_RAW_FAILURES_NO_CONVERSION", "no raw-failing constraint component exists")
        catalog_path = OUT / "constraint-catalog.json"
        with catalog_path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(problem["catalog"], stream, indent=2, allow_nan=False)
            stream.write("\n")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ConversionStop("TIME_LIMIT", "relation construction consumed the numeric deadline")
        assignments, component_results, budget = run_search(problem, remaining, MAX_SEARCH_NODES)
        candidate, gates, measurements = validate_assembled(problem, assignments)
        elapsed = time.monotonic() - started
        peak = max(peak, ex.memory_peak_ws_bytes(), budget["peak_ws"])
        if elapsed > MAX_SECONDS: raise ConversionStop("TIME_LIMIT", f"elapsed {elapsed:.3f}s exceeds {MAX_SECONDS}s")
        if peak > MAX_PEAK_WS_BYTES: raise ConversionStop("MEMORY_LIMIT", f"peak working set {peak} exceeds cap")
        receipt.update({"search_status": "COMPLETE", "search_nodes": budget["nodes"],
                        "components": component_results, "gates": gates, "measurements": measurements,
                        "constraint_catalog_path": str(catalog_path.resolve()),
                        "constraint_catalog_sha256": sha256(catalog_path),
                        "elapsed_seconds": elapsed, "peak_working_set_bytes": peak,
                        "limits": {"seconds": MAX_SECONDS, "search_nodes": MAX_SEARCH_NODES,
                                   "peak_working_set_bytes": MAX_PEAK_WS_BYTES}})
        readset_end = sha_map(local_paths)
        if readset_start != readset_end:
            raise ConversionStop("SOURCE_DRIFT", "a pinned source changed during conversion")
        receipt["source_readset_end"] = readset_end
        receipt["source_readset_equal"] = True
        if not all_gates_pass(gates):
            status = "REJECTED_ASSEMBLED_LOCAL_GATES"
            receipt["status"] = status
            receipt["failed_gates"] = [k for k, v in gates.items() if not v]
        else:
            candidate_path = OUT / "unaccepted-candidate-context.npz"
            with candidate_path.open("xb") as stream:
                np.savez_compressed(stream, candidate_context_float32=candidate.astype(np.float32),
                                    variables_rc=problem["vars_rc"],
                                    changed_rc=np.argwhere(candidate.view(np.uint32) != problem["data"]["closed"].view(np.uint32)),
                                    assignments_json=np.frombuffer(json.dumps({str(k): v for k, v in assignments.items()},
                                                                               sort_keys=True).encode("utf-8"), dtype=np.uint8))
            receipt["candidate_path"] = str(candidate_path.resolve())
            receipt["candidate_sha256"] = sha256(candidate_path)
            status = "DIAGNOSTIC_CANDIDATE_UNACCEPTED"
            receipt["status"] = status
            receipt["limitations"] = ["No water-connectivity/outside-channel-minima/exposed-area gate here.",
                                      "Not accepted or promoted; independent full consumer remains required."]
        receipt["source_pins"] = {"frozen_executor_sha256": EXPECTED_EXECUTOR_SHA,
                                  "compatibility_certificate_sha256": EXPECTED_COMPAT_DIAG_SHA,
                                  "approved_source_sha256": approved_source_sha.lower(),
                                  "approved_plan_sha256": approved_plan_sha.lower()}
        receipt["status"] = status
    except ConversionStop as exc:
        receipt["status"] = exc.status
        receipt["error"] = str(exc)
        receipt["elapsed_seconds"] = time.monotonic() - started
        receipt["peak_working_set_bytes"] = max(peak, ex.memory_peak_ws_bytes())
        receipt["source_readset_end"] = sha_map(local_paths)
        receipt["source_readset_equal"] = receipt["source_readset_start"] == receipt["source_readset_end"]
    except Exception as exc:
        receipt["status"] = "ERROR"
        receipt["error"] = f"{type(exc).__name__}: {exc}"
        receipt["elapsed_seconds"] = time.monotonic() - started
        try:
            receipt["peak_working_set_bytes"] = max(peak, ex.memory_peak_ws_bytes())
        except Exception as measurement_exc:
            receipt["peak_working_set_bytes"] = peak
            receipt["peak_working_set_error"] = f"{type(measurement_exc).__name__}: {measurement_exc}"
        try:
            receipt["source_readset_end"] = sha_map(local_paths)
            receipt["source_readset_equal"] = receipt["source_readset_start"] == receipt["source_readset_end"]
        except Exception as readset_exc:
            receipt["source_readset_end"] = None
            receipt["source_readset_equal"] = False
            receipt["source_readset_error"] = f"{type(readset_exc).__name__}: {readset_exc}"
        # Preserve a terminal ERROR receipt before propagating an unexpected
        # exception. The output directory is exclusive and no candidate is
        # written on this path.
        receipt_path = OUT / "receipt.json"
        with receipt_path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(receipt, stream, indent=2, allow_nan=False)
            stream.write("\n")
        raise
    receipt_path = OUT / "receipt.json"
    with receipt_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(receipt, stream, indent=2, allow_nan=False)
        stream.write("\n")
    return receipt


def run_self_test():
    import unittest
    suite = unittest.defaultTestLoader.discover(str(HERE), pattern="test_components.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


def main(argv=None):
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--convert", action="store_true")
    parser.add_argument("--approved-source-sha")
    parser.add_argument("--approved-plan-sha")
    args = parser.parse_args(argv)
    if args.self_test:
        return run_self_test()
    if not args.approved_source_sha or not args.approved_plan_sha:
        parser.error("--convert requires exact reviewed --approved-source-sha and --approved-plan-sha")
    receipt = run_conversion(args.approved_source_sha, args.approved_plan_sha)
    print(json.dumps({"status": receipt["status"], "receipt": str((OUT / "receipt.json").resolve())}, indent=2))
    return 0 if receipt["status"] == "DIAGNOSTIC_CANDIDATE_UNACCEPTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
