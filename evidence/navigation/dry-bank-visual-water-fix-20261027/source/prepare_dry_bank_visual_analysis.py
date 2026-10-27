from pathlib import Path
R=Path(__file__).parent
text=(R/'inspect_dry_bank_domain.py').read_text(encoding='utf-8-sig')
for old,new in [('dry-bank-domain-setup-fixed-20261027','dry-bank-visual-water-setup-20261027'),
                ('dry-bank-domain-analysis-20261027','dry-bank-visual-water-analysis-20261027'),
                ('dry-bank-domain-pilot-20261027','dry-bank-visual-water-pilot-20261027'),
                ('dry-bank-domain-run-20261027','dry-bank-visual-water-run-20261027')]:text=text.replace(old,new)
text=text.replace('The solver/result uses level as its floor reference. This independent report supplies actual visual margins;',
                  'The solver/result uses saved water Y. This separate report checks every previously dry point;')
dest=R/'inspect_dry_bank_visual_floor.py';assert not dest.exists();dest.write_text(text,encoding='utf-8')
print('New analysis prepared, not executed')
