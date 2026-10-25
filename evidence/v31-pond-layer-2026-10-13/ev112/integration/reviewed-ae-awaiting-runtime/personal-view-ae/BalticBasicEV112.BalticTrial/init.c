// Clean local terrain preview. No observers, forced movement, AI or economy.
void main()
{
    Hive ce = CreateHive();
    if (ce) ce.InitOffline();
    GetGame().GetWorld().SetDate(2026, 9, 29, 12, 0);
}

class BalticBasicMission: MissionServer
{
    override PlayerBase CreateCharacter(PlayerIdentity identity, vector pos, ParamsReadContext ctx, string characterName)
    {
        pos = "2392 0 6948";
        pos[1] = GetGame().SurfaceY(pos[0], pos[2]) + 0.2;
        return super.CreateCharacter(identity, pos, ctx, characterName);
    }
}

Mission CreateCustomMission(string path)
{
    return new BalticBasicMission();
}
