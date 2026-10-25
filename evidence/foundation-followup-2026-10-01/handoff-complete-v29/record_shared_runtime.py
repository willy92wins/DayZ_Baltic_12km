from pathlib import Path
import datetime as dt
import hashlib
import json
root=Path('P:/DayZ_Baltic_12km_dev')
out=root/'evidence/foundation-followup-2026-10-01/handoff-complete-v29'
now=dt.datetime.now(dt.timezone.utc).isoformat()
receipt={'observed_utc':now,'self_state':'none','own_runs':[],'box_occupied':True,'other_run':{'run_id':'7e4d808b-0efc-41ea-a978-997303d42a1c','mod':'@LFPowerGrid','state':'RUNNING','owner':'another session'},'action':'Read-only observation; no adoption, input, stop or lease requested. Prior Baltic cleanup receipt is the historical empty-box observation after own close.'}
(out/'shared-runtime-at-handoff.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
changes=json.loads((out/'document-changes.json').read_text('utf-8'))
def update_tracked(p,new):
    entry=next(x for x in changes['changes'] if Path(x['path'])==p)
    current=p.read_bytes()
    assert hashlib.sha256(current).hexdigest()==entry['after_sha256'], 'Concurrent edit'
    p.write_text(new,encoding='utf-8',newline='\n')
    entry['after_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()

p=root/'HANDOFF.md';h=p.read_text('utf-8')
h=h.replace('HANDOFF_V29_PARTIAL_ACCEPTANCE_NO_ACTIVE_RUNTIME','HANDOFF_V29_PARTIAL_ACCEPTANCE_NO_OWN_RUNTIME')
h=h.replace('Lease liberado; selfnone/boxempty/sinforeign. Sin DayZDiag/TB/NavMeshGenerator/AddonBuilder. ComputerUse reset/OFF. No operaciones UI nuevas.','Lease propio liberado; selfnone. Box quedo vacio al cierre; relectura posterior: otro run @LFPowerGrid 7e4d808b activo, no tocar/adoptar. Sin procesos Baltic propios niTB/NavMeshGenerator/AddonBuilder. CU reset/OFF.')
update_tracked(p,h)
p=root/'evidence/foundation-followup-2026-10-01/state.json';s=json.loads(p.read_text('utf-8'))
s['status']='HANDOFF_V29_PARTIAL_ACCEPTANCE_NO_OWN_RUNTIME'
s['updated_utc']=now
s['coordination']={'self_state':'none','own_runs':[],'box_occupied':True,'other_run':'7e4d808b-0efc-41ea-a978-997303d42a1c','other_mod':'@LFPowerGrid','observed_utc':now,'do_not_adopt_or_close':True,'receipt':'handoff-complete-v29/shared-runtime-at-handoff.json'}
s['own_processes']='None. Baltic load closed orderly and samplers exit0. Another session later launched @LFPowerGrid; leave it untouched.'
update_tracked(p,json.dumps(s,ensure_ascii=False,indent=2)+'\n')
p=Path('C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-01-dayz-baltic-handoff-base-v29.md')
v=p.read_text('utf-8')
old='- Lease liberado; `session_status`: `self.state=none`, `box.occupied=false`, sin runs ni procesos ajenos. Sin DayZDiag, TerrainBuilder, NavMeshGenerator o AddonBuilder en la lectura final de procesos.'
new='- Lease Baltic liberado. Al cerrar la prueba, `self.state=none`, `box.occupied=false` y no quedaban DayZDiag/TerrainBuilder/NavMeshGenerator/AddonBuilder. Una relectura antes de entregar ya muestra **otro run `@LFPowerGrid`, `7e4d808b-0efc-41ea-a978-997303d42a1c`, de otra sesión**. No se adoptó ni se cerró; consultar estado fresco antes de la próxima prueba. Nuestra sesión sigue sin lease ni procesos propios.'
assert old in v
p.write_text(v.replace(old,new),encoding='utf-8',newline='\n')
(out/'document-changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Own runtime remains closed; later shared run recorded without intervention.')
