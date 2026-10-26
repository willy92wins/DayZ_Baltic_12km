from pathlib import Path
R=Path(__file__).parent
s=(R/'screen_kit7_nav_corridors.py').read_text()
s=s.replace("'packed-corridor-screen.json'","'packed-full-corridor-screen.json'")
s=s.replace("record['screen_pass']=","record['corridor_wet_area']=line.buffer(2.1).intersection(allwater).area;record['corridor_outside_area']=line.buffer(2.1).difference(allowed.buffer(.01)).area;record['screen_pass']=record['corridor_wet_area']<1e-8 and record['corridor_outside_area']<1e-8 and ")
exec(compile(s,__file__,'exec'))
