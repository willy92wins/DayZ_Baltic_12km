from pathlib import Path
import sys,unittest
import numpy as np
from scipy.spatial import ConvexHull
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/water'))
from cap_stream_collision_v31 import split_roof
from review_compact_collision_v31 import overlay
def inward(p,h):
 f=h.simplices.copy();t=p[f];n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0])
 reverse=np.einsum('ij,ij->i',n,t.mean(1)-p.mean(0))>0
 f[reverse]=f[reverse,::-1];return f
def roofs(p,f):
 t=p[f];n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);return t[abs(n[:,1])>1e-8][np.cross(t[abs(n[:,1])>1e-8][:,1]-t[abs(n[:,1])>1e-8][:,0],t[abs(n[:,1])>1e-8][:,2]-t[abs(n[:,1])>1e-8][:,0])[:,1]<0]
class CapTests(unittest.TestCase):
 def test_realistic_sloping_convex_roof_keeps_full_envelope(self):
  a=np.linspace(0,2*np.pi,17,endpoint=False)
  rim=np.c_[np.cos(a),np.ones(len(a)),np.sin(a)]
  low=rim.copy();low[:,1]=0
  p=np.vstack((rim,low,[[0,1.8,0]]));h=ConvexHull(p);f=inward(p,h)
  parts=split_roof(p,f,12,20);self.assertGreater(len(parts),1)
  roof=[]
  for part in parts:
   self.assertLessEqual(len(part['points']),12);self.assertLessEqual(len(part['faces']),20)
   self.assertLessEqual((part['points']@h.equations[:,:3].T+h.equations[:,3]).max(),1e-9)
   roof.extend(roofs(part['points'],inward(part['points'],ConvexHull(part['points']))))
  original=roofs(p,f);result=overlay(original,np.array(roof),vertical_limit=1e-7,horizontal_limit=1e-7)
  self.assertTrue(all(result['checks'].values()),result)
  raised=np.array(roof);raised[:,:,1]+=.05
  self.assertFalse(overlay(original,raised,vertical_limit=1e-7,horizontal_limit=1e-7)['checks']['vertical_contact_error'])
  self.assertFalse(overlay(original,np.array(roof[:1]),vertical_limit=1e-7,horizontal_limit=1e-7)['checks']['full_source_covered'])
 def test_rejects_overhang_nonfinite_and_wrong_winding(self):
  p=np.array([[0,0,0],[1,0,0],[0,0,1],[.5,1,.5],[2,1,0],[0,1,2]])
  h=ConvexHull(p);f=inward(p,h)
  with self.assertRaisesRegex(ValueError,'vertically'):split_roof(p,f)
  with self.assertRaises(ValueError):split_roof(p,f[:,::-1])
  with self.assertRaises(ValueError):split_roof(p*np.nan,f)
 def test_exact_triangular_prism_needs_one_component(self):
  p=np.array([[0,1,0],[1,1.3,0],[0,1.2,1],[0,0,0],[1,0,0],[0,0,1]])
  h=ConvexHull(p);parts=split_roof(p,inward(p,h),6,8)
  self.assertEqual(len(parts),1);self.assertAlmostEqual(parts[0]['volume'],h.volume,places=12)
if __name__=='__main__':unittest.main()

