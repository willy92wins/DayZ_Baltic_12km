"""Freeze V7 at the unchanged V5 coordinates/criteria with road V29 heights."""
import hashlib
import inspect
import sys
from pathlib import Path
import prepare_outline_consumer_v6 as baseline


def main():
    source = Path(baseline.__file__)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == '1768297c8e9f4db3dd6faba5648a144cb7b938f7201bd4f446a76797c0eb2cfb'
    candidate = baseline.ROOT/'tests/regional_road_network_v29/baltic_road_network_v29.asc'
    assert baseline.sha(candidate) == 'ed6cdaa5a1b9100a6f74041e9338f1c21f100a6686f596c73f79f33c4b8662c6'
    code = inspect.getsource(baseline.main)
    assert code.count("'independent-consumer.json'") == 1
    code = code.replace("'independent-consumer.json'", "'continuous-outline.json'")
    # Only destination/version labels change. The frozen V5 input and all
    # classification, sample counts, geometry and physical criteria stay intact.
    code = code.replace('V6', 'V7').replace('v6', 'v7')
    namespace = vars(baseline).copy()
    exec(compile(code, str(source)+'[V7-road-binding]', 'exec'), namespace)
    previous = sys.argv
    try:
        sys.argv = [str(__file__), '--candidate', str(candidate)]
        namespace['main']()
    finally:
        sys.argv = previous


if __name__ == '__main__':
    main()
