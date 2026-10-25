// Temporary client-only fixture. One vanilla Continue request per mission.
modded class MissionGameplay
{
    private bool m_BalticVisualUIDone;
    private bool m_BalticVisualUIRequested;
    private float m_BalticVisualUIElapsed;
    private float m_BalticVisualUINext;
    private float m_BalticVisualUIRequestTime;

    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (m_BalticVisualUIDone || !GetGame() || GetGame().IsDedicatedServer())
            return;
        if (!GetGame().GetPlayer())
            return;

        m_BalticVisualUIElapsed += timeslice;
        if (m_BalticVisualUIElapsed < m_BalticVisualUINext)
            return;
        m_BalticVisualUINext = m_BalticVisualUIElapsed + 0.5;

        string world;
        GetGame().GetWorldName(world);
        if (world != "BalticTrial")
        {
            Print("[BALTIC_VISUAL_UI_V1] INACTIVE_WRONG_WORLD");
            m_BalticVisualUIDone = true;
            return;
        }

        UIScriptedMenu menu = GetGame().GetUIManager().GetMenu();
        if (m_BalticVisualUIRequested)
        {
            if (!menu)
            {
                Print("[BALTIC_VISUAL_UI_V1] VERIFIED_MENU_CLOSED");
                m_BalticVisualUIDone = true;
            }
            else if (m_BalticVisualUIElapsed - m_BalticVisualUIRequestTime > 10)
            {
                Print("[BALTIC_VISUAL_UI_V1] FAIL_MENU_REMAINS");
                m_BalticVisualUIDone = true;
            }
            return;
        }

        if (m_BalticVisualUIElapsed > 45)
        {
            Print("[BALTIC_VISUAL_UI_V1] END_NO_PAUSE_MENU");
            m_BalticVisualUIDone = true;
            return;
        }
        if (m_BalticVisualUIElapsed < 5 || !menu)
            return;
        if (menu.GetID() != MENU_INGAME)
            return;

        m_BalticVisualUIRequested = true;
        m_BalticVisualUIRequestTime = m_BalticVisualUIElapsed;
        Print("[BALTIC_VISUAL_UI_V1] REQUEST_CONTINUE_ONCE");
        GetGame().GetCallQueue(CALL_CATEGORY_GUI).Call(GetGame().GetMission().Continue);
    }
};
