from pathlib import Path
import json,subprocess,sys
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'nav-kit7-8m-preparation-20261027';target=R/'nav8-wrong-baseline-must-not-exist'
assert not target.exists()
p=subprocess.run([sys.executable,'-I',str(W/'tools/navigation/package_nav8_config_ev112.py'),'--baseline','P:/Mods/@DayZ_Baltic_EV112_Kit7NavV9/Addons/narva_trial.pbo','--expected-sha256','0'*64,'--wrp-sha256','0da63d3f258923e784a62bcb59bb1d7f2ab99866816f530bfe73cd4211b23254','--converter','C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/CfgConvert/CfgConvert.exe','--filebank','C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe','--output',str(target)],capture_output=True)
(O/'wrong-baseline.stderr.log').write_bytes(p.stderr)
assert p.returncode!=0 and b'Baseline identity mismatch' in p.stderr and not target.exists()
(O/'wrong-baseline.json').write_text(json.dumps(dict(status='PASS_NEGATIVE_REJECTED_BEFORE_OUTPUT',returncode=p.returncode,output_absent=True))+'\n')
print('PASS_NEGATIVE_REJECTED_BEFORE_OUTPUT')
