"""Reuse the complete compiled coverage consumer with explicit terrain identity."""
from pathlib import Path
import hashlib,json
B=Path('E:/DayZ-Baltic-Build/v30-native-turn-optimizer-20261009')
BASE=Path('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009')
source=BASE/'audit_global_coverage.py';text=source.read_text()
old="parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--seams',action='store_true');args=parser.parse_args()"
new="parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--seams',action='store_true');parser.add_argument('--terrain',type=Path,required=True);parser.add_argument('--terrain-hash',required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();assert sha(args.terrain)==args.terrain_hash"
assert text.count(old)==1;text=text.replace(old,new)
old="output=B/('global-coverage-final.json' if args.seams else 'global-coverage.json');assert not output.exists()"
assert text.count(old)==1;text=text.replace(old,"output=args.output;assert not output.exists()")
old="h=np.load(B10/'measured-bank-bed-r2/terrain.npz')['heights'].astype(float)"
assert text.count(old)==1;text=text.replace(old,"h=np.load(args.terrain)['heights'].astype(float)")
old="water_sha256=sha(water),world_source_sha256=sha(wp),elapsed_s=time.monotonic()-start,"
assert text.count(old)==1;text=text.replace(old,"terrain_sha256=sha(args.terrain),water_sha256=sha(water),world_source_sha256=sha(wp),elapsed_s=time.monotonic()-start,")
dest=B/'audit_candidate_coverage.py';assert not dest.exists();dest.write_text(text)
receipt=dict(original=str(source),original_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),copy=str(dest),copy_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),changes='Explicit NPZ identity/output only; all geometry and thresholds identical.')
(B/'coverage-consumer.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
