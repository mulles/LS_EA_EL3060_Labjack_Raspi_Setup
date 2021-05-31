import subprocess
from os import path
import re

class SOEMMaster(object):

    def __init__(self, interface):
        self._if = interface

    def get_slave_count(self):
        command = "sudo slaveinfo %s" % self._if
        state_string = subprocess.check_output(command,
                                               universal_newlines=True,
                                               shell=True)
        res = re.findall(r'Slave:(\d+)', state_string)
        if res:
            return len(res)
        return 0

    # SOEM slave ID starts at 1, IgH at 0
    def sii_write(self, slaveid=0, filepath="somanet_cia402.sii"):
        if path.exists(filepath) == False:
            print("Error file '{}' not found.".format(filepath))
            return False

        command = "sudo eepromtool %s %d -w %s" % (self._if, slaveid+1, filepath)
        if (subprocess.call(command, stdout=subprocess.DEVNULL, shell=True) == 1):
            return False
        return True
