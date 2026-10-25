"""Small wrapper-path fixtures; never loads the global terrain or runs rollback."""
from __future__ import annotations
import ast
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import numpy as np

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'rollback_once.py'

def load_wrapper():
    spec=importlib.util.spec_from_file_location('rollback_once_fixture_module',SOURCE)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class IdentityA:
    def __init__(self,rhs): self.rhs_a=np.asarray(rhs,dtype=np.float64)
    def matvec_a(self,x): return np.asarray(x,dtype=np.float64)

def test_float32_objective_path():
    wrapper=load_wrapper()
    x=np.array([1.00000006,-2.0000001,0.12500001],dtype=np.float64)
    rhs=np.array([0.25,-1.0,0.0],dtype=np.float64)
    got=wrapper.objective_after_float32_cast(IdentityA(rhs),x)
    q=x.astype(np.float32).astype(np.float64)-rhs
    expected=float(np.dot(q,q))
    assert got==expected
    assert np.isfinite(got) and got>0

def test_solution_lifetime_covers_float32_cost():
    tree=ast.parse(SOURCE.read_text(encoding='utf-8-sig'))
    run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run')
    cost_line=next(n.lineno for n in ast.walk(run)
                   if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)
                   and n.func.id=='objective_after_float32_cast')
    delete_lines=[n.lineno for n in ast.walk(run) if isinstance(n,ast.Delete)
                  and any(isinstance(t,ast.Name) and t.id=='solution' for t in n.targets)]
    assert delete_lines and min(delete_lines)>cost_line

def test_readset_schema_and_hashes():
    wrapper=load_wrapper()
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'input.bin'; p.write_bytes(b'fixture-readset-v1')
        got=wrapper.readset([p])
        key=str(p)
        expected=hashlib.sha256(p.read_bytes()).hexdigest()
        assert got=={key:expected}
        p.write_bytes(b'changed')
        assert wrapper.readset([p])[key]!=got[key]

def test_no_improvement_is_not_pending_acceptance():
    tree=ast.parse(SOURCE.read_text(encoding='utf-8-sig'))
    run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run')
    branch=next(n for n in ast.walk(run) if isinstance(n,ast.If)
                and isinstance(n.test,ast.Compare)
                and isinstance(n.test.left,ast.Name) and n.test.left.id=='cost_final')
    literal_values=[n.value for stmt in branch.body for n in ast.walk(stmt) if isinstance(n,ast.Constant)
                    and isinstance(n.value,str)]
    assert 'NO_OBJECTIVE_IMPROVEMENT' in literal_values
    assert 'PENDING_INDEPENDENT_CONSUMER' not in literal_values

def test_pending_candidate_is_owned_before_write_or_guard():
    tree=ast.parse(SOURCE.read_text(encoding='utf-8-sig'))
    run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run')
    assign_line=next(n.lineno for n in ast.walk(run) if isinstance(n,ast.Assign)
                     and any(isinstance(t,ast.Name) and t.id=='pending_candidate' for t in n.targets)
                     and isinstance(n.value,ast.Name) and n.value.id=='temp')
    open_line=next(n.lineno for n in ast.walk(run) if isinstance(n,ast.Call)
                   and isinstance(n.func,ast.Attribute) and n.func.attr=='open'
                   and isinstance(n.func.value,ast.Name) and n.func.value.id=='temp')
    write_guard_line=next(n.lineno for n in ast.walk(run) if isinstance(n,ast.Call)
                          and isinstance(n.func,ast.Attribute) and n.func.attr=='check'
                          and any(isinstance(a,ast.Constant) and a.value=='candidate_write' for a in n.args))
    assert assign_line<open_line<write_guard_line

def test_terrain_written_tracks_publish_and_cleanup():
    tree=ast.parse(SOURCE.read_text(encoding='utf-8-sig'))
    run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run')
    lines=[]
    for n in ast.walk(run):
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='replace':
            lines.append(('publish',n.lineno))
        if isinstance(n,ast.Assign) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,bool):
            if any(isinstance(t,ast.Subscript) and isinstance(t.value,ast.Name)
                   and t.value.id=='receipt' and isinstance(t.slice,ast.Constant)
                   and t.slice.value=='terrain_written' for t in n.targets):
                lines.append(('metadata_true' if n.value.value else 'metadata_false',n.lineno))
    published=next(line for kind,line in lines if kind=='publish')
    true_line=next(line for kind,line in lines if kind=='metadata_true')
    false_line=next(line for kind,line in lines if kind=='metadata_false')
    assert published<true_line
    assert false_line>true_line

if __name__=='__main__':
    test_float32_objective_path()
    test_solution_lifetime_covers_float32_cost()
    test_readset_schema_and_hashes()
    test_no_improvement_is_not_pending_acceptance()
    test_pending_candidate_is_owned_before_write_or_guard()
    test_terrain_written_tracks_publish_and_cleanup()
    print({'status':'PASS','fixtures':6})
