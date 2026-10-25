from pathlib import Path
import json
B=Path(__file__).parent;R=B.parent
old=R/'v30-bank-relief-smoothing-20261010'
code=(old/'author.py').read_text()
original="fixed=prior['other_fixed']|prior['large_lake_banks']|support|engineering_halo"
replacement='''m=dict(np.load(R/'v30-valley-smoothing-20261008/candidate-a/masks.npz'))
term=dict(np.load(R/'v30-native-terminal-finish-20261009/constraints.npz'))
rr,cc=np.indices(h.shape);x=cc*6;z=12282-rr*6
narva=(np.hypot(x-2417.1428225906,z-6889.8850822322)<=620)|t['narva']
border=(rr<11)|(rr>=2037)|(cc<11)|(cc>=2037)
other_fixed=(t['water']|t['beach']|(t['cls']!=0)|m['corridor']|m['summits']|border|term['controls'])
fixed=other_fixed|prior['large_lake_banks']|support|engineering_halo'''
assert code.count(original)==1
code=code.replace(original,replacement)
code=code.replace("bank_domain=(t['cls']==0)&(distance<=96)","bank_domain=(t['cls']==0)&(distance<=96)&narva")
code=code.replace('bank_domain=bank_domain)','bank_domain=bank_domain,narva=narva,other_fixed=other_fixed)')
code=code.replace('One bounded dry river-bank smoothing candidate','Narva-only dry-bank smoothing after explicit semantic mask reconstruction')
assert not (B/'author.py').exists()
(B/'author.py').write_text(code)
(old/'disposition.json').write_text(json.dumps(dict(status='REJECTED_NOT_PACKAGED',reason='Independent consumer: bank p99, four new edges above30, and local sector maxima regressions.',source_unchanged=True,compiled_exposure='Interrupted after physical pass because geometric acceptance already failed; visible audit incomplete.'),indent=2)+'\n')
print('EV79_AUTHOR_PREPARED_NO_CANDIDATE_YET')
