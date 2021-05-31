import re
import sys
import os
from subprocess import call

import setuptools
from setuptools.command.install import install

package_to_install = [
        'somanet_test_suite',
        'somanet_test_suite.daq',
        'somanet_test_suite.psu',
        'somanet_test_suite.communication',
        'somanet_test_suite.communication.ethercat',
        'somanet_test_suite.communication.uart',
        'somanet_test_suite.sanssouci',
        'somanet_test_suite.hardware_description_builder',
    ]

with open('src/somanet_test_suite/__init__.py', 'r') as f:
    version_file = f.read()
    version = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M).group(1)

if os.path.isfile('requirements.txt'):
    with open('requirements.txt', 'r') as f:
        requirements = f.read().splitlines()
else:
    requirements = ""

with open("README.rst", "r") as f:
    long_description = f.read()

def install_requirements(requirements):
    for r in requirements:
        call([sys.executable, '-m', 'pip', 'install', r])

class Install_EOL(install):
    def run(self):
        install_requirements(requirements)
        install.run(self)

setuptools.setup(
    name='somanet_test_suite',
    version=version,
    package_dir={'':'src'},
    packages=package_to_install,
    install_requires=requirements,
    license='MIT',
    author='Synapticon GmbH',
    author_email='hstroetgen@synapticon.com',
    description="A collection of different scripts and drivers (PSU, EtherCAT, Labjack,...)",
    long_description=long_description,
    cmdclass={
        'install': Install_EOL
    },
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Operating System :: POSIX :: Linux',
    ],
    keywords=('power supply unit', 'psu', 'daq', 'Labjack', 'Elektronik-Automation', 'EtherCAT', 'IgH', 'Synapticon'),
    scripts=['src/somanet_test_suite/hardware_description_builder/somanet_hw_description_builder']
)
