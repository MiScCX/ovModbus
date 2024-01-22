# Miscellaneous
### Additional tools and scripts

### ```setArea.py```
As the integration of all Ovum sensors and templates can quickly become confusing and the integration via Modbus does not represent a separate device with all entities, you can create a separate area and group the full of sensors under it.

It is very tedious and time-consuming to manually assign an area to all sensors.

The setArea.py script is designed for this purpose.

In Home Assistant, all entities are saved in a file: core.entity_registry. This file is located in the Storage folder. As all sensors are created automatically by the higher-level script, the unique_ids all start with the same pattern "ovum_". This can be used to find all Ovum sensors with this script.
In addition, you must manually create your desired area in the Home Assistant and use its area_id and assign it to the sensors. The area_id can be found in the core.area_registry file after creation in HASS (located in the same storage directory).

### How to use:

1. Create an area in the Home Assistant
2. Copy the area ID after creation
3. Update this script and add your own settings:
```
def main():
    ### CONFIGURATION
    ##
    UNIQUE_ID_STARTS_WITH = 'ovum_'.
    AREA_ID = 'ovum_warmepumpe
    ..
```
5. Copy this script to the ```storage``` folder
6. Execute the script: ```python setArea.py```
7. Check the created file ```core.entity_registry.new``` and if you are satisfied with it, save the original file ```core.entity_registry``` as ```core.entity_registry.bak``` and overwrite the file ```core.entity_registry``` with the ```.new``` file.
7) Restart Home Assistant
   

