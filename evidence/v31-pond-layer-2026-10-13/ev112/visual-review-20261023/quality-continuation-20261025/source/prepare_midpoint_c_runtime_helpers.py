from pathlib import Path
R=Path(__file__).parent
s=(R/'prepare_midpoint_native.py').read_text()
s=s.replace("O=R/'runtime-midpoint-b'","O=R/'runtime-midpoint-c'").replace('package-midpoint-b','package-midpoint-c').replace('PASS_27_MODELS_REPLACED_ALL_OTHER_ENTRIES_EXACT','PASS_25_MODELS_REPLACED_37_U2_EXACT').replace("v['unchanged_models']==35","v['unchanged_models']==37")
s=s.replace('@DayZ_Baltic_EV112_MidpointB','@DayZ_Baltic_EV112_MidpointC').replace('BalticMidpointB','BalticMidpointC')
s=s.replace("source=R/'runtime-rectangle-f/points.json'", "assert read(R/'river-131-midpoint-c/compiled-contact-review.json')['status']=='PACKED_COLLISION_AT_F_POSES_PASS'\nsource=R/'runtime-rectangle-f/points.json'")
(R/'prepare_midpoint_c_native.py').write_text(s)
s=(R/'finish_midpoint_probe.py').read_text().replace("O=R/'runtime-midpoint-b'/kind","O=R/'runtime-midpoint-c'/kind")
(R/'finish_midpoint_c_probe.py').write_text(s)
print('C native preparation ready, not launched')
