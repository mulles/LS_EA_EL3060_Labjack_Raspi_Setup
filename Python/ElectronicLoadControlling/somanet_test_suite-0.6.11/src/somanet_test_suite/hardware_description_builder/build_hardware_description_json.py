import json
import time
import logging

from .dataformat import *
from ..communication.ethercat.EtherCATMaster import EtherCATMaster

logger = logging.getLogger(__file__)

##################### DEPRECATED #######################

class JSONInfo:
    file_name = 'stack_info.json'

    def __init__(self, mac='', stack_serial='', *args):
        self.mac = mac
        self.stack_serial = stack_serial
        self.board_list = args
        self.ecat = EtherCATMaster()

    def generate(self, skip_flash=False, timestamp=None):

        # Create a new stack
        stack = StackInfo()
        # Take the MAC address from the input arguments
        if self.mac != '':
            self.mac = self.mac.replace(':', '')
            self.mac = self.mac.replace('-', '')
            stack.set_mac_address(int(self.mac, 16))
        # Add the stack serial number
        if self.stack_serial != '':
            stack.set_stack_serial_number(self.stack_serial)

        # Collect all the board infos and add them to the stack
        try:
            for arg_board in self.board_list:
                board = BoardInfo()
                board.set_description(arg_board[0])
                board.set_revision(arg_board[1])
                board.set_serial_number(arg_board[2])
                stack.add_board_info(board)
        except ValueError as e:
            logger.error(e)
            return False

        # Log the results of the stack_info file.
        lines = str(stack).split('\n')
        for line in lines: logger.info(line)
        logger.info(json.dumps(stack, ensure_ascii=False, default=lambda o: o.__dict__))

        if timestamp:
            self.file_name += '_' + timestamp

        # Write to a file
        with open(self.file_name, 'w') as stack_info_file:
            json_file = json.dumps(stack, ensure_ascii=False, default=lambda o: o.__dict__)
            stack_info_file.write(json_file)

        # Flash the stack_info.json file to the flash memory of the Core board.
        if not skip_flash:
            # Write this to flash using a private bootloader method
            try:
                if not self.ecat.is_active():
                    self.ecat.start()
                    time.sleep(2)
                if not self.ecat.set_state('BOOT'):
                    raise Exception('Set slave to state BOOT failed')
                time.sleep(0.1)
                if not self.ecat.foe_read(cmd='fs-stackunlock=DD1317'):
                    raise Exception('Unlock stack failed')
                time.sleep(0.1)
                if not self.ecat.foe_write(filepath=self.file_name):
                    raise Exception('Writing file failed')
                time.sleep(0.1)
                read_json = self.ecat.foe_read(cmd=self.file_name, output=True)
                if read_json != json_file:
                    raise Exception('Files doesn\'t match')
            except Exception as e:
                logger.error(e)
                logger.error("The file was not successfully flashed to the stack.")
                return False
        else:
            logger.warning("The file was created but not flashed to the board. Remove the --skip_flash argument if you want that.")
        return True


##################### END DEPRECATED #######################


class BuildHardwareDescription:
    file_name = '.hardware_description'

    def __init__(self):
        self.device = None
        self.assembly = None
        self.json_content = ''
        self.ecat = EtherCATMaster()

    def __generate_component(self, components):
        comp = ComponentInfo()
        comp.set_name(components[0])
        comp.set_version(components[1])
        comp.set_serial_number(components[2])
        return comp

    def __set_info(self, type, name, id, version, sn, components):
        type.set_name(name)
        type.set_id(id)
        type.set_version(version)
        type.set_serial_number(sn)
        if components:
            for c in components:
                type.add_component(self.__generate_component(c))

    def set_device(self, name, id, version, sn, components, mac=None):
        try:
            self.device = DeviceInfo()
            if mac:
                self.device.set_mac_address(mac)
            self.__set_info(self.device, name, id, version, sn, components)
        except ExceptionHardwareDescription as e:
            logger.error(e)
            return False
        return True

    def set_assembly(self, name, id, version, sn, components=None):
        try:
            self.assembly = AssemblyInfo()
            self.__set_info(self.assembly, name, id, version, sn, components)
        except ExceptionHardwareDescription as e:
            logger.error(e)
            return False
        return True

    def generate(self, timestamp=None, write_file=True):
        # Create a new stack
        hw = HardwareDescription()
        hw.set_device(self.device)
        if self.assembly:
            hw.set_assembly(self.assembly)

        # Log the results of the stack_info file.
        lines = str(hw).split('\n')

        for line in lines:
            logger.info(line)

        self.json_content = json.dumps(hw, ensure_ascii=False, default=lambda o: o.__dict__)
        logger.info(self.json_content)

        if not write_file:
            return self.json_content

        if timestamp:
            self.file_name += '_' + timestamp
        # Write to a file
        with open(self.file_name, 'w') as hardware_description_file:
            hardware_description_file.write(self.json_content)

    def flash(self):
        # Write this to flash using a private bootloader method
        try:
            if not self.ecat.is_active():
                self.ecat.start()
                time.sleep(2)
            if not self.ecat.set_state('BOOT'):
                raise Exception('Set slave to state BOOT failed')
            time.sleep(0.1)
            if not self.ecat.foe_read(cmd='fs-stackunlock=DD1317'):
                raise Exception('Unlock stack failed')
            time.sleep(0.1)
            if not self.ecat.foe_write(filepath=self.file_name):
                raise Exception('Writing file failed')
            time.sleep(0.1)
            read_json = self.ecat.foe_read(cmd=self.file_name, output=True)
            if read_json != self.json_content:
                print(read_json)
                print(self.json_content)
                raise Exception('Files doesn\'t match')
        except Exception as e:
            logger.error(e)
            logger.error("The file was not successfully flashed to the stack.")
            return False
        return True
