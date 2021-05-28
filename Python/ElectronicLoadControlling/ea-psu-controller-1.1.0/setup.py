import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ea-psu-controller",
    version="1.1.0",
    author="Henrik Strötgen",
    author_email="hstroetgen@synapticon.com",
    description="Controller for Elektro-Automatik power supplies",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='MIT',
    url="https://github.com/synapticon/somanet_test_suite/tree/master/psu",
    packages=setuptools.find_packages(),
    data_files=[('.', ['99-ea-psu.rules'])],
    install_requires=['pyserial >= 3.4'],
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows :: Windows 7",
        "Topic :: System :: Hardware :: Hardware Drivers",
    ),
    keywords=('power supply unit', 'psu')
)