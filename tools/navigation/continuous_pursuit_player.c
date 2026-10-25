#ifdef DIAG_DEVELOPER
modded class PlayerBase
{
    protected int m_BalticPursuitCommand = -1;
    void PlayerBase()
    {
        RegisterNetSyncVariableInt("m_BalticPursuitCommand", -1, 3);
    }
    int BalticPursuitCommand() { return m_BalticPursuitCommand; }
    void BalticSetPursuitCommand(int command)
    {
        if (!GetGame().IsServer() || GetGame().GetWorldName() != "BalticTrial") return;
        m_BalticPursuitCommand = command;
        SetSynchDirty();
    }
};
#endif
