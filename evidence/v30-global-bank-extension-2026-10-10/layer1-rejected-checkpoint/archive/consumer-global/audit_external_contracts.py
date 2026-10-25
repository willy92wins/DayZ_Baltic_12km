"""Read actual imported APIs, detect absent attributes and invalid explicit call shapes."""
import ast
import importlib.util
import inspect
import json
from pathlib import Path

P = Path(__file__).parent
spec = importlib.util.spec_from_file_location('audit_consumer', P / 'verify_layer.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
ev, ev91, ev87, cv, shape, ev92, idx = m.load_helpers()
objects = dict(ev=ev, ev91=ev91, ev87=ev87, cv=cv, shape=shape, ev92=ev92,
               index=idx.FaceRangeIndex)
tree = ast.parse((P / 'verify_layer.py').read_text())
missing, calls, unchecked = [], [], []
for node in ast.walk(tree):
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in objects:
        name = node.value.id
        # Instance state declared by FaceRangeIndex.__init__, not class attributes.
        if name == 'index' and node.attr in {'_shards', 'manifest'}:
            continue
        if not hasattr(objects[name], node.attr):
            missing.append({'symbol': name + '.' + node.attr, 'line': node.lineno})
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        continue
    fn = node.func
    if not isinstance(fn.value, ast.Name) or fn.value.id not in objects:
        continue
    owner = fn.value.id
    func = getattr(objects[owner], fn.attr, None)
    if not callable(func):
        continue
    label = owner + '.' + fn.attr
    row = {'symbol': label, 'line': node.lineno}
    try:
        sig = inspect.signature(func)
        row['signature'] = str(sig)
        row['source'] = inspect.getsourcefile(func)
        row['source_line'] = inspect.getsourcelines(func)[1]
        if any(isinstance(x, ast.Starred) for x in node.args) or any(x.arg is None for x in node.keywords):
            unchecked.append({**row, 'reason': 'star expansion requires runtime contract test'})
            continue
        args = [None] * len(node.args)
        if owner == 'index':
            args.insert(0, None)
        sig.bind(*args, **{x.arg: None for x in node.keywords})
        row['call_shape'] = 'BOUND'
    except (ValueError, TypeError, OSError) as exc:
        row['call_shape'] = 'ERROR'
        row['error'] = repr(exc)
    calls.append(row)
result = {'status': 'STATIC_EXTERNAL_API_CHECK_ONLY', 'consumer_sha256': m.sha(P / 'verify_layer.py'),
          'missing_attributes': missing, 'calls': calls, 'unchecked': unchecked,
          'limitations': 'Signatures and presence do not prove correct return schema or semantics.'}
output = P / ('external-api-' + result['consumer_sha256'][:8] + '.json')
output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'output': str(output), 'missing': missing,
                  'bad_calls': [x for x in calls if x.get('call_shape') != 'BOUND'],
                  'checked_calls': len(calls), 'unchecked': unchecked}))
