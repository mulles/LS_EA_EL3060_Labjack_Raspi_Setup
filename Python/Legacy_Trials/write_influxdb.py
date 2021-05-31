import requests
import time
import random

influx_org = 'LibreSolar'
influx_bucket = 'LabjackCurrentVoltage'
influx_token = '6O3aUzQNynIPhh1jwlNukYU1gx5Z2fJZNehpANlNl1rTtLsSW2Acm2rFE3mO81l2Fq_Nl8lyhqajg5ivOAzrvA=='
influx_url = f'https://influxdb.lsserver.uber.space/api/v2/write?org={influx_org}&bucket={influx_bucket}&precision=s'

device_id = 470023670


data = ""
headers = {'Authorization': 'Token %s' % influx_token}

start_time = time.time()
interval = 1
for i in range(3000):
    time.sleep(1 - time.monotonic() % 1) 
    #https://stackoverflow.com/questions/10813195/run-a-python-function-every-second
    i += i
    data = f'V,device={device_id} Bat={random.randint(120,143)/9.99}\n'
    print(data)
    r = requests.post(influx_url, headers=headers, data=data)
    print(r)    

#Format of Influx Line Protocol: https://www.youtube.com/watch?v=qqC-cco8GXM
