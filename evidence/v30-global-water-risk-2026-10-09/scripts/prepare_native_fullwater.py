"""Extend proven native census to physical water on every vertex, not only lows."""
from pathlib import Path
import numpy as np
import json,hashlib,shutil,subprocess,sys
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');E=W/'evidence/v30-global-water-risk-2026-10-09'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
src=B/'BalticNativeCensus.c';assert sha(src)=='484578c8d7cdcb5cfcee8afca5ce7f1e9cdf69820604ae4a665e7de5dc037111'
code=src.read_text().replace('BalticNativeCensusMission','BalticNativeFullWaterMission').replace('baltic_native_census_v1.log','baltic_native_fullwater_v1.log').replace('BALTIC_NATIVE_CENSUS_V1','BALTIC_NATIVE_FULLWATER_V1')
code=code.replace(' protected int m_RowBad;',' protected int m_RowBad;\n protected int m_Dry;\n protected int m_Wet;\n protected int m_DryNominal;\n protected int m_DryDynamic;\n protected int m_WetMissing;')
old='float expected=m_Fields[i+2].ToFloat();'
assert old in code
code=code.replace(old,'int field = 2 + i * 2;\n   float expected = m_Fields[field].ToFloat();\n   field++;\n   int kind = m_Fields[field].ToInt();')
code=code.replace('m_Fields.Count()!=34','m_Fields.Count()!=66')
code=code.replace('   m_Total++;','   WaterVertex(m_Row, m_Column + i, kind, measured);\n   m_Total++;')
code=code.replace('Emit("END;"+m_Total+";"+m_Bad+";"+m_RiskCount+";"+(GetGame().GetTime()-m_Start));return;', '''string summary = "END;" + m_Total + ";" + m_Bad + ";" + m_RiskCount;
   summary = summary + ";" + (GetGame().GetTime()-m_Start) + ";" + m_Dry + ";" + m_Wet;
   summary = summary + ";" + m_DryNominal + ";" + m_DryDynamic + ";" + m_WetMissing;
   Emit(summary);return;''')
marker=' void RiskPoint()'
assert marker in code
code=code.replace(marker,''' void WaterVertex(int row, int column, int kind, float ground)
 {
  float x = column * 6;
  float z = 12282 - row * 6;
  bool sea = GetGame().SurfaceIsSea(x, z);
  bool pond = GetGame().SurfaceIsPond(x, z);
  float plane = GetGame().GetWaterSurfaceHeightNoFakeWave(Vector(x, ground + 100, z));
  float depth = GetGame().GetWaterDepth(Vector(x, ground + 0.01, z));
  bool nominal = (sea || pond) && plane > ground + 0.03;
  bool dynamic = (sea || pond) && depth > 0.02;
  bool missing = kind > 0 && !sea && !pond;
  if (kind == 0)
  {
   m_Dry++;
   if (nominal) m_DryNominal++;
   if (dynamic) m_DryDynamic++;
  }
  else m_Wet++;
  if (missing) m_WetMissing++;
  if ((kind == 0 && (nominal || dynamic)) || missing)
  {
   string record = "A;" + row + ";" + column + ";" + kind;
   record = record + ";" + ground + ";" + sea + ";" + pond;
   record = record + ";" + plane + ";" + depth + ";" + GetGame().SurfaceGetSeaLevel();
   Emit(record);
  }
 }
''' + marker)
name='BalticNativeFullWaterV1.BalticTrial';dst=B/'missions'/name;dst.mkdir(parents=True,exist_ok=False)
(dst/'init.c').write_text(code)
source=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008/candidate-c1r3p/terrain_valley.npz')
t=np.load(source);h=t['heights'];cls=t['cls']
assert sha(source)=='9c3011b8af5279e807630d4e91512d2e95a434463d3523a5b4074e70bc7cc8f6'
with (dst/'grid.csv').open('w',newline='') as f:
 for r in range(2048):
  for c in range(0,2048,32):
   fields=[]
   for j in range(c,c+32):fields.extend([format(float(h[r,j]),'.9g'),str(int(cls[r,j]))])
   f.write(f'{r};{c};'+';'.join(fields)+'\n')
oldref=json.loads((B/'native-census-reference.json').read_text());points=oldref['points'][-7:]
with (dst/'risks.csv').open('w') as f:
 for i,p in enumerate(points):f.write(f"{i};{p['x']:.8f};{p['z']:.8f};{p['expected_ground']:.9g};{p['cls']}\n")
lint=subprocess.run([sys.executable,'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py',str(dst)],capture_output=True,text=True)
got=json.loads(lint.stdout);assert lint.returncode==0 and not got['errors'] and got['info']['files_scanned']==1,lint.stdout
(E/'native-fullwater-lint.json').write_text(lint.stdout)
deploy=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions')/name
shutil.copytree(dst,deploy)
files={p.name:sha(p) for p in dst.iterdir()};assert all(sha(deploy/k)==v for k,v in files.items())
for file,digest in oldref['pbo'].items():assert sha(Path('P:/Mods/@DayZ_Baltic_ValleySmoothC1R3P/Addons')/file)==digest
ref=dict(mission=str(deploy),files=files,terrain_sha256=sha(source),pbo=oldref['pbo'],vertices=4194304,
    dry=int((cls==0).sum()),wet=int((cls>0).sum()),points=points,
    limitations=['All native vertices, not the continuous subcell water domain or visual rendering.','Physical anomalies are inventoried for classification, not automatically declared product defects.'])
(E/'native-fullwater-reference.json').write_text(json.dumps(ref,indent=2)+'\n')
shutil.copyfile(dst/'init.c',E/'BalticNativeFullWater.c')
print(json.dumps(dict(mission=str(deploy),vertices=ref['vertices'],dry=ref['dry'],wet=ref['wet'],lint='PASS')))
