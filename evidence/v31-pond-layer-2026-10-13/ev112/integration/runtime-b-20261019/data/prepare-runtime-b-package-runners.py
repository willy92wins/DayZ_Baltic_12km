from pathlib import Path
import json
O=Path(__file__).parent;D=O/'water-fix-b'
s=(O/'run-final-package-gates-ae.py').read_text()
s=s.replace("assert all(v['rc']==0 for v in json.loads((O/'final-ae-stage-compile.json').read_text()))\nassert all(v['rc']==0 for v in json.loads((O/'final-ae-surface-steps.json').read_text()))","assert all(v['rc']==0 for v in json.loads((O/'water-fix-b/build-steps.json').read_text()))")
for a,b in [('surface-final-ae','surface-runtime-b'),('package-final-ae','package-runtime-b'),('stage-forest-ae','stage-runtime-b'),('surface-gates-ae-results','surface-gates-runtime-b-results'),('surface-scope-ae-binding.json','water-fix-b/surface-scope.json'),('terrain-ev112-c.npz','water-fix-b/terrain.npz'),('stage-runtime-b-report.json','water-fix-b/stage-report.json'),('final-ae-build-binding.json','runtime-b-build-binding.json'),('final-package-ae-','runtime-b-package-')]:s=s.replace(a,b)
assert "O/'water-fix-b/stage-report.json'" in s
out=O/'run-runtime-b-package-gates.py';assert not out.exists();out.write_text(s)
s=(O/'run-painted-pilot-ae.py').read_text()
for a,b in [('forest-final-tools-ae','forest-water-fix-b'),('package-final-ae','package-runtime-b'),('surface-final-ae','surface-runtime-b')]:s=s.replace(a,b)
s=s.replace("str(R/(gate.lower()+'pilot-painted.json'))","str(O/'water-fix-b'/(gate.lower()+'pilot-painted.json'))")
out=O/'run-runtime-b-painted-pilot.py';assert not out.exists();out.write_text(s)
s=(O/'run-painted-forest-ae.py').read_text()
for a,b in [('forest-final-tools-ae','forest-water-fix-b'),('package-final-ae','package-runtime-b'),('surface-final-ae','surface-runtime-b'),('forest-painted-rasters-ae','forest-painted-rasters-runtime-b'),('run-painted-pilot-ae.py','run-runtime-b-painted-pilot.py'),('forest-painted-ae-','forest-painted-runtime-b-')]:s=s.replace(a,b)
for n in ('g2g3-painted.json','g8-painted.json','g7-painted.json'):s=s.replace("R/'"+n+"'","O/'water-fix-b/"+n+"'")
out=O/'run-runtime-b-painted-forest.py';assert not out.exists();out.write_text(s)
print('Prepared isolated package and final-texture consumers; no thresholds changed')
