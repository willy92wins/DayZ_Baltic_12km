// Human input only. No position/velocity writes, no infected control.
#ifdef DIAG_DEVELOPER
modded class MissionGameplay
{
    protected float m_BalticPursuitTime;
    protected float m_BalticPursuitNext;
    protected PlayerBase m_BalticPursuitPlayer;
    protected bool m_BalticPursuitStopped;
    protected FileHandle m_BalticPursuitLog;

    override void OnMissionStart()
    {
        super.OnMissionStart();
        if (GetGame().GetWorldName() != "BalticTrial") return;
        m_BalticPursuitLog = OpenFile("$profile:baltic_continuous_pursuit_client_v1.log", FileMode.WRITE);
        if (m_BalticPursuitLog) FPrintln(m_BalticPursuitLog, "BALTIC_CONTINUOUS_PURSUIT_CLIENT_V1");
    }
    vector BalticPursuitGoal(int command)
    {
        // FROZEN_GOALS
        return "0 0 0";
    }
    void BalticPursuitRelease(string reason)
    {
        if (m_BalticPursuitPlayer)
        {
            HumanInputController control = m_BalticPursuitPlayer.GetInputController();
            if (control)
            {
                control.OverrideMovementSpeed(HumanInputControllerOverrideType.DISABLED, 0);
                control.OverrideMovementAngle(HumanInputControllerOverrideType.DISABLED, 0);
            }
        }
        if (m_BalticPursuitLog)
        {
            FPrintln(m_BalticPursuitLog, "END;" + reason + ";" + m_BalticPursuitTime);
            CloseFile(m_BalticPursuitLog); m_BalticPursuitLog = null;
        }
        m_BalticPursuitStopped = true;
    }
    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (GetGame().GetWorldName() != "BalticTrial" || m_BalticPursuitStopped) return;
        m_BalticPursuitTime = m_BalticPursuitTime + timeslice;
        if (m_BalticPursuitTime > 1250) { BalticPursuitRelease("DEADMAN"); return; }
        m_BalticPursuitPlayer = PlayerBase.Cast(GetGame().GetPlayer());
        if (!m_BalticPursuitPlayer) return;
        HumanInputController control = m_BalticPursuitPlayer.GetInputController();
        if (!control) return;
        int command = m_BalticPursuitPlayer.BalticPursuitCommand();
        if (command < 0) return;
        vector pos = m_BalticPursuitPlayer.GetPosition();
        vector goal = BalticPursuitGoal(command);
        float speed = 0; float angle = 0;
        if (command > 0)
        {
            float dx = goal[0] - pos[0]; float dz = goal[2] - pos[2];
            if (dx * dx + dz * dz > 2.25)
            {
                speed = 1;
                angle = (Math.Atan2(dx, dz) - control.GetHeadingAngle()) * Math.RAD2DEG;
                while (angle > 180) angle = angle - 360;
                while (angle < -180) angle = angle + 360;
            }
        }
        control.OverrideMovementSpeed(HumanInputControllerOverrideType.ENABLED, speed);
        control.OverrideMovementAngle(HumanInputControllerOverrideType.ENABLED, angle);
        if (m_BalticPursuitTime >= m_BalticPursuitNext)
        {
            m_BalticPursuitNext = m_BalticPursuitTime + 0.2;
            float actualSpeed; vector localDirection;
            control.GetMovement(actualSpeed, localDirection);
            if (m_BalticPursuitLog) FPrintln(m_BalticPursuitLog, "C;" + m_BalticPursuitTime + ";" + command + ";" + pos.ToString() + ";" + goal.ToString() + ";" + speed + ";" + angle + ";" + actualSpeed + ";" + localDirection.ToString());
        }
    }
    override void OnMissionFinish()
    {
        BalticPursuitRelease("MISSION_FINISH");
        super.OnMissionFinish();
    }
};
#endif
