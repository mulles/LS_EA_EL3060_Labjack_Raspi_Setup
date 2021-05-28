#!/bin/bash

REPO_ETHERCAT="https://github.com/synapticon/Etherlab_EtherCAT_Master"
REPO_SIITOOL="https://github.com/synapticon/siitool"
REPO_SOEM="https://github.com/OpenEtherCATsociety/SOEM"
LJM_FILE_URL="https://labjack.com/sites/default/files/software/"

LJM_SOFTWARE="labjack_ljm_software_2019_07_16_x86_64"

help() {
  echo "Help:"
  echo "-a - Install all"
  echo "-m MAC - MAC address of your interface for IgH"
  echo "-i NAME - <NAME> can be 'igh', 'labjack', 'siitool', 'soem' or 'psu'"
  echo "-h - Show this help"
  exit 0
}

install_soem() {
  echo "-> Install SOEM"
  git clone ${REPO_SOEM}
  cd SOEM || exit 1
  mkdir build
  cd build || exit 1
  cmake ..
  make
  make install
  cd ../..
  rm -r SOEM
}

install_ljm() {
  echo "-> Install LJM"
  URL=${LJM_FILE_URL}${LJM_SOFTWARE}".tar.gz"
  echo "-> Download LJM driver"
  wget ${URL}
  tar xf ${LJM_SOFTWARE}".tar.gz"
  cd ${LJM_SOFTWARE} || exit 1
  ./labjack_ljm_installer.run
  cd ..
  rm -r ${LJM_SOFTWARE}
  rm ${LJM_SOFTWARE}".tar.gz"
}

install_igh() {
  echo "-> Install Igh"
  git clone ${REPO_ETHERCAT}
  cd Etherlab_EtherCAT_Master/sncn_installer || exit 1
  ./install.sh ${MAC}
  cd ../..
  rm -r Etherlab_EtherCAT_Master
}

install_siitool() {
  echo "-> Install SII Tool"
  apt install libxml2-dev
  git clone ${REPO_SIITOOL}
  cd siitool || exit 1
  make
  make install
  cd ..
  rm -r siitool
}

install_psu() {
  echo "-> Install UDEV rules"
  cp src/somanet_test_suite/psu/99-ea-psu.rules /etc/udev/rules.d
  udevadm control --reload-rules
  udevadm trigger --subsystem-match=tty --attr-match=idVendor=232e --action=add
  echo "-> Add user ${SUDO_USER} to group dialout"
  adduser $SUDO_USER dialout
}

if [[ $EUID -ne 0 ]]
then
   echo "This script must be run as root"
   exit 1
fi

while getopts "am:i:h" option
do
  # shellcheck disable=SC2220
  case "${option}"
    in
    a) ALL=1;;
    m) MAC=${OPTARG};;
    i) INSTALL_THIS=${OPTARG};;
    h) help;;
  esac
done

# Install IgH
which ethercat > /dev/null
if [[ ! -z ${ALL} || "${INSTALL_THIS}" == "igh" || $? -ne 0 ]]
then
  if [ ! -z ${MAC} ]
  then
    install_igh
  elif [ $? -eq 0 ]
  then
    echo "IgH is already installed"
  else
    echo
    echo "No MAC address. Skip IgH installment"
    echo
  fi
fi

# Install LJM / Kipling
which "labjack_kipling"  > /dev/null
if [[ ! -z ${ALL} ||  "${INSTALL_THIS}" == "labjack"  ||  $? -ne 0 ]]
then
  echo "install labjack"
  install_ljm
elif [ $? -eq 0 ]
then
  echo "LJM / Kipling is already installed"
fi

# Install SII Tool
which "siitool" > /dev/null

if [[ ! -z ${ALL} || "${INSTALL_THIS}" == "siitool" || $? -ne 0 ]]
then
  install_siitool
elif [ $? -eq 0 ]
then
  echo "SII Tool already installed"
fi

# Install SOEM
which "eepromtool" > /dev/null
if [[ ! -z ${ALL} || "${INSTALL_THIS}" == "soem" || $? -ne 0 ]]
then
  install_soem
elif [ $? -eq 0 ]
then
  echo "SOEM already installed"
fi

if [[ ! -z ${ALL} || "${INSTALL_THIS}" == "psu" || $? -ne 0 ]]
then
  install_psu
fi
