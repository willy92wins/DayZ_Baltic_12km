from pathlib import Path
import sys,json,hashlib
B=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path.insert(0,str(W/'evidence/v30-full-mipmap-audit-2026-10-09'))
import audit_mipmaps as audit
audit.B=B
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ref=json.loads((B/'deploy.json').read_text());pbo=Path(ref['mod'])/'Addons/narva_trial.pbo';assert sha(pbo)==ref['files']['narva_trial.pbo']
_,_,entries=audit.read_pbo(pbo); reports=[];controls=[];done_kinds=set()
for name in ref['changed_entries']:
    base=Path(name).name;blob=entries[name];assert blob==(B/'surface/layers'/base).read_bytes()
    report=audit.verify_one(blob,base[0],B/'decoded'/Path(base).with_suffix('.png'))
    reports.append(dict(name=name,sha256=hashlib.sha256(blob).hexdigest(),**report))
    if base[0] not in done_kinds:
        for index in [3,7]:controls.append(audit.isolate_native(blob,name,index))
        done_kinds.add(base[0])
assert done_kinds=={'s','m'}
negative=audit.must_reject('new_payload_truncation_rejected',entries[ref['changed_entries'][0]][:-12])
report=dict(status='PASS_ALL_CHANGED_MIPS',changed_textures=len(reports),changed_mips=sum(len(x['levels']) for x in reports),unchanged_entries_exact=ref['unchanged_entries'],world_sha256=sha(pbo),negative=negative,native_controls=controls,files=reports,limits=['Every newly changed mip is decoded; unchanged textures inherit EV30 through exact PBO-entry identity.','Does not prove GPU streaming or close BALTIC-019.'])
(B/'changed-mips.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='files'},indent=2))
