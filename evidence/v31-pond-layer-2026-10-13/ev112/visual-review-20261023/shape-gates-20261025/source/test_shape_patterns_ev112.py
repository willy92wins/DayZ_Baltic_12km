import sys,unittest,tempfile,json
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/quality'))
from shape_patterns_ev112 import route_screen,join_screen,pyramid_fit,rectangle_components
from screen_shapes_ev112 import bind_matrix,stitch_for_screen,terrain_screen,require_site_coverage,require_placed_coverage,pilot_route_screens,shape_axis_world,K

def rotate(p,deg):
    a=np.radians(deg);return np.asarray(p)@np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]])

class ShapePatterns(unittest.TestCase):
    def test_stairs_rotated_and_resampled(self):
        p=np.array([[0,0],[25,0],[25,25],[50,25],[50,50],[75,50]])
        for deg in (0,17,45,83):
            q=rotate(p,deg)+[2000,5000]
            dense=np.vstack([a+(b-a)*np.arange(20)[:,None]/20 for a,b in zip(q[:-1],q[1:])]+[q[-1:]])
            for path in (q,dense):self.assertIn('orthogonal_staircase',[f['kind'] for f in route_screen(path)['findings']])

    def test_round_meander_and_arc_are_not_stairs_or_corners(self):
        s=np.linspace(0,300,601);a=np.linspace(0,np.pi,500)
        for p in (np.c_[s,20*np.sin(s/40)],np.c_[80*np.cos(a),80*np.sin(a)]):
            self.assertEqual(route_screen(p)['findings'],[])

    def test_long_straight_is_not_hidden_by_piece_density(self):
        for count in (2,1001):
            p=np.c_[np.linspace(0,200,count),np.zeros(count)]
            self.assertEqual([f['kind'] for f in route_screen(p)['findings']],['long_straight_run'])

    def test_join_catches_corner_and_gap_between_clean_pieces(self):
        a=[[0,0],[20,0]];b=[[20,0],[20,20]]
        self.assertEqual(route_screen(a)['findings'],[]);self.assertEqual(route_screen(b)['findings'],[])
        self.assertIn('join_tangent_break',join_screen(a,b)['findings'])
        self.assertIn('centreline_join_gap',join_screen(a,[[23,0],[40,0]])['findings'])
        self.assertEqual(join_screen(a,[[18,0],[40,0]])['findings'],[])

    def test_broad_square_and_diamond_pyramids(self):
        y,x=np.mgrid[-8:9,-8:9]*6.
        for deg in (0,17,45):
            uv=rotate(np.c_[x.ravel(),y.ravel()],deg).reshape(17,17,2);u,v=uv[:,:,0],uv[:,:,1]
            for h in (10-.04*(abs(u)+abs(v)),10-.06*np.maximum(abs(u),abs(v))):self.assertTrue(pyramid_fit(h)['detected'])

    def test_plane_ramp_ridge_and_round_hill_are_not_pyramids(self):
        y,x=np.mgrid[-8:9,-8:9]*6.
        for h in (x*0+3,3+.2*x-.1*y,10-.08*abs(x),3+4*np.exp(-(x*x+y*y)/(2*30**2))):
            self.assertFalse(pyramid_fit(h)['detected'])

    def test_rectangle_step_detected_circle_rejected(self):
        y,x=np.mgrid[:81,:81];x=x-40;y=y-40
        for deg in (0,17,45,73):
            uv=rotate(np.c_[x.ravel(),y.ravel()],deg).reshape(81,81,2)
            h=np.where((abs(uv[:,:,0])<15)&(abs(uv[:,:,1])<10),3.,0.)
            self.assertTrue(rectangle_components(h))
        for radius in (6,10,15,25):self.assertEqual(rectangle_components(np.where(x*x+y*y<radius**2,3.,0.)),[])
        self.assertEqual(rectangle_components(4*np.exp(-(x*x+y*y)/(2*12**2))),[])

    def test_invalid_inputs_never_clear(self):
        for p in ([],[[0,0],[0,0]],[[0,0],[float('nan'),3]]):
            with self.assertRaises(ValueError):route_screen(p)
        with self.assertRaises(ValueError):pyramid_fit(np.full((9,9),np.nan))
        with self.assertRaises(ValueError):rectangle_components(np.full((9,9),np.inf))

    def test_pose_nan_wrong_transform_and_reuse_rejected(self):
        m=np.array([1,0,0,0,1,0,0,0,1,100,5,100.],float);p={'model':[(7,m)]}
        for bad in (np.full(12,np.nan),m+1):
            with self.assertRaises(ValueError):bind_matrix(dict(model='model',matrix=bad),p,set())
        used=set();self.assertEqual(bind_matrix(dict(model='model',matrix=m),p,used),0)
        with self.assertRaises(ValueError):bind_matrix(dict(model='model',matrix=m),p,used)

    def test_stitched_overlap_preserves_long_line_and_does_not_bridge_gap(self):
        a=np.array([[0.,0],[40,0]]);b=np.array([[30.,0],[80,0]])
        chains,opened,bridges=stitch_for_screen([a,b],[join_screen(a,b)])
        self.assertFalse(opened);self.assertEqual(len(chains),1)
        self.assertAlmostEqual(route_screen(chains[0])['longest_straight_m'],80)
        c=np.array([[43.,0],[80,0]])
        chains,opened,bridges=stitch_for_screen([a,c],[join_screen(a,c)])
        self.assertTrue(opened);self.assertEqual(len(chains),2)

    def test_full_grid_selection_finds_broad_pyramid_old_spike_counter_misses(self):
        # Independent analytic fixture through the real NPZ/mask/candidate path.
        # 2m high / 96m radius gives only .125m per native cell at its apex.
        H=np.full((2048,2048),2.);y,x=np.mgrid[-20:21,-20:21]*6
        H[80:121,80:121]+=2*np.maximum(0,1-np.maximum(abs(x),abs(y))/96)
        y,x=np.mgrid[-48:49,-48:49]*6
        H[102:199,252:349]+=2*np.exp(-(x*x+y*y)/(2*96**2))
        H[250:270,100:125]+=2
        y,x=np.mgrid[-20:21,-20:21]*6.
        H[380:421,380:421]=10-.04*(abs(x-3)+abs(y-3))+.05*x
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);np.savez_compressed(p/'terrain.npz',heights=H)
            np.savez_compressed(p/'fp.npz',plane=np.full((2047,2047),np.nan))
            report,_=terrain_screen(p/'terrain.npz',p/'fp.npz')
        apex=[f for f in report['findings'] if abs(f['row']-100)<2 and abs(f['col']-100)<2]
        self.assertTrue(any(f['kind']=='faceted_pyramid' for f in apex))
        self.assertFalse(any(f['kind']=='native_spike' for f in apex))
        self.assertFalse(any(f['kind']=='faceted_pyramid' and abs(f['row']-150)<5 and abs(f['col']-300)<5 for f in report['findings']))
        self.assertTrue(any(f['kind']=='rectangular_terrain_transition' for f in report['findings']))
        self.assertTrue(any(f['kind']=='faceted_pyramid' and abs(f['row']-400)<2 and abs(f['col']-400)<2 for f in report['findings']))

    def test_dropping_unbuilt_reference_or_duplicate_site_rejected(self):
        ref=[dict(id='built'),dict(id='unbuilt')];good=[dict(site='built'),dict(site='unbuilt')]
        require_site_coverage(good,ref)
        for rows in ([],good[:1],good+[good[0]]):
            with self.assertRaises(ValueError):require_site_coverage(rows,ref)

    def test_piece_division_and_subthreshold_gap_keep_long_straight(self):
        for dy in (0.,1e-4,.20):
            lines=[np.array([[0.,0],[25.44,0]]),np.array([[25.44,dy],[50.88,dy]]),np.array([[50.88,0],[76.32,0]])]
            joins=[join_screen(a,b) for a,b in zip(lines,lines[1:])]
            chains,opened,bridges=stitch_for_screen(lines,joins)
            self.assertFalse(opened)
            self.assertIn('long_straight_run',[f['kind'] for c in chains for f in route_screen(c)['findings']])
            self.assertEqual(len(bridges),2 if dy else 0)

    def test_dry_apron_must_be_screened_in_addition_to_wet_span(self):
        axis=np.array([[0,0],[10,0],[10,10],[20,10],[30,10],[40,10]],float)
        report=pilot_route_screens(axis,[[20,10],[40,10]])
        self.assertEqual(report['routes'][1]['findings'],[])
        self.assertIn('abrupt_route_turn',[f['kind'] for f in report['findings']])
        self.assertTrue(all(f['scope']=='full_axis_including_dry_apron' for f in report['findings']))
        self.assertAlmostEqual(report['dry_apron_length_m'],30)

    def test_slanted_cap_rungs_are_not_macro_corners(self):
        models=json.loads(K.GEOM_PATH.read_text())['models']
        for kind in ('leaf_short_slanted','leaf_short_slanted_inv','moss_short_slanted','moss_short_slanted_inv'):
            record=dict(model='dz\\water\\streambed\\streambed_'+kind+'.p3d',matrix=[1,0,0,0,1,0,0,0,1,0,0,0])
            axis,diagnostic=shape_axis_world(record,models)
            self.assertEqual(route_screen(axis)['findings'],[])
            self.assertTrue(diagnostic['raw_route']['findings'])
            self.assertGreater(diagnostic['max_axis_offset_m'],.5)

    def test_pyramid_on_slope_and_between_grid_vertices(self):
        y,x=np.mgrid[-8:9,-8:9]*6.
        for dx,dy in ((0,0),(3,3),(-3,3)):
            for ramp in (0,.05):
                self.assertTrue(pyramid_fit(10-.04*(abs(x-dx)+abs(y-dy))+ramp*x)['detected'])

    def test_orphan_placed_piece_stone_or_duplicate_id_blocks(self):
        placed={'water':[(1,None)],'stone':[(2,None)]}
        require_placed_coverage(placed,{1,2})
        for used in ({1},{2},set(),{1,2,3}):
            with self.assertRaises(ValueError):require_placed_coverage(placed,used)
        with self.assertRaises(ValueError):require_placed_coverage({'water':[(1,None),(1,None)]},{1})

    def test_rounded_staircase_is_found_without_sharp_vertices(self):
        # Tangential quarter circles between alternating 50m legs; radius 8m.
        p=np.array([[0,0],[50,0],[50,50],[100,50],[100,100],[150,100]],float);points=[p[0]];radius=8
        for a,b,c in zip(p,p[1:],p[2:]):
            u=(b-a)/np.linalg.norm(b-a);v=(c-b)/np.linalg.norm(c-b)
            start=b-radius*u;centre=b-radius*u+radius*v
            points.append(start);theta=np.linspace(0,np.pi/2,21)[1:]
            points.extend(centre+radius*(-v*np.cos(t)+u*np.sin(t)) for t in theta)
        points.append(p[-1]);points=np.asarray(points)
        for deg in (0,17,45):
            self.assertIn('rounded_orthogonal_staircase',[f['kind'] for f in route_screen(rotate(points,deg))['findings']])

if __name__=='__main__':unittest.main()
