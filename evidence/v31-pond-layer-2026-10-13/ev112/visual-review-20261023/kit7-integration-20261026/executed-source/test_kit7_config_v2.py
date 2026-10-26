from pathlib import Path
import json,sys,re
R=Path(__file__).parent;sys.path.insert(0,str(R));import package_kit7_fc_pilot_v2 as m
O=R/'package-kit7-fc-pilot-20261026';a=(O/'old-config.cpp').read_text(encoding='utf-8-sig');b=(O/'decoded.cpp').read_text(encoding='utf-8-sig')
c=m.read(R/'river-131-midpoint-c/author-report.json')['instances']
_,_,old=m.read_pbo(R/'package-midpoint-c/Addons/baltic_stream_pilot.pbo');_,_,new=m.read_pbo(R/'river-kit7-midpoint-a-20261026/packed/baltic_stream_pilot.pbo')
om={n for n in old if n.endswith('.p3d')};nm={n for n in new if n.endswith('.p3d')}
m.verify_config(a,b,c,om,nm)
block=re.search(r'class Land_cs_kit_7_0000\s*:\s*HouseNoDestruct\s*\{.*?\};',b,re.S).group()
mutants={'wrong_scope':re.sub(r'scope\s*=\s*1\s*;','scope=2;',b,count=1),'missing_class':b.replace(block,''),'duplicate_class':b.replace(block,block+'\n'+block),'wrong_dependency':b.replace('DZ_Surfaces','DZ_NoSuchSurface'),'wrong_old_model':b.replace('\\cs_131p0_0_0000.p3d','\\cs_131p0_0_missing.p3d')}
out={}
for name,text in mutants.items():
 assert text!=b,name
 try:m.verify_config(a,text,c,om,nm)
 except AssertionError:out[name]=True
 else:raise AssertionError(name+' accepted')
p=R/'kit7-config-v2-controls.json';assert not p.exists();p.write_text(json.dumps(dict(status='PASS_REAL_CONFIG_CONTROLS',positive=True,rejected=out,existing_classes=27,repaired_legacy_classes=35,new_classes=139,total_classes=201),indent=2)+'\n');print('PASS_REAL_CONFIG_CONTROLS',out)
