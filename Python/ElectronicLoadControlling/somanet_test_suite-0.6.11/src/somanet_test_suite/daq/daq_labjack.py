import logging
import math
import os
import time

import numpy as np

logger = logging.getLogger(__file__)
logging.basicConfig(format='[%(levelname)s] %(message)s')

try:
    from labjack import ljm
except Exception as e:
    logger.warning(str(e))

# Pins that can sample frequency
PINS_FREQUENCY_IN = {
    'T7': ['DIO0', 'DIO1'],
    'T4': ['DIO4', 'DIO5'],
}
PINS_PULSE_OUT = {
    'T7': ['DIO0', 'DIO2', 'DIO3', 'DIO4', 'DIO5'],
    'T4': ['DIO6', 'DIO7'],
}

MAX_SCAN_RATE = {
    'T4': 59880,
    'T7': 100000,
}

PRECISION = 6

LIB_PATH = '/usr/local/lib'


class ExceptionNoAcknowledgement(Exception):
    pass


class ExceptionDAQ(Exception):
    pass


class DAQLabJack:
    FIO0 = 'FIO0'
    FIO1 = 'FIO1'
    FIO2 = 'FIO2'
    FIO3 = 'FIO3'
    FIO4 = 'FIO4'
    FIO5 = 'FIO5'
    FIO6 = 'FIO6'
    FIO7 = 'FIO7'

    EIO0 = 'EIO0'
    EIO1 = 'EIO1'
    EIO2 = 'EIO2'
    EIO3 = 'EIO3'
    EIO4 = 'EIO4'
    EIO5 = 'EIO5'
    EIO6 = 'EIO6'
    EIO7 = 'EIO7'

    CIO0 = 'CIO0'
    CIO1 = 'CIO1'
    CIO2 = 'CIO2'
    CIO3 = 'CIO3'

    MIO0 = 'MIO0'
    MIO1 = 'MIO1'
    MIO2 = 'MIO2'

    AIN0 = 'AIN0'
    AIN1 = 'AIN1'
    AIN2 = 'AIN2'
    AIN3 = 'AIN3'
    AIN4 = 'AIN4'
    AIN5 = 'AIN5'
    AIN6 = 'AIN6'
    AIN7 = 'AIN7'
    AIN8 = 'AIN8'
    AIN9 = 'AIN9'
    AIN10 = 'AIN10'
    AIN11 = 'AIN11'
    AIN12 = 'AIN12'
    AIN13 = 'AIN13'

    DAC0 = 'DAC0'
    DAC1 = 'DAC1'

    TRIG_FALLING = 0
    TRIG_RISING = 1

    POSITIVE_EDGES = 3
    NEGATIVE_EDGES = 4

    ONE_SHOT = 0
    CONTINUOUS = 1

    d_dio_names = {
        'FIO0': 'DIO0',
        'FIO1': 'DIO1',
        'FIO2': 'DIO2',
        'FIO3': 'DIO3',
        'FIO4': 'DIO4',
        'FIO5': 'DIO5',
        'FIO6': 'DIO6',
        'FIO7': 'DIO7',
        'EIO0': 'DIO8',
        'EIO1': 'DIO9',
        'EIO2': 'DIO10',
        'EIO3': 'DIO11',
        'EIO4': 'DIO12',
        'EIO5': 'DIO13',
        'EIO6': 'DIO14',
        'EIO7': 'DIO15',
        'CIO0': 'DIO16',
        'CIO1': 'DIO17',
        'CIO2': 'DIO18',
        'CIO3': 'DIO19',
        'MIO0': 'DIO20',
        'MIO1': 'DIO21',
        'MIO2': 'DIO22'
    }

    CORE_FREQ = 80e6

    def __init__(self, device='T7', connectionType='ANY', id='ANY'):
        if not any([e.startswith('libLabJackM') for e in os.listdir(LIB_PATH)]):
            logger.error("DAQLabJack: Labjack library 'libLabJackM' is not installed.")
            return

        self._id = id
        self._conn = connectionType
        self._device = device
        self.connect(device, connectionType, id)
        self._clock1_enabled = False
        self._clock2_enabled = False

    def __str__(self):
        return 'LJ-%s-%s' % (self._device, self._id)

    def connect(self, device, connectionType, id):
        self._handle = ljm.openS(device, connectionType, id)

    def close(self):
        ljm.close(self._handle)

    def scan(self, connectiontype=None):
        return ljm.listAllS(self._device, connectiontype or self._conn)

    def write(self, ports, values=None):
        if type(ports) is list and type(ports[0]) is tuple:
            ljm.eWriteNames(self._handle, len(ports), [c[0] for c in ports], [c[1] for c in ports])
        elif type(ports) is list and type(values) is list:
            if len(ports) != len(values):
                raise ExceptionDAQ('write_multiple(): Amount of names and values are not the same')
            ljm.eWriteNames(self._handle, len(ports), ports, values)
        else:
            ljm.eWriteName(self._handle, ports, values)

    def read(self, ports):
        if type(ports) is list:
            return ljm.eReadNames(self._handle, len(ports), ports)
        else:
            return ljm.eReadName(self._handle, ports)

    def __calc_divisor_rollvalue(self, frequency):
        divisor = 2 ** math.ceil(math.log(math.ceil(self.CORE_FREQ / (frequency * 65536)),
                                          2))  # divisor could only take the following values: 1,2,4,8,16,32,64,256
        if divisor == 128:
            divisor = 256
        roll_value = int(self.CORE_FREQ / (frequency * divisor))

        return divisor, roll_value

    def _config_common_pwm(self, port, index, divisor, roll_value, clock_source, config_a, config_b=None, config_c=None, config_d=None):

        if not self.d_dio_names[port] in PINS_PULSE_OUT[self._device]:
            raise ExceptionDAQ('Error! "%s/%s" cannot generate "Pulse Out" on "%s". Use "%s" instead.' % (port,
                                                                                                          self.d_dio_names[port],
                                                                                                          self._device,
                                                                                                          PINS_PULSE_OUT[self._device]))
        # Deactivate all clocks
        config = [
            ("DIO_EF_CLOCK0_ENABLE", 0),
            ("DIO_EF_CLOCK1_ENABLE", 0),
            ("DIO_EF_CLOCK2_ENABLE", 0)
        ]

        # self.write("DIO_EF_CLOCK%d_ENABLE" % clock_source, 0)
        self.write(config)

        if clock_source == 0:
            self._clock1_enabled = False
            self._clock2_enabled = False
        if clock_source == 1:
            self._clock1_enabled = True
        if clock_source == 2:
            self._clock2_enabled = True

        # Turn the output port off
        self.write(self.d_dio_names[port], 0)

        # Configure the signal to be generated
        _config_name_template = "%s_EF_CONFIG_%s"
        config_register = [(_config_name_template % (self.d_dio_names[port], 'A'), config_a)]

        if config_b != None:
            config_register.append((_config_name_template % (self.d_dio_names[port], 'B'), config_b))

        if config_c != None:
            config_register.append((_config_name_template % (self.d_dio_names[port], 'C'), config_c))

        if config_d != None:
            config_register.append((_config_name_template % (self.d_dio_names[port], 'D'), config_d))

        config = [
            ("%s_EF_ENABLE" % self.d_dio_names[port], 0),
            ("DIO_EF_CLOCK%d_ENABLE" % clock_source, 0),
            ("DIO_EF_CLOCK%d_DIVISOR" % clock_source, divisor),
            ("DIO_EF_CLOCK%d_ROLL_VALUE" % clock_source, roll_value),
            *config_register,
            ("%s_EF_INDEX" % self.d_dio_names[port], index),
            ("%s_EF_OPTIONS" % self.d_dio_names[port], clock_source),
        ]

        self.write(config)

        self.write(self.d_dio_names[port], 0)

        # Activate the clock and the signal
        config = []

        if self._clock1_enabled:
            config.append(("DIO_EF_CLOCK1_ENABLE", 1))

        if self._clock2_enabled:
            config.append(("DIO_EF_CLOCK2_ENABLE", 1))

        if not self._clock1_enabled and not self._clock2_enabled:
            config.append(("DIO_EF_CLOCK0_ENABLE", 1))

        config.append(("%s_EF_ENABLE" % self.d_dio_names[port], 1))

        self.write(config)

    def _get_adc_data(self, port, num_bytes):
        config = [
            ("SPI_MISO_DIONUM", int(self.d_dio_names[port][3:])),
            ("SPI_NUM_BYTES", num_bytes)
        ]

        self.write(config)

        # performing the SPI communication
        # SPI is full duplex = number of bytes read from and written to the slave must be equal
        # * to read data from a slave without sending data to it, load dummy data into SPI_DATA_TX
        dataWrite = [0] * num_bytes
        ljm.eWriteNameByteArray(self._handle, 'SPI_DATA_TX', num_bytes, dataWrite)
        # execute SPI communication
        self.write("SPI_GO", 1)

        # read the bytes
        return ljm.eReadNameByteArray(self._handle, 'SPI_DATA_RX', num_bytes)

    def _stream_port(self, port, num_scans=20, scan_rate=2000):
        """
        Acquire a number of samples from a port and average the return.
        :param port:
        :param num_scans: number of samples to acquire
        :type num_scans: int
        :param scan_rate: sampling frequency in Hz
        :type scan_rate: int
        :return:
        """

        port_address = ljm.nameToAddress(port)[0]  # returns (Address, DataType)
        # self.write("STREAM_RESOLUTION_INDEX", 2)

        # In order to acquire the correct value:
        #    1. shift multiplexer to desired port by reading from it, and ignore
        #    2. introduce delay: wait for input's dynamic response to equalize
        #    3. sample desired port again

        sampled_data_throwaway = self.read(port)
        time.sleep(0.01)  # delay in seconds

        sampled_data = ljm.streamBurst(self._handle, 1, [port_address], scan_rate, num_scans)[
            1]  # returns tuple (ScanRate, samples_acquired)
        # Labjack very occasionally returns bogus value, such as -4496.733 or -506.242, etc.
        # their support does not know the reason, this is a workaround SW fix
        if abs(np.mean(sampled_data)) > 100:
            sampled_data = ljm.streamBurst(self._handle, 1, [port_address], scan_rate, num_scans)[1]

        return np.mean(sampled_data)

    def read_average_voltage(self, ports, num_scans=20, scan_rate=2000):
        """
        Acquire a number of samples from one or mutliple ports and average the return.
        :param ports:
        :param num_scans: number of samples to acquire
        :type num_scans: int
        :param scan_rate: sampling frequency in Hz
        :type scan_rate: int
        :return:
        """
        if type(ports) is list:
            sampled_data_ave = []
            for port in ports:
                print(port)
                sampled_data_ave.append(self._stream_port(port, num_scans, scan_rate))
            return sampled_data_ave
        else:
            return self._stream_port(ports, num_scans, scan_rate)

    def get_frequency_max_min_voltage(self, port, voltage_range=10.0, num_scans=6000, scan_rate=100e3):
        """
        Sample the analog signal and extract frequency, maximum voltage and minimum voltage.
        :param port: pin name
        :type port: str
        :param voltage_range: voltage range of the analog input (ex. 10 refers to +/-10V input).
                              Supported ranges: 10, 1, 0.1, 0.01
        :type voltage_range: int
        :param num_scans: number of samples to acquire
        :type num_scans: int
        :param scan_rate: sampling frequency in Hz
        :type scan_rate: int
        :return: list [frequency, average max, average min]
        """

        if scan_rate > MAX_SCAN_RATE[self._device]:
            scan_rate = MAX_SCAN_RATE[self._device]
            print('Warning! Scan rate too high. Set it to "%d"' % scan_rate)

        port_address = ljm.nameToAddress(port)[0]  # returns (Address, DataType)
        self.write('STREAM_BUFFER_SIZE_BYTES', 32768)  # maximum size, default is 4096
        self.write('%s_RANGE' % port, voltage_range)

        cnt = 5
        while True:
            try:
                sampled_data = ljm.streamBurst(self._handle, 1, [port_address], scan_rate, num_scans)[
                    1]  # returns tuple (ScanRate, samples_acquired)
                break
            except ljm.LJMError as e:
                cnt -= 1
                if cnt == 0:
                    print('ERROR', e)
                    raise ljm.LJMError('Not able to sample signal')

        # recovering the frequency of the sampled signal
        A = sampled_data
        A = A - np.mean(A)
        sampling_freq_of_DAC = scan_rate  # maximum sampling freq=100kHz

        A_f = np.abs(np.real(np.fft.fft(A)))  # performing FFT on the data acquired, saving only real-absolute values
        A_f_trunk = A_f[1:int(len(A) / 2)]  # truncating the mirrored data from FFT

        threshold = np.max(A_f_trunk) - 5  # threshold of where to search for the frequency peaks

        freq_peak_index = np.where(A_f_trunk > threshold)[0]  # boolean comparison, finding indices
        freq_of_sig = round(freq_peak_index[0] / len(A) * sampling_freq_of_DAC, PRECISION)

        sorted_samples = np.sort(sampled_data)

        range_percent = 5  # percent
        # to avoid bursts or outliers ignore to highest and lowest 1 or whatever percent
        range_ignore_percent = 0.5  # percent

        range_ignore_index = int(range_ignore_percent * len(sorted_samples) / 100)
        range_index = int(range_percent * len(sorted_samples) / 100)

        min_values = sorted_samples[range_ignore_index:range_index]
        max_values = sorted_samples[-range_index:-range_ignore_index]

        # round off the trailing numbers
        max_value = round(float(np.mean(max_values)), PRECISION)
        min_value = round(float(np.mean(min_values)), PRECISION)

        return freq_of_sig, max_value, min_value

    def get_average_max_min_voltage(self, port, num_scans=6000, scan_rate=100e3):
        """
        Get average, maximum and minimum voltage of an analog signal using build-in functions of Labjack.
        :param port: Analog port
        :type port: str
        :param num_scans: Number of scans
        :type num_scans: int
        :param scan_rate: Scan rate in Hertz
        :type scan_rate: int
        :return: Measured values, Tuple of (average, max, min) voltage
        :rtype: tuple
        """

        config = [
            ('%s_EF_INDEX' % port, 3),
            ('%s_EF_CONFIG_A' % port, num_scans),
            ('%s_EF_CONFIG_D' % port, scan_rate),
        ]

        self.write(config)

        result = [
            '%s_EF_READ_A' % port,
            '%s_EF_READ_B' % port,
            '%s_EF_READ_C' % port,
        ]

        return self.read(result)

    def config_read_frequency(self, port_name, clock_source=0, edge=POSITIVE_EDGES, config=ONE_SHOT):
        """
        Configure Labjack to sample frequency
        :param port_name: pin name
        :type port_name: str
        :param clock_source: Clock source index, 0 (32bit), 1 (16bit), or 2 (16bit)
        :type clock_source: int
        :param edge: Sampling positive or negative edges
        :type edge: int
        :param config: Configure, if frequency is measured once (ONE_SHOT) or constantly (CONTINUOUS)
        :type config: int
        """
        if not self.d_dio_names[port_name] in PINS_FREQUENCY_IN[self._device]:
            raise ExceptionDAQ('Error! "%s/%s" cannot sample frequency. Use %s instead.' % (port_name, self.d_dio_names[port_name], PINS_FREQUENCY_IN[self._device]))

        if clock_source == 0:
            self._clock1_enabled = False
            self._clock2_enabled = False
        if clock_source == 1:
            self._clock1_enabled = True
        if clock_source == 2:
            self._clock2_enabled = True

        _config = [
            ("%s_EF_ENABLE" % self.d_dio_names[port_name], 0),  # Deactivate
            ("DIO_EF_CLOCK%d_ENABLE" % clock_source, 0),
            ("DIO_EF_CLOCK%d_DIVISOR" % clock_source, 0),
            ("DIO_EF_CLOCK%d_ROLL_VALUE" % clock_source, 0),
            ("%s_EF_CONFIG_A" % self.d_dio_names[port_name], config),
            ("%s_EF_INDEX" % self.d_dio_names[port_name], edge),  # 3 = positive edges, 4 = negative edges
        ]

        self.write(_config)

        _config = []

        if self._clock1_enabled:
            _config.append(("DIO_EF_CLOCK1_ENABLE", 1))

        if self._clock2_enabled:
            _config.append(("DIO_EF_CLOCK2_ENABLE", 1))

        if not self._clock1_enabled and not self._clock2_enabled:
            _config.append(("DIO_EF_CLOCK0_ENABLE", 1))

            _config.append(("%s_EF_ENABLE" % self.d_dio_names[port_name], 1))

        self.write(_config)

    def read_frequency(self, port_name):
        """
        Sample frequency on digital input
        :param port_name: digital port name
        :type port_name: str
        :return: Frequency in Hertz
        :rtype: int
        """
        if not self.d_dio_names[port_name] in PINS_FREQUENCY_IN[self._device]:
            raise ExceptionDAQ('Error! "%s/%s" cannot sample frequency. Use %s instead.' % (port_name, self.d_dio_names[port_name], PINS_FREQUENCY_IN[self._device]))

        # register = '%s_EF_READ_A_F_AND_RESET' % self.d_dio_names[port_name]
        register = '%s_EF_READ_A_F' % self.d_dio_names[port_name]

        cnt_try = 50

        while cnt_try > 0:
            res = self.read(register)
            if res != 0.0:
                return 1 / res
            cnt_try -= 1
        return 0

    def config_stream_trigger(self, port, enable=1):
        """
        stream_trigger = 0,  no trigger. Stream will start when Enabled
        stream_trigger = 2000,  DIO0_EF will start stream
        stream_trigger = 2001,  DIO1_EF will start stream
        stream_trigger = 2002,  DIO2_EF will start stream...to DIO7_EF

        keep in mind that scanRate of streamBurst has to be >= (numScans + 1) * 2 * frequency of triggering signal
        """
        stream_trigger = 2000 + int(self.d_dio_names[port][3:])
        if enable == 0:
            stream_trigger = 0
        # Configure LJM for unpredictable stream timing
        ljm.writeLibraryConfigStringS("LJM_STREAM_SCANS_RETURN", "LJM_STREAM_SCANS_RETURN_ALL")
        ljm.writeLibraryConfigS("LJM_STREAM_RECEIVE_TIMEOUT_MS", 0)

        self.write(port, 0)

        # 2001 sets DIO1 / FIO1 as the stream trigger
        self.write("STREAM_TRIGGER_INDEX", stream_trigger)

        # DIO%s_EF_ENABLE: Clear any previous DIO0_EF settings [0]
        # DIO%s_EF_INDEX: 12 enables conditional reset used for triggered acquisition [12]
        # DIO%s_EF_CONFIG_A:
        #       Bit 0: Edge select; 0=falling, 1=rising.
        #       Bit 1: reserved
        #       Bit 2: 0=OneShot; 1 = only reset once. 0 = reset every n edges. [1 or 5]
        config = [
            ("%s_EF_ENABLE" % self.d_dio_names[port], 0),
            ("%s_EF_INDEX" % self.d_dio_names[port], 12),
            ("%s_EF_CONFIG_A" % self.d_dio_names[port], 1),
            ("%s_EF_ENABLE" % self.d_dio_names[port], 1)
        ]

        self.write(config)

    def read_average_voltage_triggered(self, port_names, num_scans=20, scan_rate=2000):
        numPorts = len(port_names)
        port_addresses = ljm.namesToAddresses(numPorts, port_names)[0]  # returns (Address, DataType)
        # self.write('STREAM_SETTLING_US', 2000)  # stream settling time in microseconds, max = 4400
        sampled_data = ljm.streamBurst(self._handle, numPorts, port_addresses, float(scan_rate), num_scans)[1]  # returns tuple (ScanRate, samples_acquired)

        sampled_data_ave = []
        for i in range(1, numPorts + 1):
            sampled_data_per_channel = [i for i in sampled_data[i - 1::numPorts]]
            sampled_data_ave.append(np.mean(sampled_data_per_channel))

        return sampled_data_ave

    def set_voltage_range(self, port, voltage_range):
        """
        Applies the amplification on selected analog input. Default range is 10V, meaning analog input range is +/-10V.
        IMPORTANT: AIN are first mux'ed and then they are amplified. Therefore, when using MUX80, the same gain is applied to the set of mux'ed signals.

        :param port: pin name
        :type port: str
        :param voltage_range: desired voltage range after amplification
        :type voltage_range: int
        Supported ranges:
            10      : sets gain=x1, so that the analog input range is ±10 volts (default)
            1       : sets gain=x10, so that the analog input range is ±1 volts.
            0.1     : sets gain=x100, so that the analog input range is ±0.1 volts.
            0.01    : sets gain=x1000, so that the analog input range is ±0.01 volts
        """
        if self._device != 'T7':
            print('Error! Set voltage range only available on T7!')

        self.write('%s_RANGE' % port, voltage_range)

    def generate_pwm(self, port, frequency, clock_source=0, duty_cycle=0, phase_shift=None, num_pulses=None):
        """
        Generate PWM signal with controllable phase shift and controllable number of pulses.
        :param port: Pin name (e.g. FIO6)
        :type port: str
        :param frequency: Frequency of the PWM in Hz
        :type frequency: int
        :param clock_source: Clock source. Possible values are 0, 1, 2. There is only one 32bit register. 0 uses all 32 bits, 1 and 2 use the upper and the lower 16 bits.
                             If you use clock 0, you cannot use 1 and 2 and vice versa.
        :type clock_source: int
        :param duty_cycle: common duty cycle (of high pulses) in percentage
        :type duty_cycle: int
        :param phase_shift: Phase shift in degrees
        :type phase_shift: int
        :param num_pulses: Number of pulses
        :type num_pulses: int
        """
        divisor, roll_value = self.__calc_divisor_rollvalue(frequency)

        index = 0
        config_a = int(roll_value * duty_cycle / 100)
        config_b = 0
        config_c = 0

        if phase_shift != None or num_pulses != None:
            index = 1
            config_b = int((phase_shift or 0) * roll_value / 360)  # °
            count_duty_cycle = int(((duty_cycle * roll_value) / 100))  # %
            config_a = (config_b + count_duty_cycle) % roll_value

            if num_pulses != None:
                index = 2
                config_c = num_pulses

        self._config_common_pwm(port, index, divisor, roll_value, clock_source=clock_source, config_a=config_a, config_b=config_b, config_c=config_c)

    def generate_pwm_halfbridge(self, port_pwm_high, port_pwm_low, frequency=10e3, clock_source=1, dead_time=1e-6):
        """
        Generate PWM half bridge signal with controllable dead time.
        :param port_pwm_high: Pin name for high side signal (eg. FIO3)
        :type port_pwm_high str
        :param port_pwm_low: Pin name for low side signal (eg. FIO4)
        :type port_pwm_low: str
        :param frequency: Frequency of the PWM in Hz
        :type frequency: int
        :param clock_source: Clock source. Possible values are 0, 1, 2. There is only one 32bit register. 0 uses all 32 bits, 1 and 2 use the upper and the lower 16 bits.
                             If you use clock 0, you cannot use 1 and 2 and vice versa.
        :type clock_source: int
        :param dead_time: Dead time for two signals in seconds
        :type dead_time: int
        """

        index = 1
        divisor, roll_value = self.__calc_divisor_rollvalue(frequency)

        time_resolution = 1 / (frequency * roll_value)
        dead_time_counter = math.ceil(dead_time / time_resolution)
        config_A_low = (roll_value / 2) - 2 * dead_time_counter  # 50% duty cycle
        config_B_high = config_A_low + dead_time_counter
        config_A_high = config_B_high + roll_value / 2

        self._config_common_pwm(port_pwm_high, index, divisor, roll_value, clock_source, config_a=config_A_high, config_b=config_B_high)
        self._config_common_pwm(port_pwm_low, index, divisor, roll_value, clock_source, config_a=config_A_low)

    def disable_waveforms(self, *port_names):
        """
        Disable internal Labjack registers from any preconfigured states
        :param port_names: Pin names
        :type port_names: list of str
        """
        if not port_names:
            raise ExceptionDAQ("Port names list is empty")

        for p in port_names:
            self.write(p, 0)
            self.write("%s_EF_ENABLE" % self.d_dio_names[p], 0)

    def read_differential(self, port, reference_port=None):
        """
        Differential readings use a second AIN as a reference point (a.k.a. negative AIN channel).
        For AIN in extended range, positive channels can be in the following ranges:
                AIN16 to AIN23
                AIN32 to AIN39
                AIN48 to AIN55
                AIN64 to AIN71
                AIN80 to AIN87
                AIN96 to AIN103
                AIN112 to AIN119
                The negative channel is 8 higher than the positive channel. (ex. pos_ch: AIN48, neg_ch: AIN56).
        :param port:
        :param reference_port: Negative channel to be used for selected positive channel.
                               199 = Default -> single ended
        :type reference_port: int
        :return: Differential value read with reference to reference_port
        :rtype: float
        """
        if self._device != 'T7':
            print('Error! Differential analog in only available on T7')
            return

        SINGLE_ENDED = 199
        if type(reference_port) == str:
            reference_port = int(reference_port[3:])
        if reference_port is None:
            reference_port = int(port[3:]) + 8
        self.write('%s_NEGATIVE_CH' % port, reference_port)
        diff_value_read = self.read_average_voltage(port)
        # return to single_ended
        self.write('%s_NEGATIVE_CH' % port, SINGLE_ENDED)
        return diff_value_read

    def adc_config(self, clk_ch, cs_ch, mosi_ch, spi_mode=0, clk_speed=0, options=0):
        """

        :param clk_ch: DIO line for Clock (ex. CLK_ch = DIO3)
        :type clk_ch: str
        :param cs_ch: DIO line for ChipSelect (ex. CS_ch = DIO4)
        :type cs_ch: str
        :param mosi_ch: DIO line for MOSI (ex. MOSI_ch = DIO5)
        :type mosi_ch: str
        :param spi_mode: 0 =0/0=b00, 1 =0/1=b01, 2 =1/0= b10, 3 =1/1=b11
                      * for drive1000 application
                            CPOL = 0 (clock idles at 0)
                            CPHA = 0
        :type spi_mode: int
        :param clk_speed: SPI_SPEED_THROTTLE, clock frequency in kHz
                       0    = 780 (max speed)
                      65530	= 380
                      65500	= 100
                      65100	= 10
                      61100	= 1
                      21000	= 0.1
                      1     = 0.067
        :type clk_speed: int
        :param options: SPI_OPTIONS, Default = 0 => chip select active low
                      bit 0:
                      0 = Active low clock select enabled
                      1 = Active low clock select disabled.
                      bit 1:
                      0 = set DIO directions before starting the SPI operations.
                      1 = do not set DIO directions.
                      bit 2:
                      0 = transmit data MSB first
                      1 = transmit data LSB first
                      bit 3: Reserved
                      bits 4-7: Number of bits in the last byte. 0 = 8.
                      bits 8-15: Reserved
        :type options: int
        """
        # defining the ADC channels
        config = [
            ("SPI_CLK_DIONUM", int(self.d_dio_names[clk_ch][3:])),
            ("SPI_CS_DIONUM", int(self.d_dio_names[cs_ch][3:])),
            ("SPI_MOSI_DIONUM", int(self.d_dio_names[mosi_ch][3:])),
        ]

        self.write(config)

        # configuring the SPI communication
        config = [
            ("SPI_MODE", spi_mode),
            ("SPI_SPEED_THROTTLE", clk_speed),
            ("SPI_OPTIONS", options)
        ]

        self.write(config)

    def adc_get_value(self, channel_out):
        """
        Retrieve digital value from ADC
        :param channel_out: MISO_ch
        :return: ?-bit integer, number of bits dedends on ADC
        """
        # numBytes = 2 => each D_OUT is 2 bytes long
        numBytes = 2
        dataRead = self._get_adc_data(channel_out, numBytes)

        # extract the analog data.
        # this is specific to ADC used in Drive1000
        # ADC7265 sends 2 leading zeros, followed by 12 bits of data, followed by 2 trailing zeros
        dataOUT = [format(int(dataRead[0]), '08b'), format(int(dataRead[1]), '08b')]  # convert to binary numbers
        dataOUT = ''.join(dataOUT)[2:14]  # store as 12 bit number
        dataOUT = int(dataOUT, 2)  # convert to integer

        return dataOUT

    # to be verified how ADC is outputting data when a square wave is present
    # likely multiple SPI transactions needed
    def adc_get_stream(self, channel_out):
        # channel_out (MISO_ch) = adc_OUTA or adc_OUTB
        # numBytes = 2 => each D_OUT is 2 bytes long
        numBytes = 4
        dataRead = self._get_adc_data(channel_out, numBytes)

        # extract the analog data
        # go through buffered bytes and extract every second 2-byte word
        # ADC7265 sends 2 leading zeros, followed by 12 bits of data, followed by 2 trailing zeros
        data = []
        dataOUT = []
        for i in range(0, len(dataRead), 4):
            for m in range(i, i + 2):
                data.append(dataRead[m])

        for n in range(0, len(data), 2):
            data_bin = [format(int(data[n]), '08b'), format(int(dataRead[n + 1]), '08b')]  # convert to binary numbers
            data_bin = ''.join(data_bin)[2:14]  # store as 12 bit number
            dataOUT.append(int(data_bin, 2))  # convert to integer

        return dataOUT

    def i2c_config(self, SDA_ch='EIO0', SCL_ch='EIO1', CLK_speed=65516, options=0):
        """
        Args:
            SDA_ch, SCL_ch: DIO ports used as sda/scl lines
                FIO0:7 = 0:7
                EIO0:7 = 8:15
                CIO0:7 = 16:23

            CLK_speed: i2c speed. Default = 0, equivalent to 65536,= ~450 kHz
                    1 = ~40 Hz,
                65516 = ~100 kHz.

            options: controls details of the I2C protocol to improve device compatibility. Default = 0
                bit 0: 1 = Reset the I2C bus before attempting communication
                bit 1: 0 = Restarts will use a stop and a start
                       1 = Restarts will not use a stop
                bit 2: 1 = disable clock stretching
        """

        # defining the I2C channels
        ch_config = [
            ("I2C_SDA_DIONUM", int(self.d_dio_names[SDA_ch][3:])),
            ("I2C_SCL_DIONUM", int(self.d_dio_names[SCL_ch][3:]))
        ]

        self.write(ch_config)

        # configuring the I2C communication
        conf_names = [
            ("I2C_SPEED_THROTTLE", CLK_speed),
            ("I2C_OPTIONS", options)
        ]

        self.write(conf_names)

    def i2c_set_slave_address(self, slave_address):
        # 7-bit address of the slave device, shifted left by FW to allow for I2C R/W bit
        self.write("I2C_SLAVE_ADDRESS", slave_address)

    def i2c_read(self, rx_register, rx_numBytes):
        """
        Args:
            rx_register: address to the register to read data from. Type: int
            rx_numBytes: number of bytes to read
        """
        config = [("I2C_NUM_BYTES_TX", 1),
                  ("I2C_NUM_BYTES_RX", rx_numBytes)]

        self.write(config)

        # performing the I2C communication
        # data received from the slave is saved in the buffer on Labjack
        #    eWriteNameByteArray(handle, name, numBytes, Bytes)
        #    eReadNameByteArray(handle, name, numBytes)
        ljm.eWriteNameByteArray(self._handle, 'I2C_DATA_TX', 1, [rx_register])
        # executing I2C communication
        self.write("I2C_GO", 1)

        dataRead = ljm.eReadNameByteArray(self._handle, 'I2C_DATA_RX', rx_numBytes)

        # verify the transaction by reading the acknowledge bits
        # only bytes transmitted to the slave produce ACK bits
        # bit=1  transaction was successful
        # bit=0  transaction did not succeed
        # Wtf
        ack = int(self.read('I2C_ACKS'))
        if ack != (1 << ack.bit_length()) - 1 or ack == 0:
            raise ExceptionNoAcknowledgement("I2C Transaction was not successful")

        return dataRead

    def i2c_write(self, tx_register, tx_data):
        """
        Args:
            tx_register: address to the register to send data to. Type: int
            tx_data: data to send
        """

        if type(tx_register) != list:
            tx_register = [tx_register]

        if type(tx_data) != list:
            tx_data = [tx_data]

        data_to_send = tx_register + tx_data

        config = [("I2C_NUM_BYTES_TX", len(data_to_send)),
                  ("I2C_NUM_BYTES_RX", 0)]

        self.write(config)

        # performing the I2C communication
        ljm.eWriteNameByteArray(self._handle, 'I2C_DATA_TX', len(data_to_send), data_to_send)
        # executing I2C communication
        self.write("I2C_GO", 1)

        # verify the transaction by reading the acknowledge bits
        # only bytes transmitted to the slave produce ACK bits
        # bit=1  transaction was successful
        # bit=0  transaction did not succeed
        ack = int(self.read('I2C_ACKS'))
        if ack != (1 << ack.bit_length()) - 1 or ack == 0:
            raise ExceptionNoAcknowledgement("I2C Transaction was not successful")
