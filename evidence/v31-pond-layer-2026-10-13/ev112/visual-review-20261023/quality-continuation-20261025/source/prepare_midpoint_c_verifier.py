from pathlib import Path
import shutil
R=Path(__file__).parent;C=R/'river-131-midpoint-c';B=R/'river-131-midpoint-b'
shutil.copyfile(B/'f-pose-binding.json',C/'f-pose-binding.json')
s=(R/'verify_midpoint_compiled_contact.py').read_text()
s=s.replace("B=R/'river-131-midpoint-b'","B=R/'river-131-midpoint-c'")
s=s.replace('42d0b42d7ba8d07f2f5fe42515a6af57973986567781459ad6e8c15f7eb4ea39','23c5f93336b9ef781569575a35f274a7e05b6943278d7774cca46bc97ba6ed50')
s=s.replace("pbo=B/'packed/baltic_stream_pilot.pbo'","pbo=R/'package-midpoint-c/Addons/baltic_stream_pilot.pbo'")
s=s.replace('46390aff4704c9bb1a075cb4e4cf2224143dd30713a4bccf49cf0103226a28c8','c7dc430d809bcec2f29ff1fe86f266f0f9680b8ad676a8722b0b45d4494de02f')
old="_,_,entries=read_pbo(pbo);assert {n for n in entries if n.lower().endswith('.p3d')}=={i['model'].split('\\\\')[-1] for i in new['instances']}"
assert old in s
new="""_,_,entries=read_pbo(pbo)
base_pbo=Path('P:/Mods/@DayZ_Baltic_EV112_RectangleF/Addons/baltic_stream_pilot.pbo')
assert sha(base_pbo)=='c0be9abc9d36ee19c636325b825dbf09880a9dc31b5dfb8432e0f91d0e1cfa87'
_,_,base_entries=read_pbo(base_pbo)
model_names={i['model'].split('\\\\')[-1] for i in new['instances']}
changed=model_names-{'cs_131p0_0_0300.p3d','cs_131p0_0_0312.p3d'}
assert len(model_names)==27 and len(changed)==25 and set(entries)==set(base_entries)
assert {n for n in entries if entries[n]!=base_entries[n]}==changed
assert len([n for n in entries if n.lower().endswith('.p3d')])==62
"""
s=s.replace(old,new)
s=s.replace("pbo,A/'author-report.json'","pbo,base_pbo,R/'package-midpoint-c/verification.json',A/'author-report.json'")
p=R/'verify_midpoint_c_compiled_contact.py';assert not p.exists();p.write_text(s)
print('Prepared exact C consumer with25 replacements and37 baseline models checked')
