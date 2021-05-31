"""
Author Emile Schons 28.04.2021
#Source: https://github.com/labjack/labjack-ljm-python/blob/master/Examples/Basic/eNames.py
This scripts reads Battery current every second and Battery voltage every 60 seconds
Can be test on remote raspberrypi with:  
# ssh -p 40520 pi@lsserver.uber.space python3  < NamefoSCript

"""
from labjack import ljm
import requests
import time

influx_org = 'LibreSolar'
influx_bucket = 'LabjackCurrentVoltage'
influx_token = '6O3aUzQNynIPhh1jwlNukYU1gx5Z2fJZNehpANlNl1rTtLsSW2Acm2rFE3mO81l2Fq_Nl8lyhqajg5ivOAzrvA=='
influx_url = f'https://influxdb.lsserver.uber.space/api/v2/write?org={influx_org}&bucket={influx_bucket}&precision=s'
data = ""
headers = {'Authorization': 'Token %s' % influx_token}


labjack_current = 'AIN1'
labjack_voltage = 'AIN2'
interval_voltage_measurement = 60

# Open first found LabJack
#handle = ljm.openS("ANY", "ANY", "ANY")  # Any device, Any connection, Any identifier
handle = ljm.openS("T7", "USB", "ANY")  # T7 device, Any connection, Any identifier
#handle = ljm.openS("T4", "ANY", "ANY")  # T4 device, Any connection, Any identifier
#handle = ljm.open(ljm.constants.dtANY, ljm.constants.ctANY, "ANY")  # Any device, Any connection, Any identifier

#info = ljm.getHandleInfo(handle)
#print("Opened a LabJack with Device type: %i, Connection type: %i,\n"
#      "Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i" %
#      (info[0], info[1], info[2], ljm.numberToIP(info[3]), info[4], info[5]))
    

try:
    while True:
        
        
        for i in range (interval_voltage_measurement):
     
            # Improvements: TODO put timestamp by labjack 
            # Read Anlag Input ADC Adresses [AIN1] -> https://labjack.com/support/datasheets/t-series/ain
            # read Serialnumber # Serialnumber = ljm.eReadName(handle, 'SERIAL_NUMBER')
         
            Bat_current = ljm.eReadName(handle, labjack_current)
            data = f'V,device=470023670 Bat_current={Bat_current}\n'
            print(data)
            r = requests.post(influx_url, headers=headers, data=data)
            print(r)    
         
            time.sleep(1 - time.monotonic() % 1) 
            #https://stackoverflow.com/questions/10813195/run-a-python-function-every-second
      
            
        
        ljm.eWriteName(handle, 'FIO0', 0) # Turn on relais for battery voltage measurement
        time.sleep(0.5 - time.monotonic() % 1) 
        Bat_voltage = ljm.eReadName(handle, labjack_voltage)
        data = f'V,device=470023670 Bat_voltage={Bat_voltage}\n'
        print(data)
        r = requests.post(influx_url, headers=headers, data=data)
        print(r) 
        ljm.eWriteName(handle, 'FIO0', 1) # Turn off relais for battery voltage measurement
       
           
except KeyboardInterrupt:
    print('While loop ended!') 
    # Close handle 
    ljm.close(handle)
    


    




