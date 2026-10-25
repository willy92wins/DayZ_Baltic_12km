"""Independent final surface scope, bound outside the manifest being checked.

Native causeway/dam marks: cells incident to marked vertices, one cell padding,
then the original two pixel zone. Clearings: exact pixels for material slots,
three pixels of RGB blend, including world-edge padding. Road tests keep their
original road-only domain. This module does not import the patch producer.
"""
import os,json
from pathlib import Path
import numpy as np
from scipy.ndimage import maximum_filter
import gate_lib as G
_DOC=_CLEAR=_EXTRA=None

def binding():
    global _DOC
    if _DOC is None:
        p=Path(os.environ['SURFACE_EV112_BINDING']);d=json.loads(p.read_text(encoding='utf-8'))
        assert d['terrain']['sha256']==G.TARGET_TERRAIN_SHA
        assert G.sha(d['terrain']['path'])==G.TARGET_TERRAIN_SHA
        assert d['include_names']==['v31_causeway','v31_dam'] and d['include_pad_cells']==1
        assert G.sha(d['clearings']['path'])==d['clearings']['sha256']
        e=d['explicit_native_cells'];assert G.sha(e['path'])==e['sha256']
        assert G.sha(e['contract_path'])=='28191cce4fe4ec7f240bbaf14cc7a07546748a98fdaa5221661b1649150668a2'
        given=np.load(e['path'],allow_pickle=False);assert given.shape==(2047,2047) and given.dtype==bool
        expected=np.zeros_like(given)
        for cell in json.loads(Path(e['contract_path']).read_text())['cut_cells']:expected[cell['r'],cell['c']]=True
        assert np.array_equal(given,expected) and int(given.sum())==33
        _DOC=d
    return _DOC

def clearing_binding():return binding()['clearings']

def extra_cells():
    global _EXTRA
    if _EXTRA is None:
        d=binding();z=np.load(d['terrain']['path']);v=np.zeros((2048,2048),bool)
        for key in d['include_names']:
            a=z[key];assert a.shape==v.shape and a.dtype==bool;v|=a
        c=np.zeros((2047,2047),bool)
        for dr in (0,1):
            for dc in (0,1):c|=v[dr:2047+dr,dc:2047+dc]
        _EXTRA=maximum_filter(c,size=3,mode='constant',cval=0)
        _EXTRA|=np.load(d['explicit_native_cells']['path'],allow_pickle=False)
    return _EXTRA

def clearing_zone(a,b,prefix):
    global _CLEAR
    if _CLEAR is None:
        _CLEAR=np.load(clearing_binding()['path'],mmap_mode='r');assert _CLEAR.shape==(12288,12288) and _CLEAR.dtype==bool
    X,Z=G.tile_xz(a,b,pad=3);r=np.floor(12288-Z).astype(int);c=np.floor(X).astype(int);inside=(r>=0)&(r<12288)&(c>=0)&(c<12288)
    sample=np.zeros(X.shape,bool);sample[inside]=_CLEAR[r[inside],c[inside]]
    if prefix=='s':sample=maximum_filter(sample,size=7,mode='constant',cval=0)
    else:assert prefix=='m'
    return sample[3:-3,3:-3]

def allowed_zone(road_domain,a,b,prefix):
    return G.tile_zone(road_domain|extra_cells(),a,b)|clearing_zone(a,b,prefix)

def expected_tiles(road_domain):
    return [(a,b) for a in range(32) for b in range(32) if allowed_zone(road_domain,a,b,'s').any()]
