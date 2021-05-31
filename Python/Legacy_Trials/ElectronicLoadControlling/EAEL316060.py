from  ea_psu_controller import PsuEA

print("It simple works and prints Hello")


psu = PsuEA(comport='ttyUSB0')
print(psu.get_status())
# psu.remote_on()
# psu = PsuEA()
# psu.set_current(0.5)  
