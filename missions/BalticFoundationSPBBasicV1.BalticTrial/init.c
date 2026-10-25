// Clean terrain preview: no diagnostic observers, scripted movement or population.
void main()
{
    GetGame().GetWorld().SetDate(2026, 9, 29, 12, 0);
}

class BalticFoundationSPBBasicMission: MissionServer
{
    override PlayerBase CreateCharacter(PlayerIdentity identity, vector pos, ParamsReadContext ctx, string characterName)
    {
        // SPB direct-load control, no camera or native screenshot addon.
        pos = "8778 0 10122";
        pos[1] = GetGame().SurfaceRoadY(pos[0], pos[2]) + 0.2;
        return super.CreateCharacter(identity, pos, ctx, characterName);
    }
}

Mission CreateCustomMission(string path)
{
    return new BalticFoundationSPBBasicMission();
}
