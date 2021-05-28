import struct
import time
from crcmod import predefined
from .uart_labjack import UARTLabjack

import serial

class ExceptionUART(Exception):
    pass


class UARTCommon():

    CU_LABJACK = 'labjack'
    CU_SERIAL = 'serial'

    def __init__(self, uart_device, baud_rate=9600, port=None, pin_tx=0, pin_rx=1, dev_handle=None, timeout=1.0):
        self.__uart_device = uart_device
        self.__timeout = timeout
        if uart_device == self.CU_LABJACK:
            self._uart = UARTLabjack(baud_rate, pin_tx, pin_rx, dev_handle)
        elif uart_device == self.CU_SERIAL:
            if not port:
                raise ExceptionUART('Unknown port')
            self._uart = serial.Serial(port=port, baudrate=baud_rate)
            if not self._uart.is_open:
                self._uart.open()
        else:
            raise ExceptionUART('Unknown Device')

    def transmit(self, msg):
        if self.__uart_device == self.CU_SERIAL:
            _msg = struct.pack('={}B'.format(len(msg)), *msg)
            self._uart.write(_msg)
            self._uart.flush()
        elif self.__uart_device == self.CU_LABJACK:
            if type(msg) is str:
                msg = msg.encode()
            if type(msg) is bytes:
                msg = list(msg)
            #print('\t\t', msg)
            self._uart.transmit(msg)

    def receive(self, num_bytes=None):
        t0 = time.time()
        while True:
            if self.__uart_device == self.CU_SERIAL:
                bytes_in_buffer = self._uart.in_waiting
                #print('bytes in buffer', bytes_in_buffer)
                if num_bytes and num_bytes <= bytes_in_buffer:
                    to_read = num_bytes
                else:
                    to_read = bytes_in_buffer
                if to_read > 0:
                    msg = self._uart.read(to_read)
                    return list(msg)
                #raise ExceptionUART('Empty Rx Buffer')
            elif self.__uart_device == self.CU_LABJACK:
                bytes_in_buffer = self._uart.in_waiting()
                if bytes_in_buffer > 0:
                    msg = self._uart.receive()
                    #print('\t\t', msg)
                    return msg

            if (time.time() - t0) > self.__timeout:
                raise ExceptionUART('Error! Timeout')

    def write(self, msg):
        self.transmit(msg)

    def read(self, num_bytes=None):
        return self.receive(num_bytes)

    def receive_byte(self):
        msg = self.receive(1)
        if len(msg) == 1:
            return msg[0]
        raise ExceptionUART('Too many bytes')

    def close(self):
        self._uart.close()

    def reset_input_buffer(self):
        self._uart.reset_input_buffer()


class SimpleUARTProt(UARTCommon):
    """
    Simple UART protocol:
    ---------------------//----------
    |cnt of bytes*| 1 | 2 | n | CRC8 |
    ---------------------//----------

    * Count of bytes without first byte.
    """

    def __init__(self, uart_device, baud_rate=9600, port=None, pin_tx=0, pin_rx=1, dev_handle=None, timeout=1.0):
        super(SimpleUARTProt, self).__init__(uart_device, baud_rate, port, pin_tx, pin_rx, dev_handle, timeout)
        self.crc8 = predefined.mkPredefinedCrcFun('crc8')

    def __calc_checksum(self, msg):
        if type(msg) is str:
            msg = msg.encode()
        msg = bytearray(msg)
        checksum = self.crc8(msg)
        return checksum

    def read(self, format=None):
        buf = []
        while True:
            try:
                buf += self.receive()
            except ExceptionUART as e:
                print(str(e))
                return
            if len(buf)> 0:
                expected_bytes = buf[0]
                if expected_bytes == len(buf)-1:
                    break
        checksum = self.__calc_checksum(buf[1:])
        if checksum != 0:
            raise ExceptionUART('Checksum Error: %d, %s' % (checksum, str(buf)))

        buf = buf[1:-1]
        if format == 'str':
            return ''.join([chr(c) for c in buf])
        return buf

    def write(self, payload, format=None):
        if type(payload) is str and not format:
            payload = payload.encode()
            data = struct.pack('={}B'.format(len(payload)), *payload)
        elif format:
            data = struct.pack(format, *payload)
        else:
            raise ExceptionUART('Wrong Data format')
        checksum = self.__calc_checksum(data)
        msg = [len(data)+1] + list(data) + [checksum]
        self.transmit(msg)



if __name__ == '__main__':
    import random
    uart = UARTCommon(UARTCommon.CU_LABJACK)
    #data = [1, 2, 3, 4, 5, 6, 7, 8]
    data = 'flash\n'
    uart.transmit(data)
    res = uart.receive('str')
    print(res)
    uart.close()


