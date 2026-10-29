from __future__ import annotations
import hashlib, json, os, stat
from pathlib import Path
BACKSLASH = chr(92)
HEX = set('0123456789abcdef')
MAX_FILE = 16777216
MAX_TOTAL = 33554432
REQUIRED_FILES = ('b2a_models','b2a_report','b2a_config','catalog','b4a3_contract','b4a3_summary','road_models','road_entries','b4b0_contract','b4b0_report','b4b0_consumer','b4b0_recovery_receipt','b2a_correction_receipt','b2a_code_adjudication','road_execution_approval','road_report','road_inputs','road_source_table')
REQUIRED_METHODS = ('b2a_code','road_catalog_code')
class InvalidError(ValueError):
    pass
def is_int_exact(v):
    return type(v) is int
def is_sha256(v):
    return type(v) is str and len(v) == 64 and all(c in HEX for c in v)
def require_keys(obj, keys, what='object'):
    if type(obj) is not dict:
        raise InvalidError(what + ' must be object')
    if set(obj.keys()) != set(keys):
        raise InvalidError(what + ' keys mismatch')
def _no_dup(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise InvalidError('duplicate JSON key ' + repr(k))
        out[k] = v
    return out
def _bad_const(x):
    raise InvalidError('invalid JSON constant ' + x)
def strict_json_loads(data):
    if type(data) is bytes:
        try:
            text = data.decode('utf-8')
        except Exception as e:
            raise InvalidError('invalid utf-8') from e
    else:
        text = data
    try:
        return json.loads(text, object_pairs_hook=_no_dup, parse_constant=_bad_const)
    except InvalidError:
        raise
    except Exception as e:
        raise InvalidError('invalid JSON: ' + str(e)) from e
def parse_jsonl_physical(data):
    if type(data) is not bytes:
        raise InvalidError('jsonl must be bytes')
    try:
        text = data.decode('utf-8')
    except Exception as e:
        raise InvalidError('jsonl invalid utf-8') from e
    parts = text.split(chr(10))
    if parts and parts[-1] == '':
        parts = parts[:-1]
    rows = []
    for i, line in enumerate(parts):
        if line.strip() == '':
            raise InvalidError('jsonl blank line at ' + str(i))
        obj = strict_json_loads(line)
        if type(obj) is not dict:
            raise InvalidError('jsonl line not object at ' + str(i))
        rows.append(obj)
    return rows
def normalize_path_value(value, what='path'):
    if type(value) is not str:
        raise InvalidError(what + ' must be string')
    for ch in value:
        o = ord(ch)
        if o > 127 or o < 32 or o == 127:
            raise InvalidError(what + ' non-ASCII or control in raw value')
    if len(value.encode('ascii')) > 4096:
        raise InvalidError(what + ' too long')
    s = value.replace(BACKSLASH, '/').lower().strip('/')
    if s == '':
        raise InvalidError(what + ' empty after normalization')
    if len(s.encode('utf-8')) > 4096:
        raise InvalidError(what + ' too long')
    if ':' in s:
        raise InvalidError(what + ' forbidden colon')
    for p in s.split('/'):
        if p in ('', '.', '..'):
            raise InvalidError(what + ' bad component')
    return s
def normalize_join(prefix, entry):
    return normalize_path_value(prefix, 'prefix') + '/' + normalize_path_value(entry, 'entry')
def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()
def _stat_core(st):
    return (st.st_dev, st.st_ino, st.st_mtime_ns, st.st_size)
def _is_reparse(st):
    attrs = getattr(st, 'st_file_attributes', 0)
    return bool(attrs & 0x400) if attrs else False
def stable_read(path, max_bytes=MAX_FILE):
    p = Path(path)
    try:
        lst = os.lstat(p)
    except Exception as e:
        raise InvalidError('cannot stat ' + str(p)) from e
    if stat.S_ISLNK(lst.st_mode) or _is_reparse(lst) or not stat.S_ISREG(lst.st_mode):
        raise InvalidError('not a regular non-reparse file ' + str(p))
    if lst.st_size > max_bytes:
        raise InvalidError('file too large ' + str(p))
    datas = []
    cores = []
    for _ in range(2):
        fd = os.open(p, os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0))
        try:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode):
                raise InvalidError('not regular ' + str(p))
            if before.st_size > max_bytes:
                raise InvalidError('file too large ' + str(p))
            chunks = []
            total = 0
            while True:
                b = os.read(fd, 1048576)
                if not b:
                    break
                total += len(b)
                if total > max_bytes:
                    raise InvalidError('file too large ' + str(p))
                chunks.append(b)
            after = os.fstat(fd)
        finally:
            os.close(fd)
        data = b''.join(chunks)
        if len(data) != before.st_size:
            raise InvalidError('size mismatch during read ' + str(p))
        path_st = os.stat(p, follow_symlinks=False)
        if _stat_core(before) != _stat_core(after):
            raise InvalidError('unstable fstat ' + str(p))
        if _stat_core(before) != _stat_core(path_st):
            raise InvalidError('fstat/path mismatch ' + str(p))
        if stat.S_ISLNK(path_st.st_mode) or _is_reparse(path_st):
            raise InvalidError('reparse ' + str(p))
        datas.append(data)
        cores.append(_stat_core(before))
    if datas[0] != datas[1] or cores[0] != cores[1]:
        raise InvalidError('unstable double read ' + str(p))
    return datas[0], sha256_bytes(datas[0]), {'dev': cores[0][0], 'ino': cores[0][1], 'mtime_ns': cores[0][2], 'size': cores[0][3]}
def check_no_traversal_component(path_text):
    for part in str(path_text).replace(BACKSLASH, '/').split('/'):
        if part == '..':
            raise InvalidError('traversal in path')
def load_pinned_bundle(contract_path, contract_sha_arg):
    if not is_sha256(contract_sha_arg):
        raise InvalidError('contract-sha must be 64 lowercase hex')
    check_no_traversal_component(contract_path)
    cdata, csha, _info = stable_read(contract_path)
    if csha != contract_sha_arg:
        raise InvalidError('contract sha mismatch')
    contract = strict_json_loads(cdata)
    if type(contract) is not dict:
        raise InvalidError('contract must be object')
    if contract.get('schema') != 'road-b4b1.v1':
        raise InvalidError('contract schema mismatch')
    if contract.get('scope') != 'SAVED_CONTENT_IDENTITY_ONLY':
        raise InvalidError('contract scope mismatch')
    files = contract.get('files')
    methods = contract.get('methods')
    oracles_pin = contract.get('oracles')
    if type(files) is not dict or set(files.keys()) != set(REQUIRED_FILES):
        raise InvalidError('contract files must be exactly the 18 required source ids')
    if type(methods) is not dict or set(methods.keys()) != set(REQUIRED_METHODS):
        raise InvalidError('contract methods must be exactly the 2 required method ids')
    if type(oracles_pin) is not dict:
        raise InvalidError('contract oracles pin required')
    all_pins = []
    for sid in REQUIRED_FILES:
        all_pins.append((sid, files[sid]))
    for sid in REQUIRED_METHODS:
        all_pins.append((sid, methods[sid]))
    all_pins.append(('oracles', oracles_pin))
    reserved = len(cdata)
    for sid, pin in all_pins:
        if type(pin) is not dict or set(pin.keys()) != {'path', 'sha256', 'bytes'}:
            raise InvalidError('pin keys mismatch ' + sid)
        if type(pin['path']) is not str or not pin['path'] or not is_sha256(pin['sha256']) or not is_int_exact(pin['bytes']) or pin['bytes'] < 0:
            raise InvalidError('bad pin values ' + sid)
        if pin['bytes'] > MAX_FILE:
            raise InvalidError('pinned file exceeds individual cap before read ' + sid)
        check_no_traversal_component(pin['path'])
        reserved += pin['bytes']
        if reserved > MAX_TOTAL:
            raise InvalidError('total input bytes cap exceeded before read')
    sources = {}
    inputs = []
    for sid, pin in all_pins:
        data, actual, _i = stable_read(pin['path'])
        if actual != pin['sha256'] or len(data) != pin['bytes']:
            raise InvalidError('pin mismatch ' + sid)
        if sid in REQUIRED_METHODS:
            parsed = None
        elif sid == 'road_models':
            parsed = parse_jsonl_physical(data)
        else:
            parsed = strict_json_loads(data)
        sources[sid] = {'bytes_data': data, 'sha256': actual, 'bytes': len(data), 'parsed': parsed, 'path': pin['path']}
        inputs.append({'source_id': sid, 'sha256': actual, 'bytes': len(data)})
    inputs.sort(key=lambda x: x['source_id'])
    return contract, csha, sources, inputs
def resolve_pointer(obj, pointer):
    if type(pointer) is not str or not pointer.startswith('/'):
        raise InvalidError('bad pointer')
    cur = obj
    for raw in pointer[1:].split('/'):
        part = raw.replace('~1', '/').replace('~0', '~')
        if type(cur) is list:
            if not part.isdigit():
                raise InvalidError('bad list pointer')
            idx = int(part)
            if idx >= len(cur):
                raise InvalidError('pointer out of range')
            cur = cur[idx]
        elif type(cur) is dict:
            if part not in cur:
                raise InvalidError('pointer missing')
            cur = cur[part]
        else:
            raise InvalidError('pointer traverses scalar')
    return cur
def write_exclusive(path, data, max_bytes=MAX_FILE):
    if type(data) is not bytes:
        raise InvalidError('output must be bytes')
    if len(data) > max_bytes:
        raise InvalidError('output exceeds byte cap before create')
    p = Path(path)
    if os.path.lexists(p):
        raise InvalidError('output already exists')
    if p.parent and not p.parent.exists():
        raise InvalidError('output parent missing')
    fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_BINARY', 0), 0o644)
    try:
        off = 0
        while off < len(data):
            n = os.write(fd, data[off:])
            if n <= 0:
                raise InvalidError('short write')
            off += n
        os.fsync(fd)
    finally:
        os.close(fd)
def dump_json(obj):
    out = bytearray()
    for part in json.JSONEncoder(sort_keys=True, indent=2, ensure_ascii=False).iterencode(obj):
        chunk = part.encode('utf-8')
        if len(out) + len(chunk) + 1 > MAX_FILE:
            raise InvalidError('serialized report cap before retain')
        out.extend(chunk)
    out.extend(b'\n')
    return bytes(out)
def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
