"""Calibrated pattern screens, not a universal definition of natural scenery.

Positive findings require adjudication; they never grant terrain-edit permission.
All distances are metres and angles degrees. Policy is frozen before production.
"""
import numpy as np
from scipy import ndimage as ndi
from shapely.geometry import LineString, MultiPoint, Point
from shapely.ops import nearest_points

POLICY = dict(version='ev112-shapes-3', simplification_m=.25, long_straight_m=60.,
              abrupt_turn_deg=45., stair_turn_deg=60., stair_turns=3,
              stair_axis_tolerance_deg=5., stair_axis_share=.90,
              join_turn_deg=30., join_gap_m=.50,
              pyramid_rms_ratio=.025, pyramid_relief_m=.30,
              rectangle_hull_fill=.90, rectangle_perimeter_share=.85,
              rectangle_min_side_m=24., rectangle_step_m=.30,rectangle_stencil_span_cells=2.,
              stair_axis_balance=.10, chain_bridge_max_m=.50, pose_tolerance_m=.001,
              rounded_stair_run_min_m=20., rounded_stair_axis_share=.65,
              source_geometry_tolerance_m=.001, native_prominence_m=.30,
              rectangle_min_vertices=16, rectangle_min_side_support=3,
              pyramid_aspect_min=.25, pyramid_angle_step_deg=3.,
              pyramid_radius_cells=[2,4,8], pyramid_apex_offsets_cells=[0.,-.5,.5],
              pyramid_phase_search_max_rms=.15,
              pyramid_background_mode='fit_plane_without_slope_cap',
              slanted_axis_flat_tolerance_m=.001, slanted_axis_linear_tolerance_m=.01)


def path_array(points):
    p=np.asarray(points,float)
    if p.ndim!=2 or p.shape[1]!=2 or len(p)<2 or not np.isfinite(p).all():
        raise ValueError('finite nonempty Nx2 path required')
    if (np.linalg.norm(np.diff(p,axis=0),axis=1)<1e-8).any():
        raise ValueError('duplicate stations')
    return p


def route_screen(points):
    p=path_array(points)
    line=LineString(p)
    # Douglas-Peucker uses geometric deviation, not the input point spacing.
    q=np.asarray(line.simplify(POLICY['simplification_m'],preserve_topology=False).coords)
    d=np.diff(q,axis=0);length=np.linalg.norm(d,axis=1);u=d/length[:,None]
    turn=np.degrees(np.arccos(np.clip((u[:-1]*u[1:]).sum(1),-1,1)))
    headings=np.degrees(np.arctan2(d[:,1],d[:,0]))%180
    best=0.;both=0.;rounded_stairs=False;rounded_share=0.
    # Fit the axes to the route itself: rotating the map does not hide a stair.
    for a in headings:
        angle=abs((headings-a+90)%180-90)
        first=angle<=POLICY['stair_axis_tolerance_deg']
        second=abs(angle-90)<=POLICY['stair_axis_tolerance_deg']
        share=float(length[first|second].sum()/length.sum())
        balance=float(min(length[first].sum(),length[second].sum())/length.sum())
        # Rounded elbows spread a 90-degree turn across several short edges.
        # Require repeated *long straight* anchors alternating on fitted axes.
        anchors=(length>=POLICY['rounded_stair_run_min_m'])&(first|second)
        axes=second[anchors]
        alternations=int(np.count_nonzero(axes[1:]!=axes[:-1]))
        anchor_share=float(length[anchors].sum()/length.sum())
        if alternations>=POLICY['stair_turns'] and anchor_share>=POLICY['rounded_stair_axis_share']:
            rounded_stairs=True;rounded_share=max(rounded_share,anchor_share)
        if share>best or (share==best and balance>both):best,both=share,balance
    corners=np.flatnonzero(turn>=POLICY['abrupt_turn_deg'])
    long=np.flatnonzero(length>=POLICY['long_straight_m'])
    stairs=int((turn>=POLICY['stair_turn_deg']).sum())>=POLICY['stair_turns'] and best>=POLICY['stair_axis_share'] and both>=POLICY['stair_axis_balance']
    findings=[]
    for i in corners:findings.append(dict(kind='abrupt_route_turn',xy=q[i+1].tolist(),value_deg=float(turn[i])))
    for i in long:findings.append(dict(kind='long_straight_run',xy=((q[i]+q[i+1])/2).tolist(),length_m=float(length[i]),ends=q[i:i+2].tolist()))
    if stairs:findings.append(dict(kind='orthogonal_staircase',xy=q[len(q)//2].tolist(),axis_share=best,turns=int((turn>=POLICY['stair_turn_deg']).sum())))
    elif rounded_stairs:findings.append(dict(kind='rounded_orthogonal_staircase',xy=q[len(q)//2].tolist(),long_anchor_axis_share=rounded_share))
    return dict(length_m=float(line.length),simplified_stations=len(q),max_turn_deg=float(turn.max()) if len(turn) else 0.,
                longest_straight_m=float(length.max()),fitted_orthogonal_axis_share=best,findings=findings)


def join_screen(before,after):
    """Local nearest-centreline join. Never invent a water connection."""
    a,b=LineString(path_array(before)),LineString(path_array(after))
    x,y=nearest_points(a,b);sa,sb=a.project(x),b.project(y)
    def tangent(line,s):
        span=min(2.,line.length/4)
        v=np.array(line.interpolate(min(line.length,s+span)).coords[0])-np.array(line.interpolate(max(0,s-span)).coords[0])
        if np.linalg.norm(v)<1e-8:raise ValueError('undefined join tangent')
        return v/np.linalg.norm(v)
    ua,ub=tangent(a,sa),tangent(b,sb)
    angle=float(np.degrees(np.arccos(np.clip(ua@ub,-1,1))))
    gap=float(x.distance(y));findings=[]
    if angle>POLICY['join_turn_deg']:findings.append('join_tangent_break')
    if gap>POLICY['join_gap_m']:findings.append('centreline_join_gap')
    return dict(xy=list(x.coords[0]),other_xy=list(y.coords[0]),gap_m=gap,turn_deg=angle,
                before_station_m=float(sa),after_station_m=float(sb),findings=findings,
                scope='Centreline candidate only; no receiver or water-connectivity inference.')


def pyramid_fit(patch,cell=6.):
    """Fit closed four-face tents, rejecting a plane, ridge and rounded hill."""
    h=np.asarray(patch,float)
    if h.ndim!=2 or h.shape[0]!=h.shape[1] or len(h)<5 or len(h)%2!=1 or not np.isfinite(h).all() or not np.isfinite(cell) or cell<=0:
        raise ValueError('finite odd square patch >=5 and positive cell required')
    n=len(h)//2;y,x=np.mgrid[-n:n+1,-n:n+1]*cell
    edge=np.maximum(abs(x),abs(y))==n*cell
    relief=float(h[n,n]-np.median(h[edge]))
    if relief<POLICY['pyramid_relief_m']:return dict(detected=False,relief_m=relief,rms_ratio=None)
    best=None
    def evaluate(deg,dx=0.,dy=0.):
        nonlocal best
        a=np.radians(deg);u=(x-dx)*np.cos(a)+(y-dy)*np.sin(a);v=-(x-dx)*np.sin(a)+(y-dy)*np.cos(a)
        for mode in ('diamond','square'):
            basis=[np.ones_like(x),x,y]
            basis+= [abs(u),abs(v)] if mode=='diamond' else [np.maximum(abs(u),abs(v))]
            M=np.stack(basis,axis=-1).reshape(-1,len(basis));coef=np.linalg.lstsq(M,h.ravel(),rcond=None)[0]
            slope=-coef[3:]
            if (slope<=0).any() or slope.min()<POLICY['pyramid_aspect_min']*slope.max():continue
            rms=float(np.sqrt(np.mean((M@coef-h.ravel())**2))/relief)
            if best is None or rms<best['rms_ratio']:
                best=dict(detected=rms<=POLICY['pyramid_rms_ratio'],relief_m=relief,rms_ratio=rms,orientation_deg=float(deg),shape=mode,apex_offset_m=[dx,dy])
    for deg in np.arange(0.,90.,POLICY['pyramid_angle_step_deg']):evaluate(deg)
    # A grid samples a surface; its apex need not coincide with a vertex.
    # Refine the best orientation by half-cell phases, preserving the same gate.
    if best and not best['detected'] and best['rms_ratio']<=POLICY['pyramid_phase_search_max_rms']:
        angle=best['orientation_deg'];step=POLICY['pyramid_angle_step_deg']
        for dx in POLICY['pyramid_apex_offsets_cells']:
            for dy in POLICY['pyramid_apex_offsets_cells']:
                if dx==dy==0:continue
                for deg in (angle-step,angle,angle+step):evaluate(deg,dx*cell,dy*cell)
    return best or dict(detected=False,relief_m=relief,rms_ratio=None)


def rectangle_components(H,cell=6.):
    """Closed rectilinear edge components; a circular contour is a negative."""
    h=np.asarray(H,float)
    if h.ndim!=2 or min(h.shape)<9 or not np.isfinite(h).all() or not np.isfinite(cell) or cell<=0:raise ValueError('finite terrain grid required')
    residual=np.zeros_like(h)
    residual[1:-1,1:-1]=np.maximum(abs(h[1:-1,1:-1]-(h[:-2,1:-1]+h[2:,1:-1])/2),abs(h[1:-1,1:-1]-(h[1:-1,:-2]+h[1:-1,2:])/2))
    labels,count=ndi.label(residual>POLICY['rectangle_step_m'],structure=np.ones((3,3)))
    slices=ndi.find_objects(labels);found=[]
    for label,sl in enumerate(slices,1):
        local=labels[sl]==label;rr,cc=np.nonzero(local)
        if len(rr)<POLICY['rectangle_min_vertices']:continue
        coords=np.c_[(cc+sl[1].start)*cell,(rr+sl[0].start)*cell]
        hull=MultiPoint(coords).convex_hull;rect=hull.minimum_rotated_rectangle
        if rect.geom_type!='Polygon' or rect.area==0:continue
        corners=np.array(rect.exterior.coords)[:-1];sides=np.linalg.norm(np.roll(corners,-1,axis=0)-corners,axis=1)
        if sides.min()<POLICY['rectangle_min_side_m']:continue
        fill=float(hull.area/rect.area)
        if fill<POLICY['rectangle_hull_fill']:continue
        # A centred second difference marks both the interior and exterior
        # pixel at a step. A rotated step spans up to two cells in its normal;
        # the axis-aligned one-cell special case is not a valid general bound.
        tolerance=cell*POLICY['rectangle_stencil_span_cells']
        close=np.array([rect.exterior.distance(Point(p))<=tolerance for p in coords])
        share=float(close.mean())
        if share<POLICY['rectangle_perimeter_share']:continue
        # Each side must be supported; a U-shaped cut is not a closed rectangle.
        supported=[sum(LineString([a,b]).distance(Point(p))<=tolerance for p in coords) for a,b in zip(corners,np.roll(corners,-1,axis=0))]
        if min(supported)<POLICY['rectangle_min_side_support']:continue
        found.append(dict(kind='rectangular_terrain_transition',row=float(coords[:,1].mean()/cell),col=float(coords[:,0].mean()/cell),
                          bbox_rc=[sl[0].start,sl[1].start,sl[0].stop,sl[1].stop],
                          hull_fill=fill,perimeter_share=share,edge_vertices=len(coords),min_side_m=float(sides.min()),max_side_m=float(sides.max())))
    return found
