******************************************************************************
              FogLAMP South MAX31865 Async mode Plugin
******************************************************************************

This directory contains a plugin that receives readings from AM2315
humidity/temperature sensor.

Requirements:
sudo apt-get install python3-smbus

=============
Since the plugin runs in a separate process and its shutdown is controlled by the
central FogLAMP server, pressing CTRL-C does not terminate the process properly.


