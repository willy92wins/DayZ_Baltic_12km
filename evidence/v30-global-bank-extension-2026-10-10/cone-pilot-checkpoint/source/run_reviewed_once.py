"""Run the frozen original author with only its output directory isolated."""
from pathlib import Path
import hashlib
import importlib.util

here = Path(__file__).resolve().parent
source = here / 'pilot.py'
assert hashlib.sha256(source.read_bytes()).hexdigest() == 'd743f5006e0aa6606024a3c3291a74cb52b78f76c1aa5c6dfd95cdd26cdc9d2a'
spec = importlib.util.spec_from_file_location('reviewed_face_cone_author', source)
author = importlib.util.module_from_spec(spec)
spec.loader.exec_module(author)
assert author.ROOT == here
assert author.ORDER_CLOSURE == here.parent / 'real-sector-preflight/order-closure/projection.py'
author.ROOT = here / 'preflight-recheck-01'
author.run_solve_once()
