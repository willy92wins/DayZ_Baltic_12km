// Server owns all measurements; no RPC, player movement, or terrain edits.
void main()
{
    GetGame().GetWorld().SetDate(2026, 10, 2, 12, 0);
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
    weather.SetWindMaximumSpeed(20);
    weather.SetWindFunctionParams(0, 0, 1);
    weather.GetWindMagnitude().SetLimits(0.1, 0.1);
    weather.GetWindMagnitude().Set(0.1, 0, 3600);
}


class BalticShoreDiagnosticMission: MissionServer {}
Mission CreateCustomMission(string path) { return new BalticShoreDiagnosticMission(); }
