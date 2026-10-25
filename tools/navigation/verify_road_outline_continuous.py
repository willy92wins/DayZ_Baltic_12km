"""Re-run the complete V33 geometric consumer on a composed road candidate."""
from pathlib import Path
import inspect
import verify_outline_smoothing as consumer


def main():
    assert consumer.sha(Path(consumer.__file__)) == '75b97d608c659cbbfb8712ed91a7f02e6336b38aeac0987cea2b3cd4fdfe9c4f'
    design = consumer.ROOT/'tests/regional_outline_smoothing_v33'
    expected = {'pre-solve.json': '5d16aa9664008555cdc96b58ea74d424256a91fdcb9f5d350ffa7d1cc55ffa31',
                'shore-transition.json': '15652b897b68e5ab3dc7927db964cae3d732ec42ae7249cbd4204eba61f5c488'}
    for name, digest in expected.items():
        assert consumer.sha(design/name) == digest
    code = inspect.getsource(consumer.main)
    assert code.count('a.candidate.parent') == 2
    code = code.replace('a.candidate.parent', 'DESIGN')
    anchor = "    report['frozen_runtime_points']=runtime_points"
    assert code.count(anchor) == 1
    code = code.replace(anchor, anchor+"\n    report['pinned_design'] = DESIGN_PINS")
    scope = dict(vars(consumer), DESIGN=design, DESIGN_PINS=expected)
    exec(compile(code, __file__+' [unchanged full V33 consumer]', 'exec'), scope)
    scope['main']()


if __name__ == '__main__':
    main()
