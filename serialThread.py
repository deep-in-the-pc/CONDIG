
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
                if self.getTemperature1.is_set() and not self.temperature1_qtimer.isActive():
                    self.temperature1TimerStart()
                if self.getTemperature2.is_set() and not self.temperature2_qtimer.isActive():
                    self.temperature2TimerStart()
                if self.temperature1TimeSet:
                    packet = bytearray()
                    packet.append(114)
                    packet.append(14)
                    packet.append(13)
                    self.serialConnection.write(packet)
                    val = self.serialConnection.read(2)
                    temp_volt = (val[0] + val[1] * 256) * (self.adcReference / 1023)
                    temperature1 = (temp_volt - 500) * 0.1;
                    self.newTemperature1Signal.emit(temperature1)

                    self.temperature1TimeSet = False
                elif(self.temperature2TimeSet):
                    packet = bytearray()
                    packet.append(114)
                    packet.append(15)
                    packet.append(13)
                    self.serialConnection.write(packet)
                    val = self.serialConnection.read(2)
                    temp_volt = (val[0] + val[1] * 256) * (self.adcReference / 1023)
                    temperature2 = (temp_volt - 500) * 0.1;
                    self.newTemperature2Signal.emit(temperature2)

                    self.temperature2TimeSet = False
                elif(self.setLed1.is_set()):
                    packet = bytearray()
                    packet.append(119)
                    packet.append(5)
                    packet.append(self.led1)
                    packet.append(13)
                    self.serialConnection.write(packet)

                    self.setLed1.clear()
                elif(self.setLed2.is_set()):
                    packet = bytearray()
                    packet.append(119)
                    packet.append(6)
                    packet.append(self.led2)
                    packet.append(13)
                    self.serialConnection.write(packet)

                    self.setLed2.clear()
                elif (self.setTransistor1.is_set()):
                    packet = bytearray()
                    packet.append(119)
                    packet.append(9)
                    packet.append(self.transistor1)
                    packet.append(13)
                    self.serialConnection.write(packet)

                    self.setTransistor1.clear()
                elif (self.setTransistor2.is_set()):
                    packet = bytearray()
                    packet.append(119)
                    packet.append(10)
                    packet.append(self.transistor2)
                    packet.append(13)
                    self.serialConnection.write(packet)

                    self.setTransistor2.clear()
        self.serialConnection.close()

    def temperature1TimerSetup(self):
        self.temperature1_qtimer = QtCore.QTimer(self)
        self.temperature1_qtimer.timeout.connect(self.temperature1TimerCB)

    def temperature2TimerStart(self):
        self.temperature1_qtimer.start(self.temperature1DeltaTime)

    def temperature2TimerSetup(self):
        self.temperature2_qtimer = QtCore.QTimer(self)
        self.temperature2_qtimer.timeout.connect(self.temperature2TimerCB)

    def temperature2TimerStart(self):
        self.temperature2_qtimer.start(self.temperature2DeltaTime)

    def temperature1TimerCB(self):
        self.temperature1TimeSet = True

    def temperature2TimerCB(self):
        self.temperature2TimeSet = True
