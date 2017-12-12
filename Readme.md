Paths

DC:

/0/Current              Current in Amps. Value/10
/0/Power                Power in watts 
/0/Voltage              Voltage in volts. Value/10

Flags:

/ChargedBattery         0=No; 1=Yes
/FanState               0=Off; 1=On
/ElevatedVoltaje        0=No; 1=Yes
/ElevatedWind           0=No; 1=Yes
/EmergencyButton        0=Off; 1=On
/Extrem                 0=No; 1=Yes
/ExternSupply           0=No; 1=Yes

History:

/Overall/MaxRPM         Maximum revolutions reached in revolutions per minute

Mppt:

/AbsortionTime          Time in absorbtion in seconds
/BoxTemp                Temperature of the box in degrees /10
/ChargerState           0=standby; 1=charging; 2=charged.
/Dutty                  Dutty cycle 0 to 100%
/Phase                  Phase of Full-Bridge 0 to 100%
/RefMEF                 Bat Power Reference in watts
/SinkTemp               Temperature of sink in degrees /10
/StatusMEF              State of the states machine

Turbine:

/AvailablePower         Calculated available power in watts
/BatPowerLastHour       Calculated Batery Power charged last hour in watts.
/BatPowerLastMin        Calculated Batery Power charged last minute in watts.
/BreakerPowerLastMin    Calculated Braker Power derivated to resistors last minute in watts.
/IBrk                   Current of the braker in Amps
/RPM                    Revolutions of the turbine in revolutions per minute
/StimatedWind           Wind speed estimated value/10
/Stop                   Wind Turbine Brake 0=Run; 1=Stop Writable value. 
/VDC                    Voltage of DC system in volts Value/10
/WindSpeed              Wind speed (m/s) Value /100 
/WindSpeedLastHour      Calculated Wind speed last hour in m/s
/WindSpeedLastMin       Calculated Wind speed last minute in m/s

Note: Paths to show in Color Control
/0/Current              Current in Amps. Value/10
/0/Power                Power in watts 
/0/Voltage              Voltage in volts. Value/10
/RPM 
/WindSpeed   (if t
