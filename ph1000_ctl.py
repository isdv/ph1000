#!/usr/bin/python3

import argparse
import logging
import os
import sys
import threading
import time

import paho.mqtt.client as mqtt
import serial
import yaml
from serial import Serial

import ph1000

this_module = os.path.basename(__file__)
logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)-8s [%(asctime)s] %(relativeCreated)6d %(threadName)s %(message)s')
logger = logging.getLogger(__name__)


class MqttBase(mqtt.Client):
    def __init__(self, client_id="", clean_session=True, userdata=None,
                 protocol=mqtt.MQTTv311, transport="tcp"):
        super().__init__(client_id, clean_session, userdata, protocol, transport)
        self.on_disconnect = self.mqtt_on_disconnect
        self.on_connect = self.mqtt_on_connect
        self.on_publish = self.mqtt_on_publish
        self.on_message = self.mqtt_on_message
        self.on_subscribe = self.mqtt_on_subscribe
        self.on_unsubscribe = self.mqtt_on_unsubscribe
        self.on_log = self.mqtt_on_log

    def process_subscribe(self):
        pass

    def process_message(self, topic, payload):
        pass

    def mqtt_on_connect(self, mqttc, userdata, flags, rc):
        logger.info('{} Подключен! rc:'.format(mqttc._client_id, rc))
        self.process_subscribe()

    def mqtt_on_disconnect(self, mqttc, userdata, rc):
        logger.info('{} Отключен! rc:'.format(mqttc._client_id, rc))

    def mqtt_on_message(self, mqttc, userdata, msg):
        logger.debug('{} Получено сообщение от {}: {}'.format(mqttc._client_id,
                                                              msg.topic, msg.payload))
        self.process_message(msg.topic, msg.payload)

    def mqtt_on_publish(self, mqttc, userdata, mid):
        logger.debug('{} Сообщение отправлено id:{}'.format(mqttc._client_id, mid))

    def mqtt_on_subscribe(self, mqttc, userdata, mid, granted_qos=0):
        logger.info('{} Subscribed! id:{}, qos:{}'.format(mqttc._client_id, mid, granted_qos))

    def mqtt_on_unsubscribe(self, mqttc, userdata, mid):
        logger.info('{} Unsubscribed! id:{}'.format(mqttc._client_id, mid))

    def mqtt_on_log(self, mqttc, userdata, level, buf=None):
        logger.debug('{} MQTT level: {}, str: {}'.format(mqttc._client_id, level, buf))


class skdMqtt(MqttBase):
    def __init__(self, client_id="", clean_session=True, userdata=None,
                 protocol=mqtt.MQTTv311, transport="tcp"):
        super().__init__(client_id, clean_session, userdata, protocol, transport)
        self.topics = {}
        self.devices = {}

    def add_topic_device(self, topic, dev_name, device_method):
        if device_method:
            self.topics[topic] = device_method
        else:
            self.devices[dev_name] = topic

    def send(self, sender, msg):
        topic = self.devices[sender]
        self.publish(topic, msg)

    def process_subscribe(self):
        for topic in [*self.topics]:
            self.subscribe(topic)

    def process_message(self, topic, payload):
        dm = self.topics[topic]
        pl = payload.decode('utf-8')
        dm(pl)


##
##
class PollingDevices:
    def __init__(self, send_data):
        self.send_data = send_data
        self.devices = []
        self.device_next = self._gen_device_ready()
        self.device_error_timeout = 3

    def add_device(self, dev_name, method=None, polling_interval=1):
        dd = dict()
        dd['name'] = dev_name
        dd['method'] = method
        dd['time_next'] = time.time()
        dd['polling_interval'] = polling_interval
        dd['last_data'] = None
        self.devices.append(dd)

    def _gen_device_ready(self):
        while True:
            ds = sorted(self.devices, key=lambda dev: dev['time_next'])
            wait_time = ds[0]['time_next'] - time.time()
            if wait_time > 0:
                time.sleep(wait_time)
            yield ds[0]

    def start(self):
        logger.info('Запуск опроса устройств')

        while True:

            try:
                device = next(self.device_next)
                device['time_next'] = time.time() + device['polling_interval']
                data = device['method']()
                if data != device['last_data']:
                    if data:
                        self.send_data(device['name'], data)
                        logger.debug('С устройства {} прочитана карта {}'.format(device['name'], data))
                device['last_data'] = data
            except ph1000.excPH1000 as e:
                logger.exception('Ошибка: {} '.format(e.message))
                logger.debug('Ошибка с устройства {} '.format(device['name']))
                device['time_next'] = time.time() + self.device_error_timeout


class SerialTranport(Serial):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Lock = threading.Lock()
        self.reopen_timeout = 3
        self.minimum_silent_period = self._calc_minimum_silent_period()
        self.last_query = 0

    def _calc_minimum_silent_period(self):
        BITTIMES_PER_CHARACTERTIME = 11
        MINIMUM_SILENT_CHARACTERTIMES = 3.5
        bittime = 1 / float(self._baudrate)
        return bittime * BITTIMES_PER_CHARACTERTIME * MINIMUM_SILENT_CHARACTERTIMES

    def sendrecv(self, data_to_send, read_size):
        with self.Lock:
            while not self.is_open:
                try:
                    self.open()
                except serial.serialutil.SerialException as e:
                    print('Error opennig port', str(e))
                time.sleep(self.reopen_timeout)
            try:
                wt = time.time() - self.last_query
                if wt < self.minimum_silent_period:
                    time.sleep(self.minimum_silent_period - wt)
                self.write(data_to_send)
                response = self.read(read_size)  # размер буфера под данные
                self.last_query = time.time()
                return response
            except serial.serialutil.SerialException as e:
                logger.debug('Ошибка чтения/записи в порт')
                self.close()
                return None


def device_factory(dev_cfg, transport):
    logger.debug(dev_cfg)
    name = [*dev_cfg][0]
    dev_param = dev_cfg[name]
    module, device_type = dev_param['type'].split('.')
    del dev_param['type']
    dev = getattr(globals()[module], type)(transport, name, **dev_param)
    return dev


def mqtt_factory(mqtt_class, config_mqtt, devices):
    devices_topic = config_mqtt['topic-device']
    mqtt_connect = config_mqtt['connect']
    mqtt_host = mqtt_connect['host']

    del config_mqtt['topic-device']
    del config_mqtt['connect']
    del mqtt_connect['host']

    a_mqtt = mqtt_class(**config_mqtt)

    for dt in devices_topic:
        topic, device_method = list(dt.items())[0]
        try:
            device_name, method_name = device_method.split('.')
            method = getattr(devices[device_name], method_name)
        except ValueError as e:
            device_name = device_method
            method = None

        a_mqtt.add_topic_device(topic, device_name, method)

    a_mqtt.connect(mqtt_host, **mqtt_connect)

    return a_mqtt


def main(args):
    if args is None:
        raise Exception('Valid arguments not found')

    def serial_option_constructor(loader, node):
        return getattr(serial, node.value, None)

    yaml.add_constructor(u'!serial', serial_option_constructor)

    config = yaml.load(args.config)

    logger.debug('Настройка порта.')
    config_serial = config['serial']
    serial_tranport = SerialTranport(**config_serial)

    logger.debug('Настройка устройств.')
    devices = {}
    for dev_cfg in config['devices']:
        dev = device_factory(dev_cfg, serial_tranport)
        devices[dev.name] = dev

    logger.debug('Настройка подключения к MQTT.')

    config_mqtt = config['mqtt']
    skd_mqtt = mqtt_factory(skdMqtt, config_mqtt, devices)

    logger.debug('Настройка опроса устройств.')
    DP = None
    if 'PollingDevices' in config:
        DP = PollingDevices(skd_mqtt.send)
        for dp_param in [*config['PollingDevices']]:
            dev_name = [*dp_param][0]
            method = dp_param[dev_name]['method']
            del dp_param[dev_name]['method']
            DP.add_device(dev_name, getattr(devices[dev_name], method, None), **dp_param[dev_name])

    logger.debug('Старт.')
    skd_mqtt.loop_start()
    if DP: DP.start()


# main
if __name__ == "__main__":
    logger.debug('Конверетер  подключен.')
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', required=True, type=argparse.FileType('r'), nargs='?',
                        help='main configuration file yaml format')
    args = parser.parse_args()

    sys.exit(main(args))
