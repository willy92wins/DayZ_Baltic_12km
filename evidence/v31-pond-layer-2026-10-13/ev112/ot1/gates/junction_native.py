"""Independent continuous dry-gap measurement on native terrain triangles.

Split the test segment at grid edges, NW-SE diagonals and every water-face edge.
Within each interval, terrain and each water face are affine, so their crossings
are solved analytically. Pond planes come from the last generated footprint.
No sampled point count can turn a missing water connection into PASS.
"""
import numpy as np
import gatelib as G


def cross(a, b):
    return a[0]*b[1] - a[1]*b[0]


def face_y(face, q):
    a, b, c = face[:, [0, 2]]
    den = cross(b-a, c-a)
    if abs(den) < 1e-12:
        return None
    u, v = cross(q-a, c-a)/den, cross(b-a, q-a)/den
    return face[0, 1] + u*(face[1, 1]-face[0, 1]) + v*(face[2, 1]-face[0, 1])


def segment_wet(a, b, H, plane, pieces):
    d = b-a; length = float(np.linalg.norm(d))
    if length < 1e-9:
        return [], 0.0
    cuts = [0.0, 1.0]
    for origin, delta in ((a[0], d[0]), (G.ZTOP-a[1], -d[1]), (a.sum()-G.ZTOP, d.sum())):
        if abs(delta) > 1e-12:
            lo, hi = sorted((origin, origin+delta))
            cuts += [(6*k-origin)/delta for k in range(int(np.floor(lo/6))+1, int(np.ceil(hi/6)))
                     if 0 < (6*k-origin)/delta < 1]
    lo, hi = np.minimum(a,b), np.maximum(a,b)
    faces = []
    for p in pieces:
        if np.any(p.hi < lo) or np.any(p.lo > hi):
            continue
        for face in p.water:
            verts = face[:, [0, 2]]
            if np.any(verts.max(0) < lo) or np.any(verts.min(0) > hi):
                continue
            faces.append(face)
            for e, f in zip(verts, np.roll(verts, -1, axis=0)):
                den = cross(d, f-e)
                if abs(den) < 1e-12:
                    continue
                t, u = cross(e-a, f-e)/den, cross(e-a, d)/den
                if 0 < t < 1 and -1e-9 <= u <= 1+1e-9:
                    cuts.append(float(t))
    cuts = sorted(set(round(t, 12) for t in cuts))
    wet = []
    for l, r in zip(cuts[:-1], cuts[1:]):
        if r-l < 1e-10:
            continue
        mid = a + ((l+r)/2)*d
        # Interior evaluations avoid selecting an adjacent native triangle at an edge.
        q1, q2 = a+(l+(r-l)*.25)*d, a+(l+(r-l)*.75)*d
        h1, h2 = G.terrain_y(H, q1[0], q1[1]), G.terrain_y(H, q2[0], q2[1])
        hleft, hright = 1.5*h1-.5*h2, 1.5*h2-.5*h1
        rr, cc = int(np.floor((G.ZTOP-mid[1])/6)), int(np.floor(mid[0]/6))
        sheets = []
        rows = [rr, rr-1] if abs((G.ZTOP-mid[1])/6-rr) < 1e-9 else [rr]
        cols = [cc, cc-1] if abs(mid[0]/6-cc) < 1e-9 else [cc]
        for ri in rows:
            for ci in cols:
                if 0 <= ri < plane.shape[0] and 0 <= ci < plane.shape[1] and np.isfinite(plane[ri, ci]):
                    sheets.append((plane[ri, ci], plane[ri, ci]))
        for face in faces:
            y = G.tri_max(np.asarray([face]), mid.reshape(1,2), np.full(1, -np.inf))[0]
            if np.isfinite(y):
                sheets.append((face_y(face, a+l*d), face_y(face, a+r*d)))
        for y0, y1 in sheets:
            g0, g1 = y0-hleft, y1-hright
            if g0 <= 0 and g1 <= 0:
                continue
            w0, w1 = l, r
            if g0 <= 0:
                w0 = l+(r-l)*(-g0)/(g1-g0)
            if g1 <= 0:
                w1 = l+(r-l)*(-g0)/(g1-g0)
            wet.append((w0*length, w1*length))
    return wet, length


def dry_gap(path, H, plane, pieces):
    offset, intervals = 0.0, []
    for a,b in zip(path[:-1],path[1:]):
        spans, length = segment_wet(np.asarray(a),np.asarray(b),H,plane,pieces)
        intervals.extend((a+offset,b+offset) for a,b in spans)
        offset += length
    cursor, maximum, wet_length = 0.0, 0.0, 0.0
    for a,b in sorted(intervals):
        maximum = max(maximum, a-cursor)
        wet_length += max(0,b-max(a,cursor))
        cursor = max(cursor,b)
    maximum = max(maximum,offset-cursor)
    return dict(path_m=offset, max_dry_m=maximum, wet_m=wet_length, intervals=len(intervals))
