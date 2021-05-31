import serial
import re
import struct
import time
import requests

# Resources: 
# https://stackoverflow.com/questions/1592158/convert-hex-to-float

influx_org = 'LibreSolar'
influx_bucket = 'LabjackCurrentVoltage'
influx_token = '6O3aUzQNynIPhh1jwlNukYU1gx5Z2fJZNehpANlNl1rTtLsSW2Acm2rFE3mO81l2Fq_Nl8lyhqajg5ivOAzrvA=='
influx_url = f'https://influxdb.lsserver.uber.space/api/v2/write?org={influx_org}&bucket={influx_bucket}&precision=s'
data = ""
headers = {'Authorization': 'Token %s' % influx_token}
device = "EA-EL-3060"

ser = serial.Serial(
    port = '/dev/ttyUSB0',
    baudrate = 57600, # instaed of 115200 
    parity = serial.PARITY_ODD,
    stopbits = serial.STOPBITS_ONE,
    bytesize = serial.EIGHTBITS,
    timeout=5, # IMPORTANT, can be lower or higher
    #inter_byte_timeout=0.1 # Alternative
    )

#print(ser.name)         # check which port was really used 
#print(ser.connect())    # return the transport and protocol instances.
#byteData = ser.read(size=5) #Set size to something high

#print(byteData)
# Telegram Header  (SD Start Delimiter)
      
SEND = 0xC0 + 0x20 + 0x10   # See 3.3.1 The start delimiter
RECEIVE = 0x40 + 0x20 + 0x10  # See 3.3.1 The start delimiter
#GET_NAME = [RECEIVE, 0x00, 0x00, 0x00]
# [SEND + len(value_bytes) - 1, output, obj_num] + value_bytes
# Constant telegram messages
#Structure: SD     + DN  + OBJ + DATA  + CS (to calculate)
print("Enter the object of the list [0-xxx]: ")
# OBJ = hex(int(input()))
print("Please the Data length of the object which you find in the list: ")
# data_length = int(input())

# OBJ = hex(71)
# data_length = 6
# print("You selected Object",str(int(OBJ,16))," with data length",data_length,". Object in Hex:",OBJ,"\n")

# telegram_nochecksum  = [RECEIVE+data_length-1, 0x00, int(OBJ,16), 0x00]
# print("The following telegram has been constructed:")
# print("[   SD ,  DN  , OBJ  , DATA ] + [CS](not calc yet): ")
# print([hex(x) for x in telegram_nochecksum],"\n")

# checksum =  sum(telegram_nochecksum[:])
# telegram = telegram_nochecksum + [checksum]
# print("The following telegram will be send:")
# print("[   SD ,  DN  , OBJ   , DATA , CS]: ")
# print([hex(x) for x in telegram])
# print("Telegram format to use/send with Cutecom")
# print(' '.join('%02x'%i for i in telegram),"\n")

while True:
    
    #Query object 71 (6 byte int, 3 words)
    OBJ = hex(71)
    data_length = 6
    telegram_nochecksum  = [RECEIVE+data_length-1, 0x00, int(OBJ,16), 0x00]
    checksum =  sum(telegram_nochecksum[:])
    telegram = telegram_nochecksum + [checksum]
    ser.write(telegram)
    query_data = ser.read(size=data_length+5)

    
    # print("Length of data:", len(query_data))
    # print("Checksum: ",hex(int(sum(query_data[0:len(query_data)-2]))), query_data[len(query_data)-2:len(query_data)].hex())
    # print("Received data in hex: ",[hex(x) for x in query_data])
    # print("Received data hex/ascii: ",query_data)
    # print("Received data in hex: ",query_data.hex())

    # print("Voltage in hex: ",query_data[3:len(query_data)-6].hex())
    # print("Voltage scaled in int: ",int(query_data[3:len(query_data)-6].hex(),16)) 
    Bat_V = int(query_data[3:len(query_data)-6].hex(),16)*160.0/25600             
    # print("Voltage",Bat_V,"V \n")


    # print("Current in hex : ",query_data[5:len(query_data)-4].hex())
    # print("Current scaled in int: ",int(query_data[5:len(query_data)-4].hex(),16))
    Load_A = int(query_data[5:len(query_data)-4].hex(),16)*60.0/25600
    # print("Current: ",Load_A,"A \n")

    # print("Power in hex",query_data[7:len(query_data)-2].hex())
    # print("Power scaled in int ",int(query_data[7:len(query_data)-2].hex(),16))
    Load_W = int(query_data[7:len(query_data)-2].hex(),16)*400.0/25600
    # print("Power: ",Load_W,"W \n")

    data = f'V,device={device} Bat_V={Bat_V},Load_W={Load_W}\n' 
    data += f'A,device={device} Load_A={Load_A}\n'

    #Query object 69 (4 byte float)
    OBJ = hex(69)
    data_length = 4
    telegram_nochecksum  = [RECEIVE+data_length-1, 0x00, int(OBJ,16), 0x00]
    checksum =  sum(telegram_nochecksum[:])
    telegram = telegram_nochecksum + [checksum]
    ser.write(telegram)
    query_data = ser.read(size=data_length+5)
    
    # print("Checksum: ",hex(int(sum(query_data[0:len(query_data)-2]))), query_data[len(query_data)-2:len(query_data)].hex())
    # print("CoulombCounter in Hex",query_data[3:len(query_data)-2].hex())
    Dis_Ah, = struct.unpack('>f', query_data[3:7])
    # print("CoulombCounter ",Dis_Ah,"Ah \n")
    
    data += f'Info,device={device} Dis_Ah={Dis_Ah}\n' 
    print(data)
    r = requests.post(influx_url, headers=headers, data=data)
    print(r)  

    time.sleep(1 - time.monotonic() % 1) 
        
    # print("Reeived data: ",struct.unpack('f',query_data))
    # print(re.search(r'\x01E=.*', str(query_data)[11:len(str(query_data))-4] ) )
    #print(struct.unpack('f',str(query_data)[12:len(str(query_data))-5] ))
    # print(struct.unpack('>ff', binascii.unhexlify( str(query_data)[12:len(str(query_data))-4]) ))
    # print("Received data: ",bytes.fromhex(str(query_data)))

ser.close()


# print("SEND +1: ",hex((SEND + 1)))
# print([hex(x) for x in STANDARD_HEADER])

"""
Print Binary 
""" 
#scale = 16 ## equals to hexadecimal

#num_of_bits = 40
#print(hex_telegram)
##bin_telegram = bin(int(hex_telegram[:], scale))[2:].zfill(num_of_bits)
#checksum =  hex(sum(hex_telegram[:]))
#n=0b10011 # String Binary representation?
#print(checksum)

#for x in range(len(SEND)):
#    print(hex(SEND[x]))
    

    
#def __calc_checksum(self, cmd):
#  checksum = 0
#  for byte in cmd_list:
#      checksum += byte
#  return self.__int_to_bytes(checksum, 2)

#def __get_response(self, package):
#  return package[3:-2]

#def __tx_rx(self, cmd, expect_length):
#  crc = self.__calc_checksum(cmd)
#  output = self.__pack_list(cmd + crc)
#  self.psu.write(output)
#  time.sleep(0.005)
#  num = 0
#  t0 = time.time()
#  while num < (expect_length+5):
#      num = self.psu.inWaiting()
#      if time.time() - t0 > 1:
#          raise ExceptionTimeout('Didn\'t receive %d bytes in time.' % (expect_length+5))
#  res = self.__get_response(self.psu.read(num))
#  time.sleep(0.04)
#  return res
# 
# STANDARD_HEADER = [SEND + 1, 0x00, 0x36]
#            Header  Output Obj  Mask   Command
# REMOTE_ON = STANDARD_HEADER + [0x10, 0x10]
#input(Object) # Default ) 0x47
# StartDelimiter = 0x55
# Checksum = 0x9D
# Object = 0x47
#SD = StartDelimiter  , DN = 0x01, OBJ = Object,  DATA = 0x00, CS = Checksum
#hex_telegram = [SD, DN, OBJ, DATA, CS]
# hex_telegram = [0xD1, 0x05, 0x36, 0x10, 0x10, 0x01]
# Example hex_telegram = [0x55, 0x01, 0x01, 0x47, 0x00]

# ERR_STRINGS = {
#     0x0: 'NO ERROR',

#     # Communication Error
#     0x3: 'CHECKSUM WRONG',
#     0x4: 'STARTDELIMITER WRONG',
#     0x5: 'WRONG OUTPUT',
#     0x7: 'OBJECT UNDEFINED',

#     # User Error
#     0x8: 'OBJECT LENGTH INCORRECT',
#     0x9: 'NO RW ACCESS',
#     0xf: 'DEVICE IN LOCK STATE',
#     0x30: 'UPPER LIMIT OF OBJECT EXCEEDED',
#     0x31: 'LOWER LIMIT OF OBJECT EXCEEDED'
# }
