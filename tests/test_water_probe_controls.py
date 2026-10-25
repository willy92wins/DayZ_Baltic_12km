"""Observed-engine positives and failure mutations for the water consumer gates."""
import csv,io,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/navigation'))
from verify_elevated_water_probe import verify as flat
from verify_stepped_water_probe import verify as stepped
from verify_shape_boat_probe import verify as shaped
EV=ROOT/'evidence/regional-foundation-v1'


def mutate(raw,kind):
    rows=list(csv.reader(raw.decode('utf-8-sig').splitlines(),delimiter=';'))
    if kind=='truncated':rows=rows[:-1]
    elif kind=='missing_grid':
        rows.pop(next(i for i,r in enumerate(rows) if r[0]=='WATER'))
    elif kind=='stale_header':rows[0]=['OTHER_RUN']
    elif kind in {'wrong_level','not_water'}:
        for r in rows:
            if r[0]=='WATER' and r[1]=='AFTER' and r[2]=='500' and r[4]=='3000':
                r[9]='1' if kind=='wrong_level' else r[9]
                r[7]='false' if kind=='not_water' else r[7]
    else:
        keys=next(r[1:] for r in rows if r[0]=='COLUMNS')
        boats=[r for r in rows if r[0]=='B']
        idx=lambda key:keys.index(key)+1
        if kind=='damage':boats[-1][idx('health')]='590'
        if kind=='teleport':boats[len(boats)//2][idx('x')]='530'
        if kind=='lost_buoyancy':boats[-1][idx('y')]='1'
        if kind=='no_input':
            for r in boats:r[idx('input_calls')]='0'
        if kind=='no_propulsion':
            for r in boats:r[idx('engine')]='false'
    stream=io.StringIO(newline='')
    csv.writer(stream,delimiter=';',lineterminator='\n').writerows(rows)
    return stream.getvalue().encode()


class WaterProbeControls(unittest.TestCase):
    def test_actual_engine_positives_and_negatives(self):
        cases=[('elevated-water-dynamic-v1.log',lambda raw:flat(raw,False)),
               ('elevated-water-static-v1.log',lambda raw:flat(raw,True)),
               ('stepped-water-v1.log',stepped),('shape-boat-v3.log',shaped),
               ('static-shape-v2.log',lambda raw:shaped(raw,True,2))]
        for name,verify in cases:
            raw=(EV/name).read_bytes()
            with self.subTest(name=name,control='positive'):
                self.assertTrue(verify(raw)['status'].startswith('PASS_'))
            for fault in ('truncated','missing_grid','stale_header','wrong_level','not_water','damage','teleport','lost_buoyancy','no_input','no_propulsion'):
                with self.subTest(name=name,fault=fault):
                    self.assertEqual(verify(mutate(raw,fault))['status'],'FAIL')

    def test_dry_hole_and_missing_hole_controls(self):
        raw=(EV/'shape-boat-v3.log').read_bytes()
        for fault in ('flood_hole','remove_sample','duplicate_sample'):
            rows=list(csv.reader(raw.decode().splitlines(),delimiter=';'))
            i=next(i for i,r in enumerate(rows) if r[:3]==['HOLE','0','0'])
            if fault=='flood_hole':rows[i][3:]=['6','true']
            elif fault=='remove_sample':rows.pop(i)
            else:rows.append(rows[i].copy())
            stream=io.StringIO(newline='');csv.writer(stream,delimiter=';',lineterminator='\n').writerows(rows)
            with self.subTest(fault=fault):self.assertEqual(shaped(stream.getvalue().encode())['status'],'FAIL')


if __name__=='__main__':unittest.main()
