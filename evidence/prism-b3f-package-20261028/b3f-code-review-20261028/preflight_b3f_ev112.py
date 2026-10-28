"""New B3F stdlib preflight entry; does not invoke a consumed B3E2 CLI."""
import time
START=time.monotonic()
from pathlib import Path
import argparse,json,shutil,sys,traceback
sys.path.insert(0,str(Path(__file__).resolve().parent))
import preflight_b3e2_ev112 as official
meter=official.meter
FILEBANK=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe')
FILEBANK_SHA='f89aaeb22421b9158fbbf173f75d52b6f3de69986cb462e58956c78da82c4caf'

def inventory(directory):
    result={}
    for p in sorted(directory.rglob('*')):
        if p.is_symlink() or p.is_junction():raise ValueError('tool_link:'+str(p))
        if p.is_file():result[p.relative_to(directory).as_posix()]=meter.sha(p)
    if not result:raise ValueError('empty_tools')
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(exist_ok=False)
    meter.STARTED=START;meter.MAX_SECONDS=60;meter.MAX_BYTES=2*1024**3;stop=meter.bounded(a.output)
    try:
        result=official.run(a.output);before=inventory(FILEBANK.parent)
        if before.get(FILEBANK.name)!=FILEBANK_SHA:raise ValueError('filebank_identity')
        free=shutil.disk_usage(a.output).free
        if free<256*1024**2:raise ValueError('staging_disk_space')
        result.update(status='FRESH_B3F_PREFLIGHT',pboutils_directory=str(FILEBANK.parent),pboutils=before,free_bytes=free,measurement=meter.memory(),tool_inventory_limit='Installed directory bytes only; not a loaded-DLL attestation.')
        if result['measurement']['seconds']>60:raise ValueError('preflight_deadline')
        meter.dump(a.output/'report.json',result);return 0
    except Exception as e:meter.dump(a.output/'report.json',dict(status='INCONCLUSIVE_PREFLIGHT',type=type(e).__name__,reason=str(e),traceback=traceback.format_exc()));return 2
    finally:stop.set()

if __name__=='__main__':raise SystemExit(main())
