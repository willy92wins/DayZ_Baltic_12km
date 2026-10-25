"""Fixed-scale B/H native mesh and four profiles; inspection, not runtime proof."""
from pathlib import Path
import hashlib, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

HERE = Path(__file__).resolve().parent
B = HERE.parent.parent/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
REC = HERE/'authoring.json'
rec = json.loads(REC.read_text(encoding='utf-8'))
H = Path(rec['candidate_path'])
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(B) == 'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'
assert sha(H) == rec['candidate_sha256']
hb, hh = np.load(B)['heights'], np.load(H)['heights']
rr, cc = 840, 370
bb, aa = hb[rr-8:rr+9, cc-8:cc+9], hh[rr-8:rr+9, cc-8:cc+9]
fig = plt.figure(figsize=(15, 13))
specs = [('E–O', bb[8, :], aa[8, :], 6), ('N–S', bb[:, 8], aa[:, 8], 6),
         ('NO–SE', bb.diagonal(), aa.diagonal(), 6*np.sqrt(2)),
         ('NE–SO', np.fliplr(bb).diagonal(), np.fliplr(aa).diagonal(), 6*np.sqrt(2))]
for i, (name, b, h, step) in enumerate(specs):
    ax = fig.add_subplot(3, 2, i+1)
    x = np.arange(-8, 9)*step
    ax.plot(x, b, '.-', label='B referencia', color='#a55132')
    ax.plot(x, h, '.-', label='EV91 candidato', color='#126f77')
    ax.set(title=name, xlabel='Distancia al foco (m)', ylabel='Cota (m)')
    ax.grid(alpha=.2); ax.legend()
x, z = np.meshgrid(np.arange(-8, 9)*6, np.arange(8, -9, -1)*6)
tris = []
for r in range(16):
    for c in range(16):
        n = r*17+c; tris.extend(((n, n+1, n+18), (n, n+17, n+18)))
lo, hi = min(bb.min(), aa.min()), max(bb.max(), aa.max())
for i, (name, h) in enumerate((('B', bb), ('EV91', aa))):
    ax = fig.add_subplot(3, 2, 5+i, projection='3d')
    ax.plot_trisurf(x.ravel(), z.ravel(), h.ravel(), triangles=tris, cmap='terrain',
                    norm=Normalize(lo, hi), edgecolor='#11111150', linewidth=.25)
    ax.set(xlim=(-48, 48), ylim=(-48, 48), zlim=(lo, hi), title=name+' · escala vertical real',
           xlabel='X relativo (m)', ylabel='Z relativo (m)', zlabel='Cota (m)')
    ax.set_box_aspect((96, 96, hi-lo)); ax.view_init(elev=23, azim=-63)
fig.suptitle('Orilla X2220 / Z7242 · geometría offline\nMisma malla nativa, cámara y escala; no acredita aspecto ni agua en DayZ')
fig.tight_layout(rect=(0, 0, 1, .95))
fig.savefig(HERE/'profiles-mesh.png', dpi=140)
print(json.dumps({'image': str(HERE/'profiles-mesh.png'), 'candidate_sha256': sha(H)}))

