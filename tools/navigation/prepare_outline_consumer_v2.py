"""Keep the human test target stationary; infected motion remains native."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'missions/BalticOutlineChaseV1.BalticTrial/init.c'
dest=ROOT/'missions/BalticOutlineChaseV2.BalticTrial/init.c'
if dest.exists(): raise ValueError('Fresh output required')
c=source.read_text().replace('ChaseV1','ChaseV2').replace('chase_v1','chase_v2').replace('CHASE_V1','CHASE_V2')
anchor='        m_Time = m_Time + timeslice;'
assert c.count(anchor)==1
c=c.replace(anchor,anchor+'''
        if (m_Prey)
        {
            Human preyHuman = Human.Cast(m_Prey);
            HumanInputController preyControl;
            if (preyHuman) preyControl = preyHuman.GetInputController();
            if (preyControl) preyControl.OverrideMovementSpeed(HumanInputControllerOverrideType.ENABLED, 0);
        }''')
anchor='        if (m_Prey) m_Prey.SetAllowDamage(true);'
assert c.count(anchor)==1
c=c.replace(anchor,'''        if (m_Prey)
        {
            Human preyHuman = Human.Cast(m_Prey);
            HumanInputController preyControl;
            if (preyHuman) preyControl = preyHuman.GetInputController();
            if (preyControl) preyControl.OverrideMovementSpeed(HumanInputControllerOverrideType.DISABLED, 0);
            m_Prey.SetAllowDamage(true);
        }''')
dest.parent.mkdir(parents=True)
dest.write_text(c,encoding='utf-8',newline='\n')
ref=json.loads((ROOT/'evidence/regional-outline-v3/chase-reference.json').read_text())
ref.update(parent_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),mission_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),
           human_target_control='Temporary zero movement-speed override on server and client. No infected movement overrides. Client releases at450s and mission finish.')
(ROOT/'evidence/regional-outline-v3/chase-reference-v2.json').write_text(json.dumps(ref,indent=2)+'\n')
base=ROOT/'tests/regional-playview/baltic_render_probe'
new=ROOT/'tests/outline-consumer-v2/baltic_render_probe'
new.mkdir(parents=True)
(new/'config.cpp').write_bytes((base/'config.cpp').read_bytes())
c=(base/'scripts/5_Mission/BalticRenderProbe.c').read_text()
c=c.replace('baltic_regional_playview_v1','baltic_outline_view_v3').replace('BALTIC_REGIONAL_PLAYVIEW_V1','BALTIC_OUTLINE_VIEW_V3')
c=c.replace('"8775 600 9425", "8775 0 10125"','"5050 155 7470", "5225 95 7660"')
c=c.replace('"8775 1300 8725", "8775 0 10125"','"4500 850 6650", "5800 20 7600"')
c=c.replace('"10758 3 10062", "10950 1 10800"','"8200 600 4600", "8200 0 5700"')
c=c.replace('"8778 3 10122", "8730 1 10250"','"8800 1100 8600", "9050 0 10125"')
c=c.replace('        if (phase == 1) m_BalticRequestedViewDistance = 12000;', '        if (phase >= 1) m_BalticRequestedViewDistance = 6000;')
c=c.replace('        if (phase == 1) camera.SetNearPlane(10);','        if (phase >= 1) camera.SetNearPlane(10);')
c=c.replace('        if (phase >= 2) position[1] = GetGame().SurfaceY(position[0], position[2]) + 1.7;','')
c=c.replace('    protected float m_BalticRequestedViewDistance', '    protected float m_OutlineControlTime;\n    protected PlayerBase m_OutlineTarget;\n    protected float m_BalticRequestedViewDistance',1)
anchor='        if (GetGame().GetWorldName() != "BalticTrial") return;'
assert c.count(anchor)==1
c=c.replace(anchor,anchor+'''
        m_OutlineControlTime = m_OutlineControlTime + timeslice;
        m_OutlineTarget = PlayerBase.Cast(GetGame().GetPlayer());
        if (m_OutlineTarget)
        {
            HumanInputController control = m_OutlineTarget.GetInputController();
            if (control)
            {
                if (m_OutlineControlTime < 450) control.OverrideMovementSpeed(HumanInputControllerOverrideType.ENABLED, 0);
                else control.OverrideMovementSpeed(HumanInputControllerOverrideType.DISABLED, 0);
            }
        }''')
c=c.replace('        BalticRenderRestore();\n        super.OnMissionFinish();', '''        BalticRenderRestore();
        if (m_OutlineTarget)
        {
            HumanInputController control = m_OutlineTarget.GetInputController();
            if (control) control.OverrideMovementSpeed(HumanInputControllerOverrideType.DISABLED, 0);
        }
        super.OnMissionFinish();''')
target=new/'scripts/5_Mission/BalticRenderProbe.c'
target.parent.mkdir(parents=True)
target.write_text(c,encoding='utf-8',newline='\n')
# Verifier is independent source, never rewritten by fixture generation.
print(json.dumps(dict(mission=str(dest),probe=str(new))))
