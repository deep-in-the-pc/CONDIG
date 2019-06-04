
#for serial comms
import threading
import serial.tools.list_ports
from serial import Serial
import re
#for storage
import json
import time

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal



class serialThread (QThread):

    newTemperature1Signal = pyqtSignal(float)
    newTemperature2Signal = pyqtSignal(float)
    closedSignal = pyqtSignal()

    def __init__(self, threadID, name, queue):
        QThread.__init__(self)
        self._isRunning = True

        self.in_queue = queue

        self.temperature1TimeSet = False
        self.temperature2TimeSet = False

        self.threadID = threadID
        self.name = name
        self.serialConnection = serial.Serial()

        self.temperature1DeltaTime = 0
        self.temperature2DeltaTime = 0

        self.led1 = 0
        self.led2 = 0

        self.transistor1 = 0
        self.transistor2 = 0

        self.adcReference = 3300

        self.temperature1TimerSetup()
        self.temperature2TimerSetup()

    def setParameteres(self, parameters):
        self.serialConnection.bytesize = parameters[0]
        self.serialConnection.parity = parameters[1]
        self.serialConnection.stopbits = parameters[2]
        self.serialConnection.baudrate = parameters[3]
        self.serialConnection.port = parameters[4]

    def run(self):

        self.serialConnection.open()
        if(self.serialConnection.is_open):
            while self._isRunning:
                if not self.in_queue.empty():
                    msg = self.in_queue.get()
                    args = msg.split()
                    if args[0] == 'setLed1':
                        self.led1 = args[1]
                        packet = bytearray()
                        packet.append(119)
                        packet.append(32)
                        packet.append(ord('5'))
                        packet.append(32)

                        for char in str(self.led1):
                            packet.append(ord(char))

                        packet.append(13)
                        self.serialConnection.write(packet)

                    elif args[0] == 'setLed2':
                        self.led2 = args[1]
                        packet = bytearray()
                        packet.append(119)
                        packet.append(32)
                        packet.append(ord('6'))
                        packet.append(32)
                        for char in str(self.led2):
                            packet.append(ord(char))

                        packet.append(13)
                        self.serialConnection.write(packet)
                    elif args[0] == 'setTransistor1':
                        self.transistor1 = args[1]
                        packet = bytearray()
                        packet.append(119)
                        packet.append(32)
                        packet.append(ord('9'))
                        packet.append(32)
                        for char in str(self.transistor1):
                            packet.append(ord(char))
                        packet.append(13)
                        self.serialConnection.write(packet)

                    elif args[0] == 'setTransistor2':
                        self.transistor2 = args[1]
                        packet = bytearray()
                        packet.append(119)
                        packet.append(32)
                        packet.append(ord('1'))
                        packet.append(ord('0'))
                        packet.append(32)
                        for char in str(self.transistor2):
                            packet.append(ord(char))

                        packet.append(13)
                        self.serialConnection.write(packet)
                    elif args[0] == 'swithADREF':
                        packet = bytearray()
                        packet.append(101)
                        packet.append(13)
                        self.serialConnection.write(packet)
                        if self.adcReference == 3300:
                            self.adcReference = 5000
                        else:
                            self.adcReference = 3300
                    elif args[0] == 'getTemperature1':
                        if args[1] == "Start":
                            self.temperature1DeltaTime = float(args[2])
                            self.temperature1TimeSet = True
                            self.temperature1TimerSetup()
                            self.temperature1TimerStart()
                        elif args[1] == "Stop":
                            self.temperature1TimeSet = False
                            self.temperature1TimerStop()

                    elif args[0] == 'getTemperature2':
                        if args[1] == "Start":
                            self.temperature2DeltaTime = float(args[2])
                            self.temperature2TimeSet = True
                            self.temperature2TimerSetup()
                            self.temperature2TimerStart()
                        elif args[1] == "Stop":
                            self.temperature2TimeSet = False
                            self.temperature2TimerStop()

                if time.time() - self.temperature1_oldtime >= self.temperature1DeltaTime and self.temperature1TimeSet:
                    self.temperature1_oldtime = time.time()
                    packet = bytearray()
                    packet.append(114)
                    packet.append(32)
                    packet.append(ord('1'))
                    packet.append(ord('5'))
                    packet.append(13)
                    self.serialConnection.write(packet)
                    val = self.serialConnection.read(2)
                    temp_volt = (val[0] + val[1] * 256) * (self.adcReference / 1023)
                    temperature1 = (temp_volt - 500) * 0.1;
                    self.newTemperature1Signal.emit(temperature1)

                if time.time() - self.temperature2_oldtime >= self.temperature2DeltaTime and self.temperature2TimeSet:
                    self.temperature2_oldtime = time.time()
                    packet = bytearray()
                    packet.append(114)
                    packet.append(32)
                    packet.append(ord('1'))
                    packet.append(ord('4'))
                    packet.append(13)
                    self.serialConnection.write(packet)
                    val = self.serialConnection.read(2)
                    temp_volt = (val[0] + val[1] * 256) * (self.adcReference / 1023)
                    temperature2 = (temp_volt - 500) * 0.1;
                    self.newTemperature2Signal.emit(temperature2)

                QtWidgets.QApplication.processEvents()


        self.serialConnection.close()

    def stop(self):
        self._isRunning = False

    def temperature1TimerSetup(self):
        self.temperature1_oldtime = time.time()

    def temperature1TimerStart(self):

        self.temperature1TimeSet = True

    def temperature1TimerStop(self):
        self.temperature1TimeSet = False

    def temperature2TimerSetup(self):
        self.temperature2_oldtime = time.time()

    def temperature2TimerStart(self):
        self.temperature2TimeSet = True

    def temperature2TimerStop(self):
        self.temperature2TimeSet = False
