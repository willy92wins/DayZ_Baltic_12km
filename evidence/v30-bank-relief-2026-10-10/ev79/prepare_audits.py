from pathlib import Path
B=Path(__file__).parent;R=B.parent;OLD=R/'v30-bank-relief-smoothing-20261010'
code=(OLD/'audit_exposure.py').read_text()
code=code.replace("shifts={} # EV70 changes no water object or water plane.","shifts={} # No water object or water plane changes.\nchanged_cells=changed[:-1,:-1]|changed[:-1,1:]|changed[1:,:-1]|changed[1:,1:]\ncontrol=np.zeros((5,5),bool);control[2,2]=True\nassert (control[:-1,:-1]|control[:-1,1:]|control[1:,:-1]|control[1:,1:]).sum()==4")
needle="            for r in range(r0,r1):\n                for c in range(c0,c1):"
repl="            if not changed_cells[r0:r1,c0:c1].any():continue\n            for r in range(r0,r1):\n                for c in range(c0,c1):\n                    if not changed_cells[r,c]:continue"
assert code.count(needle)==1
code=code.replace(needle,repl)
code=code.replace("objects=len(objects),translated_objects", "objects=len(objects),changed_native_cells=int(changed_cells.sum()),unchanged_cell_proof='Objects and levels identical; all four native height vertices exactly equal outside selected cells',translated_objects")
assert not (B/'audit_exposure.py').exists()
(B/'audit_exposure.py').write_text(code)
(B/'audit_surface_inputs.py').write_text((OLD/'audit_surface_inputs.py').read_text())
print('EV79_COMPILED_AND_SURFACE_CONSUMERS_PREPARED')
