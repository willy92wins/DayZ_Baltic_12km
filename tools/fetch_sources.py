"""Cache official public source files selected from the approved footprint."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib, json, math, time, xml.etree.ElementTree as ET
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'raw'
META = ROOT / 'evidence'
UA = {'User-Agent': 'DayZ-Baltic-geographic-prototype/0.1 (public-data-research)'}

def fetch_metadata(url, filename):
    response = requests.get(url, headers=UA, timeout=(20, 90))
    response.raise_for_status()
    (META / filename).write_bytes(response.content)
    return response

def download(item):
    dest = RAW / item['group'] / item['filename']
    dest.parent.mkdir(parents=True, exist_ok=True)
    sidecar = dest.with_suffix(dest.suffix + '.source.json')
    if dest.exists() and sidecar.exists():
        previous = json.loads(sidecar.read_text())
        if hashlib.file_digest(dest.open('rb'), 'sha256').hexdigest() == previous['sha256']:
            print('CACHE ' + dest.name, flush=True)
            return previous
    for attempt in range(3):
        try:
            part = dest.with_suffix(dest.suffix + '.part')
            with requests.get(item['url'], headers=UA, stream=True, timeout=(20, 90)) as response:
                response.raise_for_status()
                digest = hashlib.sha256()
                md5 = hashlib.md5()
                size = 0
                with part.open('wb') as stream:
                    for block in response.iter_content(1024 * 1024):
                        size += len(block)
                        if size > 2_000_000_000:
                            raise ValueError('Unexpected single-file size over 2 GB')
                        stream.write(block); digest.update(block); md5.update(block)
                expected = response.headers.get('Content-Length')
                if expected is not None and size != int(expected):
                    raise ValueError('Incomplete response')
                if item.get('md5') and md5.hexdigest() != item['md5']:
                    raise ValueError('Published MD5 mismatch; source changed during acquisition')
                record = dict(item, path=str(dest), bytes=size, sha256=digest.hexdigest(),
                    etag=response.headers.get('ETag'), last_modified=response.headers.get('Last-Modified'),
                    retrieved_at=datetime.now(timezone.utc).isoformat())
            part.replace(dest)
            sidecar.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
            print(f"DONE {item['group']} {dest.name} {size / 1e6:.1f} MB", flush=True)
            return record
        except (requests.RequestException, ValueError) as exc:
            print(f'RETRY {dest.name} {attempt + 1}: {exc}', flush=True)
            if attempt == 2:
                raise
            time.sleep(2)

def main():
    approval = json.loads((META / 'aprobacion.json').read_text(encoding='utf-8'))
    assert approval['status'] == 'USER_APPROVED_GEOGRAPHIC_SCOPE_V0'
    poly = approval['frame_polygon_lonlat_approximate']
    west, east = min(p[0] for p in poly), max(p[0] for p in poly)
    south, north = min(p[1] for p in poly), max(p[1] for p in poly)
    items, missing = [], []
    tilelist = fetch_metadata('https://copernicus-dem-30m.s3.amazonaws.com/tileList.txt', 'copernicus-tileList.txt').text
    available = {p.strip().rstrip('/') for p in tilelist.splitlines()}
    for lat in range(math.floor(south), math.ceil(north)):
        for lon in range(math.floor(west), math.ceil(east)):
            name = f'Copernicus_DSM_COG_10_N{lat:02d}_00_E{lon:03d}_00_DEM'
            if name not in available:
                missing.append(name)
                continue
            items.append({'group':'dem', 'filename':name+'.tif', 'url':f'https://copernicus-dem-30m.s3.amazonaws.com/{name}/{name}.tif', 'release':'AWS 2021 GLO-30 public', 'nominal_sw':[lon,lat]})
    for lat in range(3*math.floor(south/3), math.ceil(north), 3):
        prefix=f'v200/2021/map/ESA_WorldCover_10m_2021_v200_N{lat:02d}'
        response = fetch_metadata('https://esa-worldcover.s3.eu-central-1.amazonaws.com/?list-type=2&prefix='+prefix, f'worldcover-list-N{lat}.xml')
        xml = ET.fromstring(response.content)
        keys = [node.text for node in xml.findall('.//{*}Key')]
        assert xml.find('{*}IsTruncated').text == 'false'
        for lon in range(3*math.floor(west/3), math.ceil(east), 3):
            key = f'v200/2021/map/ESA_WorldCover_10m_2021_v200_N{lat:02d}E{lon:03d}_Map.tif'
            assert key in keys, f'Missing WorldCover source {key}'
            items.append({'group':'worldcover','filename':Path(key).name,'url':'https://esa-worldcover.s3.eu-central-1.amazonaws.com/'+key,'release':'ESA WorldCover 2021 v200','nominal_sw':[lon,lat]})
    for region in ['russia/northwestern-fed-district', 'europe/estonia']:
        url='https://download.geofabrik.de/'+region+'-latest.osm.pbf'
        filename=region.split('/')[-1]+'.osm.pbf'
        checksum=fetch_metadata(url+'.md5',filename+'.md5').text.split()[0]
        assert len(checksum)==32
        items.append({'group':'osm','filename':filename,'url':url,'md5':checksum,'license':'ODbL 1.0; OpenStreetMap contributors'})
    plan={'bbox':[west,south,east,north],'selected':items,'missing_dem_tiles':missing,
          'missing_policy':'Never fill missing land with sea; prove ocean coverage separately before export.'}
    (META/'acquisition-plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
    print(f'Acquisition: {len(items)} files; missing DEM tiles {missing}',flush=True)
    results=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs=[pool.submit(download,item) for item in items]
        for job in as_completed(jobs):
            results.append(job.result())
    (META/'source-manifest.json').write_text(json.dumps({'sources':sorted(results,key=lambda d:d['url']),'missing_dem_tiles':missing},indent=2)+'\n',encoding='utf-8')
    print(f'COMPLETE {len(results)} sources; {sum(p["bytes"] for p in results)/1e9:.3f} GB',flush=True)

if __name__=='__main__':
    main()
