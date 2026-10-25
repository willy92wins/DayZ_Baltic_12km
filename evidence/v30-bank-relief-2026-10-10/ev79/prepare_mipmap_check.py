from pathlib import Path
B=Path(__file__).parent;R=B.parent
code=(R/'v30-complete-dry-surface-20261009/check_changed_mips.py').read_text()
assert "ref['changed_entries']" in code
code=code.replace("ref['changed_entries']","ref['changed_texture_entries']")
(B/'check_changed_mips.py').write_text(code)
