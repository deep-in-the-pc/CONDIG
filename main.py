# -*- coding: latin-1 -*-


from operator import itemgetter
from queue import Queue
import time as t
import sys
import os
import threading
import datetime
import math
import numpy as np
from serialThread import *

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import pyqtSlot
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

    def initSetup(self):
        # SerialThread
        self.serialThreadSetup()

        # Timers
        self.setupTimers()

        # Variables
        self.setupVariables()

        self.loadModelos()

        # CallBacks
        self.setupCallbacks()

        #update model list
        self.updateModelListView()
        self.updateModel1ComboBox()
        self.updateModel2ComboBox()

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
        self.currentModel1HasDelay = False

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
        self.currentModel2HasDelay = False

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

        self.temp1Count = 0
        self.temp1T = 0
        self.temp1P = 0
        self.temp1I = 0
        self.temp1D = 0
        self.temp1U = 0

        self.temp2Count = 0
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
        #t1ModeloCBox currentindexChanged Callback
        self.ui.t1ModeloCBox.currentIndexChanged.connect(self.t1ModeloCBoxCIDCB)
        #t2ModeloCBox currentindexChanged Callback
        self.ui.t2ModeloCBox.currentIndexChanged.connect(self.t2ModeloCBoxCIDCB)
        #t1ControloCBox currentindexChanged Callback
        self.ui.t1ControloCBox.currentIndexChanged.connect(self.t1ControloCBoxCIDCB)
        #t2ControloCBox currentindexChanged Callback
        self.ui.t2ControloCBox.currentIndexChanged.connect(self.t2ControloCBoxCIDCB)
        #t1CalibrateButton clicked Callback
        self.ui.t1CalibrateButton.clicked.connect(self.t1CalibrateButtonCB)
        #t2CalibrateButton clicked Callback
        self.ui.t2CalibrateButton.clicked.connect(self.t2CalibrateButtonCB)
        #removeModelButton clicked Callback
        self.ui.removeModelButton.clicked.connect(self.removeModelButtonCB)
        #graph1SaveButton clicked Callback
        self.ui.graph1SaveButton.clicked.connect(self.graph1SaveButtonCB)
        #graph1SaveButton clicked Callback
        self.ui.graph2SaveButton.clicked.connect(self.graph2SaveButtonCB)

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

        self.serialQueue = Queue()

        self.serialListenerThread = serialThread(1, "SerialListener", self.serialQueue)

        self.serialConnectionParameters = []
        self.serialConnectionParameters.append(serial.EIGHTBITS)
        self.serialConnectionParameters.append(serial.PARITY_NONE)
        self.serialConnectionParameters.append(serial.STOPBITS_ONE)
        self.serialConnectionParameters.append(115200)

        self.serialListenerThread.newTemperature1Signal[float].connect(self.temperature1CB)
        self.serialListenerThread.newTemperature2Signal[float].connect(self.temperature2CB)

    def serialThreadStart(self):

        self.serialConnectionParameters.append(self.serialCOM)
        self.serialListenerThread.setParameteres(self.serialConnectionParameters)

        self.comlist_qtimer.stop()

        self.serialListenerThread.start()
        self.is_connected = True

    def serialThreadStop(self):
        self.serialListenerThread.stop()
        self.comlist_qtimer.start(self.comlist_qtimer_interval)

        self.is_connected = False

    #Modelos
    @pyqtSlot()
    def createModel1(self):
        if self.is_connected and not self.ssReady1:

            self.ui.t1ModelTBrowser.clear()

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
            self.isCreatingModel1 = True

            #Send Input
            self.temp1U = self.ui.t1SBox.value()
            self.serialQueue.put("setTransistor1 " + str(self.temp1U))

            #Receber Dados
            self.graph1_isUpdating = True
            self.ui.temp1StartQButton.setText("Parar")
            self.startGraph1Update()

        elif self.ssReady1:
            self.ssReady1Clicked = True

    def finishModel1(self, tss):

        self.isCreatingModel1 = False
        self.serialQueue.put("setTransistor1 0")

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
        self.updateModel1ComboBox()

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

    @pyqtSlot()
    def createModel2(self):
        if self.is_connected and not self.ssReady2:

            self.ui.t2ModelTBrowser.clear()

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
            self.isCreatingModel2 = True

            #Send Input
            self.temp2U = self.ui.t2SBox.value()
            self.serialQueue.put("setTransistor2 " + str(self.temp2U))

            #Receber Dados
            self.graph2_isUpdating = True
            self.ui.temp2StartQButton.setText("Parar")
            self.startGraph2Update()

        elif self.ssReady2:
            self.ssReady2Clicked = True

    def finishModel2(self, tss):

        self.isCreatingModel2 = False
        self.serialQueue.put("setTransistor2 0")

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
        self.updateModel2ComboBox()
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

    def updateModel1ComboBox(self):

        #t1ModeloCBox currentindexChanged Callback
        self.ui.t1ModeloCBox.currentIndexChanged.disconnect(self.t1ModeloCBoxCIDCB)

        self.ui.t1ModeloCBox.clear()

        #t2ModeloCBox currentindexChanged Callback
        self.ui.t1ModeloCBox.currentIndexChanged.connect(self.t1ModeloCBoxCIDCB)

        for modelo in self.ModelList["1"]:
            parameters = self.ModelList["1"][modelo]

            dataListParam = parameters["T0"], parameters["TSS"], parameters["DeltaTemp"], parameters["K"], parameters["TauSD"], parameters["TauCD"], parameters["Delay"],
            data = QtCore.QVariant(dataListParam)

            name = "Transistor 1 - " + modelo.split('-')[0] + ' - '  +modelo.split('-')[1] + '%'
            self.ui.t1ModeloCBox.addItem(name, data)

        self.ui.t1CalibrateButton.setEnabled(True)
        if(len(self.ModelList["1"]) == 0):
            self.ui.t1CalibrateButton.setEnabled(False)
        else:
            if self.ui.t1ModeloCBox.currentData()[6] <= 0:
                self.currentModel1HasDelay = False
            else:
                self.currentModel1HasDelay = True
            self.updateMetodo1ComboBox(self.ui.t1ControloCBox.currentIndex())

    def updateModel2ComboBox(self):

        #t2ModeloCBox currentindexChanged Callback
        self.ui.t2ModeloCBox.currentIndexChanged.disconnect(self.t2ModeloCBoxCIDCB)

        self.ui.t2ModeloCBox.clear()

        #t2ModeloCBox currentindexChanged Callback
        self.ui.t2ModeloCBox.currentIndexChanged.connect(self.t2ModeloCBoxCIDCB)

        for modelo in self.ModelList["2"]:
            parameters = self.ModelList["2"][modelo]

            dataListParam = parameters["T0"], parameters["TSS"], parameters["DeltaTemp"], parameters["K"], parameters["TauSD"], parameters["TauCD"], parameters["Delay"],
            data = QtCore.QVariant(dataListParam)

            name = "Transistor 2 - " + modelo.split('-')[0] + ' - '  +modelo.split('-')[1] + '%'
            self.ui.t2ModeloCBox.addItem(name, data)



        self.ui.t2CalibrateButton.setEnabled(True)

        if (len(self.ModelList["2"]) == 0):
            self.ui.t2CalibrateButton.setEnabled(False)
        else:
            if self.ui.t2ModeloCBox.currentData()[6] <= 0:
                self.currentModel2HasDelay = False
            else:
                self.currentModel2HasDelay = True
            self.updateMetodo2ComboBox(self.ui.t2ControloCBox.currentIndex())

    def updateMetodo1ComboBox(self, index):
        self.ui.t1MetodoCBox.clear()
        self.ui.t1CalibrateButton.setEnabled(True)
        if index == 0 and self.currentModel1HasDelay:
            txtmetodoslist = ['Ziegler-Nichols Malha Aberta', 'Cohen-Coon', 'ITAE - Entradas de Referência', 'ITAE - Rejeição a Perturbações']
            self.ui.t1MetodoCBox.addItems(txtmetodoslist)
        elif index == 0 and not self.currentModel1HasDelay:
            self.ui.t1CalibrateButton.setEnabled(False)
        elif index == 1 and self.currentModel1HasDelay:
            txtmetodoslist = ['Ziegler-Nichols Malha Aberta', 'Cohen-Coon', 'ITAE - Entradas de Referência', 'ITAE - Rejeição a Perturbações', 'IMC (Sintonia agressiva)', 'IMC (Sintonia moderada)', 'IMC (Sintonia conservativa)']
            self.ui.t1MetodoCBox.addItems(txtmetodoslist)
        elif index == 1 and not self.currentModel1HasDelay:
            txtmetodoslist = ['IMC (Sintonia agressiva)', 'IMC (Sintonia moderada)', 'IMC (Sintonia conservativa)']
            self.ui.t1MetodoCBox.addItems(txtmetodoslist)
        elif index == 2 and self.currentModel1HasDelay:
            txtmetodoslist = ['Ziegler-Nichols Malha Aberta', 'Cohen-Coon', 'IMC (Sintonia agressiva)', 'IMC (Sintonia moderada)',
                              'IMC (Sintonia conservativa)']
            self.ui.t1MetodoCBox.addItems(txtmetodoslist)
        elif index == 2 and not self.currentModel1HasDelay:
            txtmetodoslist = ['IMC (Sintonia agressiva)', 'IMC (Sintonia moderada)',
                              'IMC (Sintonia conservativa)']
            self.ui.t1MetodoCBox.addItems(txtmetodoslist)
        if (len(self.ModelList["1"]) == 0):
            self.ui.t1CalibrateButton.setEnabled(False)

    def updateMetodo2ComboBox(self, index):
        self.ui.t2MetodoCBox.clear()
        self.ui.t2CalibrateButton.setEnabled(True)
        if index == 0 and self.currentModel2HasDelay:
            txtmetodoslist = ['Ziegler-Nichols Malha Aberta', 'Cohen-Coon', 'ITAE - Entradas de Referência', 'ITAE - Rejeição a Perturbações']
            self.ui.t2MetodoCBox.addItems(txtmetodoslist)
        elif index == 0 and not self.currentModel2HasDelay:
            self.ui.t2CalibrateButton.setEnabled(False)
        elif index == 1 and self.currentModel2HasDelay:
            txtmetodoslist = ['Ziegler-Nichols Malha Aberta', 'Cohen-Coon', 'ITAE - Entradas de Referência', 'ITAE - Rejeição a Perturbações', 'IMC (Sintonia agressiva)', 'IMC (Sintonia moderada)', 'IMC (Sintonia conservativa)']
            self.ui.t2MetodoCBox.addItems(txtmetodoslist)
        elif index == 1 and not self.currentModel2HasDelay:
            txtmetodoslist = ['IMC (Sintonia agressiva)', 'IMC (Sintonia moderada)', 'IMC (Sintonia conservativa)']
            self.ui.t2MetodoCBox.addItems(txtmetodoslist)
        elif index == 2 and self.currentModel2HasDelay:
            txtmetodoslist = ['Ziegler-Nichols Malha Aberta', 'Cohen-Coon', 'IMC (Sintonia agressiva)', 'IMC (Sintonia moderada)',
                              'IMC (Sintonia conservativa)']
            self.ui.t2MetodoCBox.addItems(txtmetodoslist)
        elif index == 2 and not self.currentModel2HasDelay:
            txtmetodoslist = ['IMC (Sintonia agressiva)', 'IMC (Sintonia moderada)',
                              'IMC (Sintonia conservativa)']
            self.ui.t2MetodoCBox.addItems(txtmetodoslist)
        if (len(self.ModelList["2"]) == 0):
            self.ui.t2CalibrateButton.setEnabled(False)

    #Graph

    def updateGUI(self):
        nplots = 0
        for n, plot in self.plots:
            if n == 1:
                if self.graph1_isUpdating:
                    if 'temp1' not in self.plotCurves:
                        self.plotCurves['temp1'] = self.plotsObjects[nplots].plot(name='Temperatura')
                    self.plotCurves['temp1'].setData(self.temp1Time_x[:self.temp1Count], self.temp1T_y[:self.temp1Count], pen=(255, 0, 0))
                nplots = nplots + 1
            elif n == 2:
                if self.graph1_isUpdating:

                    if 'P' in plot:
                        if 'p1' not in self.plotCurves:
                            self.plotCurves['p1'] = self.plotsObjects[nplots].plot(name='Componente proporcional')
                        self.plotCurves['p1'].setData(self.temp1Time_x[:self.temp1Count],
                                                         self.temp1P_y[:self.temp1Count], pen=(255, 0, 0))
                    if 'I' in plot:
                        if 'i1' not in self.plotCurves:
                            self.plotCurves['i1'] = self.plotsObjects[nplots].plot(name='Componente integrativa')
                        self.plotCurves['i1'].setData(self.temp1Time_x[:self.temp1Count],
                                                         self.temp1I_y[:self.temp1Count], pen=(0, 255, 0))
                    if 'D' in plot:
                        if 'd1' not in self.plotCurves:
                            self.plotCurves['d1'] = self.plotsObjects[nplots].plot(name='Componente derivativa')
                        self.plotCurves['d1'].setData(self.temp1Time_x[:self.temp1Count],
                                                         self.temp1D_y[:self.temp1Count], pen=(0, 0, 255))
                    if 'U' in plot:
                        if 'u1' not in self.plotCurves:
                            self.plotCurves['u1'] = self.plotsObjects[nplots].plot(name="Sinal de Controlo")
                        self.plotCurves['u1'].setData(self.temp1Time_x[:self.temp1Count],
                                                         self.temp1U_y[:self.temp1Count], pen=(50, 50, 50))
                nplots = nplots + 1

            elif n == 3:
                if self.graph2_isUpdating:
                    if 'temp2' not in self.plotCurves:
                        self.plotCurves['temp2'] = self.plotsObjects[nplots].plot(name='Temperatura')
                    self.plotCurves['temp2'].setData(self.temp2Time_x[:self.temp2Count],
                                                     self.temp2T_y[:self.temp2Count], pen=(255, 0, 0))
                nplots = nplots + 1

            elif n == 4:
                if self.graph2_isUpdating:

                    if 'P' in plot:
                        if 'p2' not in self.plotCurves:
                            self.plotCurves['p2'] = self.plotsObjects[nplots].plot(name='Componente proporcional')
                        self.plotCurves['p2'].setData(self.temp2Time_x[:self.temp2Count],
                                                         self.temp2P_y[:self.temp2Count], pen=(255, 0, 0))
                    if 'I' in plot:
                        if 'i2' not in self.plotCurves:
                            self.plotCurves['i2'] = self.plotsObjects[nplots].plot(name='Componente integrativa')
                        self.plotCurves['i2'].setData(self.temp2Time_x[:self.temp2Count],
                                                         self.temp2I_y[:self.temp2Count], pen=(0, 255, 0))
                    if 'D' in plot:
                        if 'd2' not in self.plotCurves:
                            self.plotCurves['d2'] = self.plotsObjects[nplots].plot(name='Componente derivativa')
                        self.plotCurves['d2'].setData(self.temp2Time_x[:self.temp2Count],
                                                         self.temp2D_y[:self.temp2Count], pen=(0, 0, 255))
                    if 'U' in plot:
                        if 'u2' not in self.plotCurves:
                            self.plotCurves['u2'] = self.plotsObjects[nplots].plot(name="Sinal de Controlo")
                        self.plotCurves['u2'].setData(self.temp2Time_x[:self.temp2Count],
                                                         self.temp2U_y[:self.temp2Count], pen=(50, 50, 50))

                nplots = nplots + 1

    def graphWindowSetup(self):
        self.ui.graphWindow.clear()
        self.plotsObjects = []
        self.plotCurves = {}
        self.plots.sort(key=itemgetter(0))
        nplots = 0
        for n, plot in self.plots:
            if n == 1:
                plot = self.ui.graphWindow.addPlot(row=nplots, col=0, title='Temperatura 1')

                plot.showGrid(x=True, y=True, alpha=0.7)
                plot.addLegend()
                self.plotsObjects.append(plot)
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
                plot.addLegend()
                self.plotsObjects.append(plot)
                nplots = nplots + 1
            elif n == 3:

                plot = self.ui.graphWindow.addPlot(row=nplots, col=0, title='Temperatura 2')
                plot.showGrid(x=True, y=True, alpha=0.7)
                plot.addLegend()
                self.plotsObjects.append(plot)
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
                plot.addLegend()
                self.plotsObjects.append(plot)
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
                self.temp1U_y = np.zeros(round(self.sizeOfArraysInSeconds * (1000.0 / self.temp1TA)))
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
                self.temp2U_y = np.zeros(round(self.sizeOfArraysInSeconds * (1000.0 / self.temp2TA)))

    def startGraph1Update(self):

        self.serialQueue.put("getTemperature1 Start " + str(self.temp1TA/1000.0))

        self.maxnumberofpoints1 = round(self.sizeOfArraysInSeconds * (1000.0 / self.temp1TA))
        self.ui.graph1SaveButton.setEnabled(False)
        self.graphArraysSetup(1)
        if not self.guiupdate_qtimer.isActive():
            self.ui.ref3v3RButton.setEnabled(False)
            self.ui.ref5vButton.setEnabled(False)
            self.guiupdate_qtimer.start(self.guiupdate_qtimer_interval)

    def stopGraph1Update(self):

        self.serialQueue.put("getTemperature1 Stop")

        self.ui.graph1SaveButton.setEnabled(True)
        if not self.graph1_isUpdating and not self.graph2_isUpdating:
            self.guiupdate_qtimer.stop()
            self.ui.ref3v3RButton.setEnabled(True)
            self.ui.ref5vButton.setEnabled(True)

    def startGraph2Update(self):

        self.serialQueue.put("getTemperature2 Start " + str(self.temp2TA / 1000.0))

        self.maxnumberofpoints2 = round(self.sizeOfArraysInSeconds * (1000.0 / self.temp2TA))
        self.ui.graph2SaveButton.setEnabled(False)
        self.graphArraysSetup(2)
        if not self.guiupdate_qtimer.isActive():
            self.ui.ref3v3RButton.setEnabled(False)
            self.ui.ref5vButton.setEnabled(False)
            self.guiupdate_qtimer.start(self.guiupdate_qtimer_interval)

    def stopGraph2Update(self):

        self.serialQueue.put("getTemperature2 Stop")

        self.ui.graph2SaveButton.setEnabled(True)
        if not self.graph1_isUpdating and not self.graph2_isUpdating:
            self.guiupdate_qtimer.stop()
            self.ui.ref3v3RButton.setEnabled(True)
            self.ui.ref5vButton.setEnabled(True)

            
    #Callbacks
    @pyqtSlot()
    def connectCB(self):

        if self.is_connected:
            self.stopGraph1Update()
            self.stopGraph2Update()
            self.serialListenerThread.newTemperature1Signal.disconnect(self.temperature1CB)
            self.serialListenerThread.newTemperature2Signal.disconnect(self.temperature2CB)
            self.serialThreadStop()
            self.ui.setupUi(self)
            self.initSetup()
        elif(self.serialCOM != None):
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

    @pyqtSlot()
    def t1EnviarCB(self):
        if self.is_connected:
            self.temp1U = self.ui.t1SBox.value()
            self.serialQueue.put("setTransistor1 " + str(self.temp1U))

    @pyqtSlot()
    def t2EnviarCB(self):
        if self.is_connected:
            self.temp2U = self.ui.t2SBox.value()
            self.serialQueue.put("setTransistor2 " + str(self.temp2U))

    @pyqtSlot()
    def l1EnviarCB(self):
        if self.is_connected:
            self.serialQueue.put("setLed1 " + str(self.ui.l1SBox.value()))

    @pyqtSlot()
    def l2EnviarCB(self):
        if self.is_connected:
            self.serialQueue.put("setLed2 " + str(self.ui.l2SBox.value()))

    @pyqtSlot(int)
    def temp1TcheckboxCB(self, state):

        if state==2:
            self.plots.append((1, 'temp1T'))
        if(state==0):
            self.plots.remove((1, 'temp1T'))

        #self.graphArraysSetup(1)
        self.graphWindowSetup()

    @pyqtSlot(int)
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

    @pyqtSlot(int)
    def temp2TcheckboxCB(self, state):
        if state==2:
            self.plots.append((3, 'temp2T'))
        if(state==0):
            self.plots.remove((3, 'temp2T'))

        #self.graphArraysSetup(2)
        self.graphWindowSetup()

    @pyqtSlot(int)
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

    @pyqtSlot()
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

    @pyqtSlot()
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

    @pyqtSlot(float)
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
            self.temp1U_y[self.temp1Count] = self.temp1U

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
                self.serialQueue.put("setTransistor1 " + str(self.temp1U))

            elif self.temp1T <= self.t1TargetTemp:
                # Send Input 255
                self.temp1U = 255
                self.serialQueue.put("setTransistor1 " + str(self.temp1U))

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
            self.serialQueue.put("setTransistor1 " + str(self.temp1U))

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

            self.serialQueue.put("setTransistor1 " + str(self.temp1U))

            # Store Data
            time = self.temp1Count * self.temp1TA / 1000.0
            self.temp1T_y[self.temp1Count] = self.temp1T
            self.temp1U_y[self.temp1Count] = self.temp1U
            self.temp1P_y[self.temp1Count] = self.temp1P
            self.temp1I_y[self.temp1Count] = self.temp1I
            self.temp1D_y[self.temp1Count] = self.temp1D
            self.temp1Time_x[self.temp1Count] = time

            self.temp1Count = self.temp1Count + 1

    @pyqtSlot(float)
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
            self.temp2U_y[self.temp2Count] = self.temp2U

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
                self.serialQueue.put("setTransistor2 " + str(self.temp2U))
            elif self.temp2T <= self.t2TargetTemp:
                # Send Input 255
                self.temp2U = 255
                self.serialQueue.put("setTransistor2 " + str(self.temp2U))

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
            self.serialQueue.put("setTransistor2 " + str(self.temp2U))

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
            self.serialQueue.put("setTransistor2 " + str(self.temp2U))

            # Store Data
            time = self.temp2Count * self.temp2TA / 1000.0
            self.temp2T_y[self.temp2Count] = self.temp2T
            self.temp2U_y[self.temp2Count] = self.temp2U
            self.temp2P_y[self.temp2Count] = self.temp2P
            self.temp2I_y[self.temp2Count] = self.temp2I
            self.temp2D_y[self.temp2Count] = self.temp2D
            self.temp2Time_x[self.temp2Count] = time

            self.temp2Count = self.temp2Count + 1

    @pyqtSlot()
    def temp1StartQCB(self):
        if self.graph1_isUpdating:
            self.graph1_isUpdating = False
            self.ui.temp1StartQButton.setText("Começar")
            self.stopGraph1Update()
        else:
            self.graph1_isUpdating = True
            self.ui.temp1StartQButton.setText("Parar")
            self.startGraph1Update()

    @pyqtSlot()
    def temp2StartQCB(self):
        if self.graph2_isUpdating:
            self.graph2_isUpdating = False
            self.ui.temp2StartQButton.setText("Começar")
            self.stopGraph2Update()
        else:
            self.graph2_isUpdating = True
            self.ui.temp2StartQButton.setText("Parar")
            self.startGraph2Update()

    @pyqtSlot()
    def switchADRef(self):
        if self.is_connected:
            self.serialQueue.put("swithADREF")

    @pyqtSlot(int)
    def currentChangedControloCB(self, index):
        if not self.is_connected:
            self.ui.Controlo.setCurrentIndex(5)

    def modelListWidgetICCB(self, item):
        Temp0, TempSS, DeltaTemp, K, TauSD, TauCD, Delay = item.data(32)

        txt = "T0: "+str(Temp0)+"\nTss: "+str(TempSS)+"\n\u0394T: "+str(DeltaTemp)+"\n K: "+str(K)+"\n\nModelo sem delay:\n\n\u03C4: "+str(TauSD)+"\n\nModelo com delay:\n\n\u03C4: "+str(TauCD)+"\n \u03C4D: "+str(Delay)
        self.ui.modelosTextBrowser.setText(txt)

        self.ui.removeModelButton.setEnabled(True)

    @pyqtSlot()
    def removeModelButtonCB(self):
        #t1ModeloCBox currentindexChanged Callback
        self.ui.t1ModeloCBox.currentIndexChanged.disconnect(self.t1ModeloCBoxCIDCB)
        #t2ModeloCBox currentindexChanged Callback
        self.ui.t2ModeloCBox.currentIndexChanged.disconnect(self.t2ModeloCBoxCIDCB)

        transistor = self.ui.modelListWidget.currentItem().text().split()[1]
        key = self.ui.modelListWidget.currentItem().text().split()[3]+"-"+self.ui.modelListWidget.currentItem().text().split()[5][:-1]
        self.ModelList[transistor].pop(key)
        self.saveModelo()
        self.updateModelListView()
        self.updateModel1ComboBox()
        self.updateModel2ComboBox()

        #t1ModeloCBox currentindexChanged Callback
        self.ui.t1ModeloCBox.currentIndexChanged.connect(self.t1ModeloCBoxCIDCB)
        #t2ModeloCBox currentindexChanged Callback
        self.ui.t2ModeloCBox.currentIndexChanged.connect(self.t2ModeloCBoxCIDCB)

    @pyqtSlot()
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
            self.serialQueue.put("setTransistor1 " + str(self.temp1U))

            self.stopGraph1Update()
            self.ui.temp1StartQButton.setText("Começar")

    @pyqtSlot()
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
            self.serialQueue.put("setTransistor2 " + str(self.temp2U))

            self.stopGraph2Update()
            self.ui.temp2StartQButton.setText("Começar")

    @pyqtSlot()
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
            self.serialQueue.put("setTransistor1 " + str(self.temp1U))

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
            self.serialQueue.put("setTransistor1 " + str(self.temp1U))

            self.stopGraph1Update()
            self.ui.temp1StartQButton.setText("Começar")

    @pyqtSlot()
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
            self.serialQueue.put("setTransistor2 " + str(self.temp2U))


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
            self.serialQueue.put("setTransistor2 " + str(self.temp2U))

            self.stopGraph2Update()
            self.ui.temp2StartQButton.setText("Começar")

    @pyqtSlot()
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
            self.serialQueue.put("setTransistor1 " + str(self.temp1U))

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
            self.serialQueue.put("setTransistor1 " + str(self.temp1U))

            self.stopGraph1Update()
            self.ui.temp1StartQButton.setText("Começar")

    @pyqtSlot()
    def pidT2StartCB(self):
        if self.is_connected and not self.isControlPID2:
            self.ui.pidT2StartButton.setText("Parar")
            self.t2TargetTemp = self.ui.pidT2TargetDSBox.value()
            self.t2ControlP = self.ui.pidT2PDSBox.value()
            self.t2ControlI = self.ui.pidT2IDSBox.value()
            self.t2ControlD = self.ui.pidT2DDSBox.value()
            
            if self.isControlAW2 and self.t2ControlD > 0:
                self.t2ControlAWTt = math.sqrt((self.t2ControlP/self.t2ControlI)*(self.t2ControlD/self.t2ControlP))
            elif self.isControlAW2 and self.t2ControlD == 0:
                self.t2ControlAWTt = 0.5*(self.t2ControlP/self.t2ControlI)
			
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
            self.ui.pidT2AWcheckBox.setEnabled(False)

            # Send Input
            self.temp2U = 0

            self.serialQueue.put("setTransistor2 " + str(self.temp2U))

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
            self.ui.pidT2AWcheckBox.setEnabled(True)

            # Send Input
            self.temp2U = 0
            self.serialQueue.put("setTransistor2 " + str(self.temp2U))

            self.stopGraph2Update()
            self.ui.temp2StartQButton.setText("Começar")

    @pyqtSlot(int)
    def pidT1AWcheckBoxCB(self, state):
        if state == 2:
            self.isControlAW1 = True
        elif state == 0:
            self.isControlAW1 = False

    @pyqtSlot(int)
    def pidT2AWcheckBoxCB(self, state):
        if state == 2:
            self.isControlAW2 = True
        elif state == 0:
            self.isControlAW2 = False

    @pyqtSlot(float)
    def pidT1AWcheckCB(self, value):
        if self.ui.pidT1PDSBox.value() > 0 and self.ui.pidT1IDSBox.value() > 0:
            self.ui.pidT1AWcheckBox.setEnabled(True)
        else:
            self.ui.pidT1AWcheckBox.setCheckState(0)
            self.ui.pidT1AWcheckBox.setEnabled(False)

    @pyqtSlot(float)
    def pidT2AWcheckCB(self, value):
        if self.ui.pidT2PDSBox.value() > 0 and self.ui.pidT2IDSBox.value() > 0:
            self.ui.pidT2AWcheckBox.setEnabled(True)
        else:
            self.ui.pidT2AWcheckBox.setCheckState(0)
            self.ui.pidT2AWcheckBox.setEnabled(False)

    @pyqtSlot()
    def t1ModeloCBoxCIDCB(self):
        if self.ui.t1ModeloCBox.currentData()[6] <= 0:
            self.currentModel1HasDelay = False
        else:
            self.currentModel1HasDelay = True
        self.updateMetodo1ComboBox(self.ui.t1ControloCBox.currentIndex())

    @pyqtSlot()
    def t2ModeloCBoxCIDCB(self):
        if self.ui.t2ModeloCBox.currentData()[6] <= 0:
            self.currentModel2HasDelay = False
        else:
            self.currentModel2HasDelay = True
        self.updateMetodo2ComboBox(self.ui.t2ControloCBox.currentIndex())

    @pyqtSlot(int)
    def t1ControloCBoxCIDCB(self, index):
        self.updateMetodo1ComboBox(index)

    @pyqtSlot(int)
    def t2ControloCBoxCIDCB(self, index):
        self.updateMetodo2ComboBox(index)

    @pyqtSlot()
    def t1CalibrateButtonCB(self):
        T0, Tss, DeltaTemp, K, TauSD, TauCD, Delay = self.ui.t1ModeloCBox.currentData()
        K = K/255.0
        controlo = self.ui.t1ControloCBox.currentText()
        metodo = self.ui.t1MetodoCBox.currentText()

        if controlo == 'P':
            if metodo == 'Ziegler-Nichols Malha Aberta':
                self.t1ControlP = TauCD/(K*Delay)
            if metodo == 'Cohen-Coon':
                self.t1ControlP = (1.03/K)*(TauCD/Delay+0.34)
            if metodo == 'ITAE - Entradas de Referência':
                self.t1ControlP = (0.2/K)*(TauCD/Delay)**1.22
            if metodo == 'ITAE - Rejeição a Perturbações':
                self.t1ControlP = (0.5/K)*(TauCD/Delay)**1.08

            self.ui.pidT1PDSBox.setValue(self.t1ControlP)
            self.ui.pidT1IDSBox.setValue(0)
            self.ui.pidT1DDSBox.setValue(0)

        elif controlo == 'PI':
            if metodo == 'Ziegler-Nichols Malha Aberta':
                self.t1ControlP = (0.9*TauCD)/(K*Delay)
                self.t1ControlI = self.t1ControlP/(Delay/0.3)
            if metodo == 'Cohen-Coon':
                self.t1ControlP = (0.9/K)*(TauCD/Delay+0.092)
                self.t1ControlI = self.t1ControlP/(3.33*Delay*((TauCD+0.092*Delay)/(TauCD+2.22*Delay)))
            if metodo == 'ITAE - Entradas de Referência':
                self.t1ControlP = (0.586/K)*(TauCD/Delay)**(-0.916)
                self.t1ControlI = self.t1ControlP/(TauCD/(1.03-0.165*(Delay/TauCD)))
            if metodo == 'ITAE - Rejeição a Perturbações':
                self.t1ControlP = (0.859/K)*(TauCD/Delay)**(-0.977)
                self.t1ControlI = self.t1ControlP/((TauCD/0.674)*(Delay/TauCD)**0.680)
            if metodo == 'IMC (Sintonia agressiva)':
                if(TauCD>0):
                    self.t1ControlP = (1/K)*(TauCD/((0.1*TauCD)+Delay))
                    self.t1ControlI = self.t1ControlP/TauCD
                else:
                    self.t1ControlP = (1/K)*(TauSD/(0.1*TauSD))
                    self.t1ControlI = self.t1ControlP/TauSD
            if metodo == 'IMC (Sintonia moderada)':
                if(TauCD>0):
                    self.t1ControlP = (1/K)*(TauCD/((1*TauCD)+Delay))
                    self.t1ControlI = self.t1ControlP/TauCD
                else:
                    self.t1ControlP = (1/K)*(TauSD/(1*TauSD))
                    self.t1ControlI = self.t1ControlP/TauSD
            if metodo == 'IMC (Sintonia conservativa)':
                if(TauCD>0):
                    self.t1ControlP = (1/K)*(TauCD/((10*TauCD)+Delay))
                    self.t1ControlI = self.t1ControlP/TauCD
                else:
                    self.t1ControlP = (1/K)*(TauSD/(10*TauSD))
                    self.t1ControlI = self.t1ControlP/TauSD

            self.ui.pidT1PDSBox.setValue(self.t1ControlP)
            self.ui.pidT1IDSBox.setValue(self.t1ControlI)
            self.ui.pidT1DDSBox.setValue(0)

        elif controlo == 'PID':
            if metodo == 'Ziegler-Nichols Malha Aberta':
                self.t1ControlP = TauCD/(K*Delay)
                self.t1ControlI = self.t1ControlP/(2*Delay)
                self.t1ControlD = self.t1ControlP*Delay*0.5
            if metodo == 'Cohen-Coon':
                self.t1ControlP = (0.9/K)*(TauCD/Delay+0.092)
                self.t1ControlI = self.t1ControlP/(2.5*Delay*((TauCD+0.185*Delay)/(TauCD+0.611*Delay)))
                self.t1ControlD = self.t1ControlP*0.37*Delay*(TauCD/(TauCD+0.185*Delay))
            if metodo == 'IMC (Sintonia agressiva)':
                if(TauCD>0):
                    self.t1ControlP = (1/K)*((TauCD+0.5*Delay)/(0.1*TauCD+0.5*Delay))
                    self.t1ControlI = self.t1ControlP/(TauCD+0.5*Delay)
                    self.t1ControlD = self.t1ControlP * (TauCD*Delay)/(2*TauCD+Delay)
                else:
                    self.t1ControlP = (1/K)*((TauSD)/(0.1*TauSD))
                    self.t1ControlI = self.t1ControlP/(TauSD)
                    self.t1ControlD = 0
            if metodo == 'IMC (Sintonia moderada)':
                if(TauCD>0):
                    self.t1ControlP = (1/K)*((TauCD+0.5*Delay)/(1*TauCD+0.5*Delay))
                    self.t1ControlI = self.t1ControlP/(TauCD+0.5*Delay)
                    self.t1ControlD = self.t1ControlP * (TauCD*Delay)/(2*TauCD+Delay)
                else:
                    self.t1ControlP = (1/K)*((TauSD)/(1*TauSD))
                    self.t1ControlI = self.t1ControlP/(TauSD)
                    self.t1ControlD = 0
            if metodo == 'IMC (Sintonia conservativa)':
                if(TauCD>0):
                    self.t1ControlP = (1/K)*((TauCD+0.5*Delay)/(10*TauCD+0.5*Delay))
                    self.t1ControlI = self.t1ControlP/(TauCD+0.5*Delay)
                    self.t1ControlD = self.t1ControlP * (TauCD*Delay)/(2*TauCD+Delay)
                else:
                    self.t1ControlP = (1/K)*((TauSD)/(10*TauSD))
                    self.t1ControlI = self.t1ControlP/(TauSD)
                    self.t1ControlD = 0

            self.ui.pidT1PDSBox.setValue(self.t1ControlP)
            self.ui.pidT1IDSBox.setValue(self.t1ControlI)
            self.ui.pidT1DDSBox.setValue(self.t1ControlD)

    @pyqtSlot()
    def t2CalibrateButtonCB(self):
        T0, Tss, DeltaTemp, K, TauSD, TauCD, Delay = self.ui.t2ModeloCBox.currentData()
        K = K/255.0
        controlo = self.ui.t2ControloCBox.currentText()
        metodo = self.ui.t2MetodoCBox.currentText()

        if controlo == 'P':
            if metodo == 'Ziegler-Nichols Malha Aberta':
                self.t2ControlP = TauCD/(K*Delay)
            if metodo == 'Cohen-Coon':
                self.t2ControlP = (1.03/K)*(TauCD/Delay+0.34)
            if metodo == 'ITAE - Entradas de Referência':
                self.t2ControlP = (0.2/K)*(TauCD/Delay)**1.22
            if metodo == 'ITAE - Rejeição a Perturbações':
                self.t2ControlP = (0.5/K)*(TauCD/Delay)**1.08

            self.ui.pidT2PDSBox.setValue(self.t2ControlP)
            self.ui.pidT2IDSBox.setValue(0)
            self.ui.pidT2DDSBox.setValue(0)

        elif controlo == 'PI':
            if metodo == 'Ziegler-Nichols Malha Aberta':
                self.t2ControlP = (0.9*TauCD)/(K*Delay)
                self.t2ControlI = self.t2ControlP/(Delay/0.3)
            if metodo == 'Cohen-Coon':
                self.t2ControlP = (0.9/K)*(TauCD/Delay+0.092)
                self.t2ControlI = self.t2ControlP/(3.33*Delay*((TauCD+0.092*Delay)/(TauCD+2.22*Delay)))
            if metodo == 'ITAE - Entradas de Referência':
                self.t2ControlP = (0.586/K)*(TauCD/Delay)**(-0.916)
                self.t2ControlI = self.t2ControlP/(TauCD/(1.03-0.165*(Delay/TauCD)))
            if metodo == 'ITAE - Rejeição a Perturbações':
                self.t2ControlP = (0.859/K)*(TauCD/Delay)**(-0.977)
                self.t2ControlI = self.t2ControlP/((TauCD/0.674)*(Delay/TauCD)**0.680)
            if metodo == 'IMC (Sintonia agressiva)':
                if(TauCD>0):
                    self.t2ControlP = (1/K)*(TauCD/((0.1*TauCD)+Delay))
                    self.t2ControlI = self.t2ControlP/TauCD
                else:
                    self.t2ControlP = (1/K)*(TauSD/(0.1*TauSD))
                    self.t2ControlI = self.t2ControlP/TauSD
            if metodo == 'IMC (Sintonia moderada)':
                if(TauCD>0):
                    self.t2ControlP = (1/K)*(TauCD/((1*TauCD)+Delay))
                    self.t2ControlI = self.t2ControlP/TauCD
                else:
                    self.t2ControlP = (1/K)*(TauSD/(1*TauSD))
                    self.t2ControlI = self.t2ControlP/TauSD
            if metodo == 'IMC (Sintonia conservativa)':
                if(TauCD>0):
                    self.t2ControlP = (1/K)*(TauCD/((10*TauCD)+Delay))
                    self.t2ControlI = self.t2ControlP/TauCD
                else:
                    self.t2ControlP = (1/K)*(TauSD/(10*TauSD))
                    self.t2ControlI = self.t2ControlP/TauSD

            self.ui.pidT2PDSBox.setValue(self.t2ControlP)
            self.ui.pidT2IDSBox.setValue(self.t2ControlI)
            self.ui.pidT2DDSBox.setValue(0)

        elif controlo == 'PID':
            if metodo == 'Ziegler-Nichols Malha Aberta':
                self.t2ControlP = TauCD/(K*Delay)
                self.t2ControlI = self.t2ControlP/(2*Delay)
                self.t2ControlD = self.t2ControlP*Delay*0.5
            if metodo == 'Cohen-Coon':
                self.t2ControlP = (0.9/K)*(TauCD/Delay+0.092)
                self.t2ControlI = self.t2ControlP/(2.5*Delay*((TauCD+0.185*Delay)/(TauCD+0.611*Delay)))
                self.t2ControlD = self.t2ControlP*0.37*Delay*(TauCD/(TauCD+0.185*Delay))
            if metodo == 'IMC (Sintonia agressiva)':
                if(TauCD>0):
                    self.t2ControlP = (1/K)*((TauCD+0.5*Delay)/(0.1*TauCD+0.5*Delay))
                    self.t2ControlI = self.t2ControlP/(TauCD+0.5*Delay)
                    self.t2ControlD = self.t2ControlP * (TauCD*Delay)/(2*TauCD+Delay)
                else:
                    self.t2ControlP = (1/K)*((TauSD)/(0.1*TauSD))
                    self.t2ControlI = self.t2ControlP/(TauSD)
                    self.t2ControlD = 0
            if metodo == 'IMC (Sintonia moderada)':
                if(TauCD>0):
                    self.t2ControlP = (1/K)*((TauCD+0.5*Delay)/(1*TauCD+0.5*Delay))
                    self.t2ControlI = self.t2ControlP/(TauCD+0.5*Delay)
                    self.t2ControlD = self.t2ControlP * (TauCD*Delay)/(2*TauCD+Delay)
                else:
                    self.t2ControlP = (1/K)*((TauSD)/(1*TauSD))
                    self.t2ControlI = self.t2ControlP/(TauSD)
                    self.t2ControlD = 0
            if metodo == 'IMC (Sintonia conservativa)':
                if(TauCD>0):
                    self.t2ControlP = (1/K)*((TauCD+0.5*Delay)/(10*TauCD+0.5*Delay))
                    self.t2ControlI = self.t2ControlP/(TauCD+0.5*Delay)
                    self.t2ControlD = self.t2ControlP * (TauCD*Delay)/(2*TauCD+Delay)
                else:
                    self.t2ControlP = (1/K)*((TauSD)/(10*TauSD))
                    self.t2ControlI = self.t2ControlP/(TauSD)
                    self.t2ControlD = 0

            self.ui.pidT2PDSBox.setValue(self.t2ControlP)
            self.ui.pidT2IDSBox.setValue(self.t2ControlI)
            self.ui.pidT2DDSBox.setValue(self.t2ControlD)

    @pyqtSlot()
    def graph1SaveButtonCB(self):
        filename = str(QtGui.QFileDialog.getSaveFileName(self, 'Save File', 'dados/dados_plot_1.txt', 'ALL (*.*)'))
        if filename != "(\'\', \'\')":
            with open(filename[2:-15], 'w') as file:
                if not self.isCreatingModel1:
                    file.write("Time Temperatura PWM P I D")
                    for i in range(self.temp1Count):
                        line = str(self.temp1Time_x[i]) +" "+ str(self.temp1T_y[i]) +" "+ str(self.temp1U_y[i]) +" "+ str(self.temp1P_y[i]) +" "+ str(self.temp1I_y[i]) +" "+ str(self.temp1D_y[i])+"\n"
                        file.write(line)
                else:
                    file.write("Time Temperatura PWM")
                    for i in range(self.temp1Count):
                        line = str(self.temp1Time_x[i]) +" "+ str(self.temp1T_y[i]) +" "+ str(self.temp1U)+"\n"
                        file.write(line)

    @pyqtSlot()
    def graph2SaveButtonCB(self):
        filename = str(QtGui.QFileDialog.getSaveFileName(self, 'Save File', 'dados/dados_plot_2.txt', 'ALL (*.*)'))
        if filename != "(\'\', \'\')":
            with open(filename[2:-15], 'w') as file:
                if not self.isCreatingModel2:
                    file.write("Time Temperatura PWM P I D")
                    for i in range(self.temp2Count):
                        line = str(self.temp2Time_x[i]) +" "+ str(self.temp2T_y[i]) +" "+ str(self.temp2U_y[i]) +" "+ str(self.temp2P_y[i]) +" "+ str(self.temp2I_y[i]) +" "+ str(self.temp2D_y[i])+"\n"
                        file.write(line)
                if self.isCreatingModel2:
                    file.write("Time Temperatura PWM")
                    for i in range(self.temp2Count):
                        line = str(self.temp2Time_x[i]) +" "+ str(self.temp2T_y[i]) +" "+ str(self.temp2U)+"\n"
                        file.write(line)			

def main():
    app = QtWidgets.QApplication(sys.argv)
    application = ApplicationWindow()
    application.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
