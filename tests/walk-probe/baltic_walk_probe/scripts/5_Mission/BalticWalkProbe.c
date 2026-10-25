// Temporary local movement fixture. APIs and unresolved angle unit: plans/narva-walk-smoke.md.
#ifdef DIAG_DEVELOPER
modded class MissionGameplay
{
    protected float m_BalticWalkTime;
    protected float m_BalticWalkSample;
    protected float m_BalticWalkTurnAt;
    protected int m_BalticWalkPhase;
    protected PlayerBase m_BalticWalkPlayer;

    override void OnMissionStart()
    {
        super.OnMissionStart();
        FileHandle report = OpenFile("$profile:baltic_walk_client_v1.csv", FileMode.WRITE);
        if (report)
        {
            FPrintln(report, "event;t;phase;x;y;z;d;cross;health_client_untrusted;angle;heading;speed;localdir");
            CloseFile(report);
        }
    }

    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (GetGame().GetWorldName() != "BalticTrial" || m_BalticWalkPhase == 4) return;
        m_BalticWalkTime = m_BalticWalkTime + timeslice;
        if (m_BalticWalkTime > 150)
        {
            BalticWalkStop("TIMEOUT");
            return;
        }
        m_BalticWalkPlayer = PlayerBase.Cast(GetGame().GetPlayer());
        if (!m_BalticWalkPlayer) return;
        HumanInputController control = m_BalticWalkPlayer.GetInputController();
        if (!control) return;
        vector position = m_BalticWalkPlayer.GetPosition();
        float dx = position[0] - 2417.143;
        float dz = position[2] - 6889.885;
        float progress = dx * 0.988364361 - dz * 0.152104866;
        float lateral = dx * 0.152104866 + dz * 0.988364361;
        // Client health read zero while the server reported100; health is a server gate.
        if (Math.AbsFloat(lateral) > 3)
        {
            BalticWalkStop("ABORT_CORRIDOR");
            return;
        }
        if (m_BalticWalkPhase == 0 && m_BalticWalkTime >= 10) m_BalticWalkPhase = 1;
        if (m_BalticWalkPhase == 1 && progress >= 28)
        {
            m_BalticWalkPhase = 2;
            m_BalticWalkTurnAt = m_BalticWalkTime + 3;
        }
        if (m_BalticWalkPhase == 2 && m_BalticWalkTime >= m_BalticWalkTurnAt) m_BalticWalkPhase = 3;
        if (m_BalticWalkPhase == 3 && progress <= -28)
        {
            BalticWalkStop("COMPLETE_BOTH_DIRECTIONS");
            return;
        }
        float speed = 0;
        float angle = 0;
        float targetDistance = 30;
        if (m_BalticWalkPhase == 3) targetDistance = -30;
        if (m_BalticWalkPhase == 1 || m_BalticWalkPhase == 3)
        {
            speed = 1;
            float tx = 2417.143 + 0.988364361 * targetDistance - position[0];
            float tz = 6889.885 - 0.152104866 * targetDistance - position[2];
            angle = (Math.Atan2(tx, tz) - control.GetHeadingAngle()) * Math.RAD2DEG;
            while (angle > 180) angle = angle - 360;
            while (angle < -180) angle = angle + 360;
        }
        control.OverrideMovementSpeed(HumanInputControllerOverrideType.ENABLED, speed);
        control.OverrideMovementAngle(HumanInputControllerOverrideType.ENABLED, angle);
        m_BalticWalkSample = m_BalticWalkSample + timeslice;
        if (m_BalticWalkSample >= 0.25)
        {
            m_BalticWalkSample = 0;
            BalticWalkRecord("SAMPLE", angle);
        }
    }

    protected void BalticWalkRecord(string marker, float angle)
    {
        FileHandle report = OpenFile("$profile:baltic_walk_client_v1.csv", FileMode.APPEND);
        if (!report) return;
        if (m_BalticWalkPlayer)
        {
            vector p = m_BalticWalkPlayer.GetPosition();
            float d = (p[0] - 2417.143) * 0.988364361 - (p[2] - 6889.885) * 0.152104866;
            float cross = (p[0] - 2417.143) * 0.152104866 + (p[2] - 6889.885) * 0.988364361;
            HumanInputController input = m_BalticWalkPlayer.GetInputController();
            float speed;
            vector movement;
            input.GetMovement(speed, movement);
            FPrintln(report, marker + ";" + m_BalticWalkTime + ";" + m_BalticWalkPhase + ";" + p[0] + ";" + p[1] + ";" + p[2] + ";" + d + ";" + cross + ";" + m_BalticWalkPlayer.GetHealth("", "Health") + ";" + angle + ";" + input.GetHeadingAngle() + ";" + speed + ";" + movement);
        }
        else FPrintln(report, marker + ";" + m_BalticWalkTime);
        CloseFile(report);
    }

    protected void BalticWalkStop(string marker)
    {
        if (m_BalticWalkPlayer)
        {
            HumanInputController input = m_BalticWalkPlayer.GetInputController();
            if (input)
            {
                input.OverrideMovementSpeed(HumanInputControllerOverrideType.DISABLED, 0);
                input.OverrideMovementAngle(HumanInputControllerOverrideType.DISABLED, 0);
            }
        }
        BalticWalkRecord(marker, 0);
        m_BalticWalkPhase = 4;
    }

    override void OnMissionFinish()
    {
        BalticWalkStop("MISSION_FINISH");
        super.OnMissionFinish();
    }
};
#endif
