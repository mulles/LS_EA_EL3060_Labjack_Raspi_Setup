import time
import subprocess
from os import path
import re
import sys
import logging

logger = logging.getLogger(__file__)
logging.basicConfig(format='[%(levelname)s] %(message)s')

if sys.platform != 'linux':
    exit(1)

# start / stop ethercat kernel module (run as root!)
# IgH EtherCAT master must be installed
ecat_master = "/etc/init.d/ethercat"

# ethercat control command
ETHERCAT_PATH = "/opt/etherlab/bin/ethercat"
ETHERCAT_CMDS = ["master", "slaves", "sii_read", "sii_write"]


class ExceptionIgH(Exception):
    pass


if not path.isfile(ETHERCAT_PATH):
    logger.warning('Warning! EtherCAT Master IgH is not installed.\n'
                   'To install IgH go to "https://github.com/synapticon/Etherlab_EtherCAT_Master/releases".')

SyncManager = {
    "MBoxIn":    0,
    "MBoxOut":   1,
    "BufferIn":  2,
    "BufferOut": 3
}

ECAT_TIMEOUT = 10  # seconds


class EtherCATMaster:
    """
    Base Class to communicate with the IgH EtherCAT Master. This class supports
    start and stop of the kernel modules and accesses low level EtherCAT functions.

    Dependencies:
    - IgH EtherCAT Master (with Synapticon patches)
    - Synapticons siitool
    """

    types_ = [
        "bool",
        "int8", "int16", "int32", "int64",
        "uint8", "uint16", "uint32", "uint64",
        "float", "double",
        "string", "octet_string", "unicode_string",
        "sm8", "sm16", "sm32", "sm64",
    ]

    def __init__(self):
        if not path.isfile(ETHERCAT_PATH):
            logger.error('Error! EtherCAT Master IgH is not installed.\n'
                         'To install IgH go to "https://github.com/synapticon/Etherlab_EtherCAT_Master/releases".')

        self.active = False
        self.siiprint = ""
        self.re_int_value = re.compile(r'(0x\w+ )?(-?\d+)')
        self.re_float_value = re.compile(r'(-?\d+.\d+)')

    def start(self):
        if (subprocess.call(["sudo", ecat_master, "start"], stdout=subprocess.DEVNULL)):
            self.active = True
        else:
            self.active = False

    def stop(self):
        if (subprocess.call(["sudo", ecat_master, "stop"], stdout=subprocess.DEVNULL)):
            self.active = False

    def restart(self):
        self.stop()
        self.start()

    def is_active(self):
        command = "sudo %s slaves" % ETHERCAT_PATH
        try:
            res_str = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            res_str = e.output

        return not 'Failed' in res_str.decode()

    def set_state(self, state, ignore_timeout=False, slaveid=0):
        _state = state.upper()
        command = "sudo %s state -p %d %s" % (ETHERCAT_PATH, slaveid, _state)

        t0 = time.time()
        act_state = None
        while act_state != _state:
            if (subprocess.call(command, stdout=subprocess.DEVNULL, shell=True) == 1):
                print('Error: Set State %s' % _state)
                return False
            act_state = self.get_state(slaveid)
            if time.time() - t0 > ECAT_TIMEOUT:
                print('Timeout: Set State %s' % _state)
                return False
            if ignore_timeout:
                return True

        return act_state == _state

    def get_state(self, slaveid=0):
        command = "sudo %s slaves -p %d" % (ETHERCAT_PATH, slaveid)
        state_string = subprocess.check_output(command,
                                               universal_newlines=True,
                                               shell=True)
        res = re.match(r'\d *\d+:\d+ +(.+?) +. (.+$)', state_string)
        if res:
            state = res.group(1)
            return state.upper()
        return 'None'

    def slaves(self):
        command = "sudo %s slaves | wc -l" % ETHERCAT_PATH
        slavecount = subprocess.check_output(command,
                                             universal_newlines=True,
                                             shell=True)
        return int(slavecount)

    def sii_read(self, slaveid=0):
        # subprocess.call([ "sudo", ethercat_cmd, ethercat_cmds[2], "-p", str(slaveid) ], subprocess.PIPE)
        command = "sudo %s sii_read -p %d | siitool -p" % (ETHERCAT_PATH, slaveid)
        self.siiprint = subprocess.check_output(command, universal_newlines=True, shell=True)

        if (self.siiprint == ""):
            return False

        return True

    def sii_write(self, slaveid=0, filepath="somanet_cia402.sii"):
        if path.exists(filepath) == False:
            print("Error file '{}' not found.".format(filepath))
            return False
        command = "sudo %s alias -f -p 0 0" % (ETHERCAT_PATH)
        print(command)
        if subprocess.call(command, stdout=subprocess.DEVNULL, shell=True, timeout=20) == 1:
            print("ERROR cannot set alias")
            return False
        command = "sudo %s sii_write -f -p %d %s" % (ETHERCAT_PATH, slaveid, filepath)
        if subprocess.call(command, stdout=subprocess.DEVNULL, shell=True, timeout=60) == 1:
            return False

        return True

    def foe_write(self, filepath, filename=None, slaveid=0):
        if not path.exists(filepath):
            print("Error, no valid file path: %s" % filepath)
            return False
        if not path.isfile(filepath):
            print("Error, not valid file: %s" % filepath)
            return False

        command = "sudo %s foe_write -p %d %s" % (ETHERCAT_PATH, slaveid, filepath)
        if filename:
            command += ' -o ' + filename

        if (subprocess.call(command, stdout=subprocess.DEVNULL, shell=True) == 1):
            return False
        return True

    def foe_read(self, slaveid=0, cmd="", output=False):
        command = "sudo %s foe_read -p %d %s" % (ETHERCAT_PATH, slaveid, cmd)
        # print("DEBUG " + command)
        if output:
            try:
                f = subprocess.check_output(command, shell=True).decode()
            except subprocess.CalledProcessError:
                return None
            return f
        else:
            if subprocess.call(command, stdout=subprocess.DEVNULL, shell=True) == 1:
                return False
            return True

    def flash_fw(self, filepath, slaveid=0):
        num_slaves = self.slaves()
        print('Found %d slaves' % num_slaves)
        if num_slaves <= slaveid or num_slaves == 0:
            return False

        print("Set BOOT state...")
        # self.set_state("BOOT")
        if not self.set_state("BOOT"):
            return False

        time.sleep(0.1)
        print("Flash firmware...")
        if not self.foe_write(slaveid=slaveid, filepath=filepath):
            return False

        return True

    def upload(self, index, subindex, type=None, slaveid=0, error=False):
        _type = ""
        if isinstance(type, str):
            if type not in self.types_:
                raise ExceptionIgH("Type '{}' is not valid. These are valid types: {}", type, self.types_)

            _type = "--type {}".format(type)

        command = "sudo {} upload -p {} 0x{:0x} {} {}".format(ETHERCAT_PATH, slaveid, index, subindex, _type)

        if error:
            _err = subprocess.STDOUT
        else:
            _err = subprocess.DEVNULL

        output = subprocess.check_output(command, shell=True, stderr=_err)

        try:
            output = output.decode().strip()
        except UnicodeDecodeError:
            return output

        res = self.re_int_value.match(output)
        if res:
            # return Int value
            return int(res.group(2))
        res = self.re_float_value.match(output)
        if res:
            return float(res.group(1))
        return output

    def download(self, index, subindex, value, type=None, slaveid=0):
        _type = ""
        if isinstance(type, str):
            if type not in self.types_:
                raise ExceptionIgH("Type '{}' is not valid. These are valid types: {}", type, self.types_)

            _type = "--type {}".format(type)

        command = "sudo {} download -p {} 0x{:0x} {} {} {}".format(ETHERCAT_PATH, slaveid, index, subindex, value, _type)

        if subprocess.call(command, stdout=subprocess.DEVNULL, shell=True) == 1:
            return False
        return True
