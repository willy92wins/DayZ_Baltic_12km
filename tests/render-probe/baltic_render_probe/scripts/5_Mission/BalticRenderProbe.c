// Temporary local diag-only visual fixture; no RPC, input emulation or persistence.
// Camera API: scripts/3_game/entities/camera.c:43,72,80,90,103.
// Position: scripts/3_game/entities/object.c:300,317. Telemetry: global/game.c:730.
#ifdef DIAG_DEVELOPER
modded class MissionGameplay
{
    protected float m_BalticRenderTime;
    protected int m_BalticRenderPhase = -1;
    protected float m_BalticRenderNextRecord = -1;
    protected bool m_BalticCameraSaved;
    protected bool m_BalticCameraWasActive;
    protected bool m_BalticCameraWasFrozen;
    protected vector m_BalticCameraOldPosition;
    protected vector m_BalticCameraOldOrientation;
    protected float m_BalticCameraOldFOV;

    override void OnMissionStart()
    {
        super.OnMissionStart();
        m_BalticRenderTime = 0;
        m_BalticRenderPhase = -1;
        BalticRenderRecord("START", true);
    }

    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (GetGame().GetWorldName() != "BalticTrial") return;
        if (m_BalticRenderPhase == 4) return;
        if (!GetGame().GetPlayer()) return;
        m_BalticRenderTime = m_BalticRenderTime + timeslice;
        if (m_BalticRenderPhase == -1 && m_BalticRenderTime >= 15)
            BalticRenderPose(0, "2380 12 6860", "2417 2 6889");
        if (m_BalticRenderPhase == 0 && m_BalticRenderTime >= 65)
            BalticRenderPose(1, "2698.90 220 6180.53", "2417 2 6889");
        if (m_BalticRenderPhase == 1 && m_BalticRenderTime >= 115)
            BalticRenderPose(2, "2698.90 643.67 6180.53", "2360.73 1.21 6665.39");
        if (m_BalticRenderPhase == 2 && m_BalticRenderTime >= 175)
            BalticRenderPose(3, "2023.47 525.28 7209.79", "2301.96 1.30 6969.29");
        if (m_BalticRenderPhase == 3 && m_BalticRenderTime >= 235)
        {
            BalticRenderRestore();
            m_BalticRenderPhase = 4;
            BalticRenderRecord("COMPLETE_RESTORED", false);
        }
        if (m_BalticRenderNextRecord > 0 && m_BalticRenderTime >= m_BalticRenderNextRecord)
        {
            BalticRenderRecord("SETTLED_" + m_BalticRenderPhase, false);
            m_BalticRenderNextRecord = -1;
        }
    }

    protected void BalticRenderPose(int phase, vector position, vector target)
    {
        FreeDebugCamera camera = FreeDebugCamera.GetInstance();
        if (!camera)
        {
            m_BalticRenderPhase = 4;
            BalticRenderRecord("FAILED_NO_CAMERA", false);
            return;
        }
        if (!m_BalticCameraSaved)
        {
            m_BalticCameraWasActive = camera.IsActive();
            m_BalticCameraWasFrozen = camera.IsFreezed();
            m_BalticCameraOldPosition = camera.GetPosition();
            m_BalticCameraOldOrientation = camera.GetOrientation();
            m_BalticCameraOldFOV = Camera.GetCurrentFOV();
            m_BalticCameraSaved = true;
        }
        camera.SetActive(true);
        camera.SetFreezed(true);
        camera.SetPosition(position);
        camera.LookAt(target);
        camera.SetFOV(1.04719755);
        m_BalticRenderPhase = phase;
        m_BalticRenderNextRecord = m_BalticRenderTime + 3;
        BalticRenderRecord("POSE_" + phase, false);
    }

    protected void BalticRenderRestore()
    {
        if (!m_BalticCameraSaved) return;
        FreeDebugCamera camera = FreeDebugCamera.GetInstance();
        if (!camera) return;
        camera.SetPosition(m_BalticCameraOldPosition);
        camera.SetOrientation(m_BalticCameraOldOrientation);
        if (m_BalticCameraOldFOV > 0) camera.SetFOV(m_BalticCameraOldFOV);
        camera.SetFreezed(m_BalticCameraWasFrozen);
        camera.SetActive(m_BalticCameraWasActive);
        m_BalticCameraSaved = false;
    }

    protected void BalticRenderRecord(string marker, bool fresh)
    {
        FileHandle report;
        Weather weather = GetGame().GetWeather();
        if (fresh) report = OpenFile("$profile:baltic_render_probe_v1.log", FileMode.WRITE);
        else report = OpenFile("$profile:baltic_render_probe_v1.log", FileMode.APPEND);
        Print("BALTIC_RENDER_V1 " + marker);
        if (!report) return;
        FPrintln(report, "BALTIC_RENDER_V1 " + marker + " elapsed=" + m_BalticRenderTime);
        FPrintln(report, "world=" + GetGame().GetWorldName());
        FPrintln(report, "camera=" + GetGame().GetCurrentCameraPosition());
        FPrintln(report, "direction=" + GetGame().GetCurrentCameraDirection());
        FPrintln(report, "weather=" + weather.GetOvercast().GetActual() + ";" + weather.GetRain().GetActual() + ";" + weather.GetFog().GetActual() + ";" + weather.GetSnowfall().GetActual());
        CloseFile(report);
    }

    override void OnMissionFinish()
    {
        BalticRenderRestore();
        super.OnMissionFinish();
    }
};
#endif
