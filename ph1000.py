#! /usr/bin/python3
#

import struct


def LiczCRC2(data):
    res = 0x0000
    poly = 0x1021
    for byte in data:
        C = (res & 0xFF00) ^ (byte << 8)
        for i in range(8):
            if C & 0x8000:
                C = ((C << 1) & 0xFFFF) ^ poly
            else:
                C = ((C << 1) & 0xFFFF)
        res = C ^ ((res << 8) & 0xFFFF)
    return res


def msb(x):
    return x.bit_length() - 1


def lsb(x):
    return msb(x & -x)


OC_ParityError = 0x1A  # ошибка четности
OC_RangeError = 0x20  # выход за пределы диапазона допустимых значений
OC_LengthError = 0x21  # Неверная длина (количество данных)
OC_NoACKFromSlave = 0x22  # нет ответа от контроллера
OC_WrongPassword = 0x30  # неправильный пароль
OC_Error = 0xFE  # ошибка
OC_Successful = 0xFF  # операция выполнена успешно

cnstCommandResponse = {OC_ParityError: ('OC_ParityError', 'ошибка четности')
    , OC_RangeError: ('OC_RangeError', 'выход за пределы диапазона допустимых значений')
    , OC_LengthError: ('OC_LengthError', 'неверная длина (количество данных)')
    , OC_NoACKFromSlave: ('OC_NoACKFromSlave', 'нет ответа от контроллера')
    , OC_WrongPassword: ('OC_WrongPassword', 'неправильный пароль')
    , OC_Error: ('OC_Error', 'ошибка')
    , OC_Successful: ('OC_Successful')
                       }

C_UniqueRead = 0x02
A_UniqueRead = C_UniqueRead + 1
C_WriteOutputs = 0x70
A_WriteOutputs = C_WriteOutputs + 1
C_ReadButton = 0x72
A_ReadButton = C_ReadButton + 1
C_CardRead = 0x20
A_CardRead = C_CardRead + 1
C_CardWrite = 0x22
A_CardWrite = C_CardWrite + 1
C_Password = 0x24
A_Password = C_Password + 1
C_LogOut = 0x14
A_LogOut = C_LogOut + 1
C_ChangePassword = 0x26
A_ChangePassword = C_ChangePassword + 1
C_ReserCardMemory = 0x28
A_ReserCardMemory = C_ReserCardMemory + 1
C_DevParamSet = 0x34
A_DevParamSet = C_DevParamSet + 1
C_DevParamGet = 0x36
A_DevParamGet = C_DevParamGet + 1
C_SoftwareVersion = 0xFE
A_SoftwareVersion = 0xFF

cmdAll = (C_UniqueRead, C_WriteOutputs, C_ReadButton, C_CardRead, C_CardWrite, C_Password, C_LogOut, C_ChangePassword
          , C_ReserCardMemory, C_DevParamSet, C_DevParamGet, C_SoftwareVersion)
resAll = (A_UniqueRead, A_WriteOutputs, A_ReadButton, A_CardRead, A_CardWrite, A_Password, A_LogOut, A_ChangePassword
          , A_ReserCardMemory, A_DevParamSet, A_DevParamGet, A_SoftwareVersion)

cmdDesc = {C_UniqueRead: {'parametrs': None}
    , A_UniqueRead: {'parametrs': 'BBBBB'}
    , C_WriteOutputs: {'parametrs': 'BB'}
    , A_WriteOutputs: {'parametrs': None}
    , C_ReadButton: {'parametrs': None}
    , A_ReadButton: {'parametrs': 'B'}
    , C_CardRead: {'parametrs': 'H'}
    , A_CardRead: {'parametrs': 'BBBBB'}
    , C_CardWrite: {'parametrs': 'HBBBBB'}
    , A_CardWrite: {'parametrs': None}
    , C_Password: {'parametrs': 'BBBBB'}
    , A_Password: {'parametrs': None}
    , C_LogOut: {'parametrs': None}
    , A_LogOut: {'parametrs': None}
    , C_ChangePassword: {'parametrs': 'BBBBBBBBBB'}
    , A_ChangePassword: {'parametrs': None}
    , C_ReserCardMemory: {'parametrs': '5s'}
    , A_ReserCardMemory: {'parametrs': None}
    , C_DevParamSet: {'parametrs': 'BBBBB'}
    , A_DevParamSet: {'parametrs': None}
    , C_DevParamGet: {'parametrs': None}
    , A_DevParamGet: {'parametrs': 'BBBBB'}
    , C_SoftwareVersion: {'parametrs': None}
    , A_SoftwareVersion: {'parametrs': '%ss'}
           }

maskDevParamB1_G01 = 0b00000011  # усиление приемной системы
maskDevParamB1_ALO = 0b00000100  # автоматический Logout
maskDevParamB1_MAT = 0b00001000  # режим работы внутренней памятикарт
maskDevParamB1_Reserved47 = 0b11110000

maskDevParamB2_S03 = 0b00001111  # S3 S2 S1 S0 - скорость линии uart
maskDevParamB2_SI0 = 0b00010000  # должно ли любое считываемое ID быть послано через линию UART
maskDevParamB2_BI0 = 0b00100000  # должно ли считываемое ID, находящееся вовнутренней базе карт, быть послано через линию UART.
maskDevParamB2_UR0 = 0b01000000  # должно ли считываемое ID быть послано циклически (2 раза/сек, через линию UART
maskDevParamB2_Reserved7 = 0b10000000  #

maskDevParamB3_A07 = 0b11111111  # A7...A0 - устанавливает логический адрес устройства считывания на шине RS-485

maskDevParamB4_B01 = 0b00000011  # биты определяют, как должен реагировать встроенный зуммер
maskDevParamB4_Reserved2 = 0b00000100  #
maskDevParamB4_BR0 = 0b00001000  # должен ли зуммер работать циклически, или только раз
maskDevParamB4_BD03 = 0b11110000  # определяет время работы зуммера после того, как появится фактор включающий его

maskDevParamB5_R01 = 0b00000011  # биты определяют, как должно реагировать встроенное реле
maskDevParamB5_NCNO = 0b00000100  # определяющий нормальное состояние реле (нормально замкнутое, либо нормально разомкнутое)
maskDevParamB5_RR0 = 0b00001000  # тот бит определяет, должно ли реле работать циклически или только раз
maskDevParamB5_RD03 = 0b11110000  # определяет время работы реле после того, как появится фактор включающий его

devParam = {'paramReaderGain': {'mask': maskDevParamB1_G01, 'byte': 0, 'text': 'Reader gain'}
    , 'paramAutoLogout': {'mask': maskDevParamB1_ALO, 'byte': 0, 'text': 'Auto logout'}
    , 'paramMemoryAutoUse': {'mask': maskDevParamB1_MAT, 'byte': 0, 'text': 'Memory auto use'}
    , 'paramB1_Reserved47': {'mask': maskDevParamB1_Reserved47, 'byte': 0, 'text': 'Reserverd bits 4-7 of byte 1'}
    , 'paramUartSpeed': {'mask': maskDevParamB2_S03, 'byte': 1, 'text': 'Uart speed'}
    , 'paramSomeIDSend': {'mask': maskDevParamB2_SI0, 'byte': 1, 'text': 'Some ID uart send'}
    , 'paramBaseIDSend': {'mask': maskDevParamB2_BI0, 'byte': 1, 'text': 'Base ID uart send'}
    , 'paramUartRepeat': {'mask': maskDevParamB2_UR0, 'byte': 1, 'text': 'Uart repeat'}
    , 'paramB2_Reserved7 ': {'mask': maskDevParamB2_Reserved7, 'byte': 1, 'text': 'Reserverd bits 4-7 of byte 2'}
    , 'paramReaderAddress': {'mask': maskDevParamB3_A07, 'byte': 2, 'text': 'Reader address'}
    , 'paramBuzzerMode': {'mask': maskDevParamB4_B01, 'byte': 3, 'text': 'Buzzer mode'}
    , 'paramB4_Reserved2': {'mask': maskDevParamB4_Reserved2, 'byte': 3, 'text': 'Reserverd bits 2 of byte 4'}
    , 'paramBuzzerRepeat': {'mask': maskDevParamB4_BR0, 'byte': 3, 'text': 'Buzzer repeat'}
    , 'paramBuzzerDelay': {'mask': maskDevParamB4_BD03, 'byte': 3, 'text': 'Buzzer delay'}
    , 'paramRelayMode': {'mask': maskDevParamB5_R01, 'byte': 4, 'text': 'Relay mode'}
    , 'paramRelayNCNO': {'mask': maskDevParamB5_NCNO, 'byte': 4, 'text': 'Relay NC/NO'}
    , 'paramRelayRepeat': {'mask': maskDevParamB5_RR0, 'byte': 4, 'text': 'Relay repeat'}
    , 'paramReleayDelay': {'mask': maskDevParamB5_RD03, 'byte': 4, 'text': 'Relay delay'}
            }

devParamFactoryDefault = [0x03, 0x03, 0x01, 0x10, 0xA9]
cnstBlockHeaderLen = 2
cnstBlockResponseMinLen = 6
cnstBlockCommandMinLen = 5


class excPH1000(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class excCmdPH1000(excPH1000):
    def __init__(self, CommandResponse):
        super().__init__(cnstCommandResponse[CommandResponse])


class excCmdUnknow(excPH1000):
    def __init__(self):
        super().__init__('Неизвестная команда')


class excResponseUnknow(excPH1000):
    def __init__(self):
        super().__init__('Ответ устройства не распознан')


class excResponseCrcError(excPH1000):
    def __init__(self):
        super().__init__('Неверная контрольная сумма пакета ответа')


class excResponseLen(excPH1000):
    def __init__(self):
        super().__init__('Размер пакета не верный')


class excCmdParam(excPH1000):
    def __init__(self, cmd, args):
        super().__init__('Ошибка в параметрах команды %s %s ' % (cmd, args))


class protocolPH1000:

    @staticmethod
    def cmdPrepare(address, cmd, args=None):
        if cmd not in cmdAll:
            raise excCmdUnknow()

        ds_header = '>BBB'
        parametrs = cmdDesc[cmd]['parametrs']
        if parametrs:
            ds_wparam = ds_header + parametrs
            if isinstance(args, str):
                block2 = struct.pack(parametrs, bytearray(args, 'utf-8'))
            elif isinstance(args, list):
                block2 = struct.pack(parametrs, *args)
            else:
                raise excCmdParam(cmd, args)
            block = struct.pack(ds_header, address,
                                struct.calcsize(ds_wparam) + 2, cmd) + block2
        else:
            block = struct.pack(ds_header, address, struct.calcsize(ds_header) + 2, cmd)

        aCRC16 = LiczCRC2(block)
        packet = block + struct.pack('>H', aCRC16)

        return packet

    @staticmethod
    def responseParse(address, cmd, response):
        if cmd not in cmdAll:
            raise excCmdUnknow()

        if len(response) < cnstBlockResponseMinLen:
            raise excResponseLen()

        crc_response = struct.unpack('>H', response[-2:])[0]
        crc_calc = LiczCRC2(response[:-2])

        if crc_response != crc_calc:
            raise excResponseCrcError()

        if (response[2] == cmd + 1) and (response[0] == address):
            parametrs = cmdDesc[cmd + 1]['parametrs']
            Data = None
            if parametrs:
                if "%s" in parametrs:
                    decode_string = ('>BBB' + parametrs + 'BH') % (len(response) - 6)
                else:
                    decode_string = '>BBB' + parametrs + 'BH'
                if struct.calcsize(decode_string) != len(response):
                    raise excResponseLen()
                address, block_len, cmdResponse, *Data, codeOperation, CRC16 = struct.unpack(decode_string, response)
            else:
                decode_string = '>BBB' + 'BH'
                if struct.calcsize(decode_string) != len(response):
                    raise excResponseLen()
                address, block_len, cmdResponse, codeOperation, CRC16 = struct.unpack(decode_string, response)

            if codeOperation != OC_Successful:
                raise excCmdPH1000(codeOperation)
            return Data

        else:
            raise excResponseUnknow()


class ph1000Base():
    def __init__(self, transport, name, address):
        self.tranposrt = transport
        self.name = name
        self.address = address

    def execCommand(self, cmd, args=None):

        prepared_data = protocolPH1000.cmdPrepare(self.address, cmd, args)
        returned_data = self.tranposrt.sendrecv(prepared_data, 16)
        if returned_data:
            parsed_data = protocolPH1000.responseParse(self.address, cmd, returned_data)
            return parsed_data
        else:
            return None

    def version(self):
        return self.execCommand(C_SoftwareVersion)


class Relay(ph1000Base):
    def on(self):
        self.execCommand(C_WriteOutputs, [2, 3])

    def off(self):
        self.execCommand(C_WriteOutputs, [2, 0])

    def parse_cmd(self, cmd):
        self.on() if str(cmd) in ['ON', '1'] else self.off()


class Buzzer(ph1000Base):
    def on(self):
        self.execCommand(C_WriteOutputs, [1, 3])

    def off(self):
        self.execCommand(C_WriteOutputs, [1, 0])

    def parse_cmd(self, cmd):
        self.on() if str(cmd) in ['ON', '1'] else self.off()


class Reader(ph1000Base):
    def __init__(self, transport, name=None, address=None, card_format='long'):
        super().__init__(transport, name, address)
        self.format = card_format

    def format_card(self, card_raw):
        if self.format and card_raw and len(card_raw) == 5:
            if self.format in 'full':
                card_num1 = '{},{}'.format(card_raw[2], card_raw[1] * 256 + card_raw[0])
                card_num2 = '{0:0>10d}'.format(
                    int(('0x{:x}{:x}'.format(card_raw[2], card_raw[1] * 256 + card_raw[0])), 16))
                return (card_raw, card_num1, card_num2)
            elif self.format in 'long':
                return '{0:0>10d}'.format(int(('0x{:x}{:x}'.format(card_raw[2], card_raw[1] * 256 + card_raw[0])), 16))
            elif self.format in 'short':
                return '{},{}'.format(card_raw[2], card_raw[1] * 256 + card_raw[0])
            elif self.format in 'hex':
                return '0x{:x}{:x}'.format(card_raw[2], card_raw[1] * 256 + card_raw[0])
        else:
            return card_raw

    def Poll(self):
        try:
            card_raw = self.execCommand(C_UniqueRead)
            return self.format_card(card_raw) if card_raw and self.format else card_raw

        except excCmdPH1000 as e:
            if e.args[0] == OC_ParityError:
                return None
            else:
                raise


class PH1000(ph1000Base):

    def __init__(self, transport, name, address, password=[1, 2, 3, 4, 5]):
        super().__init__(self, transport, name, address)
        self._devParamB15 = [0, 0, 0, 0, 0]
        self._password = password

    def getParam(self, paramName):
        p = devParam[paramName]
        res = (p['mask'] & self._devParamB15[p['byte']]) >> lsb(p['mask'])
        return res

    def setParam(self, paramName, value):
        p = devParam[paramName]
        mask_inv = ~p['mask'] & 0xFF
        value_mask = ((value & 0xFF) << lsb(p['mask']))
        self._devParamB15[p['byte']] = value_mask | (self._devParamB15[p['byte']] & mask_inv)
        return self._devParamB15

    def cmdLoadParam(self):
        self._devParamB15 = self.execCommand(C_DevParamGet)
        return self._devParamB15

    def cmdSaveParam(self):
        if any(self._devParamB15):
            res = self.execCommand(C_Password, self._password)
            res = self.execCommand(C_DevParamSet, self._devParamB15)
        return self._devParamB15

