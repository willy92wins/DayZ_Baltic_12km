"""Analytic positive/negative controls for the continuous junction gate."""
import json, pathlib, sys
from types import SimpleNamespace
import numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import gatelib as G
from junction_native import dry_gap
z = G.ZTOP
path = np.array([[0,z-3],[24,z-3]],float)
H = np.tile(np.arange(6,dtype=float),(6,1))
plane = np.full((5,5),1.5)
crossing = dry_gap(path,H,plane,[])
assert abs(crossing["wet_m"]-9)<1e-7 and abs(crossing["max_dry_m"]-15)<1e-7, crossing
face = np.array([[0,3,z],[24,3,z],[24,3,z-24]],float)
p = SimpleNamespace(lo=face[:,[0,2]].min(0),hi=face[:,[0,2]].max(0),water=np.array([face]))
H = np.full((6,6),2.0); plane[:] = np.nan
connected = dry_gap(path,H,plane,[p])
assert abs(connected["max_dry_m"]-3)<1e-7 and connected["max_dry_m"]<=6, connected
blocked = dry_gap(path,H+2,plane,[p])
assert abs(blocked["max_dry_m"]-24)<1e-7 and blocked["max_dry_m"]>6, blocked
print(json.dumps(dict(analytic_pond_crossing=crossing,connected_triangle=connected,buried_triangle=blocked)))
print("NATIVE-CONTROLS PASS")
