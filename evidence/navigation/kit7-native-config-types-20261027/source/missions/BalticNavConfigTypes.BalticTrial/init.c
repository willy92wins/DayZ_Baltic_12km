// Server-only diagnostic: configuration reads -> profile log; no client/RPC/state edit.
// APIs verified in 3_game/global/game.c:449,524,539,546,612.
void main() { GetGame().GetWorld().SetDate(2026, 10, 2, 12, 0); }
class BalticNavConfigTypesMission: MissionServer
{
    protected float m_Elapsed;
    protected bool m_Done;
    protected ref array<string> m_Paths = new array<string>;

    override void OnInit()
    {
        super.OnInit();
        if (!GetGame().IsDedicatedServer()) return;
        m_Paths.Insert("CfgWorlds BalticTrial Navmesh filterIsolatedIslandsOnLoad");
        m_Paths.Insert("CfgWorlds BalticTrial Navmesh GenParams filterIsolatedIslands");
        m_Paths.Insert("CfgWorlds ChernarusPlus Navmesh filterIsolatedIslandsOnLoad");
        m_Paths.Insert("CfgWorlds ChernarusPlus Navmesh GenParams filterIsolatedIslands");
        m_Paths.Insert("CfgWorlds BalticTrial Navmesh GenParams tileWidth");
        m_Paths.Insert("CfgWorlds ChernarusPlus Navmesh GenParams tileWidth");
        m_Paths.Insert("CfgWorlds BalticTrial startTime");
        m_Paths.Insert("CfgWorlds ChernarusPlus description");
        m_Paths.Insert("CfgWorlds BalticTrial Navmesh __missing_@PROBE_ID@");
    }

    override void OnUpdate(float timeslice)
    {
        super.OnUpdate(timeslice);
        if (!GetGame().IsDedicatedServer() || m_Done) return;
        m_Elapsed = m_Elapsed + timeslice;
        if (m_Elapsed < 5) return;
        m_Done = true;
        FileHandle output = OpenFile("$profile:baltic_nav_config_@PROBE_ID@.log", FileMode.WRITE);
        if (!output) { Print("BALTIC_NAV_CONFIG_OUTPUT_FAILED"); return; }
        string world = GetGame().GetWorldName();
        FPrintln(output, "BALTIC_NAV_CONFIG_TYPES_V1;" + world + ";@PROBE_ID@;9");
        if (world != "BalticTrial" || m_Paths.Count() != 9)
        {
            FPrintln(output, "FAIL;WORLD_OR_INPUT_COUNT");
            FPrintln(output, "END;0");
            CloseFile(output);
            return;
        }
        Print("BALTIC_NAV_CONFIG_BEGIN_@PROBE_ID@");
        for (int index = 0; index < m_Paths.Count(); index++)
        {
            string path = m_Paths[index];
            bool exists = GetGame().ConfigIsExisting(path);
            int valueType = -1;
            string textValue = "";
            bool textOk = false;
            int integerValue = 0;
            float floatValue = 0;
            if (exists)
            {
                valueType = GetGame().ConfigGetType(path);
                textOk = GetGame().ConfigGetText(path, textValue);
                integerValue = GetGame().ConfigGetInt(path);
                floatValue = GetGame().ConfigGetFloat(path);
            }
            FPrintln(output, "C;" + index + ";" + path + ";" + exists + ";" + valueType + ";" + textOk + ";" + textValue + ";" + integerValue + ";" + floatValue);
        }
        Print("BALTIC_NAV_CONFIG_END_@PROBE_ID@");
        FPrintln(output, "END;9");
        CloseFile(output);
    }
}
Mission CreateCustomMission(string path) { return new BalticNavConfigTypesMission(); }
