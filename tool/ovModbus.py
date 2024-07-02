#                                                  #
#      ovNodbus.py  Modbus Analyzer and Output     #
#                                                  #
#      Copyright 2023 MiSc                         #
#      Shout-out to "final"                        #
#                                                  #
#      This code is licensed under the GPL         #
#                                                  #

import json
import re
import argparse
import pymodbus.client as modbusClient
from pymodbus.exceptions import ModbusIOException
from slugify import slugify

# Define constants
METHOD_TCP = 'TCP'
METHOD_RTU = 'RTU'

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 502

DEFAULT_COMPORT = '/dev/ttyUSB0'
DEFAULT_BAUDRATE = 19200
DEFAULT_PARITY = 'E'
DEFAULT_STOPBITS = 1

DEFAULT_SLAVE = 247
DEFAULT_START_ADDRESS = 12288
DEFAULT_STOP_ADDRESS = 18408
DEFAULT_LANG = 'default'

JSON_UNITS = 'ovUnits.json'
JSON_DESCRIPTOR = 'ovDescriptor.json'
JSON_TYPEMAP = 'ovTypeMap.json'

HASS_MODBUS_NAME = 'ovum_modbus'

# Create YAML for Home Assistant with all sensors based on modbus
def get_hass_modbustcp_def(data):
    config_string = f"""modbus:
    - name: "modbus_ovum"
      type: tcp
      host: {data['host']}
      port: {data['port']}
      delay: 2
      message_wait_milliseconds: 0
      timeout: 5
      sensors:"""
    return (config_string)

def get_hass_modbusrtu_def(data):
    config_string = f"""modbus:
    - name: "modbus_ovum"
      type: serial
      port: {data['comport']}
      baudrate: {data['baudrate']}
      bytesize: 8
      method: rtu
      parity: {data['parity']}
      stopbits: {data['stopbits']}      
      sensors:"""
    return (config_string)

def get_hass_sensor_def(data):
    sensor_string = f"""
        - name: "{data['description']}"         
          unique_id: ovum_{data['parameter']}_sensor{data['address']}
          address: {data['address']}
          scan_interval: 15                
          data_type: int32
          scale: {data['scale']}
          precision: {data['precision']}
          swap: word
          unit_of_measurement: "{data['unit']}"
          input_type: holding
          min_value: {data['min_val'] if int(data['precision']) == 0 else float(data['min_val']) / (10 ** int(data['precision']))}
          max_value: {data['max_val'] if int(data['precision']) == 0 else float(data['max_val']) / (10 ** int(data['precision']))}
          slave: {data['slave']}                    
          {data['device_class']}"""
    return f"{sensor_string}"

def get_hass_templatesensor_def(data):
    sensor_string = f"""
        - sensor:
            - name: "{data['description']} tmpl"
              unique_id: ovum_{data['parameter']}_sensor{data['address']}_tmpl            
              device_class: enum
              availability: "{{{{ states('sensor.{data['sensor']}')|int in [{data['range']}] }}}}"
              state: >
                {{% set mapper =  {{
                    {data['map']} }} %}}            
                {{% set state = states('sensor.{data['sensor']}') %}}
                {{{{ mapper[state] if state in mapper}}}}"""
    return f"{sensor_string}"

# Load JSON
def load_json(filename):
    try:
        with open(filename, "r", encoding='UTF-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f'Error: {filename} file not found')
        return {}

def save_output(filename, content, init=False):
    try:
        mode = "w" if init else "a"
        with open(filename, mode, encoding='UTF-8') as file:
            file.write(content)
    except PermissionError:
        print(f"Error: You do not have permission to write to '{filename}'.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def generate_output(output):
    if args.output != None:
        save_output(args.output, f"{output}\n")
    else:
        print(output)

# Initial Setup, call-arguments, load json-files
def init_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('method', type=str, default=METHOD_TCP, help='How to connect: TCP or RTU')
    parser.add_argument('slave', type=int, default=DEFAULT_SLAVE, help='The Modbus-Address (Slave)')
    parser.add_argument('--host', type=str, default=DEFAULT_HOST, help='The IP address of the Modbus TCP host')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='The TCP-Port of the Modbus TCP host')
    parser.add_argument('--comport', type=str, default=DEFAULT_COMPORT, help='The COM Port Device')
    parser.add_argument('--baudrate', type=int, default=DEFAULT_BAUDRATE, help='Baudrate for RTU Connection')
    parser.add_argument('--parity', type=str, default=DEFAULT_PARITY, help='Parity for RTU Connection')
    parser.add_argument('--stopbits', type=int, default=DEFAULT_STOPBITS, help='Stopbits for RTU Connection')
    parser.add_argument('--lang', type=str, default=DEFAULT_LANG, help='Language Selector (de, en, ...)')
    parser.add_argument('--start_address', type=int, default=DEFAULT_START_ADDRESS, help='Start address of the register')
    parser.add_argument('--stop_address', type=int, default=DEFAULT_STOP_ADDRESS, help='Stop address of the register')
    parser.add_argument('--dump', action='store_true', help='Loop through addresses and dump content')
    parser.add_argument('--csv', action='store_true', help='Output is in CSV-Format')
    parser.add_argument('--hass', action='store_true', help='Create Home Assistant YAML for sensors')
    parser.add_argument('--min', action='store_true', help='Create minimal output')
    parser.add_argument('--noerror', action='store_true', help='Skip addresses with error and do not print')
    parser.add_argument('--output', type=str, default=None, help='Write output to a file')
    parser.add_argument('--dev', action='store_true', help='Debugging and test parameter')
    return parser

# Connect to Modbus TCP
def connect_to_modbusTCP(host, port):
    client = modbusClient.ModbusTcpClient(host=host, port=port)
    try:
        client.connect()
        return client, client.is_socket_open()
    except ModbusIOException as e:
        print(f"Failed to connect to tcp host: {host}")
        print("Error:", e)
        return None, False

# Connect to Modbus RTU
def connect_to_modbusRTU(comport, baudrate, parity, stopbits):
    client = modbusClient.ModbusSerialClient(port=comport, baudrate=baudrate, parity=parity, stopbits=stopbits)
    try:
        client.connect()
        return client, client.is_socket_open()
    except ModbusIOException as e:
        print(f"Failed to connect to rtu port: {comport}")
        print("Error:", e)
        return None, False

# Add Space after (n) characters
def format_space(input_string, n):
    result = ' '.join([input_string[i:i + n] for i in range(0, len(input_string), n)])
    return result.strip()

def read_register(address, count, slave):
    response = []
    try:
        register_content = client.read_holding_registers(address, count, slave)
        if register_content.isError():
            return response, True
        else:
            for i in range(0, len(register_content.registers)):
                hex = format(register_content.registers[i], '04X')
                dec_unsigned = int(hex, 16)
                if dec_unsigned & 0x8000:
                    dec_signed = -((dec_unsigned^0xFFFF)+1)
                else:
                    dec_signed = dec_unsigned
                byte1 = int(hex[:2], 16)
                byte2 = int(hex[-2:], 16)
                char1 = chr(byte1) if (31 < byte1 < 127) and (31 < byte2 < 127) else ""
                char2 = chr(byte2) if (31 < byte1 < 127) and (31 < byte2 < 127) else ""
                bin = format(register_content.registers[i], '016b')
                address_dec = address+i
                data = {"address_hex": f"{address_dec:#0{6}x}", "address": f"{address +i}", "hex": f"{hex}", "byte1": f"{byte1}", "byte2": f"{byte2}", "UInt16": f"{dec_unsigned}", "Int16": f"{dec_signed}", "char1": f"{char1}", "char2": f"{char2}", "bin": f"{bin}"}
                response.append(data)
            return response, False
    except ModbusIOException as e:
        return response, True

def generateRegisterDump(start_address, stop_address, slave, separator, noerror):
    header_titles = ["Idx", "AddrHex", "AddrDec", "Hex", "Byte_1", "Byte_2", "UInt16", "Int16", "Chr", "Bin"]
    read_count = 1
    idx = start_address
    generate_output(separator.join(header_titles))
    while idx <= stop_address:
        response, error = read_register(idx, read_count, slave)
        if not error:
            data = [f"{idx-start_address}", f"{response[0]['address_hex']}", f"{response[0]['address']}", f"{format_space(response[0]['hex'],2)}", f"{response[0]['byte1']}", f"{response[0]['byte2']}", f"{response[0]['UInt16']}", f"{response[0]['Int16']}", f"{response[0]['char1']}{response[0]['char2']}",f"{format_space(response[0]['bin'],4)}"]
        else:
            data = [f"{idx}"]
            for _ in range(1, len(header_titles)): data.append("#err")
        if not (error and noerror):
          generate_output(separator.join(data))
        idx += read_count

def generateOvumDump(start_address, stop_address, slave, separator, lang, min, noerror):
    header_titles = ["AddrHex", "AddrDec", "Param", "Int32", "Prec", "Value", "Unit", "UnitID", "MultiID", "MinVal", "MaxVal", "ReadOnly", "isMenu", "DescID", "Desc"]
    header_titles_min = ["Param", "Value", "Unit", "Desc"]
    tab_size = 16
    read_count = 10
    idx = start_address
    if min:
        generate_output(separator.join(header_titles_min).expandtabs(tab_size))
    else:
        generate_output(separator.join(header_titles).expandtabs(tab_size))
    while idx <= stop_address:
        response, error = read_register(idx, read_count, slave)
        if not error:
            address_hex = response[0]['address_hex']
            address = response[0]['address']
            parameter = f"{response[6]['char1']}{response[6]['char2']}{response[7]['char1']}{response[7]['char2']}"
            is_not_menu = (int(response[5]['bin'][0], 2) == 0)
            is_readonly = (int(response[5]['bin'][1], 2) == 0) if is_not_menu else ""
            if is_not_menu:
                value = int(f"{response[1]['hex']}{response[0]['hex']}", 16)
                if value & 0x80000000:
                    value = -((value ^ 0xFFFFFFFF) + 1)
            else:
                value = ""
            precision = int(response[4]['bin'][:4], 2) if is_not_menu else ""
            value_float = round(value * 10 ** (-precision), precision) if is_not_menu else ""
            unit_id = int(response[4]['bin'][-7:], 2) if is_not_menu else ""
            unit_text = units.get(f'{unit_id}', {}).get('expected', '') if is_not_menu else ""
            multi_id = response[9]['UInt16'] if (is_not_menu and (response[9]['UInt16'] != "0")) else ""
            if is_not_menu:
                min_val = int(f"{response[2]['hex']}", 16)
                if min_val > 32767:
                    min_val -= 65536
                if (f"{response[2]['bin']}" != "1000000000000000") and (f"{response[2]['bin']}" != "0000000000000000"):
                    min_val = round(min_val * 10 ** (-precision), precision)
                max_val = int(f"{response[3]['hex']}", 16)
                if max_val & 0x80000000:
                    max_val = -((max_val ^ 0xFFFFFFFF) + 1)
                if (f"{response[3]['bin']}" != "0111111111111111") and (f"{response[3]['bin']}" != "1111111111111111"):
                  max_val = round(max_val * 10 ** (-precision), precision)
            else:
                min_val = ""
                max_val = ""
            descriptor_id = response[8]['UInt16']
            matching_item = next((item for item in descriptor if f"{item['iddescriptor']}" == descriptor_id),None)
            descriptor_text = matching_item.get("tlangalphakey", {}).get(lang, "") if matching_item else ""
            if (multi_id != ""):
                for item in typeMap:
                    if f"{multi_id}" in item:
                        for tvalue in item[f"{multi_id}"]["tvalues"]:
                            if tvalue["in_INPUT"] == value:
                                value_float = tvalue["alphakey"][lang]
                                break
                        else:
                            value_float = ""
                        break
                else:
                    value_float = ""
            if min:
                data = [f"{parameter}", f"{value_float}", f"{unit_text}",f"{descriptor_text}"]
            else:
                data = [f"{address_hex}", f"{address}", f"{parameter}", f"{value}", f"{precision}", f"{value_float}", f"{unit_text}", f"{unit_id}", f"{multi_id}" ,f"{min_val}",f"{max_val}", f"{is_readonly}", f"{is_not_menu==False}", f"{descriptor_id}", f"{descriptor_text}"]
        else:
            data = [f"{idx}"]
            for _ in range(1, len(header_titles)): data.append("#err")
        if not (error and noerror):
          generate_output(separator.join(data).expandtabs(tab_size))
        idx += read_count

def generateOvumHASS(start_address, stop_address, slave, lang):
    if args.method == METHOD_TCP:
        data = {"host": f"{args.host}", "port": f"{args.port}"}
        generate_output(get_hass_modbustcp_def(data))
    if args.method == METHOD_RTU:
        data = {"comport": f"{args.comport}", "baudrate": f"{args.baudrate}", "parity": f"{args.parity}", "stopbits": f"{args.stopbits}"}
        generate_output(get_hass_modbusrtu_def(data))
    read_count = 10
    idx = start_address
    sensor_str = ""
    tempsens_str = "      template:\n"
    last_menu = ""
    while idx <= stop_address:
        response, error = read_register(idx, read_count, slave)
        if not error:
            is_not_menu = (int(response[5]['bin'][0], 2) == 0)
            parameter = re.sub(r'[^a-zA-Z0-9]', '',f"{response[6]['char1']}{response[6]['char2']}{response[7]['char1']}{response[7]['char2']}")
            parameter = parameter.strip()
            descriptor_id = response[8]['UInt16']
            matching_item = next((item for item in descriptor if f"{item['iddescriptor']}" == descriptor_id), None)
            descriptor_text = matching_item.get("tlangalphakey", {}).get(lang, "") if matching_item else ""
            if is_not_menu:
                address = response[0]['address']
                precision = int(response[4]['bin'][:4], 2)
                scale = round(1 * 10 ** (-precision), precision)
                descriptor_text = f"{last_menu}: {descriptor_text} ({parameter} #{address})"
                sensor = slugify(descriptor_text, separator="_")
                unit_id = int(response[4]['bin'][-7:], 2)
                unit_text = units.get(f'{unit_id}', {}).get('default', '')
                if unit_text == "": unit_text = units.get(f'{unit_id}', {}).get('expected', '')
                deviceclass_text = units.get(f'{unit_id}', {}).get('device_class', '')
                deviceclass_text = f"device_class: {deviceclass_text}" if (deviceclass_text != "None") and (deviceclass_text.strip() != "") else ""
                if is_not_menu:
                    min_val = response[2]['Int16']
                    max_val = response[3]['Int16']
                    if max_val < min_val:
                        max_val = response[3]['UInt16']
                else:
                    min_val = ""
                    max_val = ""
                multi_id = response[9]['UInt16'] if (is_not_menu and (response[9]['UInt16'] != "0")) else ""
                isEnumValue = True if (multi_id != "") else False
                map = ""
                range = ""
                if isEnumValue:
                    for item in typeMap:
                        if f"{multi_id}" in item:
                            for tvalue in item[f"{multi_id}"]["tvalues"]:
                                if len(map) > 0: map += ",\n" + "\t\t\t\t\t"
                                if tvalue["alphakey"][lang] is None:
                                  map += "'" + str(tvalue["in_INPUT"]) + "' : ''"
                                else:
                                    map += "'" + str(tvalue["in_INPUT"]) + "' : '" + tvalue["alphakey"][lang] + "'"
                                if len(range) > 0: range += ","
                                range += str(tvalue["in_INPUT"])

                data = {"sensor": f"{sensor}", "range": f"{range}", "map": f"{map}", "slave": f"{slave}", "description": f"{descriptor_text.strip()}", "parameter": f"{parameter}", "address": f"{address}", "scale": f"{scale}", "precision": f"{precision}", "unit": f"{unit_text}", "device_class": f"{deviceclass_text}", "min_val": f"{min_val}", "max_val": f"{max_val}"}
                sensor_str += f"{get_hass_sensor_def(data)}\n"
                if isEnumValue and (len(range)>0):
                    tempsens_str += f"{get_hass_templatesensor_def(data)}\n"
            else:
                if descriptor_text is None or descriptor_text == "":
                    last_menu = descriptor_text
                else:
                    last_menu = descriptor_text.capitalize()
        idx += read_count
    generate_output(sensor_str)
    generate_output(tempsens_str)

def doDevThings(lang):
    return None

# Main function to call after script starts
def main():
    global args, client, descriptor, units, typeMap

    args = init_parser().parse_args()
    descriptor = load_json(JSON_DESCRIPTOR)
    units = load_json(JSON_UNITS)
    typeMap = load_json(JSON_TYPEMAP)
    separator = ';' if args.csv else '\t'

    if args.method == METHOD_RTU:
        client, is_connected = connect_to_modbusRTU(args.comport, args.baudrate, args.parity, args.stopbits)
    else:
        client, is_connected = connect_to_modbusTCP(args.host, args.port)

    if (args.output != None): save_output(args.output, "", True)

    if args.dump:
        generateRegisterDump(args.start_address, args.stop_address, args.slave, separator, args.noerror)
    elif args.hass:
        generateOvumHASS(args.start_address, args.stop_address, args.slave, args.lang)
    elif args.dev:
        doDevThings(args.lang)
    else:
        generateOvumDump(args.start_address, args.stop_address, args.slave, separator, args.lang, args.min, args.noerror)

    if client: client.close()

# Main Call
if __name__ == "__main__":
    main()
