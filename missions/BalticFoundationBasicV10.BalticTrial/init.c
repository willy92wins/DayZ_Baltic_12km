// Clean terrain preview: no diagnostic observers, scripted movement or population.
void main()
{
    GetGame().GetWorld().SetDate(2026, 9, 29, 12, 0);
}

class BalticFoundationBasicMission: MissionServer
{
    override PlayerBase CreateCharacter(PlayerIdentity identity, vector pos, ParamsReadContext ctx, string characterName)
    {
        // Dry western terrain approach, outside the 225m V10 bridge.
        pos = "2025 0 6950";
        pos[1] = GetGame().SurfaceRoadY(pos[0], pos[2]) + 0.2;
        return super.CreateCharacter(identity, pos, ctx, characterName);
    }
}

Mission CreateCustomMission(string path)
{
    return new BalticFoundationBasicMission();
}
