import operator
import re

__version__ = "1.0.0"


# See the document located here for more details:
# https://docs.google.com/spreadsheets/d/1DtAyNrj-pb06BeFmqnnvaGMpWtoaywOvVG4DYrxqyuw
serial_validator = re.compile(r"\d{4}-\d\d-\d{7}-\d{4}")
serial_prototype_validator = re.compile(r"i\d{7}")
version_validator = re.compile(r"[A-Z]\.\d+")

# This exists to prevent typos. Update as necessary.
valid_board_descriptions = [
        "Drive 400",
        "Drive 1000",
        "Drive 2000",
        "Drive 50 Duo",
        "Core C2X",
        "Core C4X",
        "Com EtherCAT",
        "Com EtherNet",
        "Drive Circulo 700",
        "Drive Circulo 1800",
        "Core Circulo 700",
        "Core Circulo 1800",
        "Com NetX",
        "Com Serial",
        "Connector Module Circulo 700",
        "Connector Module Circulo 1800",
        "Safety Module",
        "Safe Motion Module Circulo 700",
        "Safe Motion Module Circulo 1800",
]


mac_address_oui = "40:49:8A"

class ExceptionHardwareDescription(Exception):
    pass

##################### DEPRECATED #######################

class BoardInfo:
    """
    Describe the board and give it a serial number
    >>> info = BoardInfo()
    >>> info.set_serial_number('1234-12-1234567-1817')
    >>> info.set_serial_number('124-12-1234567-1817')
    Traceback (most recent call last):
    ...
    ValueError: The serial number '124-12-1234567-1817' does not match the required format
    >>> info.set_serial_number('124a-12-1234567-1817')
    Traceback (most recent call last):
    ...
    ValueError: The serial number '124a-12-1234567-1817' does not match the required format
    >>> info.set_serial_number('12341212345671817')
    Traceback (most recent call last):
    ...
    ValueError: The serial number '12341212345671817' does not match the required format
    >>> info.set_description('Core C2X')
    >>> info.set_description('Drive1000')
    Traceback (most recent call last):
    ...
    ValueError: The description 'Drive1000' is not one of the approved strings.
    >>> info.set_revision("A3")
    Traceback (most recent call last):
    ...
    ValueError: The revision 'A3' does not match format <letter>.<digit>
    >>> info.set_revision('A.3')
    >>> str(info)
    'Core C2X revision A.3 with SN 1234-12-1234567-1817'
    """

    def __init__(self):
        self.description = ""
        self.serial_number = ""
        self.revision = ""

    def __str__(self):
        return self.description + " revision " + self.revision + " with SN " + self.serial_number

    def set_description(self, description):
        """
        Set description to one of the approved board descriptions.
        """
        if not description in valid_board_descriptions:
            raise ValueError("The description \'" + description \
                             + "\' is not one of the approved strings.")
        self.description = description

    def set_serial_number(self, serial_number):
        """
        Set the serial number in a format aaaa-bb-ccccccc-YYCW.
        """
        if not serial_validator.match(serial_number):
            raise ValueError("The serial number \'" + serial_number + "\' does not match the required format")

        self.serial_number = serial_number

    def set_revision(self, revision):
        """
        Set the revision in a format <leter>.<digit>
        """
        revision_validator = re.compile(r"[a-zA-Z]\.\d")
        if not revision_validator.match(revision):
            raise ValueError("The revision \'" + revision + "\' does not match format <letter>.<digit>")
        self.revision = revision

def string_12_bit(decimal_value):
    return "{:012x}".format(decimal_value)

class StackInfo:
    """
    Describe the entire stack, with MAC and serial numbers and board descriptions.

    A stack is composed of multiple boards.

    >>> info1 = BoardInfo()
    >>> info1.set_serial_number('1231-23-1234567-1234')
    >>> info1.set_description("Core C2X")
    >>> info1.set_revision("B.3")
    >>> info2 = BoardInfo()
    >>> info2.set_serial_number('3213-21-7654321-4321')
    >>> info2.set_description("Drive 1000")
    >>> info2.set_revision("D.3")
    >>> stack = StackInfo()
    >>> stack.set_stack_serial_number("0123-12-9876543-1817")
    >>> stack.set_stack_serial_number("0123-12-986543-1817")
    Traceback (most recent call last):
    ...
    ValueError: The serial number does not match the required format
    >>> stack.set_mac_address(0x9876abcd1234)
    >>> stack.add_board_info(info1)
    >>> stack.add_board_info(info2)
    >>> print(stack)
    MAC: 98:76:ab:cd:12:34
    Stack Serial: 0123-12-987654-1817
    Core C2X revision B.3 with SN 1231-23-123456-1234
    Drive 1000 revision D.3 with SN 3213-21-654321-4321
    """

    def __init__(self):
        """
        Initialize the class instance with default data.
        """
        self.mac_address = 0x000000000000
        self.stack_serial_number = ""
        self.boards = []

    def __str__(self):
        """
        String representation of the stack
        The set of boards is sorted by the description.
        """
        # NOTE: This may be inefficient, since the list must be sorted. Do we care? Probably not.
        mac = string_12_bit(self.mac_address)
        return "MAC: " + ":".join(mac[i:i + 2] for i in range(0, 12, 2)) + "\n" \
                                                                           "Stack Serial: " + self.stack_serial_number + '\n' \
               + "\n".join([str(info) for info in sorted(list(self.boards), key=operator.attrgetter('description'))])

    def set_mac_address(self, mac_address):
        """
        Set mac address in numerical format
        """
        if mac_address >> 24 != int(mac_address_oui.replace(':', ''), 16) and (mac_address & 0xffffffffffff) != 0:
            raise ValueError('The mac address "%d" does not match the required format' % mac_address)
        self.mac_address = mac_address

    def set_stack_serial_number(self, serial_number):
        """
        Set the serial number in a format aaaa-bb-ccccccc-YYCW.
        """
        if not serial_validator.match(serial_number):
            raise ValueError("The serial number does not match the required format")

        self.stack_serial_number = serial_number

    def add_board_info(self, board_info):
        """
        Add board info to the list of boards
        This does not check for duplicates.
        """
        self.boards.append(board_info)

##################### END DEPRECATED #######################

class ComponentInfo:
    """
    Describe the board and give it a serial number

    >>> info = ComponentInfo()
    >>> info.set_serial_number('1234-12-1234567-1817')
    >>> info.set_serial_number('124-12-1234567-1817')
    Traceback (most recent call last):
    ...
    ValueError: The serial number '124-12-1234567-1817' does not match the required format
    >>> info.set_serial_number('124a-12-1234567-1817')
    Traceback (most recent call last):
    ...
    ValueError: The serial number '124a-12-1234567-1817' does not match the required format
    >>> info.set_serial_number('12341212345671817')
    Traceback (most recent call last):
    ...
    ValueError: The serial number '12341212345671817' does not match the required format
    >>> info.set_name('Core C2X')
    >>> info.set_name('Drive1000')
    Traceback (most recent call last):
    ...
    ValueError: The description 'Drive1000' is not one of the approved strings.
    >>> info.set_version("A3")
    Traceback (most recent call last):
    ...
    ValueError: The revision 'A3' does not match format <letter>.<digit>
    >>> info.set_version('A.3')
    >>> str(info)
    'Core C2X revision A.3 with SN 1234-12-1234567-1817'
    """
    def __init__(self):
        self.name = ""
        self.serialNumber = ""
        self.version = ""

    def __str__(self):
        return "\t{} version {!r} with SN {!r}".format(self.name, self.version, self.serialNumber)

    def set_name(self, name):
        """
        Set description to one of the approved board descriptions.
        """
        # Since now a component can be everything, that test doesn't make sense anymore
        # if not name in valid_board_descriptions:
        #     raise ExceptionHardwareDescription("The description \'" + name \
        #                                        + "\' is not one of the approved strings.")
        if not isinstance(name, str):
            raise ExceptionHardwareDescription("Name is not a string: {} ({})".format(name, type(name)))

        self.name = name
    
    def set_serial_number(self, serial_number):
        """
        Set the serial number in a format aaaa-bb-ccccccc-YYCW.
        """
        # if not serial_validator.match(serial_number):
        #     raise ExceptionHardwareDescription("The serial number \'" + serial_number + "\' does not match the required format")
        if not isinstance(serial_number, str):
            raise ExceptionHardwareDescription("serial_number is not a string: {} ({})".format(serial_number, type(serial_number)))

        self.serialNumber = serial_number

    def set_version(self, version):
        """
        Set the revision in a format <leter>.<digit>
        """
        if not isinstance(version, str):
            raise ExceptionHardwareDescription("Version is not a string: {} ({})".format(version, type(version)))

        if not version_validator.match(version) and version != '':
            raise ExceptionHardwareDescription("The revision {!r} does not match format <letter>.<digit>".format(version))
        self.version = version


class AssemblyInfo:
    """
    Describe the entire stack, with MAC and serial numbers and board descriptions.
    
    A stack is composed of multiple boards.
    
    >>> info1 = ComponentInfo()
    >>> info1.set_serial_number('1231-23-1234567-1234')
    >>> info1.set_name("Core C2X")
    >>> info1.set_version("B.3")
    >>> info2 = ComponentInfo()
    >>> info2.set_serial_number('3213-21-7654321-4321')
    >>> info2.set_name("Drive 1000")
    >>> info2.set_version("D.3")
    >>> stack = AssemblyInfo()
    >>> stack.set_serial_number("0123-12-9876543-1817")
    >>> stack.set_serial_number("0123-12-986543-1817")
    Traceback (most recent call last):
    ...
    ValueError: The serial number does not match the required format
    >>> stack.add_component(info1)
    >>> stack.add_component(info2)
    >>> print(stack)
    MAC: 98:76:ab:cd:12:34
    Stack Serial: 0123-12-987654-1817
    Core C2X revision B.3 with SN 1231-23-123456-1234
    Drive 1000 revision D.3 with SN 3213-21-654321-4321
    """
    def __init__(self):
        """
        Initialize the class instance with default data.
        """
        self.serialNumber = ""
        self.name = ""
        self.id = ""
        self.version = ""

    def _get_assembly_str_repr(self):
        comp_str = ""
        if hasattr(self, 'components'):
            comp_str = "\n".join([str(info) for info in sorted(list(self.components), key=operator.attrgetter('name'))])

        return "\t{} version {!r}, ID {!r} with SN {!r}\n{}".format(self.name, self.version, self.id, self.serialNumber, comp_str)

    def __str__(self):
        """
        String representation of the stack

        The set of boards is sorted by the description.
        """
        # NOTE: This may be inefficient, since the list must be sorted. Do we care? Probably not.
        return self._get_assembly_str_repr()

    def set_serial_number(self, serial_number):
        """
        Set the serial number in a format aaaa-bb-ccccccc-YYCW.
        """
        if not ( serial_validator.match(serial_number) or serial_prototype_validator.match(serial_number) ):
            raise ExceptionHardwareDescription('The serial number {!r} does not match the required format'.format(serial_number))

        self.serialNumber = serial_number

    def add_component(self, component_info):
        """
        Add board info to the list of boards

        This does not check for duplicates.
        """
        if not hasattr(self, 'components'):
            self.components = []
        self.components.append(component_info)

    def set_id(self, id_):
        if isinstance(id_, int):
            self.id = '{:04}'.format(id_)
        else:
            self.id = id_

    def set_version(self, version):
        try:
            version = int(version)
        except ValueError as e:
            raise ExceptionHardwareDescription("AssemblyInfo.set_version(): Version number is not an integer")
        self.version = '{:02}'.format(version)

    def set_name(self, name):
        if not isinstance(name, str):
            raise ExceptionHardwareDescription("Name is not a string: {} ({})".format(name, type(name)))

        self.name = name


class DeviceInfo(AssemblyInfo):

    def __init__(self):
        self.macAddress = ""

        super().__init__()

    def __str__(self):
        return "\tMAC: {}\n{}".format(self.macAddress, self._get_assembly_str_repr())

    def set_mac_address(self, mac_address):
        """
        Set mac address in numerical format
        """
        if isinstance(mac_address, int):
            mac_address = "{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}".format(
                mac_address >> 40 & 0xff, mac_address >> 32 & 0xff, mac_address >> 24 & 0xff, mac_address >> 16 & 0xff,
                mac_address >> 8 & 0xff, mac_address & 0xff,
            )

        mac_address = mac_address.replace('-', ':')
        if not mac_address.lower().startswith(mac_address_oui.lower()) or len(mac_address) < 17:
                raise ExceptionHardwareDescription("DeviceInfo.set_mac_address(): The mac address '{}' does not match the required format".format(mac_address))

        self.macAddress = mac_address


class HardwareDescription:

    def __init__(self):
        self.fileVersion = __version__

    def __str__(self):
        ass_str = ""
        if hasattr(self, 'assembly'):
            ass_str = "assembly:\n{}\n".format(self.assembly)

        return "fileVersion: {}\n{}device:\n{}\n".format(self.fileVersion, ass_str, self.device)

    def set_assembly(self, assembly):
        self.assembly = assembly

    def set_device(self, device):
        self.device = device


if __name__ == "__main__":
    # If this file is run directly, the tests are executed.

    import doctest
    doctest.testmod()


