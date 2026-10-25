// Temporary per-instance input fixture; ordinary cars are unaffected.
modded class CarScript
{
    protected bool m_BalticDriveEnabled;
    protected float m_BalticDriveThrottle;
    protected float m_BalticDriveSteering;
    protected float m_BalticDriveBrake;
    protected int m_BalticDriveGear = CarGear.FIRST;
    protected int m_BalticDriveCalls;
    protected int m_BalticDriveExpires;

    void BalticDriveInput(float throttle, float steering, float brake, int gear)
    {
        m_BalticDriveEnabled=true;
        m_BalticDriveThrottle=throttle;
        m_BalticDriveSteering=steering;
        m_BalticDriveBrake=brake;
        m_BalticDriveGear=gear;
        m_BalticDriveExpires=GetGame().GetTime()+1000;
    }

    int BalticDriveCalls() { return m_BalticDriveCalls; }

    void BalticDriveStop()
    {
        m_BalticDriveEnabled=false;
        SetThrottle(0); SetSteering(0); SetBrake(1); SetHandbrake(1);
        SetBrakesActivateWithoutDriver(true); EngineStop();
    }

    override void OnInput(float dt)
    {
        super.OnInput(dt);
        if (!m_BalticDriveEnabled || !GetGame().IsDedicatedServer()) return;
        if (GetGame().GetTime()>m_BalticDriveExpires)
        {
            BalticDriveStop(); return;
        }
        SetBrakesActivateWithoutDriver(false);
        SetThrottle(m_BalticDriveThrottle); SetSteering(m_BalticDriveSteering);
        SetClutch(0); SetBrake(m_BalticDriveBrake); SetHandbrake(0);
        ShiftTo(m_BalticDriveGear);
        m_BalticDriveCalls++;
    }
}
