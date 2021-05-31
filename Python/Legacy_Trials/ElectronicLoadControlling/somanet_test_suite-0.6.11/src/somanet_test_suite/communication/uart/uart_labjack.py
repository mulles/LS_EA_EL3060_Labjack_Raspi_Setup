import random
from labjack import ljm
import os
import logging

logger = logging.getLogger(__file__)
logging.basicConfig(format='[%(levelname)s] %(message)s')

LIB_PATH = '/usr/local/lib'

class ExceptionUART(Exception):
    pass

class UARTLabjack():

    init_register = [
        'ASYNCH_ENABLE',  # Deactivate Uart and configure it
        'ASYNCH_TX_DIONUM',
        'ASYNCH_RX_DIONUM',
        'ASYNCH_BAUD',
        'ASYNCH_RX_BUFFER_SIZE_BYTES',
        'ASYNCH_NUM_DATA_BITS',
        'ASYNCH_NUM_STOP_BITS',
        'ASYNCH_PARITY',
        'ASYNCH_ENABLE'
    ]

    init_value = [0, 0, 1, 9600, 20, 8, 1, 0, 1]

    def __init__(self, baud_rate=9600, pin_tx=0, pin_rx=1, dev_handle=None):
        if not any([e.startswith('libLabJackM') for e in os.listdir(LIB_PATH)]):
            logger.error("UARTLabjack: Labjack library 'libLabJackM' is not installed.")
            return

        self.init_value[1] = pin_tx
        self.init_value[2] = pin_rx
        self.init_value[3] = baud_rate

        if dev_handle:
            self.handle = dev_handle
        else:
            self.handle = ljm.openS('T7', 'USB', 'ANY')

        self.write_multiple(self.init_register, self.init_value)

    def close(self):
        if self.handle:
            ljm.close(self.handle)

    def write(self, port, value):
        if type(value) == list:
            ljm.eWriteNameByteArray(self.handle, port, len(value), value)
        else:
            ljm.eWriteName(self.handle, port, value)

    def write_multiple(self, port_names, port_values):
        ljm.eWriteNames(self.handle, len(port_names), port_names, port_values)

    def read(self, port, num_bytes=0):
        if num_bytes > 0:
            return ljm.eReadNameByteArray(self.handle, port, num_bytes)
        else:
            return ljm.eReadName(self.handle, port)

    def read_multiple(self, port_names):
        return ljm.eReadNames(self.handle, len(port_names), port_names)

    def transmit(self, data):
        if type(data) == str:
            data = [ord(c) for c in data]
        if type(data) != list:
            raise ExceptionUART('ERROR: Provided data is no list')
        self.write('ASYNCH_NUM_BYTES_TX', len(data))
        for d in data:
            self.write('ASYNCH_DATA_TX', d)

        self.write('ASYNCH_TX_GO', 1)

    def receive(self, num_bytes=None):
        bytes_in_buffer = self.in_waiting()
        rx_buffer = []
        to_read = bytes_in_buffer
        if num_bytes and num_bytes <= bytes_in_buffer:
            to_read = num_bytes
        for c in range(to_read):
            rx_buffer.append(int(self.read('ASYNCH_DATA_RX')))
        return rx_buffer

    def in_waiting(self):
        return int(self.read('ASYNCH_NUM_BYTES_RX'))



if __name__ == '__main__':
    uart = UARTLabjack()
    msg = [random.randint(0, 255) for c in range(8)]
    uart.transmit([len(msg)])
    res = uart.receive()
    print(res)
    uart.close()





