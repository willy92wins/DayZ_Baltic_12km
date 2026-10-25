"""Matrix-free A/C/G operators matching the pinned CP pilot row contracts.

This module represents row geometry by compact stencil anchors and a global
variable-index raster. It deliberately does not assemble sparse coefficient
triplets or a global CSR matrix.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable

import numpy as np
from scipy.sparse.linalg import LinearOperator


def _finite_vector(value, expected: int, label: str) -> np.ndarray:
    a = np.asarray(value, dtype=np.float64)
    if a.ndim != 1 or a.size != expected:
        raise ValueError(f"{label} must be a finite vector of length {expected}")
    if not np.isfinite(a).all():
        raise ValueError(f"{label} contains non-finite values")
    return a


def validate_domain(base, variables):
    b = np.asarray(base, dtype=np.float64)
    if b.ndim != 2 or min(b.shape, default=0) < 1:
        raise ValueError("base must be a non-empty 2D array")
    if not np.isfinite(b).all():
        raise ValueError("base contains non-finite values")
    v = np.asarray(variables)
    if v.ndim != 2 or v.shape[1] != 2 or v.shape[0] == 0:
        raise ValueError("variables must be a non-empty Nx2 array")
    if not np.issubdtype(v.dtype, np.integer):
        if not np.isfinite(v).all() or not np.equal(v, np.floor(v)).all():
            raise ValueError("variable coordinates must be integers")
    v = np.asarray(v, dtype=np.int64)
    h, w = b.shape
    if np.any(v[:, 0] < 0) or np.any(v[:, 0] >= h) or np.any(v[:, 1] < 0) or np.any(v[:, 1] >= w):
        raise ValueError("variable coordinate outside base")
    if np.any(v[1:, 0] < v[:-1, 0]) or np.any((v[1:, 0] == v[:-1, 0]) & (v[1:, 1] <= v[:-1, 1])):
        raise ValueError("variables must be unique and sorted row-major")
    return np.ascontiguousarray(b), np.ascontiguousarray(v, dtype=np.int32)


def d8_witness_arrays(base):
    """Return CP-compatible non-strict-minimum center/witness flat indices."""
    b = np.asarray(base, dtype=np.float64)
    if b.ndim != 2 or not np.isfinite(b).all():
        raise ValueError("base must be finite and 2D")
    h, w = b.shape
    best = np.full((h, w), np.inf, dtype=np.float64)
    witness = np.full((h, w), -1, dtype=np.int64)
    # Lexicographically sorted offsets; strict update preserves the first tie.
    offsets = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0)]
    for dr, dc in offsets:
        r0, r1 = max(0, -dr), min(h, h-dr)
        c0, c1 = max(0, -dc), min(w, w-dc)
        if r0 >= r1 or c0 >= c1:
            continue
        rr = slice(r0, r1); cc = slice(c0, c1)
        nr = slice(r0+dr, r1+dr); nc = slice(c0+dc, c1+dc)
        cand = b[nr, nc]
        cur = best[rr, cc]
        take = cand < cur
        if np.any(take):
            cur[take] = cand[take]
            wid = (np.arange(r0+dr, r1+dr, dtype=np.int64)[:, None] * w +
                   np.arange(c0+dc, c1+dc, dtype=np.int64)[None, :])
            witness[rr, cc][take] = wid[take]
    centers = np.flatnonzero((witness.ravel() >= 0) & (b.ravel() >= best.ravel()))
    return centers.astype(np.int32), witness.ravel()[centers].astype(np.int32)


@dataclass
class MatrixFreeOperators:
    base: np.ndarray
    variables: np.ndarray
    index_grid: np.ndarray
    xx_rc: np.ndarray
    zz_rc: np.ndarray
    xz_rc: np.ndarray
    d8_centers: np.ndarray
    d8_witnesses: np.ndarray
    rhs_a: np.ndarray
    d_c: np.ndarray
    k_g: np.ndarray
    diag_a: np.ndarray
    diag_c: np.ndarray
    diag_g: np.ndarray

    @property
    def n(self):
        return int(self.variables.shape[0])

    @property
    def shape(self):
        return self.base.shape

    @property
    def n_a(self):
        return int(self.xx_rc.shape[0] + self.zz_rc.shape[0] + self.xz_rc.shape[0] + self.n)

    @property
    def n_c(self):
        return int(self.d8_centers.size)

    @property
    def n_g(self):
        h, w = self.base.shape
        return 4 * max(0, h-1) * max(0, w-1)

    def _full_delta(self, x):
        a = _finite_vector(x, self.n, "x")
        grid = np.zeros(self.base.shape, dtype=np.float64)
        grid[self.variables[:, 0], self.variables[:, 1]] = a
        return grid

    def matvec_a(self, x):
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
        out[p:] = .25 * _finite_vector(x, self.n, "x")
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
                if kind == "xx":
                    taps = ((r,c,1.),(r,c+1,-2.),(r,c+2,1.))
                elif kind == "zz":
                    taps = ((r,c,1.),(r+1,c,-2.),(r+2,c,1.))
                else:
                    s = math.sqrt(2.0)
                    taps = ((r,c,-.25*s),(r,c+2,.25*s),(r+2,c,.25*s),(r+2,c+2,-.25*s))
                for rr, cc, coef in taps:
                    np.add.at(grad, (rr, cc), q*coef)
            p += count
        grad[self.variables[:,0], self.variables[:,1]] += .25*a[p:]
        return grad[self.variables[:,0], self.variables[:,1]]

    def matvec_c(self, x):
        grid = self._full_delta(x)
        h, w = self.base.shape
        flat = grid.ravel()
        return flat[self.d8_centers] - flat[self.d8_witnesses]

    def rmatvec_c(self, y):
        a = _finite_vector(y, self.n_c, "C adjoint input")
        out = np.zeros(self.n, dtype=np.float64)
        ci = self.index_grid.ravel()[self.d8_centers]
        wi = self.index_grid.ravel()[self.d8_witnesses]
        cm = ci >= 0; wm = wi >= 0
        np.add.at(out, ci[cm], a[cm])
        np.add.at(out, wi[wm], -a[wm])
        return out

    def matvec_g(self, x):
        grid = self._full_delta(x)
        h, w = grid.shape
        if min(grid.shape) < 2:
            return np.empty(0, dtype=np.float64)
        nw, ne = grid[:-1,:-1], grid[:-1,1:]
        sw, se = grid[1:,:-1], grid[1:,1:]
        # Cell-major, triangle, component. Fill one component at a time to
        # avoid four full-grid temporaries plus a second stack allocation.
        out = np.empty((h-1,w-1,4),dtype=np.float64)
        np.subtract(ne,nw,out=out[:,:,0])
        np.subtract(ne,se,out=out[:,:,1])
        np.subtract(se,sw,out=out[:,:,2])
        np.subtract(nw,sw,out=out[:,:,3])
        return out.reshape(-1)

    def rmatvec_g(self, y):
        a = _finite_vector(y, self.n_g, "G adjoint input")
        h, w = self.base.shape
        grad = np.zeros((h,w), dtype=np.float64)
        if h < 2 or w < 2:
            return np.zeros(self.n, dtype=np.float64)
        q = a.reshape(h-1,w-1,4)
        # Unique grid slices avoid coefficient triplets; each term is a
        # scatter-add into the corresponding global vertex raster.
        grad[:-1,:-1] -= q[:,:,0]
        grad[:-1,1:] += q[:,:,0]
        grad[:-1,1:] += q[:,:,1]
        grad[1:,1:] -= q[:,:,1]
        grad[1:,1:] += q[:,:,2]
        grad[1:,:-1] -= q[:,:,2]
        grad[1:,:-1] -= q[:,:,3]
        grad[:-1,:-1] += q[:,:,3]
        return grad[self.variables[:,0], self.variables[:,1]]

    def operator_a(self):
        return LinearOperator((self.n_a,self.n), matvec=self.matvec_a, rmatvec=self.rmatvec_a, dtype=np.float64)

    def operator_c(self):
        return LinearOperator((self.n_c,self.n), matvec=self.matvec_c, rmatvec=self.rmatvec_c, dtype=np.float64)

    def operator_g(self):
        return LinearOperator((self.n_g,self.n), matvec=self.matvec_g, rmatvec=self.rmatvec_g, dtype=np.float64)

    def normal_operator(self, rho):
        if not np.isfinite(rho) or rho <= 0:
            raise ValueError("rho must be positive finite")
        def mv(x):
            return (self.rmatvec_a(self.matvec_a(x)) + float(rho) *
                    (np.asarray(x,dtype=np.float64) + self.rmatvec_c(self.matvec_c(x)) +
                     self.rmatvec_g(self.matvec_g(x))))
        return LinearOperator((self.n,self.n),matvec=mv,dtype=np.float64)

    def normal_diagonal(self, rho):
        if not np.isfinite(rho) or rho <= 0:
            raise ValueError("rho must be positive finite")
        return self.diag_a + float(rho)*(1.0+self.diag_c+self.diag_g)

    def normal_rhs(self, rhs_a, z_identity, z_c, z_g, rho):
        if not np.isfinite(rho) or rho <= 0:
            raise ValueError("rho must be positive finite")
        za = _finite_vector(rhs_a, self.n_a, "rhs_a")
        zi = _finite_vector(z_identity, self.n, "z_identity")
        zc = _finite_vector(z_c, self.n_c, "z_c")
        zg = _finite_vector(z_g, self.n_g, "z_g")
        return self.rmatvec_a(za) + float(rho)*(zi + self.rmatvec_c(zc) + self.rmatvec_g(zg-self.k_g))


def build_operators(base, variables) -> MatrixFreeOperators:
    b, v = validate_domain(base, variables)
    h, w = b.shape
    idx = np.full((h,w), -1, dtype=np.int32)
    idx[v[:,0],v[:,1]] = np.arange(len(v), dtype=np.int32)
    active = idx >= 0

    def anchors(kind):
        if kind == "xx":
            mask = active[:,:-2] | active[:,1:-1] | active[:,2:]
        elif kind == "zz":
            mask = active[:-2,:] | active[1:-1,:] | active[2:,:]
        else:
            mask = active[:-2,:-2] | active[:-2,2:] | active[2:,:-2] | active[2:,2:]
        return np.column_stack(np.nonzero(mask)).astype(np.int32,copy=False)
    xx, zz, xz = anchors("xx"), anchors("zz"), anchors("xz")

    # A affine right-hand side: negative fixed stencil contribution, then .25B.
    rhs_parts = []
    fixed = np.where(active,0.0,b)
    for rc,kind in ((xx,"xx"),(zz,"zz"),(xz,"xz")):
        r,c=rc[:,0],rc[:,1]
        if kind=="xx": val=fixed[r,c]-2*fixed[r,c+1]+fixed[r,c+2]
        elif kind=="zz": val=fixed[r,c]-2*fixed[r+1,c]+fixed[r+2,c]
        else: val=math.sqrt(2.0)*(-.25*fixed[r,c]+.25*fixed[r,c+2]+.25*fixed[r+2,c]-.25*fixed[r+2,c+2])
        rhs_parts.append(-np.asarray(val,dtype=np.float64))
    rhs_parts.append(.25*b[v[:,0],v[:,1]])
    rhs_a=np.concatenate(rhs_parts)

    centers,witnesses=d8_witness_arrays(b)
    cf=idx.ravel()[centers]; wf=idx.ravel()[witnesses]
    offset=np.zeros(len(centers),dtype=np.float64)
    cm=cf<0; wm=wf<0
    flatb=b.ravel()
    offset[cm]+=flatb[centers[cm]]
    offset[wm]-=flatb[witnesses[wm]]
    d_c=-offset

    # G affine offset from fixed endpoint heights, retaining every face row.
    if h>=2 and w>=2:
        nw,ne=fixed[:-1,:-1],fixed[:-1,1:]
        sw,se=fixed[1:,:-1],fixed[1:,1:]
        k_grid=np.empty((h-1,w-1,4),dtype=np.float64)
        np.subtract(ne,nw,out=k_grid[:,:,0])
        np.subtract(ne,se,out=k_grid[:,:,1])
        np.subtract(se,sw,out=k_grid[:,:,2])
        np.subtract(nw,sw,out=k_grid[:,:,3])
        k_g=k_grid.reshape(-1)
    else:
        k_g=np.empty(0,dtype=np.float64)

    da=np.full(len(v),.0625,dtype=np.float64)
    def add_sq(rc,kind):
        r,c=rc[:,0],rc[:,1]
        if kind=="xx": taps=((r,c,1.),(r,c+1,-2.),(r,c+2,1.))
        elif kind=="zz": taps=((r,c,1.),(r+1,c,-2.),(r+2,c,1.))
        else:
            s=math.sqrt(2.); taps=((r,c,-.25*s),(r,c+2,.25*s),(r+2,c,.25*s),(r+2,c+2,-.25*s))
        for rr,cc,a in taps:
            ii=idx[rr,cc]; m=ii>=0
            np.add.at(da,ii[m],a*a)
    add_sq(xx,"xx");add_sq(zz,"zz");add_sq(xz,"xz")

    dc=np.zeros(len(v),dtype=np.float64)
    ci=idx.ravel()[centers]; wi=idx.ravel()[witnesses]
    np.add.at(dc,ci[ci>=0],1.0);np.add.at(dc,wi[wi>=0],1.0)
    dg=np.zeros(len(v),dtype=np.float64)
    if h>=2 and w>=2:
        rr,cc=np.indices((h-1,w-1),dtype=np.int32)
        for r,c in ((rr,cc+1),(rr,cc),(rr,cc+1),(rr+1,cc+1),
                    (rr+1,cc+1),(rr+1,cc),(rr,cc),(rr+1,cc)):
            ii=idx[r,c].ravel();m=ii>=0;np.add.at(dg,ii[m],1.0)
    return MatrixFreeOperators(b,v,idx,xx,zz,xz,centers,witnesses,rhs_a,d_c,k_g,da,dc,dg)
