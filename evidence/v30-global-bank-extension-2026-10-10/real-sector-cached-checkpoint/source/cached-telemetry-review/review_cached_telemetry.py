from __future__ import annotations
import ast, ctypes, difflib, hashlib, json, os, sys, time
from pathlib import Path

RS = Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/global-operator-prototype/real-sector-preflight')
SOLVE = Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/global-operator-prototype/admm-quantized-pilot/solve.py')
OLD_DRIVER = RS/'solve_real_sector.py'
NEW_DRIVER = RS/'solve_real_sector_cached.py'
OLD_CONSUMER = RS/'verify_real_sector.py'
NEW_CONSUMER = RS/'verify_real_sector_cached.py'
AMENDMENT = RS/'AMENDMENT_CACHED_TELEMETRY.md'
OUT = RS/'cached-telemetry-review'
EXPECTED = {
    str(SOLVE): '7e8636bf54ba23f7e23bc2f06464100439468da7b4edca85f96c72d0cd40e149',
    str(OLD_DRIVER): '9f4fc8e5edc2ad7a8276264d4b6fea05ee8682b777d370cb75a283f0cb4d296e',
    str(NEW_DRIVER): '5e75e0e1d3e3c6938679cd31e87f4f317353e64ff919c471d79d1a04d50f98f9',
    str(NEW_CONSUMER): '3e7a6996f5e4b637ba7d94ad20dd3add6643f52db31d7098c6baa32e238d4799',
    str(AMENDMENT): 'd64ad4441348bb2054800851cf7ef19f5f143143d62b93e0659de804b2565f7a',
}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def module(path): return ast.parse(Path(path).read_text(encoding='utf-8'))
def find_fn(tree,name): return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
def find_class(tree,name): return next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==name)

hashes={str(p):sha(p) for p in [SOLVE,OLD_DRIVER,NEW_DRIVER,NEW_CONSUMER,AMENDMENT]}
for path, expected in EXPECTED.items():
    if hashes[path] != expected: raise AssertionError(f'pin mismatch {path}: {hashes[path]} != {expected}')
old_solve=module(SOLVE)
old_fn=find_fn(old_solve,'process_memory')
old_cls=next(n for n in old_fn.body if isinstance(n,ast.ClassDef) and n.name=='Counters')
new_driver=module(NEW_DRIVER)
new_cls=find_class(new_driver,'Counters')
new_helper=find_fn(new_driver,'_cached_process_memory')
old_body=[n for n in old_fn.body if n is not old_cls]
old_ast=ast.dump(ast.Module(body=old_body,type_ignores=[]),include_attributes=False)
new_ast=ast.dump(ast.Module(body=new_helper.body,type_ignores=[]),include_attributes=False)
class_equal=ast.dump(old_cls,include_attributes=False)==ast.dump(new_cls,include_attributes=False)
helper_body_equal=old_ast==new_ast
old_snap=find_fn(module(OLD_DRIVER),'_memory_snapshot')
new_snap=find_fn(new_driver,'_memory_snapshot')
old_snap_src=ast.dump(old_snap,include_attributes=False)
new_snap_src=ast.dump(new_snap,include_attributes=False)
old_consumer=Path(OLD_CONSUMER).read_text(encoding='utf-8').splitlines()
new_consumer=Path(NEW_CONSUMER).read_text(encoding='utf-8').splitlines()
consumer_diff=list(difflib.unified_diff(old_consumer,new_consumer,fromfile='verify_real_sector.py',tofile='verify_real_sector_cached.py',lineterm=''))
# Confirm consumer's source delta is limited to the pinned driver identity/path.
consumer_changed=[line for line in consumer_diff if line.startswith(('+','-')) and not line.startswith(('+++','---'))]
# Run the exact cached class/helper AST in this fresh GIS interpreter; do not import driver/main or solver.
ns={'ctypes':ctypes,'os':os}
exec(compile(ast.fix_missing_locations(ast.Module(body=[new_cls,new_helper],type_ignores=[])),str(NEW_DRIVER),'exec'),ns)
Counter=ns['Counters']; helper=ns['_cached_process_memory']
abi={'pointer_bits':ctypes.sizeof(ctypes.c_void_p)*8,'c_ulong_bytes':ctypes.sizeof(ctypes.c_ulong),'c_size_t_bytes':ctypes.sizeof(ctypes.c_size_t),'Counters_size':ctypes.sizeof(Counter),'field_offsets':{name:getattr(Counter,name).offset for name,_ in Counter._fields_}}
expected_offsets={'cb':0,'PageFaultCount':4,'PeakWorkingSetSize':8,'WorkingSetSize':16,'QuotaPeakPagedPoolUsage':24,'QuotaPagedPoolUsage':32,'QuotaPeakNonPagedPoolUsage':40,'QuotaNonPagedPoolUsage':48,'PagefileUsage':56,'PeakPagefileUsage':64}
abi_ok=(abi['pointer_bits']==64 and abi['c_ulong_bytes']==4 and abi['c_size_t_bytes']==8 and abi['Counters_size']==72 and abi['field_offsets']==expected_offsets)
cache_before=len(ctypes._pointer_type_cache)
t0=time.perf_counter(); last=None
for _ in range(10000): last=helper()
elapsed=time.perf_counter()-t0
cache_after=len(ctypes._pointer_type_cache)
if not class_equal or not helper_body_equal or not abi_ok: raise AssertionError('class/helper/ABI mismatch')
if set(last)!={'pid','peak_working_set_bytes','working_set_bytes','peak_commit_bytes','method'} or last['pid']!=os.getpid(): raise AssertionError('helper output contract mismatch')
if cache_after-cache_before != 1: raise AssertionError(f'expected one retained pointer type, got {cache_after-cache_before}')
if elapsed>30 or max(last['peak_working_set_bytes'],last['peak_commit_bytes'])>268435456: raise AssertionError('probe exceeded authorized wall/memory budget')
result={'schema':'cached-helper-review.v1','status':'PASS_TELEMETRY_HELPER_ONLY','hashes':hashes,'old_nested_class_equals_new_module_class':class_equal,'original_body_without_nested_Counters_equals_cached_helper_body':helper_body_equal,'old_driver_snapshot_ast':old_snap_src,'new_driver_snapshot_ast':new_snap_src,'consumer_diff_lines':consumer_diff,'consumer_changed_lines':consumer_changed,'abi':abi,'abi_matches_win32_process_memory_counters':abi_ok,'runtime':{'python':sys.version,'executable':sys.executable,'fresh_interpreter':True,'solver_called':False,'driver_main_called':False,'helper_calls':10000,'elapsed_seconds':elapsed,'pointer_type_cache_before':cache_before,'pointer_type_cache_after':cache_after,'pointer_type_cache_delta':cache_after-cache_before,'helper_result':last,'within_30_seconds':elapsed<=30,'observed_peak_working_set_bytes':last['peak_working_set_bytes'],'observed_peak_pagefile_bytes':last['peak_commit_bytes'],'within_256MiB':max(last['peak_working_set_bytes'],last['peak_commit_bytes'])<=268435456}}
(OUT/'review.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'python':sys.executable,'elapsed_seconds':elapsed,'cache_delta':cache_after-cache_before,'memory':last,'abi':abi,'class_equal':class_equal,'helper_body_equal':helper_body_equal,'consumer_changed_lines':consumer_changed},sort_keys=True))
