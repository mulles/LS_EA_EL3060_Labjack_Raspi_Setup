#Cbang can be used to excute with ./ instead of python3
"""
Listen on serial port for ThingSet data and write to influxdb
Author: Emile Schons 05.05.2021
Name: Nucleo64Serial2Raspi2influxdb.py
Can be test on remote host with
$ ssh -p 40520 pi@lsserver.uber.space python3  < Nucleo622Raspi2influxdb.py
Serial port can be access locally with: 
$ pio device monitor -b 115200 --echo --filter colorize
or  remote with 
$ ssh -t -p 40520 pi@lsserver.uber.space pio device monitor -b 115200 --echo --filter colorize
copy script to remote
$ ssh -p 40520  pi@lsserver.uber.space "cat ~/measurement_Nucleo64Serial2Raspi2influxdb.py" < Nucleo64Serial2Raspi2influxdb.py

"""

import json
import serial 
import time
import requests


#Influxdb config:

influx_org = 'LibreSolar'
influx_bucket = 'LabjackCurrentVoltage'
influx_token = '6O3aUzQNynIPhh1jwlNukYU1gx5Z2fJZNehpANlNl1rTtLsSW2Acm2rFE3mO81l2Fq_Nl8lyhqajg5ivOAzrvA=='
influx_url = f'https://influxdb.lsserver.uber.space/api/v2/write?org={influx_org}&bucket={influx_bucket}&precision=s'
data = ""
headers = {'Authorization': 'Token %s' % influx_token}

# Nucleo64 Serial port config: 

baud = "115200"
port = "/dev/ttyACM0"

# Hardcoded Serialnumber:

device="mppt-1210-hus"






# Open Serial Port
try:
    ser = serial.Serial(port, baud, timeout=10)
    ser.nonblocking()
    print("Listening on {} ..".format(port))
except serial.SerialException:
    print("Error opening port {} .. aborting".format(port))
    sys.exit(1)


# Write to and read Serial port

try:
    # make sure every 1s ?/output by mppt-1210-hus is enabled.
    ser.write(b'=pub/serial {"Enable":true}\n')
    while True:
        if ser.in_waiting > 0:
            try:
                
                raw_data = ser.readline()
                #print(raw_data)
                if raw_data[0:2] == b'# ':
                    json_data = json.loads(raw_data.strip()[2:])
                    try:
                        data = f'V,device={device} Bat_V={json_data["Bat_V"]},Solar_V={json_data["Solar_V"]}\n'
                        data += f'A,device={device} Bat_A={json_data["Bat_A"]},Solar_A={json_data["Solar_A"]},Load_A={json_data["Load_A"]}\n'                
                        data += f'Info,device={device} SOC_pct={json_data["SOC_pct"]},Dis_Ah={json_data["Dis_Ah"]},BatUsable_Ah={json_data["BatUsable_Ah"]},ChgState={json_data["ChgState"]},DCDCState={json_data["DCDCState"]}\n'
                        data += f'Info,device={device} SolarInDay_Wh={json_data["SolarInDay_Wh"]},BatChgDay_Wh={json_data["BatChgDay_Wh"]},LoadOutDay_Wh={json_data["LoadOutDay_Wh"]},BatDisDay_Wh={json_data["BatDisDay_Wh"]},LoadInfo={json_data["LoadInfo"]},ErrorFlags={json_data["ErrorFlags"]},Uptime_s={json_data["Uptime_s"]},DeepDisCount={json_data["DeepDisCount"]},UsbInfo={json_data["UsbInfo"]}\n'                 
                    except KeyError as e:
                        print(e)          
                    print(data)
                    r = requests.post(influx_url, headers=headers, data=data)
                    print(r)  
            except json.decoder.JSONDecodeError as e:
                print(e)
                pass
        time.sleep(0.1)
    
except KeyboardInterrupt:
    print('While loop ended!') 
    # Close Serial connection 
    ser.close()


