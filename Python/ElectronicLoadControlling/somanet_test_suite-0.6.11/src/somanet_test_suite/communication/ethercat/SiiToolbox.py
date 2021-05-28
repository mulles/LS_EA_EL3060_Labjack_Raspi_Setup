# Access the SII of a attached drive

from . import EtherCATMaster
import time

class SiiToolbox(object):

    def __init__(self):
        self.ecatm = EtherCATMaster.EtherCATMaster()

    def open(self):
        self.ecatm.start()
        time.sleep(2) # wait two seconds until the device has settled

    def close(self):
        self.ecatm.stop()

    def read(self):
        sii = self.ecatm.sii_read()

    def write(self, slaveid=0, siifile=""):
        return self.ecatm.sii_write(slaveid=slaveid, filepath=siifile)
