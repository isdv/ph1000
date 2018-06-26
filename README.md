# ph1000

Программа предназнaчена для управления контроллером со встроенным бесконтактным считывателем Proxy-H1000. 
Производитель Bolid. 

Программа написана на Python3 и представляет собой шлюз MQTT <--> RS485.

Зависимости:
- paho_mqtt
- pyserial
- PyYAML

Конфигурационный файл:

1. Настройка последовательного порта:
      serial:
            port: /dev/ttyUSB0
            baudrate: 9600
            timeout: 0.1
            write_timeout: 0.1

Дополнительно можно указать константы из модуля serial, например:

      !serial.PARITY_NONE


2. Устройства контроллера реле, зуммер, считыватель.


            devices:
                  - relay1:
                          address: 1
                          type: ph1000.Relay
                  - buzzer1:
                          address: 1
                          type: ph1000.Buzzer
                  - reader1:
                          address: 1
                          type: ph1000.Reader
                          card_format: long  # 

3. Настройка периодического опроса считывателя:

            PollingDevices:
                  - reader1:
                        polling_interval: 0.1
                        method: Poll


4. Подключение к MQTT серверу и настройка соответствия очередей и устройств

            mqtt:
               client_id: simpleKD
               clean_session: True
               connect:
                 host: 127.0.0.1
                 port: 1883
                 keepalive: 60
               topic-device:
                 - skd/device/relay1: relay1.parse_cmd
                 - skd/device/buzzer1: buzzer1.parse_cmd
                 - skd/device/reader1: reader1


5. Запуск:
      
            python3 ph1000_ctl.py  -с config.yaml
