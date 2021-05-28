
import paho.mqtt.subscribe as subscribe
from cbor2 import dumps, loads
import requests

mqtt_host = "awesome-librarian-01.cloudmqtt.com"
mqtt_topic = "v1/node2server/report/+"
mqtt_user = "xxx"
mqtt_pass = "xxx"

influx_org = 'xxx'
influx_bucket = 'emblem'
influx_token = 'xxx'
influx_url = f'https://influxdb.libre.solar/api/v2/write?org={influx_org}&bucket={influx_bucket}&precision=s'

#node_id_map = {
#    0x1B: 'HardwareVersion',
#    0x1C: 'FirmwareVersion',
#    0x01: 'Timestamp_s',
#    0x02: 'LoadInfo',
#    0x03: 'UsbInfo',
#    0x06: 'SOC_pct',
#    0x70: 'Bat_V',
#    0x71: 'Solar_V',
#    0x74: 'Int_degC',
#    0x78: 'ChgState',
#    0x7E: 'Solar_W',
#    0x7F: 'Load_W',
#    0x80: 'RSSI_dB',
#    0x82: 'Grid_V',
#    0x83: 'Grid_A',
#    0x84: 'Grid_W',
#    0x85: 'GridInfo',
#    0x90: 'ErrorFlags',
#    0x08: 'SolarInTotal_Wh',
#    0x09: 'LoadOutTotal_Wh',
#    0x120: 'SolarInTotal_mWh',
#    0x121: 'LoadOutTotal_mWh',
#    0xA7: 'GridImportTotal_mWh',
#    0xA8: 'GridExportTotal_mWh',
#    0xBA: 'CommErrorFlags',
#    0x0A: 'BatChgTotal_Wh',
#    0x0B: 'BatDisTotal_Wh',
#    0x0C: 'FullChgCount',
#    0x0D: 'DeepDisCount',
#    0x0E: 'BatUsable_Ah',
#}

while True:

    msg = subscribe.simple(mqtt_topic, qos=1, msg_count=1, retained=False, hostname=mqtt_host,
    port=1883, client_id="", keepalive=60, auth={'username':mqtt_user, 'password':mqtt_pass})

    #print("%s %s" % (msg.topic, msg.payload))
    print("Received: %s" % msg.topic)

    device_id = msg.topic.split('/')[3]

    obj = loads(msg.payload[1:])

    data = ""

    for key in obj:
        try:
            #print (key, '(', node_id_map[key], ') =', obj[key])
            data_name = node_id_map[key]
            name_unit = data_name.split('_')
            if len(name_unit) > 1:
                data += f"{name_unit[1]},device={device_id} {name_unit[0]}={obj[key]}\n"
            else:
                if type(obj[key]) == str:
                    data += f'{name_unit[0]},device={device_id} {name_unit[0]}="{obj[key]}"\n'
                else:
                    data += f'{name_unit[0]},device={device_id} {name_unit[0]}={obj[key]}\n'
        except: # KeyError and possibly others
            print('Error: Key %s ignored' % key)

    headers = {'Authorization': 'Token %s' % influx_token}

    print(data)

    #r = requests.post(influx_url, headers=headers, data=data)
    #print(r)

