# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: http://foglamp.readthedocs.io/
# FOGLAMP_END

""" Module for AM2315 'async' type plugin """

import asyncio
import copy
import datetime
import json
import uuid

from foglamp.common import logger
from foglamp.plugins.common import utils
from foglamp.services.south import exceptions
from foglamp.services.south.ingest import Ingest
import smbus

__author__ = "Ashwin Gopalakrishnan"
__copyright__ = "Copyright (c) 2017 OSIsoft, LLC"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"


_DEFAULT_CONFIG = {
    'plugin': {
        'description': 'AM2315 async plugin',
        'type': 'string',
        'default': 'am2315async'
    },
    'shutdownThreshold': {
        'description': 'Time in seconds allowed for shutdown to complete the pending tasks',
        'type': 'integer',
        'default': '10'
    }
}

_LOGGER = logger.setup(__name__, level=20)


def plugin_info():
    """ Returns information about the plugin.
    Args:
    Returns:
        dict: plugin information
    Raises:
    """

    return {
        'name': 'AM2315 Async plugin',
        'version': '1.0',
        'mode': 'async',
        'type': 'south',
        'interface': '1.0',
        'config': _DEFAULT_CONFIG
    }


def plugin_init(config):
    """ Initialise the plugin.
    Args:
        config: JSON configuration document for the South device configuration category
    Returns:
        handle: JSON object to be used in future calls to the plugin
    Raises:
    """
    data = copy.deepcopy(config)

    bus = smbus.SMBus(1)
    _LOGGER.info('AM2315 initialized')
    return bus


def plugin_start(bus):
    """ Extracts data from the sensor and returns it in a JSON document as a Python dict.
    Available for async mode only.
    Args:
        handle: handle returned by the plugin initialisation call
    Returns:
        returns a sensor reading in a JSON document, as a Python dict, if it is available
        None - If no reading is available
    Raises:
        TimeoutError
    """
    sensor_add      = 0x5C
    start_add       = 0x00
    function_code   = 0x03
    register_number = 0x04
    response_bytes = 8
    attempt_threshold = 50
    async def save_data():
        attempt = 1
        if bus is None:
            return
        try:
            while True:
                await asyncio.sleep(1)
                try:
                    try:
                        # wake up call
                        bus.write_i2c_block_data(sensor_add, function_code, [start_add, register_number])
                    except Exception as e:
                        # expected exception as sensor is sleeping
                        pass
                    # request data
                    bus.write_i2c_block_data(sensor_add, function_code, [start_add, register_number])
                    # read data
                    sensor_response = bytearray(bus.read_i2c_block_data(sensor_add, function_code, response_bytes))
                    # function_code=sensor_response[0]
                    # bytes_returned=sensor_response[1]
                    # relative_humidity_high=sensor_response[2]
                    # relative_humidity_low=sensor_response[3]
                    # temperature_high=sensor_response[4]
                    # temperature_low=sensor_response[5]
                    # crc_low=sensor_response[6]
                    # crc_high=sensor_response[7]

                    # temperature
                    temperature= (sensor_response[4] * 256 + sensor_response[5])/10
                    # humidity
                    humidity= (sensor_response[2] * 256 + sensor_response[3])/10
                    # crc
                    crc = sensor_response[7] * 256 + sensor_response[6]
                    # calc crc to verify
                    calc_crc = 0xFFFF
                    for byte in sensor_response[0:6]:
                        calc_crc = calc_crc ^ byte
                        for i in range(1,9):
                            if(calc_crc & 0x01):
                                calc_crc = calc_crc >> 1
                                calc_crc = calc_crc ^ 0xA001
                            else:
                                calc_crc = calc_crc >> 1
            
                    if calc_crc != crc:
                        pass

                    time_stamp = str(datetime.datetime.now(tz=datetime.timezone.utc))
                    data = {
                        'asset': 'temperature',
                        'timestamp': time_stamp,
                        'key': str(uuid.uuid4()),
                        'readings': {
                            "temperature": temperature,
                        }
                    }
                    await Ingest.add_readings(asset='AM2315/{}'.format(data['asset']),
                                                           timestamp=data['timestamp'], key=data['key'],
                                                           readings=data['readings'])
                    data = {
                        'asset': 'humidity',
                        'timestamp': time_stamp,
                        'key': str(uuid.uuid4()),
                        'readings': {
                            "humidity": humidity,
                        }
                    }
                    await Ingest.add_readings(asset='AM2315/{}'.format(data['asset']),
                                                           timestamp=data['timestamp'], key=data['key'],
                                                           readings=data['readings'])
                    attempt = 1
                except (Exception) as ex:
                    attempt += 1
                    if attempt > attempt_threshold:
                        raise RuntimeError("Attempt {} exceeds attempt threshold of {}".format(attempt, attempt_threshold))
        except (Exception, RuntimeError, pexpect.exceptions.TIMEOUT) as ex:
            _LOGGER.exception("AM2315 async exception: {}".format(str(ex)))
            raise exceptions.DataRetrievalError(ex)
        _LOGGER.debug("AM2315 async reading: {}".format(json.dumps(data)))
        return
    asyncio.ensure_future(save_data())


def plugin_reconfigure(handle, new_config):
    """ Reconfigures the plugin

    it should be called when the configuration of the plugin is changed during the operation of the South device service;
    The new configuration category should be passed.

    Args:
        handle: handle returned by the plugin initialisation call
        new_config: JSON object representing the new configuration category for the category
    Returns:
        new_handle: new handle to be used in the future calls
    Raises:
    """
    _LOGGER.info("Old config for AM2315 plugin {} \n new config {}".format(handle, new_config))

    # Find diff between old config and new config
    diff = utils.get_diff(handle, new_config)

    # TODO
    new_handle = copy.deepcopy(new_config)
    new_handle['restart'] = 'no'
    return new_handle


def _plugin_stop(handle):
    """ Stops the plugin doing required cleanup, to be called prior to the South device service being shut down.

    Args:
        handle: handle returned by the plugin initialisation call
    Returns:
    Raises:
    """
    _LOGGER.info('AM2315 (async) Disconnected.')


def plugin_shutdown(handle):
    """ Shutdowns the plugin doing required cleanup, to be called prior to the South device service being shut down.

    Args:
        handle: handle returned by the plugin initialisation call
    Returns:
    Raises:
    """
    _plugin_stop(handle)
    _LOGGER.info('AM2315 async plugin shut down.')
