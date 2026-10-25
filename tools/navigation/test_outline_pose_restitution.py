"""Reject pose corruption; retain an independent frozen-object positive oracle."""
from pathlib import Path
import copy, struct, tempfile, unittest
from canonicalize_outline_water_poses import BASELINE, ROOT, read, restore, native_pair, key


class Restitution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=read(BASELINE)
        cls.raw=read(ROOT/'tb/regional_outline_smoothing_v33/5.wrp')
        cls.water=next(o for o in cls.raw['objects'] if o['name'].startswith('baltic_water\\'))
        cls.bridge=next(o for o in cls.raw['objects'] if not o['name'].startswith('baltic_water\\'))

    def parse(self, data):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'test.wrp';p.write_bytes(data);return read(p)

    def test_frozen_baseline_oracle(self):
        data,changes=restore(self.old,self.raw)
        out=self.parse(data)
        self.assertEqual(sorted(map(key,self.old['objects'])),sorted(map(key,out['objects'])))
        self.assertEqual(len(changes),670)
        allowed={i for c in changes for i in range(c['offset'],c['offset']+4)}
        self.assertTrue({i for i,(a,b) in enumerate(zip(data,self.raw['bytes'])) if a!=b}<=allowed)
        self.assertEqual(data[:out['objects_start']],self.raw['bytes'][:self.raw['objects_start']])

    def test_bad_poses(self):
        cases=[('x',self.water,36,.1),('z',self.water,44,.1),('rotation',self.water,0,.01),
               ('water1mm',self.water,40,.001),('bridge',self.bridge,40,.000001),('nan',self.water,40,float('nan'))]
        for name,obj,offset,delta in cases:
            with self.subTest(name=name):
                data=bytearray(self.raw['bytes']);at=obj['start']+offset
                value=struct.unpack_from('<f',data,at)[0];struct.pack_into('<f',data,at,value+delta)
                with self.assertRaises(ValueError):restore(self.old,self.parse(data))
        for name,offset in [('id',48),('model',56)]:
            with self.subTest(name=name):
                data=bytearray(self.raw['bytes']);data[self.water['start']+offset]^=1
                with self.assertRaises(ValueError):restore(self.old,self.parse(data))

    def test_persistence_and_truncation(self):
        for offset in (24,24+2048*2048*4):
            data=bytearray(self.raw['bytes']);data[offset]^=1
            with self.assertRaises(ValueError):native_pair(self.raw,self.parse(data))
        with self.assertRaises((ValueError,struct.error)):self.parse(self.raw['bytes'][:-5])


if __name__=='__main__':unittest.main()
