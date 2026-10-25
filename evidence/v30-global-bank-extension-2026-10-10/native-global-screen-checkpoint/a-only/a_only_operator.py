"""A-only matrix-free operator for the EV95 unconstrained diagnostic.

This intentionally does not construct C/G data or D8 rows. D8 witnesses are
still available from the pinned source helper after the one diagnostic action.
The A row formulas and tap ordering mirror structured_operator.py at its pinned
source revision; the companion fixture compares them against that full builder.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


def _finite_vector(value, expected: int, label: str) -> np.ndarray:
    a = np.asarray(value, dtype=np.float64)
    if a.ndim != 1 or a.size != expected or not np.isfinite(a).all():
        raise ValueError(f"{label} must be a finite vector of length {expected}")
    return a


def validate_domain(base, variables):
    b = np.asarray(base, dtype=np.float64)
    if b.ndim != 2 or min(b.shape, default=0) < 1 or not np.isfinite(b).all():
        raise ValueError("base must be a finite non-empty 2D array")
    v = np.asarray(variables)
    if v.ndim != 2 or v.shape[1] != 2 or v.shape[0] == 0:
        raise ValueError("variables must be a non-empty Nx2 array")
    if not np.issubdtype(v.dtype, np.integer):
        if not np.isfinite(v).all() or not np.equal(v, np.floor(v)).all():
            raise ValueError("variables must contain integer coordinates")
    h, w = b.shape
    if np.any(v[:, 0] < 0) or np.any(v[:, 0] >= h) or np.any(v[:, 1] < 0) or np.any(v[:, 1] >= w):
        raise ValueError("variable coordinate outside base")
    if v.shape[0] > 1:
        row_increases = v[1:, 0] > v[:-1, 0]
        same_row_col_increases = (v[1:, 0] == v[:-1, 0]) & (v[1:, 1] > v[:-1, 1])
        if not np.all(row_increases | same_row_col_increases):
            raise ValueError("variables must be unique and sorted row-major")
    return np.ascontiguousarray(b), np.ascontiguousarray(v, dtype=np.int32)


@dataclass
class AOnlyOperators:
    """Only state needed by A, A.T and the fused A.T A action."""
    base: np.ndarray
    variables: np.ndarray
    xx_rc: np.ndarray
    zz_rc: np.ndarray
    xz_rc: np.ndarray
    rhs_a: np.ndarray
    diag_a: np.ndarray

    @property
    def n(self):
        return int(self.variables.shape[0])

    @property
    def n_a(self):
        return int(self.xx_rc.shape[0] + self.zz_rc.shape[0] + self.xz_rc.shape[0] + self.n)

    @property
    def shape(self):
        return self.base.shape

    def _full_delta(self, x):
        a = _finite_vector(x, self.n, "x")
        grid = np.zeros(self.base.shape, dtype=np.float64)
        grid[self.variables[:, 0], self.variables[:, 1]] = a
        return grid

    def matvec_a(self, x):
        # Formula/tap order matches the pinned full operator's matvec_a.
        x = _finite_vector(x, self.n, "x")
        grid = self._full_delta(x)
        out = np.empty(self.n_a, dtype=np.float64)
        p = 0
        for rc, kind in ((self.xx_rc, "xx"), (self.zz_rc, "zz"), (self.xz_rc, "xz")):
            count = len(rc)
            if count:
                r, c = rc[:, 0], rc[:, 1]
                if kind == "xx": vals = grid[r, c] - 2.0*grid[r, c+1] + grid[r, c+2]
                elif kind == "zz": vals = grid[r, c] - 2.0*grid[r+1, c] + grid[r+2, c]
                else: vals = math.sqrt(2.0)*(-.25*grid[r,c] + .25*grid[r,c+2] + .25*grid[r+2,c] - .25*grid[r+2,c+2])
                out[p:p+count] = vals
            p += count
        out[p:] = .25 * x
        return out

    def rmatvec_a(self, y):
        a = _finite_vector(y, self.n_a, "A adjoint input")
        grad = np.zeros(self.base.shape, dtype=np.float64)
        p = 0
        for rc, kind in ((self.xx_rc, "xx"), (self.zz_rc, "zz"), (self.xz_rc, "xz")):
            count = len(rc)
            if count:
                r, c = rc[:, 0], rc[:, 1]
                q = a[p:p+count]
                if kind == "xx": taps = ((r,c,1.),(r,c+1,-2.),(r,c+2,1.))
                elif kind == "zz": taps = ((r,c,1.),(r+1,c,-2.),(r+2,c,1.))
                else:
                    s = math.sqrt(2.0)
                    taps = ((r,c,-.25*s),(r,c+2,.25*s),(r+2,c,.25*s),(r+2,c+2,-.25*s))
                for rr, cc, coef in taps:
                    np.add.at(grad, (rr, cc), q*coef)
            p += count
        grad[self.variables[:,0], self.variables[:,1]] += .25*a[p:]
        return grad[self.variables[:,0], self.variables[:,1]]


def build_a_only(base, variables) -> AOnlyOperators:
    """Build exactly the A rows/rhs/diagonal without allocating C or G state."""
    b, v = validate_domain(base, variables)
    h, w = b.shape

    # A needs only a membership mask. The full EV95 operator additionally
    # builds an int32 index grid for C/D8 and G; retain a temporary index map
    # below only while accumulating A's exact diagonal.
    active = np.zeros((h, w), dtype=np.bool_)
    active[v[:, 0], v[:, 1]] = True

    def anchors(kind):
        if kind == "xx":
            mask = active[:, :-2] | active[:, 1:-1] | active[:, 2:]
        elif kind == "zz":
            mask = active[:-2, :] | active[1:-1, :] | active[2:, :]
        else:
            mask = active[:-2, :-2] | active[:-2, 2:] | active[2:, :-2] | active[2:, 2:]
        return np.column_stack(np.nonzero(mask)).astype(np.int32, copy=False)

    xx, zz, xz = anchors("xx"), anchors("zz"), anchors("xz")
    counts = (len(xx), len(zz), len(xz), len(v))
    rhs_a = np.empty(sum(counts), dtype=np.float64)

    # Fill one final RHS array directly. This avoids keeping all rhs_parts
    # alive while np.concatenate allocates a second full 11M-row array.
    fixed = b.copy()
    fixed[v[:, 0], v[:, 1]] = 0.0
    p = 0
    for rc, kind in ((xx, "xx"), (zz, "zz"), (xz, "xz")):
        count = len(rc)
        if count:
            r, c = rc[:, 0], rc[:, 1]
            if kind == "xx": val = fixed[r,c] - 2.0*fixed[r,c+1] + fixed[r,c+2]
            elif kind == "zz": val = fixed[r,c] - 2.0*fixed[r+1,c] + fixed[r+2,c]
            else: val = math.sqrt(2.0)*(-.25*fixed[r,c] + .25*fixed[r,c+2] + .25*fixed[r+2,c] - .25*fixed[r+2,c+2])
            rhs_a[p:p+count] = -np.asarray(val, dtype=np.float64)
        p += count
    rhs_a[p:] = .25 * b[v[:,0], v[:,1]]

    # Exact diag(A.T A) formula and tap order from structured_operator.py.
    idx = np.full((h, w), -1, dtype=np.int32)
    idx[v[:,0], v[:,1]] = np.arange(len(v), dtype=np.int32)
    da = np.full(len(v), .0625, dtype=np.float64)

    def add_sq(rc, kind):
        r, c = rc[:,0], rc[:,1]
        if kind == "xx": taps=((r,c,1.),(r,c+1,-2.),(r,c+2,1.))
        elif kind == "zz": taps=((r,c,1.),(r+1,c,-2.),(r+2,c,1.))
        else:
            s=math.sqrt(2.); taps=((r,c,-.25*s),(r,c+2,.25*s),(r+2,c,.25*s),(r+2,c+2,-.25*s))
        for rr,cc,a in taps:
            ii=idx[rr,cc]; m=ii>=0
            np.add.at(da,ii[m],a*a)

    add_sq(xx,"xx"); add_sq(zz,"zz"); add_sq(xz,"xz")
    del idx, active, fixed
    return AOnlyOperators(b,v,xx,zz,xz,rhs_a,da)
