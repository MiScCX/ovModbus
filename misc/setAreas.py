#                                                  #
#      setAreaHelper.py  Helper to set areas       #
#                                                  #
#      Copyright 2024 MiSc                         #
#                                                  #
#      This code is licensed under the GPL         #
#                                                  #

import json

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

def update_area_id(obj, unique_id_starts_with, area_id):
    if isinstance(obj, dict):
        if 'unique_id' in obj and obj['unique_id'].startswith(unique_id_starts_with):
            obj['area_id'] = area_id
        for key, value in obj.items():
            obj[key] = update_area_id(value)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            obj[i] = update_area_id(item)
    return obj

def main():
    ### CONFIGURATION
    ##
    UNIQUE_ID_STARTS_WITH = 'ovum_'
    AREA_ID = 'ovum_warmepumpe'
    #
    ################################

    CORE_ENTITY_REGISTRY = 'core.entity_registry'
    CORE_ENTITY_REGISTRY_NEW = CORE_ENTITY_REGISTRY + '.new'

    data = load_json(CORE_ENTITY_REGISTRY)
    updated_data = update_area_id(data, UNIQUE_ID_STARTS_WITH, AREA_ID)

    save_output(CORE_ENTITY_REGISTRY + '.new', json.dumps(updated_data, indent=2, ensure_ascii=False), True)
    print('New file created: ' + CORE_ENTITY_REGISTRY_NEW)

if __name__ == "__main__":
    main()
