"""Replay the pinned local sources. Downloads require explicit --acquire."""
from pathlib import Path
import argparse,json,subprocess,sys

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--acquire',action='store_true',help='Acquire source data; existing valid cache entries are reused. New OSM downloads can be newer than the pinned snapshot.')
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    if args.acquire:
        subprocess.run([sys.executable,str(root/'tools/fetch_sources.py')],check=True)
    manifest=root/'evidence/source-manifest.json'
    if not manifest.exists():parser.error('Source manifest absent. Review the approved crop before --acquire.')
    missing=[s['path'] for s in json.loads(manifest.read_text())['sources'] if not Path(s['path']).is_file()]
    if missing:parser.error('Pinned sources absent: restore the original cache or consciously acquire a new snapshot. '+str(missing[:2]))
    for script in ['geo_common','build_rasters','extract_vectors','extract_border','prepare_prototype','inspect_narva_crossings','export_narva_detail','test_ascii_validator','validate_prototype','audit_roads','registration_probe','render_preview']:
        subprocess.run([sys.executable,str(root/f'tools/{script}.py')],check=True)
    subprocess.run([sys.executable,str(root/'tools/audit_roads.py'),'--narva-detail'],check=True)
    # Keep the consumer-facing source layout synchronized after successful checks.
    import shutil
    shutil.copytree(root/'derived/tb/source',root/'source',dirs_exist_ok=True)
    print('Offline candidate ready. Terrain Builder and game gates remain pending.')

if __name__=='__main__':main()
