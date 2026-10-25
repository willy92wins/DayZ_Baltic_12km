#!/usr/bin/env python
"""Build a read-only, global ODOL face/range cache for frozen terrain B.

Nothing in the source package or game is opened for writing. A successful run
creates a new timestamped directory beneath this script's ``runs`` folder.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import secrets
import struct
import sys
import time
import traceback

import numpy as np

ROOT=Path(r'E:/DayZ-Baltic-Build')
OUT_ROOT=ROOT/'v30-global-bank-extension-20261010/ev93-face-index'
PLAN=ROOT/'v30-global-bank-extension-20261010/plan.md'
EV87_PATH=ROOT/'v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py'
EV90_PATH=ROOT/'v30-wide-bank-fairing-pilot-20261010/next-method-preflight/ev90_preflight.py'
EXPECTED_PLAN_SHA='ccc018a9e1cc8a51b075a91905b1cbe7d3cdaf72040e51992f2ac55db8ad7e82'
EXPECTED_EV87_SHA='964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27'
EXPECTED_EV90_SHA='5892e917335ca2d8caa427f04f48ba8acbd8e16a5e1b400be596d5dd636afb7f'
SCHEMA='ev93.face-range-index.v1'
MAX_BYTES=2*1024**3
MAX_SECONDS=10*60
SHARD_RECORDS=100_000
PHYSICAL_RES=float(np.float32(3e15))
VISIBLE_RES=float(np.float32(1.0))
GRID_N=2048
KIND={'physical':0,'visible':1}
KIND_NAME={v:k for k,v in KIND.items()}


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()


def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:raise ImportError(f'cannot import {path}')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def verify_source_pins():
    for path,want in ((PLAN,EXPECTED_PLAN_SHA),(EV87_PATH,EXPECTED_EV87_SHA),(EV90_PATH,EXPECTED_EV90_SHA)):
        if not want:
            raise AssertionError('approved EV93 plan SHA must be frozen in source before build')
        got=sha(path)
        if got!=want:raise AssertionError(f'EV93 source pin mismatch: {path}: {got} != {want}')


def _closed_axis_range(vmin,vmax,scale,offset,limit):
    """Cells whose closed intervals touch a conservatively rounded bbox axis."""
    lo=(float(vmin)-float(offset))/float(scale)
    hi=(float(vmax)-float(offset))/float(scale)
    lo=math.nextafter(lo,-math.inf);hi=math.nextafter(hi,math.inf)
    first=math.ceil(lo)-1
    last=math.floor(hi)
    if last<0 or first>limit:return None
    first=max(0,first);last=min(limit,last)
    if first>last:return None
    return int(first),int(last)


def conservative_cell_range(xyz,cell=6.0,z0=12282.0,n=2048):
    """Return inclusive [rmin,rmax,cmin,cmax], or [-1,-1,-1,-1] off-grid."""
    q=np.asarray(xyz,dtype=np.float64)
    if q.shape!=(3,3) or not np.isfinite(q).all():raise ValueError('XYZ must be finite float64 [3,3]')
    rows=_closed_axis_range(z0-float(q[:,2].max()),z0-float(q[:,2].min()),cell,0.0,n-2)
    cols=_closed_axis_range(float(q[:,0].min()),float(q[:,0].max()),cell,0.0,n-2)
    if rows is None or cols is None:return np.asarray([-1,-1,-1,-1],dtype=np.int32)
    return np.asarray([rows[0],rows[1],cols[0],cols[1]],dtype=np.int32)


def query_mask(cell_ranges,window,kind_values=None,kind=None):
    """Candidate range overlap; exact polygon/native-triangle clipping is downstream."""
    ranges=np.asarray(cell_ranges,dtype=np.int32)
    if ranges.ndim!=2 or ranges.shape[1]!=4:raise ValueError('cell_range_rc must be [n,4] int32')
    r0,r1,c0,c1=map(int,window)
    if r0<0 or c0<0 or r1<r0 or c1<c0 or r1>GRID_N-2 or c1>GRID_N-2:
        raise ValueError('invalid query window')
    mask=(ranges[:,0]<=r1)&(ranges[:,1]>=r0)&(ranges[:,2]<=c1)&(ranges[:,3]>=c0)
    if kind is not None:
        if kind not in KIND:raise ValueError(f'unknown face kind: {kind}')
        if kind_values is None:raise ValueError('kind_values required for kind-filtered query')
        kv=np.asarray(kind_values,dtype=np.uint8)
        if kv.shape!=(len(ranges),):raise ValueError('kind array must be row-aligned')
        mask &= kv==KIND[kind]
    return mask


def empty_arrays():
    return {'kind':np.empty(0,dtype=np.uint8),'object_id':np.empty(0,dtype=np.int32),
        'model_id':np.empty(0,dtype=np.uint32),'face_id':np.empty(0,dtype=np.uint32),
        'xyz':np.empty((0,3,3),dtype=np.float64),'plane_y_xz':np.empty((0,3),dtype=np.float64),
        'area_xz':np.empty(0,dtype=np.float64),'cell_range_rc':np.empty((0,4),dtype=np.int32),
        'degenerate':np.empty(0,dtype=np.uint8)}


class FaceRangeIndex:
    """Read complete EV93 shards and return bbox candidates for exact clipping."""
    def __init__(self,run_dir):
        self.run_dir=Path(run_dir)
        self.manifest_path=self.run_dir/'manifest.json'
        manifest_before=sha(self.manifest_path)
        self.manifest=json.loads(self.manifest_path.read_text(encoding='utf-8'))
        if sha(self.manifest_path)!=manifest_before:raise AssertionError('EV93 manifest changed while loading')
        if self.manifest.get('schema')!=SCHEMA or self.manifest.get('status')!='COMPLETE':
            raise ValueError('only a COMPLETE EV93 face-range index can be queried')
        self._manifest_sha=manifest_before
        self._shards=[]
        for shard in self.manifest['shards']:
            path=self.run_dir/shard['path']
            if sha(path)!=shard['sha256']:raise AssertionError(f'shard hash mismatch: {path}')
            with np.load(path,allow_pickle=False) as z:arrays={k:z[k] for k in z.files}
            self._validate_arrays(arrays,int(shard['records']),path)
            self._shards.append((shard,arrays))

    @staticmethod
    def _validate_arrays(arrays,expected_rows,path):
        if set(arrays)!=set(empty_arrays()):raise AssertionError(f'face shard schema mismatch: {path}')
        n=expected_rows
        shapes={'kind':(n,),'object_id':(n,),'model_id':(n,),'face_id':(n,),
            'xyz':(n,3,3),'plane_y_xz':(n,3),'area_xz':(n,),
            'cell_range_rc':(n,4),'degenerate':(n,)}
        dtypes={'kind':np.dtype('uint8'),'object_id':np.dtype('int32'),'model_id':np.dtype('uint32'),
            'face_id':np.dtype('uint32'),'xyz':np.dtype('float64'),'plane_y_xz':np.dtype('float64'),
            'area_xz':np.dtype('float64'),'cell_range_rc':np.dtype('int32'),'degenerate':np.dtype('uint8')}
        for name,shape in shapes.items():
            if arrays[name].shape!=shape or arrays[name].dtype!=dtypes[name]:
                raise AssertionError(f'face shard array contract mismatch: {path}:{name}')
        for name in ('xyz','plane_y_xz','area_xz'):
            if not np.isfinite(arrays[name]).all():raise AssertionError(f'non-finite face shard data: {path}:{name}')
        if np.any(arrays['kind']>1) or np.any(arrays['degenerate']>1):raise AssertionError(f'invalid categorical face value: {path}')
        deg=arrays['degenerate'].astype(bool)
        if np.any(arrays['area_xz']<0) or not np.array_equal(deg,arrays['area_xz']<=0):
            raise AssertionError(f'degenerate classification disagrees with area: {path}')
        if np.any(arrays['cell_range_rc']<-1):raise AssertionError(f'invalid negative cell range: {path}')

    def query_window(self,r0,r1,c0,c1,kind=None):
        if kind is not None and kind not in KIND:raise ValueError(f'unknown face kind: {kind}')
        result=[];window=(r0,r1,c0,c1)
        for _,arrays in self._shards:
            mask=query_mask(arrays['cell_range_rc'],window,arrays['kind'],kind)
            if mask.any():result.append({k:v[mask] for k,v in arrays.items()})
        if not result:return empty_arrays()
        return {k:np.concatenate([part[k] for part in result],axis=0) for k in result[0]}

    def query_cell(self,r,c,kind=None):return self.query_window(r,r,c,c,kind)

    def reverify(self):
        """Re-hash the manifest and every loaded shard after a query batch."""
        if sha(self.manifest_path)!=self._manifest_sha:raise AssertionError('EV93 manifest changed during query batch')
        for shard,_ in self._shards:
            path=self.run_dir/shard['path']
            if sha(path)!=shard['sha256']:raise AssertionError(f'shard changed during query batch: {path}')
        return True


def _record_lod_arrays(preflight,ev87,model,lod,kind,object_id,model_id,tx,ty,tz,cell,z0,n):
    rows=[];areas=[];planes=[];ranges=[];deg=[];face_ids=[]
    vertices=lod.vertices
    for face_id,face in enumerate(lod.faces):
        ids=list(face.vertex_indices)
        if len(ids)!=3:raise AssertionError(f'non-triangle ODOL face: model={model}, {kind}:{face_id}')
        if min(ids)<0 or max(ids)>=len(vertices):raise AssertionError(f'face vertex index out of range: {model}:{kind}:{face_id}')
        xyz=np.asarray([[float(vertices[i].x)+tx,float(vertices[i].y)+ty,float(vertices[i].z)+tz] for i in ids],dtype=np.float64)
        if not np.isfinite(xyz).all():raise AssertionError(f'non-finite translated vertex: {model}:{kind}:{face_id}')
        xy=xyz[:,[0,2]]
        poly=ev87.Polygon(xy)
        area=float(poly.area)
        if not math.isfinite(area) or area<0:raise AssertionError(f'invalid XZ area: {model}:{kind}:{face_id}')
        is_degenerate=(area<=0.0)
        if is_degenerate:
            # There is no unique Y(X,Z) plane for zero XZ area. Keep the face,
            # label it, and use a finite zero sentinel that consumers must ignore.
            coeff=np.zeros(3,dtype=np.float64)
        else:
            if not poly.is_valid:raise AssertionError(f'invalid positive-area XZ triangle: {model}:{kind}:{face_id}')
            try:
                coeff=np.asarray(ev87.affine_coeff(xy,xyz[:,1]),dtype=np.float64)
                ev90_coeff=np.asarray(preflight.affine(xy,xyz[:,1]),dtype=np.float64)
            except np.linalg.LinAlgError as exc:raise AssertionError(f'positive-area face has singular plane: {model}:{kind}:{face_id}') from exc
            if coeff.shape!=(3,) or not np.isfinite(coeff).all():raise AssertionError(f'non-finite plane coefficient: {model}:{kind}:{face_id}')
            if not np.allclose(coeff,ev90_coeff,rtol=0.0,atol=1e-12):
                raise AssertionError(f'EV87/EV90 affine coefficient disagreement: {model}:{kind}:{face_id}')
        rows.append(xyz);areas.append(area);planes.append(coeff)
        ranges.append(conservative_cell_range(xyz,cell,z0,n));deg.append(int(is_degenerate));face_ids.append(face_id)
    count=len(face_ids)
    return {'kind':np.full(count,KIND[kind],dtype=np.uint8),
        'object_id':np.full(count,int(object_id),dtype=np.int32),
        'model_id':np.full(count,int(model_id),dtype=np.uint32),
        'face_id':np.asarray(face_ids,dtype=np.uint32),
        'xyz':np.asarray(rows,dtype=np.float64).reshape((-1,3,3)),
        'plane_y_xz':np.asarray(planes,dtype=np.float64).reshape((-1,3)),
        'area_xz':np.asarray(areas,dtype=np.float64),
        'cell_range_rc':np.asarray(ranges,dtype=np.int32).reshape((-1,4)),
        'degenerate':np.asarray(deg,dtype=np.uint8)}


def _arrays_nbytes(arrays):return sum(int(a.nbytes) for a in arrays.values())


def _combine(parts):
    if not parts:return empty_arrays()
    return {key:np.concatenate([part[key] for part in parts],axis=0) for key in parts[0]}


def _write_manifest(path,manifest):
    tmp=Path(path).with_suffix('.json.tmp')
    tmp.write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    tmp.replace(path)


def _object_hash(ids):
    return hashlib.sha256(np.asarray(sorted(ids),dtype='<i4').tobytes()).hexdigest()


def build(output_root=OUT_ROOT,deadline_seconds=MAX_SECONDS,max_bytes=MAX_BYTES):
    started=time.monotonic();deadline=started+float(deadline_seconds)
    if Path(output_root).resolve()!=OUT_ROOT.resolve():
        raise ValueError(f'EV93 output must stay under the reviewed new folder: {OUT_ROOT}')
    verify_source_pins()
    preflight=load_module('ev90_preflight_ev93_index',EV90_PATH)
    ev87=load_module('ev87_face_source_ev93_index',EV87_PATH)
    if sha(EV90_PATH)!=EXPECTED_EV90_SHA or sha(EV87_PATH)!=EXPECTED_EV87_SHA:
        raise AssertionError('EV87/EV90 source changed while importing')
    src=preflight.check_linkage_and_load()
    if (preflight.N,preflight.CELL,preflight.Z0)!=(ev87.N,ev87.CELL,ev87.Z0):
        raise AssertionError('EV87 and EV90 global grid conventions differ')
    if tuple(tuple(t) for t in ev87.TRIS)!=((0,1,3),(0,2,3)):
        raise AssertionError('EV87 native NW-SE triangle split changed')
    wrp=src['wrp'];bounds=src['bounds'];deploy=src['deploy']
    objects_by_id={int(o['id']):o for o in bounds['objects']}
    if len(objects_by_id)!=18024:raise AssertionError('duplicate or missing IDs in compiled bounds inventory')
    water=[o for o in wrp['objects'] if 'baltic_water_v30' in o['name'].replace('\\','/').lower()]
    if len(water)!=18024:raise AssertionError(f'expected 18,024 water objects, got {len(water)}')
    water_ids=[int(o['id']) for o in water]
    if len(set(water_ids))!=18024 or set(water_ids)!=set(objects_by_id):
        raise AssertionError('water WRP IDs are not an exact bijection with bounds manifest IDs')
    if bounds.get('world_sha256')!=ev87.BOUNDS_WORLD_SHA or bounds.get('water_sha256')!=deploy.get('files',{}).get('baltic_water_v30.pbo'):
        raise AssertionError('compiled bounds source-world/water identity differs from EV87/deployed B pins')
    if src['compiled_oprw_sha']!=deploy.get('compiled_wrp_sha256'):
        raise AssertionError('embedded deployed OPRW hash differs from B deploy manifest')
    model_bounds=bounds['models'];model_names=sorted({o['name'].replace('\\','/').split('/')[-1] for o in water})
    model_id={name:i for i,name in enumerate(model_names)}
    by_model={name:[] for name in model_names}
    rotation_bad=[];max_bounds_delta=0.0
    for obj in sorted(water,key=lambda x:int(x['id'])):
        ident=int(obj['id']);entry=objects_by_id[ident]
        name=obj['name'].replace('\\','/').split('/')[-1]
        if entry['model'].lower()!=name.lower():raise AssertionError(f'model name mismatch for object {ident}')
        matrix=np.asarray(obj['matrix'],dtype=np.float64)
        if matrix.shape!=(12,) or not np.isfinite(matrix).all():raise AssertionError(f'bad WRP transform for object {ident}')
        if not np.array_equal(matrix[:9].reshape(3,3),np.eye(3)):rotation_bad.append(ident);continue
        if not np.array_equal(matrix[[9,11]].astype(np.float32),np.asarray(entry['position'],dtype=np.float32)[[0,2]]):
            raise AssertionError(f'WRP transform disagrees with linked bounds position for object {ident}')
        local=model_bounds.get(name)
        if local is None:raise AssertionError(f'missing compiled bounds model record: {name}')
        lb=np.asarray(local['bounds'],dtype=np.float64);tx,tz=float(matrix[9]),float(matrix[11])
        computed=np.asarray([lb[0]+tx,lb[1]+tz,lb[2]+tx,lb[3]+tz],dtype=np.float64)
        actual=np.asarray(entry['bounds'],dtype=np.float64)
        delta=float(np.max(np.abs(computed-actual)));max_bounds_delta=max(max_bounds_delta,delta)
        if not np.isfinite(actual).all() or delta>1e-4:raise AssertionError(f'compiled bounds mismatch for object {ident}: {delta}')
        by_model[name].append((obj,entry,matrix))
    if rotation_bad:raise AssertionError(f'non-translation water transforms: {len(rotation_bad)}')

    now=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    run_dir=Path(output_root)/'runs'/f'{now}-{secrets.token_hex(4)}'
    (run_dir/'shards').mkdir(parents=True,exist_ok=False)
    manifest_path=run_dir/'manifest.json'
    initial_hashes={str(path):digest for path,digest in src['hashes'].items()}
    initial_hashes[str(EV87_PATH)]=sha(EV87_PATH);initial_hashes[str(EV90_PATH)]=sha(EV90_PATH);initial_hashes[str(PLAN)]=sha(PLAN)
    initial_hashes[str(src['world_pbo'])]=sha(src['world_pbo']);initial_hashes[str(src['water_pbo'])]=sha(src['water_pbo'])
    initial_hashes[str(preflight.BOUNDS)]=sha(preflight.BOUNDS)
    initial_hashes[str(Path(__file__).resolve())]=sha(Path(__file__).resolve())
    manifest_builder_sha=initial_hashes[str(Path(__file__).resolve())]
    odol_module=sys.modules[src['ODOL'].__module__]
    for module in (src['wrp0wzd'],src['attach_navmesh'],odol_module):
        module_path=Path(module.__file__).resolve();initial_hashes[str(module_path)]=sha(module_path)
    parser_dir=Path(odol_module.__file__).resolve().parent
    for helper_name in ('bis_reader.py','math_types.py','lzo_decompress.py','lzss_decompress.py'):
        helper=parser_dir/helper_name
        if helper.is_file():initial_hashes[str(helper)]=sha(helper)
    manifest={'schema':SCHEMA,'status':'BUILDING','created_utc':now,'plan_sha256':sha(PLAN),
        'ev87_source':{'path':str(EV87_PATH),'sha256':sha(EV87_PATH)},
        'ev90_source':{'path':str(EV90_PATH),'sha256':sha(EV90_PATH)},
        'builder_source':{'path':str(Path(__file__).resolve()),'sha256':manifest_builder_sha},
        'base_identity':{'terrain_sha256':initial_hashes[str(preflight.B/'candidate/terrain.npz')],
            'wrp_source_sha256':sha(preflight.WRP),'bounds_world_sha256':bounds['world_sha256'],
            'compiled_oprw_sha256':src['compiled_oprw_sha'],
            'world_pbo_sha256':sha(src['world_pbo']),'water_pbo_sha256':sha(src['water_pbo']),
            'bounds_sha256':sha(preflight.BOUNDS),'world_manifest_sha256':src['bounds']['world_sha256'],
            'water_manifest_sha256':src['bounds']['water_sha256']},
        'models':[],'object_count':18024,'water_object_ids_sha256':_object_hash(water_ids),
        'counts':{'faces':0,'physical':0,'visible':0,'degenerate_physical':0,'degenerate_visible':0},
        'observed_counts':{'faces':0,'physical':0,'visible':0,'degenerate_physical':0,'degenerate_visible':0},
        'shards':[],'input_hashes':initial_hashes,'max_output_bytes':int(max_bytes),
        'time_budget_seconds':int(deadline_seconds),'max_bounds_delta_m':max_bounds_delta,
        'geometry_contract':{'lod_physical':PHYSICAL_RES,'lod_visible':VISIBLE_RES,
            'degenerate_rule':'area_xz <= 0.0; retained with plane_y_xz zero sentinel',
            'tiny_positive_faces':'retained regardless of EV87 downstream clipping-area threshold',
            'range':'inclusive closed-bbox overlap; exact geometry still requires consumer clipping'},
        'incomplete_reason':None}
    _write_manifest(manifest_path,manifest)

    pending=[];pending_rows=0;total_bytes=0;shard_i=0;model_records=[];input_model_paths=[]
    def flush_pending():
        nonlocal pending,pending_rows,total_bytes,shard_i
        if not pending_rows:return
        arrays=_combine(pending);estimated=_arrays_nbytes(arrays)+16_384
        if total_bytes+estimated>max_bytes:
            raise _StopBuild('OUTPUT_LIMIT',f'next shard needs about {estimated} bytes; cap={max_bytes}, written={total_bytes}')
        rel=Path('shards')/f'faces-{shard_i:06d}.npz';out=run_dir/rel
        with out.open('xb') as f:
            np.savez(f,**arrays);f.flush();os.fsync(f.fileno())
        size=out.stat().st_size
        if total_bytes+size>max_bytes:raise _StopBuild('OUTPUT_LIMIT','actual shard size exceeded output cap')
        shard={'path':str(rel).replace('\\','/'),'sha256':sha(out),'records':int(pending_rows),'bytes':int(size)}
        manifest['shards'].append(shard);total_bytes+=size;shard_i+=1
        manifest['counts']['faces']+=int(pending_rows)
        for kind_name in KIND:
            mask=arrays['kind']==KIND[kind_name]
            manifest['counts'][kind_name]+=int(np.count_nonzero(mask))
            manifest['counts'][f'degenerate_{kind_name}']+=int(np.count_nonzero(mask & arrays['degenerate'].astype(bool)))
        pending=[];pending_rows=0
        _write_manifest(manifest_path,manifest)

    try:
        for mid,name in enumerate(model_names):
            if time.monotonic()>deadline:raise _StopBuild('TIME_LIMIT',f'deadline reached before model {name}')
            model_path=Path(preflight.MODEL_DIR)/name
            local=model_bounds[name];expected=local.get('sha256')
            if not expected:raise AssertionError(f'missing model SHA in bounds manifest: {name}')
            digest=sha(model_path)
            if digest!=expected:raise AssertionError(f'compiled model hash mismatch: {name}')
            input_model_paths.append(model_path);initial_hashes[str(model_path)]=digest
            with model_path.open('rb') as f:header=f.read(8)
            if len(header)!=8 or header[:4]!=b'ODOL':raise AssertionError(f'not an ODOL P3D: {name}')
            version=struct.unpack_from('<I',header,4)[0]
            if version not in (54,55):raise AssertionError(f'unverified ODOL version {version} for {name}')
            model=src['ODOL'].from_file(str(model_path))
            lods={}
            for kind,res in (('physical',PHYSICAL_RES),('visible',VISIBLE_RES)):
                exact=[lod for lod in model.lods if lod.resolution==res]
                if len(exact)!=1:raise AssertionError(f'{name}: expected exactly one {kind} LOD {res}, found {len(exact)}')
                lods[kind]=exact[0]
            rec={'model_id':mid,'basename':name,'sha256':digest,'odol_version':version,
                'physical_resolution':PHYSICAL_RES,'visible_resolution':VISIBLE_RES,
                'physical_faces':len(lods['physical'].faces),'visible_faces':len(lods['visible'].faces)}
            model_records.append(rec)
            for obj,entry,matrix in by_model[name]:
                if time.monotonic()>deadline:raise _StopBuild('TIME_LIMIT',f'deadline reached during model {name}')
                ident=int(obj['id']);tx,ty,tz=map(float,matrix[9:12])
                for kind in ('physical','visible'):
                    arrays=_record_lod_arrays(preflight,ev87,name,lods[kind],kind,ident,mid,tx,ty,tz,
                        preflight.CELL,preflight.Z0,preflight.N)
                    count=len(arrays['kind']);pending.append(arrays);pending_rows+=count
                    manifest['observed_counts']['faces']+=count;manifest['observed_counts'][kind]+=count
                    manifest['observed_counts'][f'degenerate_{kind}']+=int(arrays['degenerate'].sum())
                    if pending_rows>=SHARD_RECORDS:flush_pending()
            if mid%64==0:
                manifest['models']=model_records.copy();manifest['progress']={'models_read':mid+1,'models_total':len(model_names),
                    'objects_total':sum(len(by_model[n]) for n in model_names[:mid+1]),'bytes_written':total_bytes}
                _write_manifest(manifest_path,manifest)
        flush_pending()
        if len(model_records)!=len(model_names):raise AssertionError('model table incomplete')
        if sum(len(v) for v in by_model.values())!=18024:raise AssertionError('indexed water object count changed')
        if manifest['counts']['physical']+manifest['counts']['visible']!=manifest['counts']['faces']:
            raise AssertionError('face count accounting mismatch')
        if manifest['counts']!=manifest['observed_counts']:
            raise AssertionError('observed faces differ from persisted shard face counts')
        if time.monotonic()>deadline:raise _StopBuild('TIME_LIMIT','deadline reached during final integrity checks')
        if sha(PLAN)!=EXPECTED_PLAN_SHA or sha(EV87_PATH)!=EXPECTED_EV87_SHA or sha(EV90_PATH)!=EXPECTED_EV90_SHA:
            raise AssertionError('source changed during index build')
        for path,digest in initial_hashes.items():
            if sha(path)!=digest:raise AssertionError(f'input changed during build: {path}')
        manifest['models']=model_records
        manifest['status']='COMPLETE'
        manifest['output_bytes']=total_bytes
        manifest['elapsed_seconds']=time.monotonic()-started
        _write_manifest(manifest_path,manifest)
        return run_dir,manifest
    except _StopBuild as exc:
        flush_pending_if_budget=exc.reason=='TIME_LIMIT'
        if flush_pending_if_budget:
            try:flush_pending()
            except _StopBuild:pass
        manifest['models']=model_records
        manifest['status']=f'INCOMPLETE_{exc.reason}'
        manifest['incomplete_reason']=str(exc)
        manifest['buffered_unwritten_records']=int(pending_rows)
        manifest['output_bytes']=total_bytes
        manifest['elapsed_seconds']=time.monotonic()-started
        _write_manifest(manifest_path,manifest)
        return run_dir,manifest
    except Exception as exc:
        manifest['models']=model_records
        manifest['status']='ERROR'
        manifest['incomplete_reason']=repr(exc)
        manifest['traceback']=traceback.format_exc()
        manifest['output_bytes']=total_bytes
        manifest['elapsed_seconds']=time.monotonic()-started
        _write_manifest(manifest_path,manifest)
        raise


class _StopBuild(Exception):
    def __init__(self,reason,message):self.reason=reason;super().__init__(message)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',action='store_true',help='explicitly build a new timestamped cache (read-only source inputs)')
    args=parser.parse_args()
    if not args.build:parser.error('pass --build to start the bounded index build')
    run_dir,manifest=build(OUT_ROOT)
    print(json.dumps({'status':manifest['status'],'run_dir':str(run_dir),
        'faces':manifest['counts']['faces'],'objects':manifest['object_count'],
        'models':len(manifest['models']),'output_bytes':manifest.get('output_bytes')}))
    if manifest['status']!='COMPLETE':raise SystemExit(2)


if __name__=='__main__':main()
