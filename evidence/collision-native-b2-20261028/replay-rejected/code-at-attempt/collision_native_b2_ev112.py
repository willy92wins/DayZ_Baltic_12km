"""B2 native record contract. Completeness never promotes a physical FAIL.

Pure parsing/evaluation; an external binder must prove run/artifact identity.
No native or historical surface identity is inferred from empty object sets.
"""
from collections import defaultdict
import re
from water_query_diag_b1_ev112 import (require, finite, f32, integer, boolean,
                                     vector, scalar_error, ulp32, origin_matches)

IDS = (349, 348, 350, 311, 700, 701, 723, 725, 1425, 1426)
OFFSETS = ((0.,0.),(.005,0.),(-.005,0.),(.02,0.),(-.02,0.),
           (0.,.005),(0.,-.005),(0.,.02),(0.,-.02))
CODES = ('RH', 'RL', 'BH', 'BL')
HEADER = 'BALTIC_COLLISION_B2;BalticTrial'
VECTOR_ERROR = .500001e-6  # Six fractional decimal places, not a physical band.


def source_points(frozen, original):
    require(original['status'] == 'FAIL' and original['points'] == 2658, 'original_verdict')
    orig = {p['id']: p for p in original['rows']}
    require(len(orig) == len(original['rows']) == 2658, 'original_ids')
    require(len({p['id'] for p in original['failures']}) == 47 and
            len({p['id'] for p in original['inconclusive']}) == 21, 'original_coverage')
    require([(p['id'],p['slot']) for p in frozen] == [(i,s) for i in IDS for s in range(9)], 'point_universe')
    points = []
    for p in frozen:
        o = orig[p['id']]
        e = o['expected']
        dx, dz = OFFSETS[p['slot']]
        require(p['x'] == f32(e['x']+dx) and p['z'] == f32(e['z']+dz), 'central_or_offset_changed')
        require(p['H'] == e['ground'] and p['B'] == e['effective_bed'] and
                p['original_states'] == o['states'], 'original_binding')
        require(p['nominal_offset'] == [dx,dz] and
                p['effective_offset'] == [p['x']-e['x'],p['z']-e['z']], 'offset_binding')
        require(p['low_y'] == f32(max(p['H'],p['B'])+2), 'fixed_low_changed')
        require(p['state'] == 'CLEAR_UNDER_FRAME_HYPOTHESES', 'offline_condition_changed')
        for k in ('x','z','H','B','low_y','terrain_at_offset'):
            finite(p[k])
        points.append(dict(p, original_expected=e, original_measured=o['measured']))
    return points


def csv_for(points):
    require([(p['id'],p['slot']) for p in points] == [(i,s) for i in IDS for s in range(9)], 'csv_universe')
    return ''.join(f"{p['id']};{p['slot']};{f32(p['x']):.9g} 0 {f32(p['z']):.9g};{f32(p['low_y']):.9g}\n" for p in points)


def signed_component(s):
    require(bool(re.fullmatch(r'-1|0|[1-9][0-9]*', s)), 'component')
    return int(s)


def parse(text, points):
    require(len(points) == 90, 'point_count')
    lines = text.splitlines()
    require(lines[:4] == [HEADER,'BEGIN;90;3','LINK;GetTransform;BEGIN','LINK;GetTransform;OK']
            and lines[-1:] == ['END;270'], 'header_footer_or_link')
    cursor, last_end, rows, observed_layer = 4, -1, [], None
    def take(tag, n, key):
        nonlocal cursor
        require(cursor < len(lines)-1, 'truncated')
        a = lines[cursor].split(';'); cursor += 1
        require(len(a) == n and a[0] == tag, 'schema:'+tag)
        require(tuple(map(integer,a[1:4])) == key, 'record_order:'+tag)
        return a
    for rnd in range(3):
        for p in points:
            key = (rnd,p['id'],p['slot'])
            a = take('Q',15,key)
            t0,t1,t2 = map(integer,a[4:7])
            require(last_end < t0 <= t1 <= t2, 'clock_order')
            last_end = t2
            r = dict(round=rnd,id=p['id'],slot=p['slot'],t0=t0,t1=t1,t2=t2,
                     pos=vector(a[7]),ground=finite(a[8]),high=vector(a[9]),low=vector(a[10]),
                     end=vector(a[11]),object_count=integer(a[12]),proxy_count=integer(a[13]),
                     bullet_layer=integer(a[14]),rays={},objects=[])
            # Q observes script string representation of the same symbol used
            # in the native call, not the integer received inside the engine.
            require(r['bullet_layer'] > 0, 'bullet_layer_nonpositive')
            if observed_layer is None: observed_layer = r['bullet_layer']
            require(r['bullet_layer'] == observed_layer, 'bullet_layer_drift')
            require(r['object_count'] <= 10000 and r['proxy_count'] <= 10000, 'object_limit')
            for code in CODES:
                b = take('R',11,key)
                require(b[4] == code, 'ray_order')
                ray = dict(hit=boolean(b[5]),pos=vector(b[6]),normal=vector(b[7]),
                           component=signed_component(b[8]),fraction=finite(b[9]),objects=[])
                count = integer(b[10])
                require(count <= 10000, 'hit_limit')
                require(code.startswith('R') or (count == 1 and ray['component'] == -1), 'bullet_schema')
                require(not code.startswith('R') or ray['fraction'] == 0, 'rv_fraction')
                for index in range(count):
                    h = take('H',9,key)
                    require(h[4] == code and integer(h[5]) == index, 'hit_order')
                    obj = dict(valid=boolean(h[6]),shape=h[7],pos=vector(h[8]))
                    require(obj['valid'] or (obj['shape'] == '' and obj['pos'] == [0.,0.,0.]), 'null_hit_payload')
                    ray['objects'].append(obj)
                r['rays'][code] = ray
            for oi in range(r['object_count']):
                b = take('O',12,key)
                require(integer(b[4]) == oi, 'object_order')
                obj = dict(index=oi,valid=boolean(b[5]),shape=b[6],pos=vector(b[7]),
                           matrix=[v for s in b[8:12] for v in vector(s)])
                require(obj['valid'] or (obj['shape'] == '' and not any(obj['pos']+obj['matrix'])), 'null_object_payload')
                r['objects'].append(obj)
            rows.append(r)
    require(cursor == len(lines)-1, 'extra_records')
    return rows


def norm(name):
    return name.replace('\\','/').strip('/').lower()


def match_pose(obj, candidates):
    """All same-model scene instances, not merely the four ray candidates."""
    if not obj['valid'] or not obj['shape']:
        return dict(state='INVALID_OR_NULL',matches=[])
    matches = []
    for p in candidates:
        delta = [a-b for a,b in zip(obj['pos'],p['matrix'][9:])]
        if max(map(abs,delta)) <= VECTOR_ERROR:
            item = dict(instance=int(p['id']),position_residual=delta)
            if 'matrix' in obj:
                residual = [a-b for a,b in zip(obj['matrix'],p['matrix'])]
                item.update(matrix_residual=residual,matrix_matches_format=max(map(abs,residual)) <= VECTOR_ERROR)
            matches.append(item)
    return dict(state='UNMATCHED' if not matches else 'AMBIGUOUS' if len(matches)>1 else 'MATCHED',matches=matches)


def classify(ray, ground):
    if not ray['hit']:
        return dict(label='MISS',contact_height=None,contact_minus_nominal_surfacey=None)
    error = ray['pos'][1]-ground
    if any(o['valid'] for o in ray['objects']):
        label = 'OBJECT_HIT'
    else:
        label = 'NO_OBJECT_NEAR_SURFACE' if abs(error) <= VECTOR_ERROR+scalar_error(ground) else 'NO_OBJECT_OFF_SURFACE'
    return dict(label=label,contact_height=ray['pos'][1],contact_minus_nominal_surfacey=error)


def evaluate(points, rows, hits, candidate_ids, lookup):
    require([(r['round'],r['id'],r['slot']) for r in rows] ==
            [(rnd,p['id'],p['slot']) for rnd in range(3) for p in points], 'evaluation_order')
    bypoint = {(p['id'],p['slot']):p for p in points}
    byhit = defaultdict(list)
    for h in hits:
        require((h['id'],h['slot']) in bypoint, 'geometry_point')
        finite(h['height']); byhit[h['id'],h['slot']].append(h)
    first, central, details, confounders, ground_mismatches = {}, {}, [], [], []
    for r in rows:
        key = (r['id'],r['slot']); p = bypoint[key]
        x,z,h = p['x'],p['z'],r['pos'][1]
        err = VECTOR_ERROR + .5*ulp32(h)
        require(all(f32(r['pos'][i]) == value for i,value in ((0,x),(2,z))), 'position_identity')
        require(abs(r['ground']-h) <= scalar_error(r['ground'])+VECTOR_ERROR, 'ground_echo')
        require(origin_matches(r['high'],[x,f32(h+100),z],err) and
                origin_matches(r['end'],[x,f32(h-10),z],err), 'high_or_end_origin')
        require(abs(r['low'][1]-p['low_y']) <= VECTOR_ERROR and
                all(f32(r['low'][i]) == v for i,v in ((0,x),(2,z))), 'fixed_low_origin')
        reasons, poses, seen = ['native_bullet_layer_ordinal_unverified'], [], set()
        if r['t1'] != r['t0']: reasons.append('ray_interval_clock_changed_not_motion_proof')
        if r['proxy_count']: reasons.append('native_proxy_snapshot_unbound')
        for obj in r['objects']:
            m = lookup(obj)
            poses.append(dict(index=obj['index'],**m))
            seen.update(v['instance'] for v in m['matches'])
            if m['state'] != 'MATCHED': reasons.append('object_'+m['state'].lower())
            if any(not v.get('matrix_matches_format',False) for v in m['matches']): reasons.append('matrix_differs_from_WRP')
        missing = sorted(set(candidate_ids)-seen)
        if missing: reasons.append('ray_candidate_not_in_native_snapshot')
        stable = sorted((o['valid'],norm(o['shape']),tuple(o['pos']),tuple(o['matrix'])) for o in r['objects'])
        if key not in first: first[key] = stable
        elif stable != first[key]: reasons.append('round_state_drift')
        delta_h = r['ground']-p['terrain_at_offset']
        if abs(delta_h) > .01:
            ground_mismatches.append(dict(round=r['round'],id=r['id'],slot=r['slot'],error=delta_h))
        ray_details = {}
        for code,ray in r['rays'].items():
            matches = [lookup(o) for o in ray['objects']]
            if any(o['valid'] and m['state'] != 'MATCHED' for o,m in zip(ray['objects'],matches)):
                reasons.append('hit_object_unbound:'+code)
            # Miss out-parameters are unspecified; retain raw data, never classify them as a contact.
            comparison = []
            if ray['hit']:
                for hit in byhit[key]:
                    comparison.append(dict(hit,native_minus_geometry=ray['pos'][1]-hit['height']))
            ray_details[code] = dict(classify(ray,r['ground']),objects=matches,
                contact_xz_delta=[ray['pos'][0]-x,ray['pos'][2]-z] if ray['hit'] else None,
                geometry_at_nominal_xz=comparison)
        ck = (r['round'],r['id'])
        if r['slot'] == 0: central[ck] = ray_details
        offset_comparison = {}
        for code in CODES:
            v = ray_details[code]['contact_height']; c = central[ck][code]['contact_height']
            offset_comparison[code] = None if v is None or c is None else v-c
        differences = {}
        for name,a,b in (('RV_high_minus_low','RH','RL'),('Bullet_high_minus_low','BH','BL')):
            va,vb = ray_details[a]['contact_height'],ray_details[b]['contact_height']
            differences[name] = None if va is None or vb is None else va-vb
        reasons = sorted(set(reasons))
        confounders.extend(dict(round=r['round'],id=r['id'],slot=r['slot'],reason=v) for v in reasons)
        details.append(dict(round=r['round'],id=r['id'],slot=r['slot'],measured=r,
            original_states=p['original_states'],original_expected=p['original_expected'],
            original_measured=p['original_measured'],offline_origin_state=p['state'],
            ground_minus_npz=delta_h,poses=poses,missing_candidates=missing,rays=ray_details,
            high_low=differences,offset_minus_central=offset_comparison,confounders=reasons))
    return dict(status='INCONCLUSIVE_DIAGNOSTIC',contract_complete=True,identity_bound=False,
        rows=len(rows),rays=len(rows)*4,original_native_verdict='FAIL',original_fail_points=47,
        original_uncertain_points=21,ground_reference_mismatches=ground_mismatches,
        confounders=confounders,details=details,layer_observation=dict(
            script_representation=rows[0]['bullet_layer'],symbol='PhxInteractionLayers.BUILDING',
            previous_ordinal_hypothesis=2,mapping_status='UNVERIFIED_FOR_ANY_VALUE'),limits=[
            'Positive stable layer representation is an instrument restriction, not certification of engine layer semantics.',
            'The former ordinal2 hypothesis was rejected by native data; no integer, including2, certifies the mapping.',
            'RV versus Bullet uses different consumers/layers; disagreement alone is not a geometric cause.',
            'Empty returned objects do not identify terrain; SurfaceY comparison uses nominal emitted XZ.',
            'Geometry contacts are conditional frame hypotheses at nominal XZ, not native surface identity.',
            'On-disk static census does not certify animation, dynamic objects or occupied volume.',
            'WRP matrix layout versus native aside/up/dir/position remains a hypothesis; residuals alone do not prove motion.',
            'No original state, tolerance or product expectation is changed.'])


def consume(text, csv, frozen, original, hits, candidate_ids, lookup):
    points = source_points(frozen,original)
    require(csv == csv_for(points), 'csv_source_binding')
    return evaluate(points,parse(text,points),hits,candidate_ids,lookup)
