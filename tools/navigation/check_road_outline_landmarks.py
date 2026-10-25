"""Run the existing physical landmark consumer with pinned V33 design metadata."""
import inspect
from pathlib import Path
import check_outline_landmarks as consumer


def main():
    assert consumer.sha(Path(consumer.__file__)) == '0b20213cff7fdab6d9ffeb92f5eedd36fa0e326a9948addb32975035a1386e5b'
    design = consumer.ROOT/'tests/regional_outline_smoothing_v33'
    assert consumer.sha(design/'pre-solve.json') == '5d16aa9664008555cdc96b58ea74d424256a91fdcb9f5d350ffa7d1cc55ffa31'
    code = inspect.getsource(consumer.main)
    assert code.count('a.candidate.parent') == 4
    code = code.replace('a.candidate.parent', 'DESIGN')
    # Only the already approved seed coordinates come from the design parent;
    # terrain, reported hash and all positive/negative tests use --candidate.
    scope = dict(vars(consumer), DESIGN=design)
    exec(compile(code, __file__+' [pinned landmark consumer]', 'exec'), scope)
    scope['main']()


if __name__ == '__main__':
    main()
