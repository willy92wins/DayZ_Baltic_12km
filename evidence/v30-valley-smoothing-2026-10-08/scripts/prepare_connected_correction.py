"""C1: exact source supports only at independently measured local regressions."""
from pathlib import Path
B=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008')
text=(B/'build_connected_valley.py').read_text()
for old,new in [("out=B/'candidate-c'","out=B/'candidate-c1'"),("fixed=mask['fixed'].copy()","fixed=mask['fixed'].copy()\nfixed|=np.load(B/'contour-c1-fixed.npz')['fixed']"),("E/'authoring-c.json'","E/'authoring-c1.json'")]:
    assert text.count(old)==1,old
    text=text.replace(old,new)
(B/'correct_connected_valley.py').write_text(text)
print('Generated C1 single correction: exact source pins on 73 local vertices.')
