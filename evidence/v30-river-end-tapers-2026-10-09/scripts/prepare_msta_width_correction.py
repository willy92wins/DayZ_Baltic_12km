from pathlib import Path
B=Path('E:/DayZ-Baltic-Build/v30-river-end-tapers-20261009')
src=(B/'author_msta_taper.py').read_text()
old="radius=max(.01,pt.distance(old.boundary)) if old.covers(pt) else .01"
new="radius=max(.01,section(h,p,axis,max(float(s),18.))['width_m']/2)"
assert src.count(old)==1
src=src.replace(old,new).replace("out=B/'candidate-msta'","out=B/'candidate-msta-r2'")
src=src.replace("print(json.dumps(sections,indent=1))","print('Section widths retained in authoring.json')")
(B/'author_msta_taper_r2.py').write_text(src)
ver=(B/'verify_msta_taper.py').read_text().replace('candidate-msta/','candidate-msta-r2/').replace("'msta-verification.json'","'msta-r2-verification.json'").replace("'msta-native-contour.png'","'msta-r2-native-contour.png'")
(B/'verify_msta_taper_r2.py').write_text(ver)
turn=(B/'check_msta_turns.py').read_text().replace('candidate-msta/','candidate-msta-r2/').replace("'msta-turns.json'","'msta-r2-turns.json'")
(B/'check_msta_turns_r2.py').write_text(turn)
print('R2 measures transverse width; terminal boundary distance no longer feeds the radius. All other parameters preserved.')
