#!/usr/bin/env python

"""Listen on serial port for ThingSet data and write data into
sqlite database"""

import sys
import argparse
import json
from datetime import datetime
import serial
from pandas.io.json import json_normalize
import time

def wait(timetowait,message):
    """Wait for timetowait and outputs the remaining seconds"""
    for i in range(timetowait,0,-1):
        print("{message}{i}", end="\r", flush=if timetowait > 1) # Screen is cleared for Timers.
        time.sleep(1)

def connect_serial(port, baud):
    """Connect to serial port. Returns port instance."""
    try:
        ser = serial.Serial(port, baud, timeout=10)
        ser.nonblocking()
        print("Listening on {} ..".format(port))
    except serial.SerialException:
        print("Error opening port {} .. aborting".format(port))
        sys.exit(1)

    return ser

def write_data(ser, floatchargevoltage, dischargetime, nochargetime):
    while True:
        ser.write(b'==input {"LoadEn":false}\n') # Make sure Discharging is disabled
        # Verify if battery is full
           # read influxdb voltage and check if >= discharge
           # wait(1,"Still Charging not full yet") 
           # ser.write(b'=input {"DcdcEn":false}\n' # Stop Charging
           # wait(nochargetime,"Time not charging left:")       
           # ser.write(b'==input {"LoadEn":true}\n') # Start Discharging
           # wait(dischargetime,"Time discharging left:") 
           # ser.write(b'==input {"LoadEn":false}\n') # Stop Discharging
           # wait(nochargetime,"Time not charging left:")   
           # ser.write(b'=input {"DcdcEn":true}\n' # Start Charging.
           # TODO Write function to check feedback of Serialport answer
           # TODO use socat if disconnection of measurement script make problems.         
           
           
        if ser.in_waiting > 0:
            try:
                raw_data = ser.readline()
                if raw_data[0:2] == b'# ':
                    json_data = json.loads(raw_data.strip()[2:])
                    #=input {"LoadEn":true}
            except json.decoder.JSONDecodeError as e:
                pass
        time.sleep(0.1)

def main():
    """This is the main function. Calls connect_serial(port, baud) and write_data(ser)"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", help="Serial port to listen to (default: /dev/ttyACM0)", default="/dev/ttyACM0")
    parser.add_argument("--baud",help="Baud rate (default: 115200)", default="115200")
    parser.add_argument("--floatChV",help="Float Charge Voltage define battery is full)", default="13.5")
    parser.add_argument("--disCh", help="Time to discharge with 1A in minutes", default="60")
    parser.add_argument("--NoCh", help="Time to neither charge or discharge in minutes", default="30")  # For Voltage to stabalise, before discharging.    
    args = parser.parse_args()

    ser = connect_serial(args.port, args.baud)
    write_data(ser, args.floatChV, args.disCh, args.NoCh)
    


if __name__ == '__main__':
    main()
