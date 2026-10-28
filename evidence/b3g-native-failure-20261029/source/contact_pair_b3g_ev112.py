"""B3G wire/physical channels: raw evidence first, never a global map verdict.

Pure offline consumer. A separate native identity binder must establish both arms.
B2 supplies only the frozen point contract and strict Q/R/H/O syntax, not its
historical geometry comparison, capture, CLI or physical verdict.
"""
import hashlib,math
from collections import Counter
import collision_native_b2_ev112 as wire
from water_query_diag_b1_ev112 import require,integer,boolean,finite,f32,scalar_error,ulp32,origin_matches

HEADER='BALTIC_CONTACT_B3G;BalticTrial'
CHANNELS=('ground','roadway','water','rv_high','rv_low','bullet_high','bullet_low')
REQUIRED=('id','x','z','ground','roadway','effective_bed','water_ext','expect','bed_shapes','uncertain')
UNCERTAIN={'water_boundary_numeric','water_depth_numeric','flagged_surface','outside_changed_model_after_roundtrip','foreign_bed_support'}


def contract(frozen,original):
    points=wire.source_points(frozen,original)
    for p in points:
        e=p['original_expected']
        require(all(k in e for k in REQUIRED),'incomplete_original_contract')
        require(e['id']==p['id'] and e['expect'] in ('dry','wet'),'expectation_identity')
        require(set(e['uncertain'])<=UNCERTAIN,'unknown_uncertainty')
        for k in ('x','z','ground','roadway'):finite(e[k])
        for k in ('effective_bed','water_ext'):
            if e[k] is not None:finite(e[k])
        require(e['expect']!='wet' or e['water_ext'] is not None,'wet_without_surface')
        require(isinstance(e['bed_shapes'],list) and all(isinstance(v,str) and v for v in e['bed_shapes']),'bed_shapes')
        require(e['effective_bed'] is None or e['bed_shapes'],'bed_without_identity')
    return points


def parse(text,points):
    lines=text.splitlines();require(lines and lines[0]==HEADER,'b3g_header')
    plain=[wire.HEADER];water=[];i=1
    while i<len(lines):
        line=lines[i];require(not line.startswith('W;'),'water_out_of_order')
        plain.append(line);i+=1
        if not line.startswith('Q;'):continue
        require(i<len(lines),'water_missing');a=lines[i].split(';');q=line.split(';');i+=1
        require(len(a)==20 and a[0]=='W' and a[1:4]==q[1:4],'water_schema_or_key')
        water.append(dict(start=integer(a[4]),end=integer(a[5]),sea=boolean(a[6]),pond=boolean(a[7]),
                          surface=finite(a[8]),depth=finite(a[9]),road=finite(a[10]),
                          refs=[dict(sea=boolean(a[k]),pond=boolean(a[k+1]),surface=finite(a[k+2])) for k in (11,14,17)]))
    adapted='\n'.join(plain)+'\n';rows=wire.parse(adapted,points)
    require(len(water)==len(rows)==270,'water_count')
    for r,w in zip(rows,water):
        require(r['t0']<=r['t1']<=w['start']<=w['end']<=r['t2'],'water_clock_order')
        r['water']=w
    return rows,dict(normalized_text_sha256=hashlib.sha256(text.encode()).hexdigest(),adapted_sha256=hashlib.sha256(adapted.encode()).hexdigest(),
                     transformation='Validated B3G header, removed exactly one W immediately after every Q, replaced header by fixed B2 syntax header; no other record transformed.')


def origins(r,p):
    x,z,h=p['x'],p['z'],r['pos'][1];err=wire.VECTOR_ERROR+.5*ulp32(h)
    require(all(f32(r['pos'][i])==v for i,v in ((0,x),(2,z))),'position_identity')
    require(abs(r['ground']-h)<=scalar_error(r['ground'])+wire.VECTOR_ERROR,'ground_echo')
    require(origin_matches(r['high'],[x,f32(h+100),z],err) and origin_matches(r['end'],[x,f32(h-10),z],err),'high_end_origin')
    require(abs(r['low'][1]-p['low_y'])<=wire.VECTOR_ERROR and all(f32(r['low'][i])==v for i,v in ((0,x),(2,z))),'fixed_low_origin')


def central_channels(r,e):
    """Same physical bands/uncertainties as dry_road_native_consumer:27-61.

    Bullet has no fresh independent calibration: no guessed/old margin used.
    RV empty-object case is the original identity predicate, not terrain identity.
    """
    u=set(e['uncertain']);w=r['water'];s={};why={}
    def put(k,ok,reason):
        s[k]='PASS' if ok else 'FAIL'
        if not ok:why[k]=reason
    def pending(k,reason):s[k]='INCONCLUSIVE';why[k]=reason
    put('ground',abs(r['ground']-e['ground'])<=.01,'terrain_height')
    if u & {'water_boundary_numeric','flagged_surface','outside_changed_model_after_roundtrip'}:pending('roadway','roadway_boundary_unresolved')
    else:put('roadway',abs(w['road']-e['roadway'])<=.03,'roadway_height')
    if u & {'water_boundary_numeric','water_depth_numeric','flagged_surface'}:pending('water','water_or_depth_boundary_unresolved')
    elif e['expect']=='wet':put('water',w['pond'] and not w['sea'] and w['depth']>0 and abs(w['surface']-e['water_ext'])<=.05,'pond_water_state_or_height')
    else:put('water',not w['pond'] and not w['sea'] and w['depth']<=0,'water_on_dry_control')
    for code,label in (('RH','rv_high'),('RL','rv_low')):
        bed=e['effective_bed'];ray=r['rays'][code]
        if bed is None or u & {'outside_changed_model_after_roundtrip','flagged_surface','foreign_bed_support'}:pending(label,'collision_surface_unresolved');continue
        expected=max(e['ground'],bed);shapes={wire.norm(v) for v in e['bed_shapes']}
        actual={wire.norm(o['shape']) for o in ray['objects'] if o['valid']}
        identity=(not actual if e['ground']>bed+.03 else bool(actual) and actual<=shapes if bed>e['ground']+.03 else actual<=shapes)
        xz=all(abs(ray['pos'][i]-e[k])<=.01 for i,k in ((0,'x'),(2,'z')))
        put(label,ray['hit'] and identity and xz and abs(ray['pos'][1]-expected)<=.03,'RV_height_identity_or_ray_position')
    for c in ('bullet_high','bullet_low'):pending(c,'no_fresh_independent_calibration_and_layer_semantics_unverified')
    return dict(states=s,reasons=why)


def snapshot(r):
    return sorted((o['valid'],wire.norm(o['shape']),tuple(o['pos']),tuple(o['matrix'])) for o in r['objects'])


def consume(text,csv,frozen,original):
    points=contract(frozen,original);require(csv==wire.csv_for(points),'csv_source_binding')
    rows,adapter=parse(text,points);index={(p['id'],p['slot']):p for p in points};first={};details=[];counts={k:Counter() for k in CHANNELS}
    for r in rows:
        p=index[r['id'],r['slot']];origins(r,p);w=r['water'];key=(r['id'],r['slot'])
        conf=['native_bullet_layer_semantics_unverified','snapshot_does_not_certify_animation_or_empty_volume','WRP_pose_binding_pending']
        if r['t0']!=r['t1']:conf.append('ray_clock_changed_not_motion_proof')
        if w['start']!=w['end']:conf.append('water_clock_changed_not_motion_proof')
        if r['t1']!=w['end']:conf.append('rays_and_water_not_same_tick')
        if r['proxy_count']:conf.append('native_proxy_snapshot_unbound')
        if not all(v['sea'] and not v['pond'] for v in w['refs']):conf.append('sea_reference_flags_invalid')
        if max(v['surface'] for v in w['refs'])-min(v['surface'] for v in w['refs'])>.05:conf.append('sea_reference_spread')
        snap=snapshot(r)
        if key in first and snap!=first[key]:conf.append('round_snapshot_drift')
        first.setdefault(key,snap)
        channels=central_channels(r,p['original_expected']) if p['slot']==0 else None
        if channels:
            for k,v in channels['states'].items():counts[k][v]+=1
        rays={c:dict(wire.classify(ray,r['ground']),xz_delta=[ray['pos'][0]-p['x'],ray['pos'][2]-p['z']] if ray['hit'] else None) for c,ray in r['rays'].items()}
        details.append(dict(round=r['round'],id=r['id'],slot=r['slot'],measured=r,rays=rays,channels=channels,
                            original_states=p['original_states'],original_expected=p['original_expected'] if p['slot']==0 else None,
                            ground_minus_npz=r['ground']-p['terrain_at_offset'],ground_npz_state='PASS' if abs(r['ground']-p['terrain_at_offset'])<=.01 else 'FAIL',confounders=conf))
    return dict(status='INCONCLUSIVE_DIAGNOSTIC',contract_complete=True,identity_bound=False,rows=270,rays=1080,water_groups=270,
                original_fail_points=47,original_uncertain_points=21,coverage={k:dict(v) for k,v in counts.items()},adapter=adapter,details=details,
                limits=['Channel states compare only the frozen product contract; no independent water design reference.',
                        'Offsets have no inherited central water/road/bed expectations.',
                        'No pose or geometry match inferred from proximity; no empty hit list identifies terrain.',
                        'No native/global/visual/driving/RAM acceptance. Fresh Bullet calibration remains required.'])


def compare(control,candidate):
    require(control['contract_complete'] and candidate['contract_complete'],'incomplete_arm')
    require(len(control['details'])==len(candidate['details'])==270,'pair_coverage')
    out=[]
    for a,b in zip(control['details'],candidate['details']):
        key=tuple(a[k] for k in ('round','id','slot'));require(key==tuple(b[k] for k in ('round','id','slot')),'pair_order')
        require(a['original_expected']==b['original_expected'] and a['original_states']==b['original_states'],'pair_expectations')
        ra,rb=a['measured'],b['measured']
        require(ra['pos'][::2]==rb['pos'][::2] and ra['low']==rb['low'],'pair_origins')
        changes={c:dict(control_hit=ra['rays'][c]['hit'],candidate_hit=rb['rays'][c]['hit'],
                       candidate_minus_control_y=None if not ra['rays'][c]['hit'] or not rb['rays'][c]['hit'] else rb['rays'][c]['pos'][1]-ra['rays'][c]['pos'][1]) for c in wire.CODES}
        conf=sorted(set(a['confounders']+b['confounders']))
        if snapshot(ra)!=snapshot(rb):conf.append('pair_snapshot_drift')
        if ra['bullet_layer']!=rb['bullet_layer']:conf.append('pair_layer_value_changed')
        out.append(dict(round=key[0],id=key[1],slot=key[2],rays=changes,control_channels=a['channels'],candidate_channels=b['channels'],
                        water_deltas={k:rb['water'][k]-ra['water'][k] for k in ('surface','depth','road')},confounders=conf))
    return dict(status='INCONCLUSIVE_PAIRED_DIAGNOSTIC',identity_bound=False,causality='UNPROVEN',rows=270,details=out)
