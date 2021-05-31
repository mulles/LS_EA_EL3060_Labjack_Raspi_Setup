#!/usr/bin/env python3

"""Listen on serial port for ThingSet data and print to CommandLine"""
"""Modified by Emile Schons 03.05.2021"""

import sys
import argparse
import json
from datetime import datetime
import serial
from pandas import json_normalize 
import time

def out(msg):
    """Print message on command line."""
    print(msg)
    sys.stdout.flush()

def connect_serial(port, baud):
    """Connect to serial port. Returns port instance."""
    try:
        ser = serial.Serial(port, baud, timeout=10)
        ser.nonblocking()
        out("Listening on {} ..".format(port))
    except serial.SerialException:
        out("Error opening port {} .. aborting".format(port))
        sys.exit(1)

    return ser

def write_data(ser):
    ser.write(b'=pub/serial {"Enable":true}\n')
    while True:
        if ser.in_waiting > 0:
            try:
                raw_data = ser.readline()
                time.sleep(1)
#                if raw_data[0:2] == b'# ':
#                    json_data = json.loads(raw_data.strip()[2:])
#                    data_frame = json_normalize(json_data)
#                    data_frame['time'] = datetime.now()
#                    out(data_frame)
#                    out("{}: data written to db.".format(data_frame.loc[0]['time']))
                #out(raw_data)
                print(raw_data)
            except json.decoder.JSONDecodeError as e:
                pass
        time.sleep(0.1)

def main():
    """This is the main function. Calls connect_serial(port, baud) and write_data(ser, dbcon, table)"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", help="Serial port to listen to (default: /dev/ttyACM0)", default="/dev/ttyACM0")
    parser.add_argument("--baud",help="Baud rate (default: 115200)", default="115200")
    args = parser.parse_args()
    ser = connect_serial(args.port, args.baud)
    write_data(ser)
    

if __name__ == '__main__':
    main()
