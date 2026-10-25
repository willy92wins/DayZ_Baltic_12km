// Bounded physical consumer. No infected motion overrides after spawning.
void main()
{
    GetGame().GetWorld().SetDate(2026, 9, 29, 12, 0);
    Weather weather = GetGame().GetWeather();
    weather.MissionWeather(true);
    weather.GetOvercast().SetLimits(0.1, 0.1);
    weather.GetOvercast().Set(0.1, 0, 3600);
    weather.GetRain().SetLimits(0, 0);
    weather.GetRain().Set(0, 0, 3600);
    weather.GetFog().SetLimits(0, 0);
    weather.GetFog().Set(0, 0, 3600);
    weather.GetSnowfall().SetLimits(0, 0);
    weather.GetSnowfall().Set(0, 0, 3600);
}

class BalticFoundationVisualMission: MissionServer
{
    override PlayerBase CreateCharacter(PlayerIdentity identity, vector pos, ParamsReadContext ctx, string characterName)
    {
        // Frozen dry anchor near this camera group; avoids player occlusion.
        pos = "2000 0 6955";
        pos[1] = GetGame().SurfaceRoadY(pos[0], pos[2]) + 0.2;
        return super.CreateCharacter(identity, pos, ctx, characterName);
    }
}

Mission CreateCustomMission(string path)
{
    return new BalticFoundationVisualMission();
}
