```
Paths

Hardware compatible:

- Bornay Wind+ MPPT.

Firmware:

- 1.01 or higher.

Adapters:

- Bornay RS485 to USB adapter.

DC:

/DC/0/Current              Current in Amps. Value/10
/DC/0/Power                Power in watts 
/DC/0/Voltage              Voltage in volts. Value/10

Flags:

/Flags/ChargedBattery         0=No; 1=Yes If the battery is charged sets this flag
/Flags/FanState               0=Off; 1=On Status of the fan
/Flags/ElevatedVoltage        0=No; 1=Yes 
/Flags/ElevatedWind           0=No; 1=Yes 
/Flags/EmergencyButton        0=Off; 1=On Status of emergency button
/Flags/Extrem                 0=No; 1=Yes flag to elevated speed
/Flags/ExternSupply           0=No; 1=Yes Fail of extern supply

History:

/History/Overall/MaxRPM         Maximum revolutions reached in revolutions per minute

Mppt:

/Mppt/AbsortionTime          Time in absorbtion in seconds
/Mppt/BoxTemp                Temperature of the box in degrees /10
/Mppt/ChargerState           0=standby; 1=charging; 2=charged.
/Mppt/DutyCycle              Duty cycle 0 to 100%
/Mppt/Phase                  Phase of Full-Bridge 0 to 100%
/Mppt/RefMEF                 Bat Power Reference in watts
/Mppt/SinkTemp               Temperature of sink in degrees /10
/Mppt/StatusMEF              State of the states machine

Turbine:

/Turbine/AvailablePower         Calculated available power in watts
/Turbine/BatPowerLastHour       Calculated Batery Power charged last hour in watts.
/Turbine/BatPowerLastMin        Calculated Batery Power charged last minute in watts.
/Turbine/BreakerPowerLastMin    Calculated Braker Power derivated to resistors last minute in watts.
/Turbine/EstimatedWind           Wind speed estimated value/10
/Turbine/IBrk                   Current of the braker in Amps
/Turbine/RPM                    Revolutions of the turbine in revolutions per minute
/Turbine/Stop                   Wind Turbine Brake 0=Run; 1=Stop Writable value. 
/Turbine/VDC                    Voltage of DC system in volts Value/10
/Turbine/WindSpeed              Wind speed (m/s) Value /100 
/Turbine/WindSpeedLastHour      Calculated Wind speed last hour in m/s
/Turbine/WindSpeedLastMin       Calculated Wind speed last minute in m/s

Note: 
Paths to show in Color Control GX
/DC/0/Current
/DC/0/Power
/DC/0/Voltage              
/Turbine/RPM
/Turbine/WindSpeed  (if there are anemomemeter)

Paths to adjust.
/Turbine/Stop                     Wind Turbine Brake 0=Run; 1=Stop Writable value.```
