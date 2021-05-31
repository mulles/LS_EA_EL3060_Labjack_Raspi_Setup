"""

#Source: https://github.com/labjack/labjack-ljm-python/blob/master/Examples/Basic/eNames.py
Demonstrates how to use the labjack.ljm.eNames (LJM_eNames) function.
Relevant Documentation:
 
LJM Library:
    LJM Library Installer:
        https://labjack.com/support/software/installers/ljm
    LJM Users Guide:
        https://labjack.com/support/software/api/ljm
    Opening and Closing:
        https://labjack.com/support/software/api/ljm/function-reference/opening-and-closing
    eNames:
        https://labjack.com/support/software/api/ljm/function-reference/ljmenames
 
T-Series and I/O:
    Modbus Map:
        https://labjack.com/support/software/api/modbus/modbus-map
    Hardware Overview(Device Information Registers):
        https://labjack.com/support/datasheets/t-series/hardware-overview
"""
from labjack import ljm
import requests

influx_org = 'LibreSolar'
influx_bucket = 'LabjackCurrentVoltage'
influx_token = '6O3aUzQNynIPhh1jwlNukYU1gx5Z2fJZNehpANlNl1rTtLsSW2Acm2rFE3mO81l2Fq_Nl8lyhqajg5ivOAzrvA=='
influx_url = f'https://influxdb.lsserver.uber.space/api/v2/write?org={influx_org}&bucket={influx_bucket}&precision=s'


# Open first found LabJack
#handle = ljm.openS("ANY", "ANY", "ANY")  # Any device, Any connection, Any identifier
handle = ljm.openS("T7", "USB", "ANY")  # T7 device, Any connection, Any identifier
#handle = ljm.openS("T4", "ANY", "ANY")  # T4 device, Any connection, Any identifier
#handle = ljm.open(ljm.constants.dtANY, ljm.constants.ctANY, "ANY")  # Any device, Any connection, Any identifier

#info = ljm.getHandleInfo(handle)
#print("Opened a LabJack with Device type: %i, Connection type: %i,\n"
#      "Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i" %
#      (info[0], info[1], info[2], ljm.numberToIP(info[3]), info[4], info[5]))

# Local constants to save screen space
WRITE = ljm.constants.WRITE
READ = ljm.constants.READ
FLOAT32 = ljm.constants.FLOAT32
UINT16 = ljm.constants.UINT16
UINT32 = ljm.constants.UINT32

# Setup and call eNames to write/read values to/from the LabJack.
# TODO write to Adress for making current measurements. 
# TODO put timestamp by labjack 
# Read Anlag Input ADC Adresses [AIN0-AIN13] -> https://labjack.com/support/datasheets/t-series/ain
# read firmware version.
numFrames = 4
aNames = ['FIO0','AIN1', 'AIN2', 'SERIAL_NUMBER']
#'AIN0', 'AIN1', 'AIN2', 'AIN3', 'AIN4', 'AIN5', 'AIN6', 'AIN7', 'AIN8', 'AIN9', 'AIN10', 'AIN11', 'AIN12', 'AIN13', 
aWrites = [WRITE, READ, READ, READ]
aNumValues = [1, 1, 1, 1]
aValues =    [0, 0, 0, 0]


results = ljm.eNames(handle, numFrames, aNames, aWrites, aNumValues, aValues)

print("\neNames results: ")
start = 0
for i in range(numFrames):

    end = start + aNumValues[i]
    print("    Name - %16s, write - %i, values %s" %
          (aNames[i], aWrites[i], results[start:end]))
    start = end
    
    
print(results)    
data = f'V,device={results[3]} Bat_current={results[1]}\n'
print(data)
r = requests.post(influx_url, headers=headers, data=data)
print(r)    
    
#ljm.eWriteName(handle, 'FIO0', 1)

# Close handle
ljm.close(handle)

# TODO write to influxdb






