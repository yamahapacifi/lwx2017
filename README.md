Component
---------

Name: lwx2017
Introduced: 5/19/2017
Format: Python scripts

Description
-----------

lwx2017 includes scripts that start a Modbus server and periodically polls temperature, humidity, compass, and gyroscopic (pitch, roll, yaw) sensors. The sensor values are written to modbus holding registers, using the mapping described below:

temperature (Fahrenheit)    40001
humidity (percent)          40002
pitch (degrees)             40003
roll (degrees)              40004
yaw (degrees)               40005
compass (degrees from N)    40006

Two scripts are included:
* Script "server.py" reads the values from a Raspberry Pi SenseHAT and displays the current temperature on the SenseHAT's 8x8 LED grid. 
* Script "backup_server.py" simulates the values and displays the current temperature to stdout. 

