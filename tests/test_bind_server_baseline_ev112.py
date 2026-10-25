import copy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/performance'))
from bind_server_baseline_ev112 import prepare,finish
from read_server_baseline_ev112 import require_inputs
from compare_server_baseline_ev112 import conditions_identity


class Binding(unittest.TestCase):
    def test_pre_post_bound_files_and_derived_conditions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            paths={key:root/name for key,name in [('mission','init.c'),('executable','game.exe'),('server_config','server.cfg'),('pbo','map.pbo'),('engine','baltic_ab_01_123456789abc.log'),('host','host.jsonl')]}
            for key,p in paths.items():p.write_text(key,encoding='utf-8')
            paths['mission'].write_text('guard("baltictrial"); Open("baltic_ab_01_123456789abc.log"); Open("baltic_ab_01_123456789abc.log");',encoding='utf-8')
            spec=dict(world='BalticTrial',artifacts={k:str(paths[k]) for k in ('mission','executable','server_config')},packages=[str(paths['pbo'])])
            snapshot=prepare(spec)
            with self.assertRaisesRegex(ValueError,'precede process'):
                finish(snapshot,'run-1',100,'2000-01-01T18:00:00Z',paths['engine'],paths['host'])
            snapshot['prepared_utc']='2026-10-25T17:59:59Z'
            ref=finish(snapshot,'run-1',100,'2026-10-25T18:00:00Z',paths['engine'],paths['host'])
            require_inputs(ref,paths['engine'],paths['host'])
            conditions=conditions_identity(ref)
            self.assertEqual(len(conditions['canonical_mission']),64)
            changed=copy.deepcopy(ref);changed['world']='ChernarusPlus'
            with self.assertRaisesRegex(ValueError,'world guard'):conditions_identity(changed)
            changed=copy.deepcopy(ref);changed['artifacts']['engine']=str(root/'other.log')
            with self.assertRaisesRegex(ValueError,'log identity'):conditions_identity(changed)
            changed=copy.deepcopy(ref);changed['packages']={}
            with self.assertRaisesRegex(ValueError,'Package identities'):conditions_identity(changed)
            changed=copy.deepcopy(ref);changed['packages'][str(paths['pbo'])]='0'*64
            with self.assertRaisesRegex(ValueError,'not bound'):conditions_identity(changed)
            paths['pbo'].write_text('changed')
            with self.assertRaisesRegex(ValueError,'Pre-launch input changed'):
                finish(snapshot,'run-1',100,'2026-10-25T18:00:00Z',paths['engine'],paths['host'])
            rebound=prepare(spec);rebound['prepared_utc']='2026-10-25T17:59:59Z'
            with self.assertRaisesRegex(ValueError,'aliases'):
                finish(rebound,'run-1',100,'2026-10-25T18:00:00Z',paths['mission'],paths['host'])
            spec['packages']=[]
            with self.assertRaisesRegex(ValueError,'stack required'):prepare(spec)


if __name__=='__main__':unittest.main()
