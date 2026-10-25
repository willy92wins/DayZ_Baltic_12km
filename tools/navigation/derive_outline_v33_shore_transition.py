"""Solve the V32 shore transition while preserving V31 frozen runtime points."""
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[2]
source = ROOT / 'tools/navigation/solve_outline_v31_frozen_water.py'
destination = ROOT / 'tools/navigation/solve_outline_v33_frozen_water.py'
assert not destination.exists()
text = source.read_text()
replacements = {
    'regional_outline_smoothing_v28': 'regional_outline_smoothing_v32',
    'regional_outline_smoothing_v31': 'regional_outline_smoothing_v33',
    'baltic_outline_smoothing_v31.asc': 'baltic_outline_smoothing_v33.asc',
    'fd321b02bd6027cc1fcf13fb4ccac52a8c7549eb9c8b061d1a9800b75500c254':
        '1d1919e2eda2e7837ab9bba15fad21c99e686a9a87143c43e26a9f8f896d667f',
    '7ee7fa04049bed00d7ce807aa2731d17cbfef809eaf39b30045d7ed5611e8501':
        'b32684f80a27f8fc7484bcf8f7713f2dc5cd2b1ae5a4a4bc4010fca63873e603',
}
for old, new in replacements.items():
    assert text.count(old) == 1, old
    text = text.replace(old, new)
destination.write_text(text)
print(destination)
print('sha256', hashlib.sha256(destination.read_bytes()).hexdigest())
