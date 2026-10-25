"""Archive native DayZ DDS pixels with exact camera/run provenance, no visual verdict."""
from pathlib import Path
from datetime import datetime, timezone
import argparse,hashlib,json,shutil
from PIL import Image
from verify_foundation_visual_records import blocks,verify_camera,summarize_metrics
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reference',type=Path,required=True);ap.add_argument('--identity',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();assert not a.out.exists();a.out.mkdir()
    ref=json.loads(a.reference.read_text(encoding='utf-8-sig'));identity=json.loads(a.identity.read_text(encoding='utf-8-sig'))
    clients=[p for p in identity['processes'] if p['role']=='client'];assert len(clients)==1
    start=datetime.fromisoformat(clients[0]['creation_time_utc'].replace('Z','+00:00')).timestamp()
    profile=Path('P:/DayZ_MCP_dev/_client/profiles');now=datetime.now(timezone.utc).timestamp()
    report=dict(status='FAILED_CAPTURE_PROVENANCE',run_id=identity['run_id'],reference_sha256=sha(a.reference),identity_sha256=sha(a.identity),images=[])
    try:
        for key,name in [('camera_log','camera.log'),('metrics_log','client-metrics.log')]:
            source=profile/ref[key];assert source.stat().st_mtime>=start-2
            shutil.copy2(source,a.out/name)
        text=(a.out/'camera.log').read_text(encoding='utf-8-sig');report['camera']=verify_camera(text,ref)
        report['metrics']=summarize_metrics((a.out/'client-metrics.log').read_text(encoding='utf-8-sig'),ref)
        assert report['camera']['status']=='PASS_CAMERA_TELEMETRY_AND_RESTORE'
        data=blocks(text,ref['camera_header'])
        for pose in ref['poses']:
            phase=pose['phase'];record=data[f'CAPTURE_REQUEST_{phase}']
            assert record['native_capture_requested']=='true' and record['application_active']=='true',('App not active at capture',phase)
            expected=ref['capture_prefix']+str(phase)
            if ref.get('capture_full_path',False):
                source=profile/(expected+'.dds')
                candidates=[source] if source.is_file() and start-2<=source.stat().st_mtime<=now+2 else []
            else:
                candidates=[p for directory in ['ScreenShotes','ScreenShots'] for p in (profile/directory).glob('*.dds') if p.stem.endswith(expected) and start-2<=p.stat().st_mtime<=now+2]
            assert len(candidates)==1,(phase,[str(p) for p in candidates])
            source=candidates[0];dds=a.out/f'phase-{phase}.dds';png=a.out/f'phase-{phase}.png';shutil.copy2(source,dds)
            assert sha(dds)==sha(source)
            # DDS decoding only: no crop, resizing, filtering or retouching.
            with Image.open(dds) as image:
                rgb=image.convert('RGB');rgb.save(png);pixel_hash=hashlib.sha256(rgb.tobytes()).hexdigest();size=rgb.size
            report['images'].append(dict(phase=phase,name=pose['name'],camera=pose['position'],target=pose['target'],
                source=str(source),source_mtime_utc=datetime.fromtimestamp(source.stat().st_mtime,timezone.utc).isoformat(),
                dds=str(dds),dds_sha256=sha(dds),png=str(png),png_sha256=sha(png),rgb_pixels_sha256=pixel_hash,width=size[0],height=size[1]))
        report['status']='ARCHIVED_NATIVE_PIXELS_REQUIRE_VISUAL_REVIEW'
    except (AssertionError,ValueError,KeyError,FileNotFoundError,OSError) as error:
        report['error']=str(error)
    report['logs_sha256']={p.name:sha(p) for p in a.out.glob('*.log')}
    report['limit']='File/run/camera provenance only. Actual terrain, water and textures need independent pixel review.'
    (a.out/'capture-provenance.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report));raise SystemExit(0 if report['status'].startswith('ARCHIVED_') else 1)

if __name__=='__main__':main()
