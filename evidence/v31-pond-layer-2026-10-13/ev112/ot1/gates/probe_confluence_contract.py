"""Independent G7 confluence checks; no imports from the point generator.

The ordinary G7 side checks still enforce origin, two sides, six metre distance,
orientation and piece identity. This module checks the approved wet exception.
"""
import numpy as np
import gatelib as G


def validate(points, pieces, site_list, heights, runtime):
    errors = []
    def fail(name, *detail):
        errors.append((name, *detail))
    linked = set()
    for site in site_list:
        for end, relation in site.get('extend', {}).items():
            partner = relation.get('partner')
            if partner and site.get('ends', {}).get(end) == 'kit':
                linked.add(frozenset((site['id'], partner)))
    branches = {}
    for (sid, _), piece in pieces.items():
        branches.setdefault(sid, []).append(piece)
    required = set()
    for p in points:
        if p.get('kind') != 'kit_confluence':
            continue
        ident = p.get('id'); sid = p.get('site'); other = p.get('other_site')
        if p.get('expect') != 'wet':
            fail('confluence_expect', ident, p.get('expect'))
        if not isinstance(other,str) or other == sid or sid not in branches or other not in branches:
            fail('confluence_built_partner', ident, other); continue
        pair = frozenset((sid,other))
        if pair not in linked:
            fail('confluence_relation', ident, sid, other); continue
        q = np.array([p.get('x',np.nan),p.get('z',np.nan)],float)
        if not np.isfinite(q).all():
            fail('confluence_position', ident); continue
        distance = np.inf
        for pc in branches[other]:
            line = pc.world(pc.centre_model)[:,[0,2]]
            for a,b in zip(line[:-1],line[1:]):
                ab=b-a; length2=float(ab@ab)
                t=float(np.clip((q-a)@ab/length2,0,1)) if length2 else 0.0
                distance=min(distance,float(np.linalg.norm(q-(a+t*ab))))
        if not distance <= 1.8:
            fail('confluence_axis_distance',ident,float(distance))
        ground=float(G.terrain_y(heights,q[0],q[1]))
        water=float(G.surface(branches[other],q.reshape(1,2),'water')[0])
        if not (np.isfinite([ground,water]).all() and water > ground):
            fail('confluence_partner_not_wet',ident,other)
        for key,actual in (('ground',ground),('other_water',water),('other_axis_distance',distance)):
            stated=p.get(key)
            if not isinstance(stated,(int,float)) or not np.isfinite(stated) or not abs(stated-actual)<=1e-3:
                fail('confluence_value',ident,key)
        required.add(pair)
    sampled={frozenset((p['site'],p['other_site'])) for p in runtime if p.get('kind')=='kit_confluence' and isinstance(p.get('other_site'),str)}
    for pair in sorted(required-sampled,key=lambda pair:sorted(pair)):
        fail('runtime_confluence_coverage',*sorted(pair))
    return errors
