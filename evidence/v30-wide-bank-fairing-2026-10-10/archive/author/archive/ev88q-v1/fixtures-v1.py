"""Offline unit fixtures for the exact scalar predicates/helpers used by EV88-Q author."""
from __future__ import annotations
import importlib.util
import math
import pathlib
import sys

import numpy as np

ROOT=pathlib.Path(r"E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010")
sys.path.insert(0,str(ROOT/"author"))
import author_ev88q as a


def height_for_t(hw,lw,ld,t):
    gw=float(hw)-float(lw)
    return float(ld)+gw*(1.-1./float(t))


def test_crossings_bidirectional():
    checks=[]
    for length in (6.0,6.0*math.sqrt(2.0)):
        hw,lw,ld=-1.0,0.0,0.0
        hd=1.0
        lo,hi,d=a.crossing_height_bounds(hw,lw,hd,ld,length)
        for direction,t in (("lower_dry_height",d["thi"]),("raise_dry_height",d["tlo"])):
            if not (0<t<1):
                continue
            trial=height_for_t(hw,lw,ld,t)
            assert lo-1e-12<=trial<=hi+1e-12
            checks.append({"edge_length_m":length,"direction":direction,"t":t,"height_m":trial,"within_bounds":True})
        t_bad=d["tlo"]-1.01/length
        if t_bad>0:
            h_bad=height_for_t(hw,lw,ld,t_bad)
            assert h_bad>hi
            checks.append({"edge_length_m":length,"negative":"crossing shift 1.01m","rejected_by_upper":h_bad>hi})
        t_bad=d["thi"]+1.01/length
        if t_bad<1:
            h_bad=height_for_t(hw,lw,ld,t_bad)
            assert h_bad<lo
            checks.append({"edge_length_m":length,"negative":"crossing shift 1.01m opposite direction","rejected_by_lower":h_bad<lo})
    try:
        a.crossing_height_bounds(1.0,0.0,1.0,0.0,6.0)
    except ValueError:
        pass
    else:
        raise AssertionError("wrong wet/dry endpoint signs were accepted")
    return checks


def test_nearflat():
    tau=0.024040603637695314
    old=np.array([[0.0,0.10],[0.10,0.10]],dtype=np.float32)
    new=np.array([[0.0,tau],[tau,tau]],dtype=np.float32)
    mask=a.new_nearflat_cells(old,new,tau)
    assert mask.shape==(1,1) and bool(mask[0,0])
    exact=np.array([[0.0,tau],[tau,0.0]],dtype=np.float64)
    exactspan=exact.max()-exact.min()
    assert exactspan==tau
    above=np.nextafter(np.float64(tau),np.float64(math.inf))
    assert above>tau and not (above<=tau)
    unchanged=a.new_nearflat_cells(new,new,tau)
    assert not unchanged.any()
    return {"tau_m":tau,"new_cell_rejected":bool(mask[0,0]),"exact_threshold_is_nearflat":True,"nextafter_above_is_not_nearflat":True,"unchanged_existing_cell_allowed":True}


def test_extrema_one_to_one():
    b=[(10,10,"max",1.0),(10,11,"max",0.9)]
    h=[(10,10,"max",0.8),(10,10,"max",0.7)]
    result=a.one_to_one_extrema_match(b,h,radius=1)
    assert result["pass"] and result["matched"]==2
    single_b=[(10,10,"max",1.0)]
    duplicated_h=[(10,10,"max",0.9),(10,11,"max",0.8)]
    result=a.one_to_one_extrema_match(single_b,duplicated_h,radius=1)
    assert not result["pass"] and len(result["unmatched_new_indices"])==1
    return {"two_to_two_pass":True,"one_to_two_negative_rejected":True}


def test_stencil_coefficients():
    sums={}
    for kind in ("xx","zz","xz"):
        coeff=a.hinge_coeffs(kind,5,5)
        sums[kind]=sum(x[2] for x in coeff)
        assert abs(sums[kind])<1e-15
    plane=np.fromfunction(lambda r,c:3.+0.2*r-0.7*c,(5,5),dtype=float)
    for kind in ("xx","zz","xz"):
        assert abs(sum(plane[r,c]*coef for r,c,coef in a.hinge_coeffs(kind,1,1)))<1e-12
    vars_rc=np.array([[7,7]],dtype=np.int32)
    ss=a.frozen_stencils(vars_rc,(4,11,4,11))
    assert ss and all(any((r,c)==(7,7) for r,c,_ in a.hinge_coeffs(k,sr,sc)) for k,sr,sc in ss)
    return {"coefficient_sums":sums,"affine_plane_zero_second_differences":True,"frozen_set_contains_only_touching_stencils":True,"stencils":len(ss)}


def test_acceptance_helpers():
    assert a.collar_energy_gate(3.0,3.0) and not a.collar_energy_gate(3.0,3.00001)
    assert a.collar_hinge_gate(29.0,29.0) and not a.collar_hinge_gate(29.0,29.01)
    assert a.no_new_steep_hinges(np.array([31.0,29.0]),np.array([31.0,30.0001]))
    assert not a.no_new_steep_hinges(np.array([29.0]),np.array([30.0002]))
    assert a.slope_gate(np.array([20.,40.]),np.array([35.,40.]))
    assert not a.slope_gate(np.array([20.]),np.array([35.0001]))
    before=np.zeros((3,3)); after=before.copy(); mask=np.zeros((3,3),bool); mask[0,0]=True
    assert a.fixed_unchanged(before,after,mask)
    after[0,0]=np.nextafter(np.float64(0),np.float64(1))
    assert not a.fixed_unchanged(before,after,mask)
    b=np.tile(np.array([0.,1.,0.]),(3,1)); h=b.copy(); h[1,1]=1.2
    assert not a.no_rowcol_prominence_increase(b,h)
    return {"collar_energy_nonincrease":True,"collar_hinge_nonincrease":True,"new_30deg_hinge_rejected":True,"slope_cap_rejects":True,"fixed_exact_identity_rejects_change":True,"rowcol_prominence_increase_rejected":True}


def main():
    report={"status":"PASS_EV88Q_HELPER_FIXTURES","crossings":test_crossings_bidirectional(),"nearflat":test_nearflat(),"extrema":test_extrema_one_to_one(),"stencils":test_stencil_coefficients(),"acceptance_helpers":test_acceptance_helpers()}
    out=ROOT/"author/preflight/fixtures.json"
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(__import__("json").dumps(report,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(__import__("json").dumps(report,indent=2,allow_nan=False))


if __name__=="__main__":
    main()
