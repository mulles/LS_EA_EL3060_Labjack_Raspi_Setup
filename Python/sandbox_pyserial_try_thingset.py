#Author Emile Schons
#27.04.2021
# This Script should get SOC information from MPPT-1210-HUS via NucleaSerial-Interface with the thingset protocol.
#Based on https://libre.solar/thingset/2b_text_mode.html#read-data

#import serial
#ser = serial.Serial('/dev/ttyAMA0')  # open serial port
#print(ser.name)         # check which port was really used
#ser.write(b'?output')     # write a string
##ser_bytes = ser.readline()
##print(ser_bytes)
##ser.close()             # close port?output

#print('HelloWORLD') 

import time
import serial
import codecs
    
print ("Starting program")


print(b'?output')
#ser = serial.Serial('/dev/ttyACM0', baudrate=115200,
#                    stopbits=serial.STOPBITS_ONE,
#                    parity=serial.PARITY_NONE,
#                    bytesize=serial.EIGHTBITS
#                    )
#print(ser.name)  
#                
#print ('Serialconnectionsetup')
#time.sleep(1)

#print ('Writing output')
#ser.write(b'?/')

#print ('Output written')
#    
#while True:
#        if ser.inWaiting() > 0:
#            data = ser.read()
#            print (data.decode('iso-8859-1'))
