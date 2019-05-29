# -*- coding: latin-1 -*-


from operator import itemgetter
import time as t
import sys
import os
import threading
import datetime
import math
import numpy as np
from serialThread import *

from PyQt5 import QtWidgets, QtGui, QtCore
try:
    from QtCore import QString
except ImportError:
    QString = str
from PyQt5.QtCore import QThread, pyqtSignal
from SERT_GUI_CONDIG import Ui_MainWindow
from pyqtgraph import *

class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(ApplicationWindow, self).__init__()

        #PyQtGraph config
        setConfigOption('background', 'w')
        setConfigOption('foreground', 'k')

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.initSetup()

        #TODO implement pid tunning from condig classes
        #TODO implement option to delete models
        #TODO Add save button to graphs for data
        #TODO Change serial connection from thread to process

    def initSetup(self):
        # SerialThread
        self.serialThreadSetup()

        # Timers
        self.setupTimers()

        # Variables
        self.setupVariables()

        self.loadModelos()

        #update model list
        self.updateModelListView()

        # CallBacks
        self.setupCallbacks()

    def setupVariables(self):
        #Serial
        self.is_connected = False

        #Model
        self.isCreatingModel1 = False
        self.modelo1Temp0 = None
        self.modelo1TempSS = None
        self.modelo1DeltaTemp = None
        self.modelo1K = None
        self.modelo1TauSD = None
        self.modelo1TauCD = None
        self.modelo1Delay = None
        self.ssReady1 = False
        self.ssReady1Clicked = False

        self.isCreatingModel2 = False
        self.modelo2Temp0 = None
        self.modelo2TempSS = None
        self.modelo2DeltaTemp = None
        self.modelo2K = None
        self.modelo2TauSD = None
        self.modelo2TauCD = None
        self.modelo2Delay = None
        self.ssReady2 = False
        self.ssReady2Clicked = False

        #Control
        self.t1TargetTemp = None
        self.t1TempError = None
        self.t1ControlP = 0
        self.t1ControlI = 0
        self.t1ControlD = 0
        self.t1ControlAWTt = 0
        self.t1ControlLastError = 0

        self.t2TargetTemp = None
        self.t2TempError = None
        self.t2ControlP = 0
        self.t2ControlI = 0
        self.t2ControlD = 0
        self.t2ControlAWTt = 0
        self.t2ControlLastError = 0

        self.isControlOnOff1 = False
        self.isControlOnOff2 = False

        self.isControlHist1 = False
        self.isControlHist2 = False

        self.isControlPID1 = False
        self.isControlPID2 = False

        self.isControlAW1 = False
        self.isControlAW2 = False

        #Graph
        self.temp1TA = None
        self.temp2TA = None
        self.plots = []
        self.plotsObjects = []
        self.maxnumberofpoints1 = None
        self.maxnumberofpoints2 = None
        self.sizeOfArraysInSeconds = 3600
        self.graph1_isUpdating = False
        self.graph2_isUpdating = False
        

        self.temp1T = 0
        self.temp1P = 0
        self.temp1I = 0
        self.temp1D = 0
        self.temp1U = 0

        self.temp2T = 0
        self.temp2P = 0
        self.temp2I = 0
        self.temp2D = 0
        self.temp2U = 0

    def setupTimers(self):
        self.comlist_qtimer = QtCore.QTimer(self)
        self.comlist_qtimer.timeout.connect(self.getCOMList)
        self.comlist_qtimer_interval = 100
        self.comlist_qtimer.start(self.comlist_qtimer_interval)
        self.guiupdate_qtimer = QtCore.QTimer(self)
        self.guiupdate_qtimer.timeout.connect(self.updateGUI)
        self.guiupdate_qtimer_interval = 1000

    def setupCallbacks(self):
        #CallBacks

        #conectarButton Callback
        self.ui.conectarButton.clicked.connect(self.connectCB)
        #t1EnviarButton Callback
        self.ui.t1EnviarButton.clicked.connect(self.t1EnviarCB)
        #t2EnviarButton Callback
        self.ui.t2EnviarButton.clicked.connect(self.t2EnviarCB)
        #l1EnviarButton Callback
        self.ui.l1EnviarButton.clicked.connect(self.l1EnviarCB)
        #l2EnviarButton Callback
        self.ui.l2EnviarButton.clicked.connect(self.l2EnviarCB)
        # temp1StartQButton Callback
        self.ui.temp1StartQButton.clicked.connect(self.temp1StartQCB)
        # temp1StartQButton Callback
        self.ui.temp2StartQButton.clicked.connect(self.temp2StartQCB)
        #temp1TCheckBox Callback
        self.ui.temp1TcheckBox.stateChanged.connect(self.temp1TcheckboxCB)
        #temp1PIDUCheckBox Callback
        self.ui.temp1PcheckBox.stateChanged.connect(self.temp1PIDUcheckboxCB)
        self.ui.temp1IcheckBox.stateChanged.connect(self.temp1PIDUcheckboxCB)
        self.ui.temp1DcheckBox.stateChanged.connect(self.temp1PIDUcheckboxCB)
        self.ui.temp1UcheckBox.stateChanged.connect(self.temp1PIDUcheckboxCB)
        # temp2TCheckBox Callback
        self.ui.temp2TcheckBox.stateChanged.connect(self.temp2TcheckboxCB)
        #temp2PIDUCheckBox Callback
        self.ui.temp2PcheckBox.stateChanged.connect(self.temp2PIDUcheckboxCB)
        self.ui.temp2IcheckBox.stateChanged.connect(self.temp2PIDUcheckboxCB)
        self.ui.temp2DcheckBox.stateChanged.connect(self.temp2PIDUcheckboxCB)
        self.ui.temp2UcheckBox.stateChanged.connect(self.temp2PIDUcheckboxCB)
        #temp1TAEdit Edited Callback
        self.ui.temp1TAEdit.textEdited.connect(self.temp1TAEditValidateCB)
        #temp2TAEdit Edited Callback
        self.ui.temp2TAEdit.textEdited.connect(self.temp2TAEditValidateCB)
        #t1CriarModeloButton Callback
        self.ui.t1CriarModeloButton.clicked.connect(self.createModel1)
        #t2CriarModeloButton Callback
        self.ui.t2CriarModeloButton.clicked.connect(self.createModel2)
        #ref3v3RButton Callback
        self.ui.ref3v3RButton.clicked.connect(self.switchADRef)
        #ref5vButton Callback
        self.ui.ref5vButton.clicked.connect(self.switchADRef)
        #Controlo tabChange Callback
        self.ui.Controlo.currentChanged.connect(self.currentChangedControloCB)
        #modelListWidget line selected Callback
        self.ui.modelListWidget.itemClicked.connect(self.modelListWidgetICCB)
        #ooT1StartButton Callback
        self.ui.ooT1StartButton.clicked.connect(self.ooT1StartCB)
        #ooT2StartButton Callback
        self.ui.ooT2StartButton.clicked.connect(self.ooT2StartCB)
        #hstT1StartButton Callback
        self.ui.hstT1StartButton.clicked.connect(self.hstT1StartCB)
        #hstT2StartButton Callback
        self.ui.hstT2StartButton.clicked.connect(self.hstT2StartCB)
        #pidT1StartButton Callback
        self.ui.pidT1StartButton.clicked.connect(self.pidT1StartCB)
        #pidT2StartButton Callback
        self.ui.pidT2StartButton.clicked.connect(self.pidT2StartCB)
        #pidT1AWcheckBox Callback
        self.ui.pidT1AWcheckBox.stateChanged.connect(self.pidT1AWcheckBoxCB)
        #pidT2AWcheckBox Callback
        self.ui.pidT2AWcheckBox.stateChanged.connect(self.pidT2AWcheckBoxCB)
        #pidT1PDSBox valueChanged Callback
        self.ui.pidT1PDSBox.valueChanged.connect(self.pidT1AWcheckCB)
        #pidT1IDSBox valueChanged Callback
        self.ui.pidT1IDSBox.valueChanged.connect(self.pidT1AWcheckCB)
        #pidT1DDSBox valueChanged Callback
        self.ui.pidT1DDSBox.valueChanged.connect(self.pidT1AWcheckCB)
        #pidT2PDSBox valueChanged Callback
        self.ui.pidT2PDSBox.valueChanged.connect(self.pidT2AWcheckCB)
        #pidT2IDSBox valueChanged Callback
        self.ui.pidT2IDSBox.valueChanged.connect(self.pidT2AWcheckCB)
        #pidT2DDSBox valueChanged Callback
        self.ui.pidT2DDSBox.valueChanged.connect(self.pidT2AWcheckCB)
    #Communication

    def getCOMList(self):

        comlist = [comport.device for comport in serial.tools.list_ports.comports()]
        if len(comlist) != self.ui.portaCBox.count():
            self.ui.portaCBox.clear()
            self.ui.portaCBox.addItems(comlist)
            self.serialCOM = self.ui.portaCBox.currentText()

        if self.ui.portaCBox.count() == 0:
            self.serialCOM = None

        if len(comlist)>0 and self.comlist_qtimer_interval == 100:
            self.comlist_qtimer_interval = 2000
            self.comlist_qtimer.stop()
            self.comlist_qtimer.start(self.comlist_qtimer_interval)
        else:
            self.comlist_qtimer_interval = 100
            self.comlist_qtimer.stop()
            self.comlist_qtimer.start(self.comlist_qtimer_interval)

    def serialThreadSetup(self):
        self.serialListenerThread = serialThread(1, "SerialListener")

        self.serialConnectionParameters = []
        self.serialConnectionParameters.append(serial.EIGHTBITS)
        self.serialConnectionParameters.append(serial.PARITY_NONE)
        self.serialConnectionParameters.append(serial.STOPBITS_ONE)
        self.serialConnectionParameters.append(115200)

        self.serialListenerThread.newTemperature1Signal.connect(self.temperature1CB)
        self.serialListenerThread.newTemperature2Signal.connect(self.temperature2CB)

        self.serialListenerThread.closeEvent.set()

    def serialThreadStart(self):

        self.serialConnectionParameters.append(self.serialCOM)
        self.serialListenerThread.setParameteres(self.serialConnectionParameters)

        self.comlist_qtimer.stop()

        self.serialListenerThread.start()
        self.is_connected = True

    def serialThreadStop(self):
        self.serialListenerThread.closeEvent.set()
        self.comlist_qtimer.start(self.comlist_qtimer_interval)

        self.is_connected = False

    #Modelos

    def createModel1(self):
        if self.is_connected and not self.ssReady1:

            #disable all other transistor 1 related functions
            self.ui.t1CriarModeloButton.setEnabled(False)
            self.ui.t1EnviarButton.setEnabled(False)
            self.ui.t1SBox.setEnabled(False)
            self.ui.temp1StartQButton.setEnabled(False)
            self.ui.temp1TAEdit.setEnabled(False)
            self.ui.ooT1StartButton.setEnabled(False)
            self.ui.hstT1StartButton.setEnabled(False)
            self.ui.pidT1StartButton.setEnabled(False)
            self.ui.t1CalibrateButton.setEnabled(False)
            self.ui.temp1PcheckBox.setEnabled(False)
            self.ui.temp1IcheckBox.setEnabled(False)
            self.ui.temp1DcheckBox.setEnabled(False)
            self.ui.temp1UcheckBox.setEnabled(False)
            self.isCreatingModel1 = True

            #Send Input
            self.temp1U = self.ui.t1SBox.value()
            self.serialListenerThread.transistor1 = self.temp1U
            self.serialListenerThread.setTransistor1.set()

            #Receber Dados
            self.graph1_isUpdating = True
            self.ui.temp1StartQButton.setText("Parar")
            self.startGraph1Update()

        elif self.ssReady1:
            self.ssReady1Clicked = True

    def finishModel1(self, tss):

        self.isCreatingModel1 = False
        self.serialListenerThread.transistor1 = 0
        self.serialListenerThread.setTransistor1.set()

        self.graph1_isUpdating = False
        self.ui.temp1StartQButton.setText("Começar")
        self.ssReady1 = False
        self.ui.t1CriarModeloButton.setText("Criar Modelo")
        self.stopGraph1Update()

        self.modelo1Temp0 = round(self.temp1T_y[0],3)
        self.modelo1TempSS = round(tss,3)
        self.modelo1DeltaTemp = round(self.modelo1TempSS - self.modelo1Temp0,3)
        self.modelo1K = round(self.modelo1DeltaTemp / (self.temp1U/255.0),3)

        index = np.where(self.temp1T_y >= (self.modelo1DeltaTemp*0.632)+self.modelo1Temp0)[0]

        self.modelo1TauSD = round(self.temp1Time_x[index[0]],3)

        t1index = np.where(self.temp1T_y >= (self.modelo1DeltaTemp*0.283)+self.modelo1Temp0)[0]
        t1 = self.temp1Time_x[t1index[0]]
        t2index = np.where(self.temp1T_y >= (self.modelo1DeltaTemp*0.632)+self.modelo1Temp0)[0]
        t2 = self.temp1Time_x[t2index[0]]


        self.modelo1TauCD = round((3.0/2.0)*(t2-t1),3)
        self.modelo1Delay = round(t2 - self.modelo1TauCD,3)

        #Store model
        modelName = str(round(self.modelo1Temp0,2))+"-"+str(round(100*self.temp1U/255.0,2))
        self.ModelList["1"][modelName] = {'T0':self.modelo1Temp0, 'TSS':self.modelo1TempSS, 'DeltaTemp':self.modelo1DeltaTemp, 'K':self.modelo1K, 'TauSD':self.modelo1TauSD, 'TauCD':self.modelo1TauCD, 'Delay':self.modelo1Delay}
        self.saveModelo()

        self.updateModelListView()

        txt = "T0: "+str(self.modelo1Temp0)+"\nTss: "+str(self.modelo1TempSS)+"\n\u0394T: "+str(self.modelo1DeltaTemp)+"\n K: "+str(self.modelo1K)+"\n\nModelo sem delay:\n\n\u03C4: "+str(self.modelo1TauSD)+"\n\nModelo com delay:\n\n\u03C4: "+str(self.modelo1TauCD)+"\n \u03C4D: "+str(self.modelo1Delay)
        self.ui.t1ModelTBrowser.setText(txt)

        self.ui.t1CriarModeloButton.setEnabled(True)
        self.ui.t1EnviarButton.setEnabled(True)
        self.ui.t1SBox.setEnabled(True)
        self.ui.temp1StartQButton.setEnabled(True)
        self.ui.temp1TAEdit.setEnabled(True)
        self.ui.ooT1StartButton.setEnabled(True)
        self.ui.hstT1StartButton.setEnabled(True)
        self.ui.pidT1StartButton.setEnabled(True)
        self.ui.t1CalibrateButton.setEnabled(True)
        self.ui.temp1PcheckBox.setEnabled(True)
        self.ui.temp1IcheckBox.setEnabled(True)
        self.ui.temp1DcheckBox.setEnabled(True)
        self.ui.temp1UcheckBox.setEnabled(True)
    
    def createModel2(self):
        if self.is_connected and not self.ssReady2:

            #disable all other transistor 2 related functions
            self.ui.t2CriarModeloButton.setEnabled(False)
            self.ui.t2EnviarButton.setEnabled(False)
            self.ui.t2SBox.setEnabled(False)
            self.ui.temp2StartQButton.setEnabled(False)
            self.ui.temp2TAEdit.setEnabled(False)
            self.ui.ooT2StartButton.setEnabled(False)
            self.ui.hstT2StartButton.setEnabled(False)
            self.ui.pidT2StartButton.setEnabled(False)
            self.ui.t2CalibrateButton.setEnabled(False)
            self.ui.temp2PcheckBox.setEnabled(False)
            self.ui.temp2IcheckBox.setEnabled(False)
            self.ui.temp2DcheckBox.setEnabled(False)
            self.ui.temp2UcheckBox.setEnabled(False)
            self.isCreatingModel2 = True

            #Send Input
            self.temp2U = self.ui.t2SBox.value()
            self.serialListenerThread.transistor2 = self.temp2U
            self.serialListenerThread.setTransistor2.set()

            #Receber Dados
            self.graph2_isUpdating = True
            self.ui.temp2StartQButton.setText("Parar")
            self.startGraph2Update()

        elif self.ssReady2:
            self.ssReady2Clicked = True

    def finishModel2(self, tss):

        self.isCreatingModel2 = False
        self.serialListenerThread.transistor2 = 0
        self.serialListenerThread.setTransistor2.set()

        self.graph2_isUpdating = False
        self.ui.temp2StartQButton.setText("Começar")
        self.ssReady2 = False
        self.ui.t2CriarModeloButton.setText("Criar Modelo")
        self.stopGraph2Update()

        self.modelo2Temp0 = round(self.temp2T_y[0],3)
        self.modelo2TempSS = round(tss,3)
        self.modelo2DeltaTemp = round(self.modelo2TempSS - self.modelo2Temp0,3)
        self.modelo2K = round(self.modelo2DeltaTemp / (self.temp2U/255.0),3)

        index = np.where(self.temp2T_y >= (self.modelo2DeltaTemp*0.632)+self.modelo2Temp0)[0]

        self.modelo2TauSD = round(self.temp2Time_x[index[0]],3)

        t1index = np.where(self.temp2T_y >= (self.modelo2DeltaTemp*0.283)+self.modelo2Temp0)[0]
        t1 = self.temp2Time_x[t1index[0]]
        t2index = np.where(self.temp2T_y >= (self.modelo2DeltaTemp*0.632)+self.modelo2Temp0)[0]
        t2 = self.temp2Time_x[t2index[0]]


        self.modelo2TauCD = round((3.0/2.0)*(t2-t1),3)
        self.modelo2Delay = round(t2 - self.modelo2TauCD,3)

        #Store model
        modelName = str(round(self.modelo2Temp0,2))+"-"+str(round(100*self.temp2U/255.0,2))
        self.ModelList["2"][modelName] = {'T0':self.modelo2Temp0, 'TSS':self.modelo2TempSS, 'DeltaTemp':self.modelo2DeltaTemp, 'K':self.modelo2K, 'TauSD':self.modelo2TauSD, 'TauCD':self.modelo2TauCD, 'Delay':self.modelo2Delay}
        self.saveModelo()

        self.updateModelListView()

        txt = "T0: "+str(self.modelo2Temp0)+"\nTss: "+str(self.modelo2TempSS)+"\n\u0394T: "+str(self.modelo2DeltaTemp)+"\n K: "+str(self.modelo2K)+"\n\nModelo sem delay:\n\n\u03C4: "+str(self.modelo2TauSD)+"\n\nModelo com delay:\n\n\u03C4: "+str(self.modelo2TauCD)+"\n \u03C4D: "+str(self.modelo2Delay)
        self.ui.t2ModelTBrowser.setText(txt)

        self.ui.t2CriarModeloButton.setEnabled(True)
        self.ui.t2EnviarButton.setEnabled(True)
        self.ui.t2SBox.setEnabled(True)
        self.ui.temp2StartQButton.setEnabled(True)
        self.ui.temp2TAEdit.setEnabled(True)
        self.ui.ooT2StartButton.setEnabled(True)
        self.ui.hstT2StartButton.setEnabled(True)
        self.ui.pidT2StartButton.setEnabled(True)
        self.ui.t2CalibrateButton.setEnabled(True)
        self.ui.temp2PcheckBox.setEnabled(True)
        self.ui.temp2IcheckBox.setEnabled(True)
        self.ui.temp2DcheckBox.setEnabled(True)
        self.ui.temp2UcheckBox.setEnabled(True)

    def enableSteadyStateReady1(self):
        self.ssReady1 = True
        self.ui.t1CriarModeloButton.setEnabled(True)
        self.ui.t1CriarModeloButton.setText("Terminar Modelo")

    def enableSteadyStateReady2(self):
        self.ssReady2 = True
        self.ui.t2CriarModeloButton.setEnabled(True)
        self.ui.t2CriarModeloButton.setText("Terminar Modelo")

    def saveModelo(self):
        with open("modelos.json", 'w') as outfile:
            json.dump(self.ModelList, outfile, indent=4)

    def loadModelos(self):
        try:
            with open("modelos.json") as json_file:
                self.ModelList = json.load(json_file)
        except Exception:
            self.ModelList = {"1":{}, "2":{}}

    def updateModelListView(self):

        self.ui.modelListWidget.clear()

        for modelo in self.ModelList["1"]:
            parameters = self.ModelList["1"][modelo]

            dataListParam = parameters["T0"], parameters["TSS"], parameters["DeltaTemp"], parameters["K"], parameters["TauSD"], parameters["TauCD"], parameters["Delay"],

            listEntry = QtWidgets.QListWidgetItem()
            listEntry.setText("Transistor 1 - " + modelo.split('-')[0] + ' - '  +modelo.split('-')[1] + '%')
            listEntry.setData(32, dataListParam)
            self.ui.modelListWidget.addItem(listEntry)

        for modelo in self.ModelList["2"]:
            parameters = self.ModelList["2"][modelo]

            dataListParam = parameters["T0"], parameters["TSS"], parameters["DeltaTemp"], parameters["K"], parameters["TauSD"], parameters["TauCD"], parameters["Delay"],

            listEntry = QtWidgets.QListWidgetItem()
            listEntry.setText("Transistor 2 - " + modelo.split('-')[0] + ' - '  +modelo.split('-')[1] + '%')
            listEntry.setData(32, dataListParam)
            self.ui.modelListWidget.addItem(listEntry)

    #Graph

    def updateGUI(self):
        nplots = 0
        for n, plot in self.plots:
            if n == 1:
                if self.graph1_isUpdating:
                    for item in self.plotsObjects[nplots][0].listDataItems():
                        if item.name() == "Temperatura 1":
                            self.plotsObjects[nplots][0].removeItem(item)
                    temp = self.plotsObjects[nplots][0].plot(self.temp1Time_x[:self.temp1Count], self.temp1T_y[:self.temp1Count], pen=(255, 0, 0),name="Temperatura 1")
                    self.plotsObjects[nplots][1].removeItem('Temperatura 1')
                    self.plotsObjects[nplots][1].addItem(temp, 'Temperatura 1')
                nplots = nplots + 1
            elif n == 2:
                if self.graph1_isUpdating:

                    if 'P' in plot:
                        for item in self.plotsObjects[nplots][0].listDataItems():
                            if item.name() == "Componente proporcional 1":
                                self.plotsObjects[nplots][0].removeItem(item)
                        temp = self.plotsObjects[nplots][0].plot(self.temp1Time_x[:self.temp1Count], self.temp1P_y[:self.temp1Count], pen=(255, 0, 0),
                                                                 name="Componente proporcional 1")
                        self.plotsObjects[nplots][1].removeItem('Componente proporcional 1')
                        self.plotsObjects[nplots][1].addItem(temp, 'Componente proporcional 1')
                    if 'I' in plot:
                        for item in self.plotsObjects[nplots][0].listDataItems():
                            if item.name() == "Componente integrativa 1":
                                self.plotsObjects[nplots][0].removeItem(item)
                        temp = self.plotsObjects[nplots][0].plot(self.temp1Time_x[:self.temp1Count], self.temp1I_y[:self.temp1Count], pen=(0, 255, 0),
                                                                 name="Componente integrativa 1")
                        self.plotsObjects[nplots][1].removeItem('Componente integrativa 1')
                        self.plotsObjects[nplots][1].addItem(temp, 'Componente integrativa 1')
                    if 'D' in plot:
                        for item in self.plotsObjects[nplots][0].listDataItems():
                            if item.name() == "Componente derivativa 1":
                                self.plotsObjects[nplots][0].removeItem(item)
                        temp = self.plotsObjects[nplots][0].plot(self.temp1Time_x[:self.temp1Count], self.temp1D_y[:self.temp1Count], pen=(0, 0, 255),
                                                                 name="Componente derivativa 1")
                        self.plotsObjects[nplots][1].removeItem('Componente derivativa 1')
                        self.plotsObjects[nplots][1].addItem(temp, 'Componente derivativa 1')
                    if 'U' in plot:
                        for item in self.plotsObjects[nplots][0].listDataItems():
                            if item.name() == "Sinal de Controlo 1":
                                self.plotsObjects[nplots][0].removeItem(item)
                        temp = self.plotsObjects[nplots][0].plot(self.temp1Time_x[:self.temp1Count], self.temp1U_y[:self.temp1Count], pen=(191, 191, 0),
                                                                 name="Sinal de Controlo 1")
                        self.plotsObjects[nplots][1].removeItem('Sinal de Controlo 1')
                        self.plotsObjects[nplots][1].addItem(temp, 'Sinal de Controlo 1')

                nplots = nplots + 1

            elif n == 3:
                if self.graph2_isUpdating:

                    for item in self.plotsObjects[nplots][0].listDataItems():
                        if item.name() == "Temperatura 2":
                            self.plotsObjects[nplots][0].removeItem(item)
                    temp = self.plotsObjects[nplots][0].plot(self.temp2Time_x[:self.temp2Count], self.temp2T_y[:self.temp2Count], pen=(255, 0, 0),name="Temperatura 2")
                    self.plotsObjects[nplots][1].removeItem('Temperatura 2')
                    self.plotsObjects[nplots][1].addItem(temp, 'Temperatura 2')
                nplots = nplots + 1

            elif n == 4:
                if self.graph2_isUpdating:

                    if 'P' in plot:
                        for item in self.plotsObjects[nplots][0].listDataItems():
                            if item.name() == "Componente proporcional 2":
                                self.plotsObjects[nplots][0].removeItem(item)
                        temp = self.plotsObjects[nplots][0].plot(self.temp2Time_x[:self.temp2Count], self.temp2P_y[:self.temp2Count], pen=(255, 0, 0),
                                                                 name="Componente proporcional 2")
                        self.plotsObjects[nplots][1].removeItem('Componente proporcional 2')
                        self.plotsObjects[nplots][1].addItem(temp, 'Componente proporcional 2')
                    if 'I' in plot:
                        for item in self.plotsObjects[nplots][0].listDataItems():
                            if item.name() == "Componente integrativa 2":
                                self.plotsObjects[nplots][0].removeItem(item)
                        temp = self.plotsObjects[nplots][0].plot(self.temp2Time_x[:self.temp2Count], self.temp2I_y[:self.temp2Count], pen=(0, 255, 0),
                                                                 name="Componente integrativa 2")
                        self.plotsObjects[nplots][1].removeItem('Componente integrativa 2')
                        self.plotsObjects[nplots][1].addItem(temp, 'Componente integrativa 2')
                    if 'D' in plot:
                        for item in self.plotsObjects[nplots][0].listDataItems():
                            if item.name() == "Componente derivativa 2":
                                self.plotsObjects[nplots][0].removeItem(item)
                        temp = self.plotsObjects[nplots][0].plot(self.temp2Time_x[:self.temp2Count], self.temp2D_y[:self.temp2Count], pen=(0, 0, 255),
                                                                 name="Componente derivativa 2")
                        self.plotsObjects[nplots][1].removeItem('Componente derivativa 2')
                        self.plotsObjects[nplots][1].addItem(temp, 'Componente derivativa 2')
                    if 'U' in plot:
                        for item in self.plotsObjects[nplots][0].listDataItems():
                            if item.name() == "Sinal de Controlo 2":
                                self.plotsObjects[nplots][0].removeItem(item)
                        temp = self.plotsObjects[nplots][0].plot(self.temp2Time_x[:self.temp2Count], self.temp2U_y[:self.temp2Count], pen=(191, 191, 0),
                                                                 name="Sinal de Controlo 2")
                        self.plotsObjects[nplots][1].removeItem('Sinal de Controlo 2')
                        self.plotsObjects[nplots][1].addItem(temp, 'Sinal de Controlo 2')

                nplots = nplots + 1

    def graphWindowSetup(self):
        self.ui.graphWindow.clear()
        self.plotsObjects = []
        self.plots.sort(key=itemgetter(0))
        nplots = 0
        for n, plot in self.plots:
            if n == 1:
                plot = self.ui.graphWindow.addPlot(row=nplots, col=0, title='Temperatura 1')
                plot.showGrid(x=True, y=True, alpha=0.7)
                legend = LegendItem((80, 30), offset=(60, 30))
                legend.setParentItem(plot)
                self.plotsObjects.append((plot, legend))
                nplots = nplots + 1
            elif n == 2:

                txt = 'Transistor 1 - '
                if 'P' in plot:
                    txt = txt + 'P'
                if 'I' in plot:
                    txt = txt + 'I'
                if 'D' in plot:
                    txt = txt + 'D'
                if 'U' in plot:
                    txt = txt + 'U'
                plot = self.ui.graphWindow.addPlot(row=nplots, col=0, title=txt)
                plot.showGrid(x=True, y=True, alpha=0.7)
                legend = LegendItem((80, 30), offset=(60, 30))
                legend.setParentItem(plot)
                self.plotsObjects.append((plot, legend))
                nplots = nplots + 1
            elif n == 3:

                plot = self.ui.graphWindow.addPlot(row=nplots, col=0, title='Temperatura 2')
                plot.showGrid(x=True, y=True, alpha=0.7)
                legend = LegendItem((80, 30), offset=(60, 30))
                legend.setParentItem(plot)
                self.plotsObjects.append((plot, legend))
                nplots = nplots + 1
            elif n == 4:

                txt = 'Transistor 2 - '
                if 'P' in plot:
                    txt = txt + 'P'
                if 'I' in plot:
                    txt = txt + 'I'
                if 'D' in plot:
                    txt = txt + 'D'
                if 'U' in plot:
                    txt = txt + 'U'

                plot = self.ui.graphWindow.addPlot(row=nplots, col=0, title=txt)
                plot.showGrid(x=True, y=True, alpha=0.7)
                legend = LegendItem((80, 30), offset=(60, 30))
                legend.setParentItem(plot)
                self.plotsObjects.append((plot, legend))
                nplots = nplots + 1

    def graphArraysSetup(self, plot):
        if plot == 1:
            if not self.isCreatingModel1:
                self.temp1Count = 0
                self.temp1Time_x = np.zeros(self.maxnumberofpoints1)
                
                self.temp1T_y = np.zeros(self.maxnumberofpoints1)
                self.temp1P_y = np.zeros(self.maxnumberofpoints1)
                self.temp1I_y = np.zeros(self.maxnumberofpoints1)
                self.temp1D_y = np.zeros(self.maxnumberofpoints1)
                self.temp1U_y = np.zeros(self.maxnumberofpoints1)
            else:
                self.temp1Count = 0
                self.temp1Time_x = np.zeros(round(self.sizeOfArraysInSeconds * (1000.0 / self.temp1TA)))
                self.temp1T_y = np.zeros(round(self.sizeOfArraysInSeconds * (1000.0 / self.temp1TA)))
        elif plot == 2:
            if not self.isCreatingModel2:
                self.temp2Count = 0
                self.temp2Time_x = np.zeros(self.maxnumberofpoints2)

                self.temp2T_y = np.zeros(self.maxnumberofpoints2)
                self.temp2P_y = np.zeros(self.maxnumberofpoints2)
                self.temp2I_y = np.zeros(self.maxnumberofpoints2)
                self.temp2D_y = np.zeros(self.maxnumberofpoints2)
                self.temp2U_y = np.zeros(self.maxnumberofpoints2)
            else:
                self.temp2Count = 0
                self.temp2Time_x = np.zeros(round(self.sizeOfArraysInSeconds * (1000.0 / self.temp2TA)))
                self.temp2T_y = np.zeros(round(self.sizeOfArraysInSeconds * (1000.0 / self.temp2TA)))

    def startGraph1Update(self):
        self.serialListenerThread.temperature1DeltaTime = self.temp1TA/1000.0
        self.serialListenerThread.getTemperature1.set()
        self.maxnumberofpoints1 = round(self.sizeOfArraysInSeconds * (1000.0 / self.temp1TA))
        self.graphArraysSetup(1)
        if not self.guiupdate_qtimer.isActive():
            self.ui.ref3v3RButton.setEnabled(False)
            self.ui.ref5vButton.setEnabled(False)
            self.guiupdate_qtimer.start(self.guiupdate_qtimer_interval)

    def stopGraph1Update(self):
        self.serialListenerThread.getTemperature1.clear()
        if not self.graph1_isUpdating and not self.graph2_isUpdating:
            self.guiupdate_qtimer.stop()
            self.ui.ref3v3RButton.setEnabled(True)
            self.ui.ref5vButton.setEnabled(True)

    def startGraph2Update(self):
        self.serialListenerThread.temperature2DeltaTime = self.temp2TA / 1000.0
        self.serialListenerThread.getTemperature2.set()
        self.maxnumberofpoints2 = round(self.sizeOfArraysInSeconds * (1000.0 / self.temp2TA))
        self.graphArraysSetup(2)
        if not self.guiupdate_qtimer.isActive():
            self.ui.ref3v3RButton.setEnabled(False)
            self.ui.ref5vButton.setEnabled(False)
            self.guiupdate_qtimer.start(self.guiupdate_qtimer_interval)

    def stopGraph2Update(self):
        self.serialListenerThread.getTemperature2.clear()
        if not self.graph1_isUpdating and not self.graph2_isUpdating:
            self.guiupdate_qtimer.stop()
            self.ui.ref3v3RButton.setEnabled(True)
            self.ui.ref5vButton.setEnabled(True)
            
    #Callbacks

    def connectCB(self):

        if not self.serialListenerThread.closeEvent.is_set():
            self.stopGraph1Update()
            self.stopGraph2Update()
            self.serialListenerThread.newTemperature1Signal.disconnect(self.temperature1CB)
            self.serialListenerThread.newTemperature2Signal.disconnect(self.temperature2CB)
            self.serialThreadStop()
            self.ui.setupUi(self)
            self.initSetup()
        elif(self.serialCOM != None):
            self.serialListenerThread.closeEvent.clear()
            self.serialThreadStart()
            if(self.serialListenerThread.isRunning()):
                self.ui.Controlo.setCurrentIndex(0)
                self.ui.connectionLabel.setText("Conexão: Ligado")
                # If connection is established set text as disconnect
                self.ui.conectarButton.setText("Disconnect")
                self.ui.Controlo.setEnabled(True)
                self.ui.frame.setEnabled(True)
                self.ui.temp1TAEdit.setEnabled(True)
                self.ui.temp2TAEdit.setEnabled(True)
                self.ui.ref3v3RButton.setEnabled(True)
                self.ui.ref5vButton.setEnabled(True)

                self.ui.temp1TAEdit.setText('500')
                self.ui.temp1TcheckBox.setEnabled(True)
                self.ui.temp1PcheckBox.setEnabled(True)
                self.ui.temp1IcheckBox.setEnabled(True)
                self.ui.temp1DcheckBox.setEnabled(True)
                self.ui.temp1UcheckBox.setEnabled(True)
                self.temp1TA = 500
                self.ui.temp2TAEdit.setText('500')
                self.ui.temp2TcheckBox.setEnabled(True)
                self.ui.temp2PcheckBox.setEnabled(True)
                self.ui.temp2IcheckBox.setEnabled(True)
                self.ui.temp2DcheckBox.setEnabled(True)
                self.ui.temp2UcheckBox.setEnabled(True)
                self.temp2TA = 500

    def t1EnviarCB(self):
        if self.is_connected:
            self.temp1U = self.ui.t1SBox.value()
            self.serialListenerThread.transistor1 = self.temp1U
            self.serialListenerThread.setTransistor1.set()

    def t2EnviarCB(self):
        if self.is_connected:
            self.temp2U = self.ui.t2SBox.value()
            self.serialListenerThread.transistor2 = self.temp2U
            self.serialListenerThread.setTransistor2.set()

    def l1EnviarCB(self):
        if self.is_connected:
            self.serialListenerThread.led1 = self.ui.l1SBox.value()
            self.serialListenerThread.setLed1.set()

    def l2EnviarCB(self):
        if self.is_connected:
            self.serialListenerThread.led2 = self.ui.l2SBox.value()
            self.serialListenerThread.setLed2.set()

    def temp1TcheckboxCB(self, state):

        if state==2:
            self.plots.append((1, 'temp1T'))
        if(state==0):
            self.plots.remove((1, 'temp1T'))

        #self.graphArraysSetup(1)
        self.graphWindowSetup()

    def temp1PIDUcheckboxCB(self, state):

        for n, plot in self.plots:
            if n == 2:
                self.plots.remove((n, plot))
                break

        txt = "temp1"
        if self.ui.temp1PcheckBox.isChecked():
            txt = txt + "P"
        if self.ui.temp1IcheckBox.isChecked():
            txt = txt + "I"
        if self.ui.temp1DcheckBox.isChecked():
            txt = txt + "D"
        if self.ui.temp1UcheckBox.isChecked():
            txt = txt + "U"
        if not txt == "temp1":
            self.plots.append((2, txt))

        #self.graphArraysSetup(1)
        self.graphWindowSetup()

    def temp2TcheckboxCB(self, state):
        if state==2:
            self.plots.append((3, 'temp2T'))
        if(state==0):
            self.plots.remove((3, 'temp2T'))

        #self.graphArraysSetup(2)
        self.graphWindowSetup()

    def temp2PIDUcheckboxCB(self, state):

        for n, plot in self.plots:
            if n == 4:
                self.plots.remove((n, plot))
                break

        txt = "temp2"
        if self.ui.temp2PcheckBox.isChecked():
            txt = txt + "P"
        if self.ui.temp2IcheckBox.isChecked():
            txt = txt + "I"
        if self.ui.temp2DcheckBox.isChecked():
            txt = txt + "D"
        if self.ui.temp2UcheckBox.isChecked():
            txt = txt + "U"
        if not txt == "temp2":
            self.plots.append((4, txt))

        #self.graphArraysSetup(2)
        self.graphWindowSetup()

    def temp1TAEditValidateCB(self):
        if self.temp1TA != None:
            old = str(self.temp1TA)
        else:
            old = ''
        newtext = self.ui.temp1TAEdit.text()
        if newtext == '':
            self.ui.temp1TAEdit.clear()
            self.temp1TA = None
        else:
            try:
                self.temp1TA = int(newtext)
                if not self.temp1TA:
                    self.ui.temp1TA.clear()
                    self.temp1TA = None
            except Exception:
                if self.temp1TA != None:
                    self.temp1TA = old
                else:
                    self.temp1TA = None
                self.ui.temp1TAEdit.setText(old)
        if self.temp1TA != None:
            self.ui.temp1TcheckBox.setEnabled(True)
            self.ui.temp1PcheckBox.setEnabled(True)
            self.ui.temp1IcheckBox.setEnabled(True)
            self.ui.temp1DcheckBox.setEnabled(True)
            self.ui.temp1UcheckBox.setEnabled(True)
        else:
            self.ui.temp1TcheckBox.setEnabled(False)
            self.ui.temp1PcheckBox.setEnabled(False)
            self.ui.temp1IcheckBox.setEnabled(False)
            self.ui.temp1DcheckBox.setEnabled(False)
            self.ui.temp1UcheckBox.setEnabled(False)

    def temp2TAEditValidateCB(self):
        if self.temp2TA != None:
            old = str(self.temp2TA)
        else:
            old = ''
        newtext = self.ui.temp2TAEdit.text()
        if newtext == '':
            self.ui.temp2TAEdit.clear()
            self.temp2TA = None
        else:
            try:
                self.temp2TA = int(newtext)
                if not self.temp2TA:
                    self.ui.temp2TA.clear()
                    self.temp2TA = None
            except Exception:
                if self.temp2TA != None:
                    self.temp2TA = old
                else:
                    self.temp1TA = None
                self.ui.temp2TAEdit.setText(old)
                
        if self.temp2TA != None:
            self.ui.temp2TcheckBox.setEnabled(True)
            self.ui.temp2PcheckBox.setEnabled(True)
            self.ui.temp2IcheckBox.setEnabled(True)
            self.ui.temp2DcheckBox.setEnabled(True)
            self.ui.temp2UcheckBox.setEnabled(True)
        else:
            self.ui.temp2TcheckBox.setEnabled(False)
            self.ui.temp2PcheckBox.setEnabled(False)
            self.ui.temp2IcheckBox.setEnabled(False)
            self.ui.temp2DcheckBox.setEnabled(False)
            self.ui.temp2UcheckBox.setEnabled(False)

    def temperature1CB(self, temp):
        self.temp1T = temp

        if not self.isCreatingModel1 and not self.isControlOnOff1 and not self.isControlHist1 and not self.isControlPID1:

            if (self.temp1Count < self.maxnumberofpoints1):

                time = self.temp1Count * self.temp1TA / 1000.0
                self.temp1T_y[self.temp1Count] = self.temp1T
                self.temp1P_y[self.temp1Count] = self.temp1P
                self.temp1I_y[self.temp1Count] = self.temp1I
                self.temp1D_y[self.temp1Count] = self.temp1D
                self.temp1U_y[self.temp1Count] = self.temp1U

                self.temp1Time_x[self.temp1Count] = time

                self.temp1Count = self.temp1Count + 1
            else:

                lasttime = self.temp1Time_x[-1]
                time = lasttime + self.temp1TA / 1000.0
                self.temp1T_y = np.roll(self.temp1T_y, -1)
                self.temp1P_y = np.roll(self.temp1P_y, -1)
                self.temp1I_y = np.roll(self.temp1I_y, -1)
                self.temp1D_y = np.roll(self.temp1D_y, -1)
                self.temp1U_y = np.roll(self.temp1U_y, -1)

                self.temp1Time_x = np.roll(self.temp1Time_x, -1)

                self.temp1T_y[-1] = self.temp1T
                self.temp1P_y[-1] = self.temp1P
                self.temp1I_y[-1] = self.temp1I
                self.temp1D_y[-1] = self.temp1D
                self.temp1U_y[-1] = self.temp1U

                self.temp1Time_x[-1] = time

        elif self.isCreatingModel1 and not self.isControlOnOff1 and not self.isControlHist1 and not self.isControlPID1:
            time = self.temp1Count * self.temp1TA / 1000.0
            self.temp1T_y[self.temp1Count] = self.temp1T
            self.temp1Time_x[self.temp1Count] = time


            #Check if last 30 seconds are stable
            if self.temp1Time_x[self.temp1Count] > 30:
                ns = round(30*(1000.0/self.temp1TA))
                avrg = sum(self.temp1T_y[self.temp1Count-ns:self.temp1Count])/ns
                avrgerror = sum(abs(self.temp1T_y[self.temp1Count-ns:self.temp1Count] - avrg)) / ns
                if avrgerror < 0.3 and not self.ssReady1: #permitir ao utilizado terminar o modelo manualmente
                    self.enableSteadyStateReady1()
                if avrgerror < 0.05 or self.ssReady1Clicked: # certeza superior a 99.95%
                    self.ssReady1Clicked = False
                    self.finishModel1(avrg)
                    return
            self.temp1Count = self.temp1Count + 1
            if self.temp1Count == round(self.sizeOfArraysInSeconds * (1000.0 / self.temp1TA)):
                self.finishModel1(avrg)
                return

        elif self.isControlOnOff1 and not self.isCreatingModel1 and not self.isControlHist1:

            #Controlo ON OFF
            if self.temp1T > self.t1TargetTemp:
                # Send Input 0
                self.temp1U = 0
                self.serialListenerThread.transistor1 = self.temp1U
                self.serialListenerThread.setTransistor1.set()
            elif self.temp1T <= self.t1TargetTemp:
                # Send Input 255
                self.temp1U = 255
                self.serialListenerThread.transistor1 = self.temp1U
                self.serialListenerThread.setTransistor1.set()

            time = self.temp1Count * self.temp1TA / 1000.0
            self.temp1T_y[self.temp1Count] = self.temp1T
            self.temp1U_y[self.temp1Count] = self.temp1U
            self.temp1Time_x[self.temp1Count] = time

            self.temp1Count = self.temp1Count + 1

        elif self.isControlHist1 and not self.isCreatingModel1 and not self.isControlOnOff1 and not self.isControlPID1:

            error = self.t1TargetTemp - self.temp1T

            #Controlo Histerese
            if error > -self.t1TempError and self.temp1U == 255:
                self.temp1U = 255
            elif error <= -self.t1TempError and self.temp1U == 255:
                self.temp1U = 0
            elif error < self.t1TempError and self.temp1U == 0:
                self.temp1U = 0
            elif error >= self.t1TempError and self.temp1U == 0:
                self.temp1U = 255
            
            #Send Input
            self.serialListenerThread.transistor1 = self.temp1U
            self.serialListenerThread.setTransistor1.set()

            #Store Data
            time = self.temp1Count * self.temp1TA / 1000.0
            self.temp1T_y[self.temp1Count] = self.temp1T
            self.temp1U_y[self.temp1Count] = self.temp1U
            self.temp1Time_x[self.temp1Count] = time

            self.temp1Count = self.temp1Count + 1

        elif self.isControlPID1 and not self.isCreatingModel1 and not self.isControlOnOff1 and not self.isControlHist1:

            if self.isControlAW1:
                erro = self.t1TargetTemp - self.temp1T

                derivativo = (erro - self.t1ControlLastError) / (self.temp1TA / 1000.0)

                self.temp1P = erro * self.t1ControlP;

                self.temp1D = derivativo * self.t1ControlD

                pwm = self.temp1P + self.temp1I + self.temp1D

                self.t1ControlLastError = erro

                # Saturação
                self.temp1U = pwm

                if pwm > 255:
                    self.temp1U = 255
                elif pwm < 0:
                    self.temp1U = 0

                #Anti Windup
                self.temp1I = self.temp1I + self.t1ControlI * (self.temp1TA / 1000.0 ) * erro + ((self.temp1TA / 1000.0) / self.t1ControlAWTt) * (self.temp1U - pwm);

            else:
                erro = self.t1TargetTemp - self.temp1T

                derivativo = (erro - self.t1ControlLastError)/(self.temp1TA / 1000.0 )

                self.temp1P = erro * self.t1ControlP;

                self.temp1I = self.temp1I + erro * self.t1ControlI * (self.temp1TA / 1000.0 )

                self.temp1D = derivativo * self.t1ControlD

                self.temp1U = self.temp1P + self.temp1I + self.temp1D

                self.t1ControlLastError = erro


                #Saturação

                if self.temp1U > 255:
                    self.temp1U = 255
                elif self.temp1U < 0:
                    self.temp1U = 0

            # Send Input
            self.temp1U = round(self.temp1U)
            self.serialListenerThread.transistor1 = round(self.temp1U)
            self.serialListenerThread.setTransistor1.set()

            # Store Data
            time = self.temp1Count * self.temp1TA / 1000.0
            self.temp1T_y[self.temp1Count] = self.temp1T
            self.temp1U_y[self.temp1Count] = self.temp1U
            self.temp1P_y[self.temp1Count] = self.temp1P
            self.temp1I_y[self.temp1Count] = self.temp1I
            self.temp1D_y[self.temp1Count] = self.temp1D
            self.temp1Time_x[self.temp1Count] = time

            self.temp1Count = self.temp1Count + 1

    def temperature2CB(self, temp):
        
        self.temp2T = temp
        if not self.isCreatingModel2 and not self.isControlOnOff2 and not self.isControlHist2 and not self.isControlPID2:
            if (self.temp2Count < self.maxnumberofpoints2):

                time = self.temp2Count * self.temp2TA / 1000.0
                self.temp2T_y[self.temp2Count] = self.temp2T
                self.temp2P_y[self.temp2Count] = self.temp2P
                self.temp2I_y[self.temp2Count] = self.temp2I
                self.temp2D_y[self.temp2Count] = self.temp2D
                self.temp2U_y[self.temp2Count] = self.temp2U

                self.temp2Time_x[self.temp2Count] = time

                self.temp2Count = self.temp2Count + 1
            else:

                lasttime = self.temp2Time_x[-1]
                time = lasttime + self.temp2TA / 1000.0
                self.temp2T_y = np.roll(self.temp2T_y, -1)
                self.temp2P_y = np.roll(self.temp2P_y, -1)
                self.temp2I_y = np.roll(self.temp2I_y, -1)
                self.temp2D_y = np.roll(self.temp2D_y, -1)
                self.temp2U_y = np.roll(self.temp2U_y, -1)

                self.temp2Time_x = np.roll(self.temp2Time_x, -1)

                self.temp2T_y[-1] = self.temp2T
                self.temp2P_y[-1] = self.temp2P
                self.temp2I_y[-1] = self.temp2I
                self.temp2D_y[-1] = self.temp2D
                self.temp2U_y[-1] = self.temp2U

                self.temp2Time_x[-1] = time

        elif self.isCreatingModel2 and not self.isControlOnOff2 and not self.isControlHist2 and not self.isControlPID2:
            time = self.temp2Count * self.temp2TA / 1000.0
            self.temp2T_y[self.temp2Count] = self.temp2T
            self.temp2Time_x[self.temp2Count] = time


            #Check if last 30 seconds are stable
            if self.temp2Time_x[self.temp2Count] > 30:
                ns = round(30*(1000.0/self.temp2TA))
                avrg = sum(self.temp2T_y[self.temp2Count-ns:self.temp2Count])/ns
                avrgerror = sum(abs(self.temp2T_y[self.temp2Count-ns:self.temp2Count] - avrg)) / ns
                if avrgerror < 0.05 or self.ssReady2Clicked: # certeza superior a 99.95%
                    self.finishModel2(avrg)
                    return
                if avrgerror < 0.3 and not self.ssReady2: #permitir ao utilizado terminar o modelo manualmente
                    self.enableSteadyStateReady2()
            self.temp2Count = self.temp2Count + 1
            if self.temp2Count == round(self.sizeOfArraysInSeconds * (1000.0 / self.temp2TA)):
                self.finishModel2(avrg)
                return

        elif self.isControlOnOff2 and not self.isCreatingModel2 and not self.isControlHist2 and not self.isControlPID2:

            #Controlo
            if self.temp2T > self.t2TargetTemp:
                # Send Input 0
                self.temp2U = 0
                self.serialListenerThread.transistor2 = self.temp2U
                self.serialListenerThread.setTransistor2.set()
            elif self.temp2T <= self.t2TargetTemp:
                # Send Input 255
                self.temp2U = 255
                self.serialListenerThread.transistor2 = self.temp2U
                self.serialListenerThread.setTransistor2.set()

            #Store Data
            time = self.temp2Count * self.temp2TA / 1000.0
            self.temp2T_y[self.temp2Count] = self.temp2T
            self.temp2U_y[self.temp2Count] = self.temp2U
            self.temp2Time_x[self.temp2Count] = time

            self.temp2Count = self.temp2Count + 1

        elif self.isControlHist2 and not self.isCreatingModel2 and not self.isControlOnOff2 and not self.isControlPID2:

            error = self.t2TargetTemp - self.temp2T

            # Controlo Histerese
            if error > -self.t2TempError and self.temp2U == 255:
                self.temp2U = 255
            elif error <= -self.t2TempError and self.temp2U == 255:
                self.temp2U = 0
            elif error < self.t2TempError and self.temp2U == 0:
                self.temp2U = 0
            elif error >= self.t2TempError and self.temp2U == 0:
                self.temp2U = 255

            # Send Input
            self.serialListenerThread.transistor2 = self.temp2U
            self.serialListenerThread.setTransistor2.set()

            # Store Data
            time = self.temp2Count * self.temp2TA / 1000.0
            self.temp2T_y[self.temp2Count] = self.temp2T
            self.temp2U_y[self.temp2Count] = self.temp2U
            self.temp2Time_x[self.temp2Count] = time

            self.temp2Count = self.temp2Count + 1

        elif self.isControlPID2 and not self.isCreatingModel2 and not self.isControlOnOff2 and not self.isControlHist2:

            if self.isControlAW2:
                erro = self.t2TargetTemp - self.temp2T

                derivativo = (erro - self.t2ControlLastError) / (self.temp2TA / 1000.0)

                self.temp2P = erro * self.t2ControlP;

                self.temp2D = derivativo * self.t2ControlD

                pwm = self.temp2P + self.temp2I + self.temp2D

                self.t2ControlLastError = erro

                # Saturação
                self.temp2U = pwm

                if pwm > 255:
                    self.temp2U = 255
                elif pwm < 0:
                    self.temp2U = 0

                #Anti Windup
                self.temp2I = self.temp2I + self.t2ControlI * (self.temp2TA / 1000.0 ) * erro + ((self.temp2TA / 1000.0) / self.t2ControlAWTt) * (self.temp2U - pwm);

            else:
                erro = self.t2TargetTemp - self.temp2T

                derivativo = (erro - self.t2ControlLastError)/(self.temp2TA / 1000.0 )

                self.temp2P = erro * self.t2ControlP;

                self.temp2I = self.temp2I + erro * self.t2ControlI * (self.temp2TA / 1000.0 )

                self.temp2D = derivativo * self.t2ControlD

                self.temp2U = self.temp2P + self.temp2I + self.temp2D

                self.t2ControlLastError = erro


                #Saturação

                if self.temp2U > 255:
                    self.temp2U = 255
                elif self.temp2U < 0:
                    self.temp2U = 0

            # Send Input
            self.temp2U = round(self.temp2U)
            self.serialListenerThread.transistor2 = round(self.temp2U)
            self.serialListenerThread.setTransistor2.set()

            # Store Data
            time = self.temp2Count * self.temp2TA / 1000.0
            self.temp2T_y[self.temp2Count] = self.temp2T
            self.temp2U_y[self.temp2Count] = self.temp2U
            self.temp2P_y[self.temp2Count] = self.temp2P
            self.temp2I_y[self.temp2Count] = self.temp2I
            self.temp2D_y[self.temp2Count] = self.temp2D
            self.temp2Time_x[self.temp2Count] = time

            self.temp2Count = self.temp2Count + 1

    def temp1StartQCB(self):
        if self.graph1_isUpdating:
            self.graph1_isUpdating = False
            self.ui.temp1StartQButton.setText("Começar")
            self.stopGraph1Update()
        else:
            self.graph1_isUpdating = True
            self.ui.temp1StartQButton.setText("Parar")
            self.startGraph1Update()

    def temp2StartQCB(self):
        if self.graph2_isUpdating:
            self.graph2_isUpdating = False
            self.ui.temp2StartQButton.setText("Começar")
            self.stopGraph2Update()
        else:
            self.graph2_isUpdating = True
            self.ui.temp2StartQButton.setText("Parar")
            self.startGraph2Update()

    def switchADRef(self):
        if self.is_connected:
            self.serialListenerThread.swithADREF.set()

    def currentChangedControloCB(self, index):
        if not self.is_connected:
            self.ui.Controlo.setCurrentIndex(5)

    def modelListWidgetICCB(self, item):
        Temp0, TempSS, DeltaTemp, K, TauSD, TauCD, Delay = item.data(32)

        txt = "T0: "+str(Temp0)+"\nTss: "+str(TempSS)+"\n\u0394T: "+str(DeltaTemp)+"\n K: "+str(K)+"\n\nModelo sem delay:\n\n\u03C4: "+str(TauSD)+"\n\nModelo com delay:\n\n\u03C4: "+str(TauCD)+"\n \u03C4D: "+str(Delay)
        self.ui.modelosTextBrowser.setText(txt)

    def ooT1StartCB(self):
        if self.is_connected and not self.isControlOnOff1:
            self.ui.ooT1StartButton.setText("Parar")
            self.t1TargetTemp = self.ui.ooT1TargetDSBox.value()
            self.isControlOnOff1 = True

            #disable all other transistor 1 related functions
            self.ui.groupBox_10.setEnabled(False)
            self.ui.groupBox_4.setEnabled(False)
            self.ui.groupBox_2.setEnabled(False)
            self.ui.ooT1TargetDSBox.setEnabled(False)
            self.ui.temp1TAEdit.setEnabled(False)
            self.ui.temp1StartQButton.setEnabled(False)
            self.ui.temp1PcheckBox.setEnabled(False)
            self.ui.temp1IcheckBox.setEnabled(False)
            self.ui.temp1DcheckBox.setEnabled(False)

            #Receber Dados
            self.graph1_isUpdating = True
            self.ui.temp1StartQButton.setText("Parar")
            self.startGraph1Update()


        elif self.is_connected and self.isControlOnOff1:
            self.ui.ooT1StartButton.setText("Começar")
            self.isControlOnOff1 = False
            self.graph1_isUpdating = False
            
            #enable all other transistor 1 related functions
            self.ui.groupBox_10.setEnabled(True)
            self.ui.groupBox_4.setEnabled(True)
            self.ui.groupBox_2.setEnabled(True)
            self.ui.ooT1TargetDSBox.setEnabled(True)
            self.ui.temp1TAEdit.setEnabled(True)
            self.ui.temp1StartQButton.setEnabled(True)
            self.ui.temp1PcheckBox.setEnabled(True)
            self.ui.temp1IcheckBox.setEnabled(True)
            self.ui.temp1DcheckBox.setEnabled(True)

            # Send Input
            self.temp1U = 0
            self.serialListenerThread.transistor1 = self.temp1U
            self.serialListenerThread.setTransistor1.set()

            self.stopGraph1Update()
            self.ui.temp1StartQButton.setText("Começar")

    def ooT2StartCB(self):
        if self.is_connected and not self.isControlOnOff2:
            self.ui.ooT2StartButton.setText("Parar")
            self.t2TargetTemp = self.ui.ooT2TargetDSBox.value()
            self.isControlOnOff2 = True

            # disable all other transistor 2 related functions
            self.ui.groupBox_11.setEnabled(False)
            self.ui.groupBox_5.setEnabled(False)
            self.ui.groupBox_3.setEnabled(False)
            self.ui.ooT2TargetDSBox.setEnabled(False)
            self.ui.temp2TAEdit.setEnabled(False)
            self.ui.temp2StartQButton.setEnabled(False)
            self.ui.temp2PcheckBox.setEnabled(False)
            self.ui.temp2IcheckBox.setEnabled(False)
            self.ui.temp2DcheckBox.setEnabled(False)

            # Receber Dados
            self.graph2_isUpdating = True
            self.ui.temp2StartQButton.setText("Parar")
            self.startGraph2Update()


        elif self.is_connected and self.isControlOnOff2:
            self.ui.ooT2StartButton.setText("Começar")
            self.isControlOnOff2 = False
            self.graph2_isUpdating = False

            # enable all other transistor 2 related functions
            self.ui.groupBox_11.setEnabled(True)
            self.ui.groupBox_5.setEnabled(True)
            self.ui.groupBox_3.setEnabled(True)
            self.ui.ooT2TargetDSBox.setEnabled(True)
            self.ui.temp2TAEdit.setEnabled(True)
            self.ui.temp2StartQButton.setEnabled(True)
            self.ui.temp2PcheckBox.setEnabled(True)
            self.ui.temp2IcheckBox.setEnabled(True)
            self.ui.temp2DcheckBox.setEnabled(True)

            # Send Input
            self.temp2U = 0
            self.serialListenerThread.transistor2 = self.temp2U
            self.serialListenerThread.setTransistor2.set()

            self.stopGraph2Update()
            self.ui.temp2StartQButton.setText("Começar")

    def hstT1StartCB(self):
        if self.is_connected and not self.isControlHist1:
            self.ui.hstT1StartButton.setText("Parar")
            self.t1TargetTemp = self.ui.hstT1TargetDSBox.value()
            self.t1TempError = self.ui.hstT1ErroDSBox.value()
            self.isControlHist1 = True

            #disable all other transistor 1 related functions
            self.ui.groupBox_10.setEnabled(False)
            self.ui.groupBox_6.setEnabled(False)
            self.ui.groupBox_2.setEnabled(False)
            self.ui.hstT1TargetDSBox.setEnabled(False)
            self.ui.hstT1ErroDSBox.setEnabled(False)
            self.ui.temp1TAEdit.setEnabled(False)
            self.ui.temp1StartQButton.setEnabled(False)
            self.ui.temp1PcheckBox.setEnabled(False)
            self.ui.temp1IcheckBox.setEnabled(False)
            self.ui.temp1DcheckBox.setEnabled(False)

            # Send Input
            self.temp1U = 0
            self.serialListenerThread.transistor1 = self.temp1U
            self.serialListenerThread.setTransistor1.set()

            #Receber Dados
            self.graph1_isUpdating = True
            self.ui.temp1StartQButton.setText("Parar")
            self.startGraph1Update()

        elif self.is_connected and self.isControlHist1:
            self.ui.hstT1StartButton.setText("Começar")
            self.isControlHist1 = False
            self.graph1_isUpdating = False

            # enable all other transistor 1 related functions
            self.ui.groupBox_10.setEnabled(True)
            self.ui.groupBox_6.setEnabled(True)
            self.ui.groupBox_2.setEnabled(True)
            self.ui.hstT1TargetDSBox.setEnabled(True)
            self.ui.hstT1ErroDSBox.setEnabled(True)
            self.ui.temp1TAEdit.setEnabled(True)
            self.ui.temp1StartQButton.setEnabled(True)
            self.ui.temp1PcheckBox.setEnabled(True)
            self.ui.temp1IcheckBox.setEnabled(True)
            self.ui.temp1DcheckBox.setEnabled(True)

            # Send Input
            self.temp1U = 0
            self.serialListenerThread.transistor1 = self.temp1U
            self.serialListenerThread.setTransistor1.set()

            self.stopGraph1Update()
            self.ui.temp1StartQButton.setText("Começar")
            
    def hstT2StartCB(self):
        if self.is_connected and not self.isControlHist2:
            self.ui.hstT2StartButton.setText("Parar")
            self.t2TargetTemp = self.ui.hstT2TargetDSBox.value()
            self.t2TempError = self.ui.hstT2ErroDSBox.value()
            self.isControlHist2 = True

            #disable all other transistor 2 related functions
            self.ui.groupBox_11.setEnabled(False)
            self.ui.groupBox_7.setEnabled(False)
            self.ui.groupBox_3.setEnabled(False)
            self.ui.hstT2TargetDSBox.setEnabled(False)
            self.ui.hstT2ErroDSBox.setEnabled(False)
            self.ui.temp2TAEdit.setEnabled(False)
            self.ui.temp2StartQButton.setEnabled(False)
            self.ui.temp2PcheckBox.setEnabled(False)
            self.ui.temp2IcheckBox.setEnabled(False)
            self.ui.temp2DcheckBox.setEnabled(False)

            # Send Input
            self.temp2U = 0
            self.serialListenerThread.transistor2 = self.temp2U
            self.serialListenerThread.setTransistor2.set()

            #Receber Dados
            self.graph2_isUpdating = True
            self.ui.temp2StartQButton.setText("Parar")
            self.startGraph2Update()

        elif self.is_connected and self.isControlHist2:
            self.ui.hstT2StartButton.setText("Começar")
            self.isControlHist2 = False
            self.graph2_isUpdating = False

            # enable all other transistor 2 related functions
            self.ui.groupBox_11.setEnabled(True)
            self.ui.groupBox_7.setEnabled(True)
            self.ui.groupBox_3.setEnabled(True)
            self.ui.hstT2TargetDSBox.setEnabled(True)
            self.ui.hstT2ErroDSBox.setEnabled(True)
            self.ui.temp2TAEdit.setEnabled(True)
            self.ui.temp2StartQButton.setEnabled(True)
            self.ui.temp2PcheckBox.setEnabled(True)
            self.ui.temp2IcheckBox.setEnabled(True)
            self.ui.temp2DcheckBox.setEnabled(True)

            # Send Input
            self.temp2U = 0
            self.serialListenerThread.transistor2 = self.temp2U
            self.serialListenerThread.setTransistor2.set()

            self.stopGraph2Update()
            self.ui.temp2StartQButton.setText("Começar")

    def pidT1StartCB(self):
        if self.is_connected and not self.isControlPID1:
            self.ui.pidT1StartButton.setText("Parar")
            self.t1TargetTemp = self.ui.pidT1TargetDSBox.value()
            self.t1ControlP = self.ui.pidT1PDSBox.value()
            self.t1ControlI = self.ui.pidT1IDSBox.value()
            self.t1ControlD = self.ui.pidT1DDSBox.value()

            if self.isControlAW1 and self.t1ControlD > 0:
                self.t1ControlAWTt = math.sqrt((self.t1ControlP/self.t1ControlI)*(self.t1ControlD/self.t1ControlP))
            elif self.isControlAW1 and self.t1ControlD == 0:
                self.t1ControlAWTt = 0.5*(self.t1ControlP/self.t1ControlI)

            self.isControlPID1 = True

            #disable all other transistor 1 related functions
            self.ui.t1CalibrateButton.setEnabled(False)
            self.ui.groupBox_10.setEnabled(False)
            self.ui.groupBox_6.setEnabled(False)
            self.ui.groupBox_4.setEnabled(False)
            self.ui.pidT1TargetDSBox.setEnabled(False)
            self.ui.pidT1PDSBox.setEnabled(False)
            self.ui.pidT1IDSBox.setEnabled(False)
            self.ui.pidT1DDSBox.setEnabled(False)
            self.ui.temp1TAEdit.setEnabled(False)
            self.ui.temp1StartQButton.setEnabled(False)
            self.ui.pidT1AWcheckBox.setEnabled(False)

            # Send Input
            self.temp1U = 0
            self.serialListenerThread.transistor1 = self.temp1U
            self.serialListenerThread.setTransistor1.set()

            #Receber Dados
            self.graph1_isUpdating = True
            self.ui.temp1StartQButton.setText("Parar")
            self.startGraph1Update()

        elif self.is_connected and self.isControlPID1:
            self.ui.pidT1StartButton.setText("Começar")
            self.isControlPID1 = False
            self.graph1_isUpdating = False

            # enable all other transistor 1 related functions
            self.ui.t1CalibrateButton.setEnabled(True)
            self.ui.groupBox_10.setEnabled(True)
            self.ui.groupBox_6.setEnabled(True)
            self.ui.groupBox_4.setEnabled(True)
            self.ui.pidT1TargetDSBox.setEnabled(True)
            self.ui.pidT1PDSBox.setEnabled(True)
            self.ui.pidT1IDSBox.setEnabled(True)
            self.ui.pidT1DDSBox.setEnabled(True)
            self.ui.temp1TAEdit.setEnabled(True)
            self.ui.temp1StartQButton.setEnabled(True)
            self.ui.pidT1AWcheckBox.setEnabled(True)

            # Send Input
            self.temp1U = 0
            self.serialListenerThread.transistor1 = self.temp1U
            self.serialListenerThread.setTransistor1.set()

            self.stopGraph1Update()
            self.ui.temp1StartQButton.setText("Começar")

    def pidT2StartCB(self):
        if self.is_connected and not self.isControlPID2:
            self.ui.pidT2StartButton.setText("Parar")
            self.t2TargetTemp = self.ui.pidT2TargetDSBox.value()
            self.t2ControlP = self.ui.pidT2PDSBox.value()
            self.t2ControlI = self.ui.pidT2IDSBox.value()
            self.t2ControlD = self.ui.pidT2DDSBox.value()
            self.isControlPID2 = True

            #disable all other transistor 2 related functions
            self.ui.t2CalibrateButton.setEnabled(False)
            self.ui.groupBox_11.setEnabled(False)
            self.ui.groupBox_7.setEnabled(False)
            self.ui.groupBox_5.setEnabled(False)
            self.ui.pidT2TargetDSBox.setEnabled(False)
            self.ui.pidT2PDSBox.setEnabled(False)
            self.ui.pidT2IDSBox.setEnabled(False)
            self.ui.pidT2DDSBox.setEnabled(False)
            self.ui.temp2TAEdit.setEnabled(False)
            self.ui.temp2StartQButton.setEnabled(False)
            self.ui.temp2PcheckBox.setEnabled(False)
            self.ui.temp2IcheckBox.setEnabled(False)
            self.ui.temp2DcheckBox.setEnabled(False)
            self.ui.pidT2AWcheckBox.setEnabled(False)

            # Send Input
            self.temp2U = 0
            self.serialListenerThread.transistor2 = self.temp2U
            self.serialListenerThread.setTransistor2.set()

            #Receber Dados
            self.graph2_isUpdating = True
            self.ui.temp2StartQButton.setText("Parar")
            self.startGraph2Update()

        elif self.is_connected and self.isControlPID2:
            self.ui.pidT2StartButton.setText("Começar")
            self.isControlPID2 = False
            self.graph2_isUpdating = False

            # enable all other transistor 2 related functions
            self.ui.t2CalibrateButton.setEnabled(True)
            self.ui.groupBox_11.setEnabled(True)
            self.ui.groupBox_7.setEnabled(True)
            self.ui.groupBox_5.setEnabled(True)
            self.ui.pidT2TargetDSBox.setEnabled(True)
            self.ui.pidT2PDSBox.setEnabled(True)
            self.ui.pidT2IDSBox.setEnabled(True)
            self.ui.pidT2DDSBox.setEnabled(True)
            self.ui.temp2TAEdit.setEnabled(True)
            self.ui.temp2StartQButton.setEnabled(True)
            self.ui.temp2PcheckBox.setEnabled(True)
            self.ui.temp2IcheckBox.setEnabled(True)
            self.ui.temp2DcheckBox.setEnabled(True)
            self.ui.pidT2AWcheckBox.setEnabled(True)

            # Send Input
            self.temp2U = 0
            self.serialListenerThread.transistor1 = self.temp2U
            self.serialListenerThread.setTransistor2.set()

            self.stopGraph2Update()
            self.ui.temp2StartQButton.setText("Começar")

    def pidT1AWcheckBoxCB(self, state):
        if state == 2:
            self.isControlAW1 = True
        elif state == 0:
            self.isControlAW1 = False

    def pidT2AWcheckBoxCB(self, state):
        if state == 2:
            self.isControlAW2 = True
        elif state == 0:
            self.isControlAW2 = False

    def pidT1AWcheckCB(self, value):
        if self.ui.pidT1PDSBox.value() > 0 and self.ui.pidT1IDSBox.value() > 0:
            self.ui.pidT1AWcheckBox.setEnabled(True)
        else:
            self.ui.pidT1AWcheckBox.setCheckState(0)
            self.ui.pidT1AWcheckBox.setEnabled(False)
    def pidT2AWcheckCB(self, value):
        if self.ui.pidT2PDSBox.value() > 0 and self.ui.pidT2IDSBox.value() > 0:
            self.ui.pidT2AWcheckBox.setEnabled(True)
        else:
            self.ui.pidT2AWcheckBox.setCheckState(0)
            self.ui.pidT2AWcheckBox.setEnabled(False)
def main():
    app = QtWidgets.QApplication(sys.argv)
    application = ApplicationWindow()
    application.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
