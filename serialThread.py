
#for serial comms
import threading
import serial.tools.list_ports
from serial import Serial
import re
#for storage
import json
import time

from PyQt5 import QtCore
from PyQt5.QtCore import QThread, pyqtSignal



class serialThread (QThread):

    newTemperature1Signal = pyqtSignal(float)
    newTemperature2Signal = pyqtSignal(float)
    closedSignal = pyqtSignal()

    def __init__(self, threadID, name):
        QThread.__init__(self)
        self.closeEvent = threading.Event() #main thread loop

        self.setLed1 = threading.Event()#send pwm to led 1
        self.setLed2 = threading.Event()#send pwm to led 2
        self.setTransistor1 = threading.Event()#send pwm to transistor 1
        self.setTransistor2 = threading.Event()#send pwm to transistor 2

        self.getTemperature1 = threading.Event()#receive temperature 1
        self.getTemperature2 = threading.Event()#receive temperature 2

        self.swithADREF = threading.Event()#switch ad reference

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

        #TODO add setAdcReference event to loop with command 97 (\x61)

    def setParameteres(self, parameters):
        self.serialConnection.bytesize = parameters[0]
        self.serialConnection.parity = parameters[1]
        self.serialConnection.stopbits = parameters[2]
        self.serialConnection.baudrate = parameters[3]
        self.serialConnection.port = parameters[4]

    def run(self):

        self.serialConnection.open()
        if(self.serialConnection.is_open):
            while not self.closeEvent.is_set():
                if not self.getTemperature1.is_set() and self.temperature1TimeSet:
                    self.temperature1TimerStop()
                if not self.getTemperature2.is_set() and self.temperature2TimeSet:
                    self.temperature2TimerStop()
                if self.getTemperature1.is_set() and not self.temperature1TimeSet:
                    self.temperature1TimerSetup()
                    self.temperature1TimerStart()
                if self.getTemperature2.is_set() and not self.temperature2TimeSet:
                    self.temperature2TimerSetup()
                    self.temperature2TimerStart()
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

                if(self.setLed1.is_set()):
                    packet = bytearray()
                    packet.append(119)
                    packet.append(32)
                    packet.append(ord('5'))
                    packet.append(32)

                    for char in str(self.led1):
                        packet.append(ord(char))

                    packet.append(13)
                    self.serialConnection.write(packet)

                    self.setLed1.clear()
                if(self.setLed2.is_set()):
                    packet = bytearray()
                    packet.append(119)
                    packet.append(32)
                    packet.append(ord('6'))
                    packet.append(32)
                    for char in str(self.led2):
                        packet.append(ord(char))

                    packet.append(13)
                    self.serialConnection.write(packet)

                    self.setLed2.clear()
                if (self.setTransistor1.is_set()):
                    packet = bytearray()
                    packet.append(119)
                    packet.append(32)
                    packet.append(ord('9'))
                    packet.append(32)
                    for char in str(self.transistor1):
                        packet.append(ord(char))
                    packet.append(13)
                    self.serialConnection.write(packet)

                    self.setTransistor1.clear()
                if (self.setTransistor2.is_set()):
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

                    self.setTransistor2.clear()
                if self.swithADREF.is_set():
                    packet = bytearray()
                    packet.append(101)
                    packet.append(13)
                    self.serialConnection.write(packet)
                    if self.adcReference == 3300:
                        self.adcReference = 5000
                    else:
                        self.adcReference = 3300
                    self.swithADREF.clear()
        self.serialConnection.close()

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
