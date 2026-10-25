// Clean terrain preview: no diagnostic observers, scripted movement or population.
void main()
{
    GetGame().GetWorld().SetDate(2026, 9, 29, 12, 0);
}

class BalticNativeBasicMission: MissionServer
{
    override PlayerBase CreateCharacter(PlayerIdentity identity, vector pos, ParamsReadContext ctx, string characterName)
    {
        // Western dry landing, outside the 75m bridge; honor its prepared roadway.
        pos = "2357.841309 0 6899.011230";
        pos[1] = GetGame().SurfaceRoadY(pos[0], pos[2]) + 0.2;
        return super.CreateCharacter(identity, pos, ctx, characterName);
    }
}

Mission CreateCustomMission(string path)
{
    return new BalticNativeBasicMission();
}
