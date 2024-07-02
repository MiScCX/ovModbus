# ovModbus
## Modbus Data Extractor

**Modbus Data Extractor** is a Python script that allows you to extract data from Modbus devices using either TCP or RTU communication methods. 
The following main tasks can be called up:
- General dump of the Modbus holding registers
- Read out Ovum heat pump Modbus map
- Create configuration for Home Assistant which then creates all Ovum heat pump parameters as sensors

1. [Installation](#installation)
2. [Usage](#usage)
3. [Examples](#examples)
4. [Modbus TCP](#modbustcp)
5. [Modbus RTU](#modbusrtu)
6. [Create a DUMP of a holding register](#dump)
7. [Create a Ovum Heatpump Modbus Map](#ovummap)
8. [Create a YAML/Configuration for Home Assistant and the sensors for Ovum heatpump](#hass)
9. [All Options](#options)

## Installation
<a name="installation"></a>

Before using this script, you need to install the required Python libraries. You can do this using pip:

```bash
pip install pymodbus
pip install python-slugify
```

## Usage
<a name="usage"></a>

```bash
python ovModbus.py [OPTIONS]
```
## Examples
<a name="examples"></a>
### Modbus TCP
<a name="modbustcp"></a>
```bash
python ovModbus.py TCP 247 --host 192.168.1.100 --port 502 [OPTIONS]
```

### Modbus RTU
<a name="modbusrtu"></a>
```bash
python ovModbus.py RTU 247 --comport /dev/ttyUSB0 --baudrate 19200 --parity E --stopbits 1 [OPTIONS]
```

### 1. Create Dump
<a name="dump"></a>
Connect to Host ```192.168.1.100``` Port ```502``` and Slave ```247```

Read holding Register (as a Dump) address ```12288``` until address ```18408``` and save output in a file ```modbus.dump```
```bash
python ovModbus.py TCP 247 --host 192.168.1.100 --port 502 --dump --start_address 12288 --stop_address 18408 --output modbus.dump
```
**Output:**
```
Idx	AddrHex	AddrDec	Hex	Byte_1	Byte_2	UInt16	Int16	Chr	Bin
0	0x3000	12288	00 00	0	0	0	0		0000 0000 0000 0000
1	0x3001	12289	30 0A	48	10	12298	12298		0011 0000 0000 1010
2	0x3002	12290	00 00	0	0	0	0		0000 0000 0000 0000
3	0x3003	12291	00 FE	0	254	254	254		0000 0000 1111 1110
4	0x3004	12292	00 00	0	0	0	0		0000 0000 0000 0000
5	0x3005	12293	80 00	128	0	32768	-32768		1000 0000 0000 0000
6	0x3006	12294	4D 45	77	69	19781	19781	ME	0100 1101 0100 0101
7	0x3007	12295	4E 55	78	85	20053	20053	NU	0100 1110 0101 0101
8	0x3008	12296	00 00	0	0	0	0		0000 0000 0000 0000
9	0x3009	12297	00 01	0	1	1	1		0000 0000 0000 0001
...
```

### 2. Read/Create Ovum Heatpumnp Modbus Map
<a name="ovummap"></a>
Connect to Host ```192.168.1.100``` Port ```502``` and Slave ```247```

Read holding Register from Ovum Heatpump address ```12288``` until address ```18408``` and save output in a file ```modbus.ovum```. Language is set to ```en```

```bash
python ovModbus.py TCP 247 --host 192.168.1.100 --port 502 --start_address 12288 --stop_address 18408 --output modbus.ovum --lang en
```
**Output:**
```
AddrHex         AddrDec         Param           Int32           Prec            Value           Unit            UnitID          MultiID         MinVal          MaxVal          ReadOnly        isMenu          DescID          Desc
0x3000          12288           MENU                                                                                                                                                            True            0               
0x300a          12298           REAL                                                                                                                                                            True            3370            Heat Pump
0x3014          12308           Rps             0               0               0               rps             59                              0               130             True            False           5985            Inverter RPS set
0x301e          12318           HS              1               0               ON                              127             420             0               1               True            False           4568            Main switch
0x3028          12328           ALAR            0               0               No                              127             130             0               1               True            False           583             Active Alarm
0x3032          12338           Anfo            0               0               Standby                         127             865             0               255             True            False           4571            Operating Mode
0x303c          12348           CoMi            0               0               0               min             3                               0               65535           True            False           4569            Running time
0x3046          12358           CoHo            604             0               604             h               4                               0               65535           True            False           4570            Working hours
0x3050          12368           HePw            0               3               0.0             kW              35                              0               65535           True            False           4633            Heating power
0x305a          12378           PvWa            0               2               0.0             kW              35                              -32768          32767           True            False           5992            PVWatch power
0x3064          12388           ATvz            26              1               2.6             °C              0                               -32768          32767           True            False           4599            Ambient.t.avg.
...
```

### 3. Create Configuration for Home Assistant and add sensors of the Ovum Heatpumnp Modbus Map
<a name="hass"></a>
Connect to Host ```192.168.1.100``` Port ```502``` and Slave ```247```

Read holding Register from Ovum Heatpump address ```12288``` until address ```18408``` and create HASS YAML and save it in a file ```ovum-modbus.yaml```. Language is set to ```en```

```bash
python ovModbus.py TCP 247 --host 192.168.1.100 --port 502 --hass --output ovum-modbus.yaml --lang en
```
**Output:**
```
modbus:
    - name: "modbus_ovum"
      type: tcp
      host: 192.168.1.100
      port: 502
      delay: 2
      message_wait_milliseconds: 0
      timeout: 5
      sensors:
        - name: "Heat pump: Inverter RPS set (Rps #12308)"         
          unique_id: ovum_Rps_sensor12308
          address: 12308
          scan_interval: 15                
          data_type: int32
          scale: 1
          precision: 0
          swap: word
          unit_of_measurement: "rps"
          input_type: holding
          min_value: 0
          max_value: 130
          slave: 247                    
          device_class: speed
        - name: "Heat pump: Main switch (HS #12318)"         
          unique_id: ovum_HS_sensor12318
          address: 12318
          scan_interval: 15                
          data_type: int32
          scale: 1
          precision: 0
          swap: word
          unit_of_measurement: " "
          input_type: holding
          min_value: 0
          max_value: 1
          slave: 247
      template:
        - sensor:
            - name: "Heat pump: Main switch (HS #12318) tmpl"
              unique_id: ovum_HS_sensor12318_tmpl            
              device_class: enum
              availability: "{{ states('sensor.heat_pump_main_switch_hs_12318')|int in [0,1] }}"
              state: >
                {% set mapper =  {
                    '0' : 'OFF',
                    '1' : 'ON' } %}            
                {% set state = states('sensor.heat_pump_main_switch_hs_12318') %}
                {{ mapper[state] if state in mapper}}
...
```

## Options
<a name="options"></a>

- **method** (str, TCP):
  - Description: How to connect (TCP or RTU).
- **slave** (int, default: 247):
  - Description: The Modbus-Address (Slave).
- **--host** (str, default: 127.0.0.1):
  - Description: The IP address of the Modbus TCP host.
- **--port** (int, default: 502):
  - Description: The TCP-Port of the Modbus TCP host.
- **--comport** (str, default: /dev/ttyUSB0):
  - Description: The COM Port Device.
- **--baudrate** (int, default: 19200):
  - Description: Baudrate for RTU Connection.
- **--parity** (str, default: E):
  - Description: Parity for RTU Connection.
- **--stopbits** (int, default: 1):
  - Description: Stopbits for RTU Connection.
- **--lang** (str, default: default):
  - Description: Language Selector (de, en, ...).
  - FOR GERMAN: Do not use this parameter.
- **--start_address** (int, default: 12288):
  - Description: Start address of the register.
- **--stop_address** (int, default: 18408):
  - Description: Stop address of the register.
- **--dump** (boolean):
  - Description: Loop through addresses and dump content.
- **--csv** (boolean):
  - Description: Output is in CSV-Format.
- **--hass** (boolean):
  - Description: Create Home Assistant YAML for sensors.
- **--min** (boolean):
  - Description: Create minimal output.
- **--noerror** (boolean):
  - Description: Skip addresses with errors and do not print.
- **--output** (str, default: None):
  - Description: Write output to a file.
- **--dev** (boolean):
  - Description: Debugging and test parameter.
