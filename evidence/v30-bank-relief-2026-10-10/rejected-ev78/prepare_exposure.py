from pathlib import Path
B=Path(__file__).parent;R=B.parent
old=(R/'v30-remaining-exact-dry-support-20261009/audit_exposure.py').read_text()
a="S=R/'v30-exact-dry-support-20261009'";assert old.count(a)==1
new=old.replace(a,"S=R/'v30-remaining-exact-dry-support-20261009'")
new=new.replace('bb2662993963892c4b0903492d2b4b100ec075c517d63e0797b0f9782e91d435','d89b92af86f3b376e50b2b0d107a94dd94a380f966ca9c666ba9fbc8d95f88d7')
a="objects=[]\nfor o in read(src)['objects']:"
b="all_objects=read(src)['objects']\nwater_ids={o['id'] for o in all_objects if o['name'].lower().startswith('baltic_water_v30')}\nassert len(water_ids)==18024 and water_ids.issubset(bounds), 'Incomplete compiled bounding inventory'\nobjects=[]\nfor o in all_objects:"
assert a in new;new=new.replace(a,b)
(B/'audit_exposure.py').write_text(new,encoding='utf-8')
print('Exposure consumer prepared against exact EV71 WRP, unchanged compiled water, complete object inventory.')
