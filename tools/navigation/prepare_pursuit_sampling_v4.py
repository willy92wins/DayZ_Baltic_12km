"""Freeze a cadence-aware consumer before a new run of the unchanged V3 mission."""
from pathlib import Path
import datetime,hashlib,json
ROOT=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    source=ROOT/'tools/navigation/verify_continuous_pursuit_v3.py'
    target=ROOT/'tools/navigation/verify_continuous_pursuit_v4.py'
    controls=ROOT/'tools/navigation/test_continuous_pursuit_v4_controls.py'
    ev=ROOT/'evidence/foundation-followup-2026-10-01/continuous-pursuit-v4'
    assert not target.exists() and not controls.exists() and not ev.exists()
    code=source.read_text(encoding='utf-8')
    old='''            dt=np.diff(times);step=np.linalg.norm(np.diff(pos[:,[0,2]],axis=0),axis=1)
            speed=np.divide(step,dt,out=np.full_like(step,np.inf),where=dt>0)
            speed[(dt==0)&(step<=.002)]=0'''
    new='''            periodic=np.array([i for i,r in enumerate(active) if r['event']=='SAMPLE'],dtype=int)
            cadence=False;event_bounds=False;peak=math.inf
            if len(periodic)>=3:
                pt=times[periodic];dt=np.diff(pt)
                cadence=bool(np.all(dt>=limits['minimum_periodic_gap_s']) and max(dt)<=limits['maximum_gap_s'] and pt[0]-times[0]<=limits['maximum_gap_s'] and times[-1]-pt[-1]<=limits['maximum_gap_s'])
                step=np.linalg.norm(np.diff(pos[periodic][:,[0,2]],axis=0),axis=1)
                rate=np.divide(step,dt,out=np.full_like(step,np.inf),where=dt>0)
                peak=float(np.max(rate))
                right=np.clip(np.searchsorted(pt,times),0,len(pt)-1)
                left=np.maximum(right-1,0)
                nearest=np.where(abs(pt[left]-times)<abs(pt[right]-times),left,right)
                separation=np.linalg.norm((pos-pos[periodic[nearest]])[:,[0,2]],axis=1)
                envelope=maximum_speed*(abs(times-pt[nearest])+limits['periodic_nominal_s'])
                event_bounds=bool(np.all(separation<=envelope))
            speed=np.array([peak])'''
    assert code.count(old)==1;code=code.replace(old,new)
    old="return dict(bounded_speed=finite and peak<=maximum_speed,maximum_speed_mps=peak if finite else None,"
    new="return dict(bounded_speed=finite and peak<=maximum_speed and cadence and event_bounds,periodic_cadence=cadence,event_position_bounds=event_bounds,periodic_samples=int(len(periodic)),maximum_speed_mps=peak if finite else None,"
    assert code.count(old)==1;code=code.replace(old,new)
    target.write_text(code,encoding='utf-8')
    csource=ROOT/'tools/navigation/test_continuous_pursuit_v3_controls.py'
    ccode=csource.read_text(encoding='utf-8').replace('from verify_continuous_pursuit_v3 import verify','from verify_continuous_pursuit_v4 import verify')
    anchor='    results=[]'
    insert='''    noise=next(i for i in range(spawn+1,len(base)) if base[i].startswith('P;0;') and base[i].split(';')[3]=='NOISE')
    changes['periodic_position_jump']=(field(5,move(base[sample].split(';')[5],[2,0,0]),sample),client)
    changes['event_position_jump']=(field(5,move(base[noise].split(';')[5],[3,0,0]),noise),client)
    changes['no_periodic_samples']=('\\n'.join(s for s in base if not(s.startswith('P;0;') and s.split(';')[3]=='SAMPLE'))+'\\n',client)
'''
    assert ccode.count(anchor)==1;ccode=ccode.replace(anchor,insert+anchor)
    anchor="        if accepted(result):raise ValueError('False acceptance: '+name)"
    ccode=ccode.replace(anchor,anchor+"\n        if name in ('periodic_position_jump','event_position_jump','no_periodic_samples') and result['cases'][0].get('checks',{}).get('prey_no_teleport',True):raise ValueError('Required motion rejection absent: '+name)")
    controls.write_text(ccode,encoding='utf-8')
    parent=ROOT/'evidence/foundation-followup-2026-10-01/continuous-pursuit-v3/reference.json'
    ref=json.loads(parent.read_text(encoding='utf-8'))
    ref.update(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),previous_reference_sha256=sha(parent),preflight_revision='Unchanged V3 mission/addon. Rates on periodic SAMPLE records; all events remain physically checked. Independent new run required.',consumer_sha256=sha(target),controls_sha256=sha(controls))
    ref['criteria'].update(minimum_periodic_gap_s=.199,periodic_nominal_s=.2)
    ref['limits'].append('Cadence-aware motion gate resolves 200ms periodic samples with one-period event envelope. Does not prove absence of smaller replication adjustments; old strict failures remain.')
    ev.mkdir();(ev/'reference.json').write_text(json.dumps(ref,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='FROZEN_BEFORE_REPEAT',reference_sha256=sha(ev/'reference.json'),consumer_sha256=sha(target))))

if __name__=='__main__':main()
