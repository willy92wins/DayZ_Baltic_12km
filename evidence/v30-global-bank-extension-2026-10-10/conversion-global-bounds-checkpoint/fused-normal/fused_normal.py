"""Exact matrix-free ADMM normal action with A^T A fused by grid stencils.

This keeps the frozen structured_operator API and replaces only the expensive
composition rmatvec_a(matvec_a(x)). C and G retain their validated callbacks.
"""
from __future__ import annotations

import math

import numpy as np
from scipy.sparse.linalg import LinearOperator


class FusedNormalAction:
    def __init__(self, structured):
        self.structured = structured
        h,w=structured.base.shape
        self.xx_rows=np.zeros((h,max(0,w-2)),dtype=np.bool_)
        self.zz_rows=np.zeros((max(0,h-2),w),dtype=np.bool_)
        self.xz_rows=np.zeros((max(0,h-2),max(0,w-2)),dtype=np.bool_)
        if structured.xx_rc.size:
            self.xx_rows[structured.xx_rc[:,0],structured.xx_rc[:,1]]=True
        if structured.zz_rc.size:
            self.zz_rows[structured.zz_rc[:,0],structured.zz_rc[:,1]]=True
        if structured.xz_rc.size:
            self.xz_rows[structured.xz_rc[:,0],structured.xz_rc[:,1]]=True

    def a_normal(self, x):
        """Return exact A.T@(A@x), without materializing A or its transpose."""
        op=self.structured
        x=np.asarray(x,dtype=np.float64)
        if x.ndim!=1 or x.size!=op.n or not np.isfinite(x).all():
            raise ValueError(f'x must be a finite vector of length {op.n}')
        grid=op._full_delta(x)
        h,w=grid.shape
        grad=np.zeros((h,w),dtype=np.float64)
        qwork=np.empty((h,w),dtype=np.float64)

        if w>=3 and self.xx_rows.size:
            q=qwork[:,:w-2]
            np.subtract(grid[:,:-2],grid[:,1:-1],out=q)
            np.subtract(q,grid[:,1:-1],out=q)
            np.add(q,grid[:,2:],out=q)
            np.multiply(q,self.xx_rows,out=q,casting='unsafe')
            np.add(grad[:,:-2],q,out=grad[:,:-2])
            np.subtract(grad[:,1:-1],q,out=grad[:,1:-1])
            np.subtract(grad[:,1:-1],q,out=grad[:,1:-1])
            np.add(grad[:,2:],q,out=grad[:,2:])

        if h>=3 and self.zz_rows.size:
            q=qwork[:h-2,:]
            np.subtract(grid[:-2,:],grid[1:-1,:],out=q)
            np.subtract(q,grid[1:-1,:],out=q)
            np.add(q,grid[2:,:],out=q)
            np.multiply(q,self.zz_rows,out=q,casting='unsafe')
            np.add(grad[:-2,:],q,out=grad[:-2,:])
            np.subtract(grad[1:-1,:],q,out=grad[1:-1,:])
            np.subtract(grad[1:-1,:],q,out=grad[1:-1,:])
            np.add(grad[2:,:],q,out=grad[2:,:])

        if h>=3 and w>=3 and self.xz_rows.size:
            q=qwork[:h-2,:w-2]
            np.subtract(grid[:-2,2:],grid[:-2,:-2],out=q)
            np.add(q,grid[2:,:-2],out=q)
            np.subtract(q,grid[2:,2:],out=q)
            np.multiply(q,math.sqrt(2.0)*0.25,out=q)
            np.multiply(q,self.xz_rows,out=q,casting='unsafe')
            # q is the A-row value; its transpose contributes another
            # sqrt(2)/4 coefficient at each corner.
            np.multiply(q,math.sqrt(2.0)*0.25,out=q)
            np.subtract(grad[:-2,:-2],q,out=grad[:-2,:-2])
            np.add(grad[:-2,2:],q,out=grad[:-2,2:])
            np.add(grad[2:,:-2],q,out=grad[2:,:-2])
            np.subtract(grad[2:,2:],q,out=grad[2:,2:])

        result=grad[op.variables[:,0],op.variables[:,1]]
        # A includes the .25 identity rows, so A.T A adds .25^2 * x.
        result += 0.0625*x
        return result

    def matvec(self, x, rho):
        if not np.isfinite(rho) or rho<=0:
            raise ValueError('rho must be positive finite')
        op=self.structured
        x=np.asarray(x,dtype=np.float64)
        # Same normal equation as pilot.make_x_operator, with A's expensive
        # pair fused. C/G still use the independently validated callbacks.
        result=self.a_normal(x)
        np.add(result,float(rho)*x,out=result)
        c=op.rmatvec_c(op.matvec_c(x))
        np.add(result,float(rho)*c,out=result)
        g=op.rmatvec_g(op.matvec_g(x))
        np.add(result,float(rho)*g,out=result)
        return result

    def linear_operator(self,rho):
        return LinearOperator((self.structured.n,self.structured.n),
                              matvec=lambda x:self.matvec(x,rho),
                              rmatvec=lambda x:self.matvec(x,rho),dtype=np.float64)

    def diagonal(self,rho):
        return self.structured.normal_diagonal(rho)
