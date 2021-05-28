SOMANET Test Suite
==================

All modules to make successful and complete testing of SOMANET modules possible.

Even though this suite is written for Linux, at least the Elektronik Automation Power Supply Driver also runs under Windows.

Installation
------------

1) Install non-python tools (only Linux)
    ``sudo ./install.sh -a -m <MAC_OF_ETHERCAT_INTERFACE>``

    This will install:
        - IgH EtherCAT Master
        - UDEV rules for power supplies
        - LabJack driver and Kipling
        - SOEM EtherCAT Master
        - SII tool

    If one of these tools are already installed, the script will skip the installation
    and continue with the next tool.
    Call "-h" to show the help text.

2) Install python script
    ``python setup.py install``


Usage
-----

1. PSU
^^^^^^
Import module
"""""""""""""
``import somanet_test_suite as sts``

Create object
"""""""""""""
To connect to a specific PSU, you can call

Linux: ``psu = sts.PsuEA(comport='ttyACM0')`` or ``psu = sts.PsuEA(comport='usb-EA_Elektro-Automatik_PS_2042-10B_2815450332-if00')``

Windows: ``psu = sts.PsuEA(comport='COM1')`` or as com port description: ``psu = sts.PsuEA(comport='PS 2000 B')``

If you added the device rule and you connected only one PSU, there is no need to provide a device name:

``psu = sts.PsuEA()``

Also possible is:

``psu = sts.PsuEA(comport='ea-ps-20xx-xx-0')``

| If there is more then one PSU connected to the host, the script will connect to the first device found.
| It is also possible to take the S/N written on the back of the PSU and call:

``psu = sts.PsuEA(sn='0123456789')``

or to use the device designator:

``psu = sts.PsuEA(desi='PS 2142-10B')``


Dis/connect to power supply for controlling
"""""""""""""""""""""""""""""""""""""""""""
``psu.remote_on()``

``psu.remote_off()``

For multi output devices most functions provide an additional output argument:

``psu.remote_on(output_num=0)`` or ``psu.remote_on(output_num=1)``

| It's only necessary to call ``remote_on()``, when you want to control the PSU.
| If you just want to read device information, you don't need to.

Power on and off output
""""""""""""""""""""""""""
``psu.output_on()``

``psu.output_off()``

or

``psu.output_on(output_num=1)``

``psu.output_off(output_num=1)``

Set parameters
""""""""""""""""""""""""""
Arguments can be int or float.

``psu.set_voltage(24, output_num=0)``

``psu.set_current(0.5, output_num=0)``

``psu.set_ovp(30, output_num=0)``

``psu.set_ocp(8, output_num=0)``

The script will always set the maximum possible values in dependency of the nominal power.

| For example:
| Nominal power = 160 W
| When you set the voltage to 40 V, it's not possible to set a higher current than 4 A (=160W/40V),
| regardless of the maximum current output of the device.
| If you want to set a higher current, you must first reduce the voltage.

| Also this script treats voltage with a higher priority.
| It will decrease the current, if the maximum power is reached.
| For example:
| Nominal power = 160 W, set current = 10 A
| When you set the voltage to 32 V, it'll results in a maximum current of 5 A.


Get parameters
""""""""""""""""""""""""""
Return argument: float.

``psu.get_voltage(output_num=0)``

``psu.get_current(output_num=0)``

``psu.get_power(output_num=0)``

Maximum sampling rate is ~10 Hz.

Get status
"""""""""""""
Return argument: dictionary

``psu.get_status(update : bool)``

Dictionary contains following keys:

- 'output' (int)
- 'remote on' (bool)
- 'output on' (bool)
- 'controller state' ('CV', 'CC')
- 'tracking active' (bool)
- 'OVP activ' (bool)
- 'OCP activ' (bool)
- 'OPP activ' (bool)
- 'OTP activ' (bool)
- 'act voltage' (float)
- 'act current' (float)

Get device description
""""""""""""""""""""""""""
Return argument: tuple (name, SN)

``psu.get_device_description(update : bool)``


Close connection
""""""""""""""""""""""""""
To close the connection, call:

``psu.close()``

This will just stop the communication, the PSU outputs will remain in their current states.



2. SANSSOUCI - So(manet) Se(nsor) Si(mulator)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A framework to simulate different sensors (Hall, QEI, ...).
Currently only velocity is supported for Hall and QEI.

Preperation
""""""""""""""""""""""""""
What you need:
 - LabJack
 - SN75174 Differential Line Driver (for RS-422 communication and as level shifter 3.3V -> 5V)

Connection
""""""""""""""""""""""""""
See also: https://doc.synapticon.com/hardware/drive/drive_1000/d3/docs/index.html#encoder-port-1

+--------------+------------------+
| Pin SN75174  | Encoder/Labjack  |
+==============+==================+
| 1            | LJ: FIO0         |
+--------------+------------------+
| 2            | A+               |
+--------------+------------------+
| 3            | A-               |
+--------------+------------------+
| 4            | Connect with     |
|              | 10kOhm to Vcc    |
|              | or NC            |
+--------------+------------------+
| 5            | B-               |
+--------------+------------------+
| 6            | B+               |
+--------------+------------------+
| 7            | LJ: FIO01        |
+--------------+------------------+
| 8            | GND of LJ and    |
|              | Encoder          |
+--------------+------------------+
| 9            | LJ: FIO2         |
+--------------+------------------+
| 10           | I+               |
+--------------+------------------+
| 11           | I-               |
+--------------+------------------+
| 12           | Connect with     |
|              | 10kOhm to Vcc    |
|              | or NC            |
+--------------+------------------+
| 13           | N.C.             |
+--------------+------------------+
| 14           | N.C.             |
+--------------+------------------+
| 15           | N.C.             |
+--------------+------------------+
| 16           | Vcc (5V)         |
+--------------+------------------+

Usage
""""""""""""""""""""""""""

**Hall**

``sensor = Sanssouci(printer.write, 'HALL', pole_pairs=7)``

``sensor.set_velocity(20)``

**QEI**

``sensor = Sanssouci(printer.write, 'QEI', resolution=100)``

``sensor.set_velocity(20)``
