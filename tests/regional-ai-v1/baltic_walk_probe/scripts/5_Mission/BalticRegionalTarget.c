// Temporary local diagnostic; stationary HUMAN target only, no AI overrides.
#ifdef DIAG_DEVELOPER
modded class MissionGameplay
{
    protected float m_BalticTargetTime;
    protected PlayerBase m_BalticTarget;
    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (GetGame().GetWorldName()!="BalticTrial") return;
        m_BalticTargetTime=m_BalticTargetTime+timeslice;
        m_BalticTarget=PlayerBase.Cast(GetGame().GetPlayer());
        if (!m_BalticTarget) return;
        HumanInputController control=m_BalticTarget.GetInputController();
        if (!control) return;
        if (m_BalticTargetTime<3600) control.OverrideMovementSpeed(HumanInputControllerOverrideType.ENABLED,0);
        else control.OverrideMovementSpeed(HumanInputControllerOverrideType.DISABLED,0);
    }
    override void OnMissionFinish()
    {
        if (m_BalticTarget)
        {
            HumanInputController control=m_BalticTarget.GetInputController();
            if (control) control.OverrideMovementSpeed(HumanInputControllerOverrideType.DISABLED,0);
        }
        super.OnMissionFinish();
    }
};
#endif
