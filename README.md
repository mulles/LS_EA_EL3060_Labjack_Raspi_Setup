# Battery SoC algorithm development and testing laboratory infrastucture 


**Infrastucture to charge and discharge a battery connected to the charge controller [MPTT-HUS-1210](https://github.com/LibreSolar/mppt-1210-hus), while monitoring current and voltage:**


![SoC_Setup](https://user-images.githubusercontent.com/13488510/139695457-870b3181-8af0-4463-a811-158720de3773.png)


![IMG_20210402_150654](https://user-images.githubusercontent.com/13488510/139695525-7b8c8207-56b0-46ea-a0fc-d6cb0fe3aa57.jpg)


This infrastructure resides in 2 physical locations (Sensors inside and outside of MPPT-HUS-1210 + Nucleo + RaspberryPi and Linux-Server in FrankfurtMain Datascenter) and is implemented via infrastructure as code (IaC). On the Linux server the time series database software **influxdb** and visualisation software **grafana** are reproducibly deployed with Ansible. 
   
   The Lab setup consists of 2 sensor pairs, one inside the MPPT-HUS-1210 and one outside: 
     - Shunt for current measurment combined with a resitance divider for voltage measurements digitalised by the interal 12 bit ADC of the STM32 uC, exposed by LS.Thingset Serial Protocol to the PI over USB. 
     - Outside, the current measurement is provided by a LEM LA55-P Hall Sensor and the voltage by a resitance voltage divider and digitalized and exposed via USB to the PI, by Labjack-T7's 16bit ADC
   
   Further more the Electronic Load (EA_EL3060) discharging the battery provides Ah, A and V via RS232 Serial over USB interface to the PI. 
   
   On the PI there are 4 scripts running:
   
   1. measurement_Nucleo64Serial2Raspi2influxdb.py (Read A and V and general Info from MPPT-HUS-1210 and writes it to InfluxDB)
   2. measurement_Labjack2Raspi2influxdb.py (Reads A and V from sensors connected to LabjackT7 and writes it to influxDB) TODO Improve by changing the settings in AIN registers
   3. measurement_EA-EL-3060-2Serial2Raspi2Influxdb.py ( Reads Ah, A and V from the Electronic load the writes it to influxDB)
   4. TODO resides inside Ansible Raspberrypi-Provision_Raspi_PIO.yml file (Makes sure that WLAN automatically reconnects)
   
   
   COULDDO All scripts are written currently in Procedural Code Style, some may or should be refactored to FP Style. 

[**Algorithm to calculate the SoC: ( moved to  https://github.com/mulles/kalman-soc/)** 
   
   TODO remove this section
   In development reside in /Python/ExtendedKalmanFilter/Plett_BMStoolbox_SOC_Est_SPKF.py 
   Create virtual environement (venv) and install dependencies:
   python3 -m venv /path/to/new/virtual/environment (creat venv)
   source <venv>/bin/activate (active venv)
   pip3 install -r requirements.txt (install dependencies) ]
   
**The Repository is structure in files and folders as follows:**

/Ansible folder contains all Ansible Scripts to run for setting up the infrastucture: 
   
 -Raspberrypi-Provision_Raspi_PIO.yml (Configures Raspi an pulls the scripts from this Repo /Python folder (TODO write now manually copied, just systemd Service     by Ansible).  
 -Provision_PopOS_localhost.yml (configures my linux maschine to flash code on the STM32 onboard of MPPT-HUS-1210.  
 -Provision_Uberspace_Influx.yml (configures a Linux-server (CentOS7) hosted by Uberspace.de running Influxdb (store the sensor data) and Grafana (to visualize     the sensor data and do some simple caculations)    
 -hosts (tells you the IP adress of the machines which are to be configured)  
 -ansible.cfg (the configuration for ansible used when running on my linux machine.)  
 
 COULDDO use Ansible roles to stucture, modularize and abstract parts of Raspi and Uberspace provisioning.  
 COULDDO automate Raspberry image building with docker image, instead of running ansible locally an raspberrypi.     

/Python folder contains all python scripts deployed and in developement (TODO remove)  

**WARNING** This repository is not meant to be fully Open Sources yet, because it contains sensible data: f.i. Password to Servers and databases. 
