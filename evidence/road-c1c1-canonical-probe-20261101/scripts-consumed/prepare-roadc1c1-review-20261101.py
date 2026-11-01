from pathlib import Path
import json,hashlib,shutil,time
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025');D=R/'road-c1c1-local-author-20261101';W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');py='C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe'
snap=D/'source-R0';snap.mkdir()
for n in json.loads((D/'author-completion.json').read_bytes())['files']:shutil.copyfile(D/n,snap/n)
brief='''Review the bounded RoadC1C1 DELTA, contract and tests. You are independent external reviewer; Codex is local executor/integrator with shared context. Return SOUND, SOUND-with-fixes or NEEDS-WORK, concrete file:line findings, fixes and limits; no claiming runtime success. 180 seconds, one complete compact report. No writing/running code or tools. Previous plan review consumed, do not repeat it. Check process identities, canonical alias rejection, STARTED vs never launched, logger bytes and contract. Signature anchoring preserved Authenticode Valid AND raw chainBuilt=false; an extra preparer assertion was rejected before contract: assess whether this meets plan, don't silently call the chain valid. Only native compile probe may run after review and suite; no DayZ/map. Previously consumed C1C is immutable. Header/magic is not terrain decoding. Review supplied full implementation and tests, focus false passes.\n'''
paths=[W/'plans/ev112-road-c1c1-canonical-preflight-probe-20261029.md',D/'contract.json',D/'oracle-c1c1.json',D/'oracle.json',D/'signature-receipt.json',D/'signature-r1.stdout',D/'probe_road_compile_c1c1.py',D/'observe_road_compile_c1c1.py',D/'test_probe_road_compile_c1c1.py']
for p in paths:brief+='\nFILE '+p.name+'\n'+'\n'.join(f'{i}: {line}' for i,line in enumerate(p.read_text(encoding='utf-8').splitlines(),1))+'\n'
(D/'review-brief.txt').write_text(brief,encoding='utf-8')
jobs=[{'id':'suite-r0','command':[py,'-I','-X','utf8',str(D/'test_probe_road_compile_c1c1.py'),'-v'],'cwd':str(D),'out':str(R/'road-c1c1-suite-r0-20261101'),'seconds':120,'max_bytes':268435456}]
(D/'suite-config.json').write_text(json.dumps({'parallel':1,'jobs':jobs}))
print(json.dumps({'brief_bytes':len(brief.encode()),'files':len(paths)}))
