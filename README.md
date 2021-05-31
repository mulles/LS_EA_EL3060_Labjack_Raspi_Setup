# LS_EA_EL3060_Labjack_Raspi_Setup

This Repository contains two things, 1.IaC and 2.SOC Algo:

1. Infrastucture to do and verify current and voltage measurements on the battery connected to the MPTT-HUS-1210: 
   
   This infrastructure resides in at least 4 physical locations (Sensors inside and outside of MPPT-HUS-1210, RaspberryPi, Linux-Server) and is implemented via infrastructure as code (IaC).
   
   The 2 sensor pairs, the one inside the MPPT-HUS-1210 the one outside are as follow: 
     - Shunt for current measurment combined with a resitance divider for voltage measurements digitalised by the interal 12 bit ADC of the STM32 uC onboard and exposed by LS.Thingset Serial Protocol. 
     - The current measurement are provided by an LEM LA55-P Hall Sensor combined with a resitance voltage divider and digitalized by Labjack-T7's 16bit ADC
   
   Future more the Electronic Load discharging the battery provides Ah, A and V via RS232 Serial interface to the PI. 
   
   On the PI their are 4 scripts running:
   
   1. measurement_Nucleo64Serial2Raspi2influxdb.py (Read A and V and general Info from MPPT-HUS-1210 and writes it to InfluxDB)
   2. measurement_Labjack2Raspi2influxdb.py (Reads A and V from sensors connected to LabjackT7 and writes it to influxDB) TODO Improve by changing the settings in AIN registers
   3. measurement_EA-EL-3060-2Serial2Raspi2Influxdb.py ( Reads Ah, A and V from the Electronic load the writes it to influxDB)
   4. TODO resides inside Ansible Raspberrypi-Provision_Raspi_PIO.yml file (Makes sure that WLAN automatically reconnects)
   
   
   COULDDO All scripts are written currently in Procedural Code Style, some may or should be refactored to FP Style. 

2. Algorithm to calculate the SOC: 
   
   In development reside in /Python/ExtendedKalmanFilter/Plett_BMStoolbox_SOC_Est_SPKF.py 
   Create virtual environement (venv) and install dependencies:
   python3 -m venv /path/to/new/virtual/environment (creat venv)
   source <venv>/bin/activate (active venv)
   pip3 install -r requirements.txt (install dependencies)
   
The Code is structure in files and folders as follows:  

/Ansible folder contains all Ansible Scripts to run for setting up the infrastucture: 
 -Raspberrypi-Provision_Raspi_PIO.yml (Configures Raspi an pulls the scripts from this Repo /Python folder (TODO write now manually copied, just systemd Service by Ansible).
 -Provision_PopOS_localhost.yml (configures my linux maschine to flash code on the STM32 onboard of MPPT-HUS-1210.
 -Provision_Uberspace_Influx.yml (configures a Linux-server (CentOS7) hosted by Uberspace.de running Influxdb (store the sensor data) and Grafana (to visualize the sensor data and do some simple caculations)  
 -hosts (tells you the IP adress of the machines which are to be configured)
 -ansible.cfg (the configuration for ansible used when running on my linux machine.)
 
 COULDDO use Ansible roles to stucture, modularize and abstract parts of Raspi and Uberspace provisioning.
 COULDDO automate Raspberry image building with docker image, instead of running ansible locally an raspberrypi. 

/Python folder contains all python scripts deployed and in developement: 

**WARNING** This repository is not meant to be fully Open Sources yet, because it contains sensible data: f.i. Password to Servers and databases. 
TODO Migrate this into an Ansible Vault

TODO link/combine this Repo with LATEX Master Thesis Doc.
COULDDO modularize this Repo into Ansible and Python Scripts at least  
 


