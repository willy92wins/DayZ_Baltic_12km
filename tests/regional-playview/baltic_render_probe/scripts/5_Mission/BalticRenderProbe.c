// Temporary local diag-only visual fixture; no RPC, input emulation or persistence.
// Camera API: scripts/3_game/entities/camera.c:43,72,80,90,103.
// Position: scripts/3_game/entities/object.c:300,317. Telemetry: global/game.c:730.
#ifdef DIAG_DEVELOPER
modded class MissionGameplay
{
    protected float m_BalticRequestedViewDistance = 1600;
    protected float m_BalticRenderTime;
    protected int m_BalticRenderPhase = -1;
    protected float m_BalticRenderNextRecord = -1;
    protected bool m_BalticCameraSaved;
    protected bool m_BalticCameraWasActive;
    protected bool m_BalticCameraWasFrozen;
    protected vector m_BalticCameraOldPosition;
    protected vector m_BalticCameraOldOrientation;
    protected float m_BalticCameraOldFOV;
    protected float m_BalticCameraOldNear;

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
            BalticRenderPose(0, "8775 600 9425", "8775 0 10125");
        if (m_BalticRenderPhase == 0 && m_BalticRenderTime >= 65)
            BalticRenderPose(1, "8775 1300 8725", "8775 0 10125");
        if (m_BalticRenderPhase == 1 && m_BalticRenderTime >= 115)
            BalticRenderPose(2, "10758 3 10062", "10950 1 10800");
        if (m_BalticRenderPhase == 2 && m_BalticRenderTime >= 175)
            BalticRenderPose(3, "8778 3 10122", "8730 1 10250");
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
            m_BalticCameraOldNear = camera.GetNearPlane();
            m_BalticCameraSaved = true;
        }
        m_BalticRequestedViewDistance = 1600;
        if (phase == 1) m_BalticRequestedViewDistance = 12000;
        GetGame().GetWorld().SetViewDistance(m_BalticRequestedViewDistance);
        camera.SetNearPlane(m_BalticCameraOldNear);
        if (phase == 1) camera.SetNearPlane(10);
        if (phase >= 2) position[1] = GetGame().SurfaceY(position[0], position[2]) + 1.7;
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
        camera.SetNearPlane(m_BalticCameraOldNear);
        camera.SetOrientation(m_BalticCameraOldOrientation);
        if (m_BalticCameraOldFOV > 0) camera.SetFOV(m_BalticCameraOldFOV);
        camera.SetFreezed(m_BalticCameraWasFrozen);
        camera.SetActive(m_BalticCameraWasActive);
        m_BalticRequestedViewDistance = 1600;
        GetGame().GetWorld().SetViewDistance(m_BalticRequestedViewDistance);
        m_BalticCameraSaved = false;
    }

    protected void BalticRenderRecord(string marker, bool fresh)
    {
        FileHandle report;
        Weather weather = GetGame().GetWeather();
        if (fresh) report = OpenFile("$profile:baltic_regional_playview_v1.log", FileMode.WRITE);
        else report = OpenFile("$profile:baltic_regional_playview_v1.log", FileMode.APPEND);
        Print("BALTIC_REGIONAL_PLAYVIEW_V1 " + marker);
        if (!report) return;
        FPrintln(report, "BALTIC_REGIONAL_PLAYVIEW_V1 " + marker + " elapsed=" + m_BalticRenderTime);
        if (GetGame().GetPlayer()) FPrintln(report, "player=" + GetGame().GetPlayer().GetPosition());
        FreeDebugCamera camera = FreeDebugCamera.GetInstance();
        if (camera) FPrintln(report, "near_plane=" + camera.GetNearPlane());
        FPrintln(report, "original_near_plane=" + m_BalticCameraOldNear);
        FPrintln(report, "world=" + GetGame().GetWorldName());
        FPrintln(report, "camera=" + GetGame().GetCurrentCameraPosition());
        FPrintln(report, "direction=" + GetGame().GetCurrentCameraDirection());
        FPrintln(report, "weather=" + weather.GetOvercast().GetActual() + ";" + weather.GetRain().GetActual() + ";" + weather.GetFog().GetActual() + ";" + weather.GetSnowfall().GetActual());
        FPrintln(report, "requested_view_distance=" + m_BalticRequestedViewDistance);
        CloseFile(report);
    }

    override void OnMissionFinish()
    {
        BalticRenderRestore();
        super.OnMissionFinish();
    }
};
#endif
