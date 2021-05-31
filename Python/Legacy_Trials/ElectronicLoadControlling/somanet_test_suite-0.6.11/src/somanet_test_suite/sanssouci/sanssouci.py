import threading
import queue
import time

class DAQCallback():

    def __init__(self, port_a, port_b, port_c, device='T7', connectionType='USB', id='ANY', daq=None):
        if daq == None:
            self.daq = DAQLabJack(device, connectionType, id)
        else:
            self.daq = daq
        self.port_a = port_a
        self.port_b = port_b
        self.port_c = port_c

    @staticmethod
    def print(h1, h2, h3):
        h1_repr = '|  ' if h1 == 0 else '  |'
        h2_repr = '|  ' if h2 == 0 else '  |'
        h3_repr = '|  ' if h3 == 0 else '  |'
        _output_string = '%s     %s     %s' % (h3_repr, h2_repr, h1_repr)
        print(_output_string)

    def write(self, a, b, c):
        self.daq.write_multiple([self.port_a, self.port_b, self.port_c], [a, b, c])



class Sanssouci():

    SECONDS_PER_MINUTE = 60

    def __init__(self, output_callback, sensor, resolution=0, pole_pairs=0):
        self.__sensor = sensor
        self.__resolution = resolution
        self.__pole_pairs = pole_pairs
        self.__cmd_queue = queue.Queue()
        self.__alive = threading.Event()
        self.__alive.set()
        self.__output_callback = output_callback
        self.__thread = None

        self.state = 0
        self.ticks = 0
        self.i = 0
        self.polarity = 0

    def __del__(self):
        self.close()

    def close(self):
        self.__alive.clear()
        if self.__thread:
            self.__thread.join()

    def _start_thread(self):
        if self.__sensor == 'HALL':
            self.__thread = threading.Thread(target=self._thread, args=(self._hall,))
            self.__thread.start()
        elif self.__sensor == 'QEI':
            self.__thread = threading.Thread(target=self._thread, args=(self._qei,))
            self.__thread.start()

    def _calc_timing(self, velocity):
        time_electric_turn = 0
        time_mechanical_turn = 0
        loop_time = 0
        if self.__sensor == 'HALL':
            time_electric_turn = abs(self.SECONDS_PER_MINUTE/(velocity*self.__pole_pairs ))
            loop_time = time_electric_turn/6 # time for electrical 60°
        elif self.__sensor == 'QEI':
            time_mechanical_turn = abs(self.SECONDS_PER_MINUTE / velocity)
            time_abi_tick = time_mechanical_turn / self.__resolution
            loop_time = time_abi_tick
        self.polarity = velocity / abs(velocity)

        return loop_time

    def _hall(self):
        h1 = 0
        h2 = 0
        h3 = 0
        if self.state == 0:  # 0/360 degree
            h1 = 1
            h2 = 0
            h3 = 1
        elif self.state == 1:  # 60 degree
            h1 = 1
            h2 = 0
            h3 = 0
        elif self.state == 2:  # 120
            h1 = 1
            h2 = 1
            h3 = 0
        elif self.state == 3:  # 180
            h1 = 0
            h2 = 1
            h3 = 0
        elif self.state == 4:  # 240
            h1 = 0
            h2 = 1
            h3 = 1
        elif self.state == 5:  # 300
            h1 = 0
            h2 = 0
            h3 = 1

        if self.polarity > 0:
            self.state = (self.state + 1) % 6
        elif self.polarity < 0:
            self.state -= 1
            if self.state == -1:
                self.state = 5

        return h1, h2, h3

    def _qei(self):
        a = 0
        b = 0
        if self.state == 0:
            a = 0
            b = 1
        elif self.state == 1:
            a = 0
            b = 0
        elif self.state == 2:
            a = 1
            b = 0
        elif self.state == 3:
            a = 1
            b = 1

        if self.polarity > 0:
            self.state = (self.state + 1) % 4
            self.ticks = (self.ticks + 1) % self.__resolution
        elif self.polarity < 0:
            self.state -= 1
            if self.state == -1:
                self.state = 3
            self.ticks -= 1
            if self.ticks < 0:
                self.ticks = self.__resolution

        if self.i == 1 and self.state == 2:
            self.i = 0
        if self.ticks == 0 and self.state == 0:
            self.i = 1

        return self.i, b, a
        
    def _thread(self, sensor_callback):
        loop_time = 0

        while self.__alive.is_set():
            t0 = time.time()
            h1_i, h2_b, h3_a = sensor_callback()

            if not self.__cmd_queue.empty():
                loop_time = self.__cmd_queue.get_nowait()

            self.__output_callback(h1_i, h2_b, h3_a) # some output write function
            t1 = time.time()
            td = t1 - t0 # time delta
            if (loop_time - td) > 0:
                time.sleep(loop_time - td)  # - t1 - t0)


    def set_velocity(self, velocity):
        if not self.__thread:
            self._start_thread()
        # Because of a typical sensor problem, velocity is always one RPM less
        if velocity > 0:
            velocity += 1
        elif velocity < 0:
            velocity -= 1
        loop_time = self._calc_timing(velocity)
        self.__cmd_queue.put(loop_time)

if __name__ == '__main__':
    import somanet_test_suite as sts    

    print("Start Sanssouci")
    printer = DAQCallback('MIO2', 'MIO1', 'MIO0', daq=sts.DAQLabJack())
    """
    hall_gen = Sanssouci(printer.write, 'HALL', pole_pairs=7)
    hall_gen.set_velocity(100)
    #time.sleep(5)
    #hall_gen.set_velocity(-100)
    #time.sleep(5)
    #hall_gen.set_velocity(2000)
    #time.sleep(5)
    """
    #qei_gen = Sanssouci(printer.write, 'HALL', pole_pairs=7)
    qei_gen = Sanssouci(printer.write, 'QEI', resolution=100)
    qei_gen.set_velocity(40)
    #time.sleep(5)
    #hall_gen.set_velocity(-100)
    #time.sleep(5)
    #hall_gen.set_velocity(2000)
    #time.sleep(5)
else:    
    from ..daq.daq_labjack import DAQLabJack
