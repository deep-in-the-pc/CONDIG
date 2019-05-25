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

        self.serialThreadSetup()
        self.is_connected = False

        self.comlist_qtimer = QtCore.QTimer(self)
        self.comlist_qtimer.timeout.connect(self.getCOMList)
        self.comlist_qtimer_interval = 100
        self.comlist_qtimer.start(self.comlist_qtimer_interval)
        self.guiupdate_qtimer = QtCore.QTimer(self)
        self.guiupdate_qtimer.timeout.connect(self.updateGUI)
        self.guiupdate_qtimer_interval = 1000

        #Model
        self.isCreatingModel1 = False

        #Graph
        self.temp1TA = None
        self.temp2TA = None
        self.plots = []
        self.plotsObjects = []
        self.maxnumberofpoints1 = None
        self.maxnumberofpoints2 = None
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

        self.ui.t1CriarModeloButton.clicked.connect(self.createModel1)

        #TODO reset everything when disconneting
        #TODO add set analogReference
        #TODO store model in file
        #TODO Load models on startup
        #TODO implement on-off control
        #TODO implement histerese control
        #TODO implement PID control
        #TODO implement pid tunning from condig classes
        #TODO implement option to delete models

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
        if self.is_connected:

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

    def finishModel1(self, tss):

        self.isCreatingModel1 = False
        self.serialListenerThread.transistor1 = 0
        self.serialListenerThread.setTransistor1.set()

        self.graph1_isUpdating = False
        self.ui.temp1StartQButton.setText("Começar")
        self.stopGraph1Update()

        self.modelo1Temp0 = self.temp1T_y[0]
        self.modelo1TempSS = tss
        self.modelo1DeltaTemp = self.modelo1TempSS - self.modelo1Temp0
        self.modelo1K = self.modelo1DeltaTemp / (self.temp1U/255.0)

        index = np.where(self.temp1T_y >= (self.modelo1DeltaTemp*0.632)+self.modelo1Temp0)[0]

        self.modelo1TauSD = self.temp1T_x[index[0]]

        t1index = np.where(self.temp1T_y >= (self.modelo1DeltaTemp*0.283)+self.modelo1Temp0)[0]
        t1 = self.temp1T_x[t1index[0]]
        t2index = np.where(self.temp1T_y >= (self.modelo1DeltaTemp*0.632)+self.modelo1Temp0)[0]
        t2 = self.temp1T_x[t2index[0]]


        self.modelo1TauCD = (3.0/2.0)*(t2-t1)
        self.modelo1Delay = t2 - self.modelo1TauCD

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
    #Graph

    def updateGUI(self):
        nplots = 0
        for n, plot in self.plots:
            if n == 1:
                if self.graph1_isUpdating:
                    for item in self.plotsObjects[nplots][0].listDataItems():
                        if item.name() == "Temperatura 1":
                            self.plotsObjects[nplots][0].removeItem(item)
                    temp = self.plotsObjects[nplots][0].plot(self.temp1T_x[:self.temp1Count], self.temp1T_y[:self.temp1Count], pen=(255, 0, 0),name="Temperatura 1")
                    self.plotsObjects[nplots][1].removeItem('Temperatura 1')
                    self.plotsObjects[nplots][1].addItem(temp, 'Temperatura 1')
                nplots = nplots + 1
            elif n == 2:
                if self.graph1_isUpdating:

                    if 'P' in plot:
                        for item in self.plotsObjects[nplots][0].listDataItems():
                            if item.name() == "Componente proporcional 1":
                                self.plotsObjects[nplots][0].removeItem(item)
                        temp = self.plotsObjects[nplots][0].plot(self.temp1P_x[:self.temp1Count], self.temp1P_y[:self.temp1Count], pen=(255, 0, 0),
                                                                 name="Componente proporcional 1")
                        self.plotsObjects[nplots][1].removeItem('Componente proporcional 1')
                        self.plotsObjects[nplots][1].addItem(temp, 'Componente proporcional 1')
                    if 'I' in plot:
                        for item in self.plotsObjects[nplots][0].listDataItems():
                            if item.name() == "Componente integrativa 1":
                                self.plotsObjects[nplots][0].removeItem(item)
                        temp = self.plotsObjects[nplots][0].plot(self.temp1I_x[:self.temp1Count], self.temp1I_y[:self.temp1Count], pen=(0, 255, 0),
                                                                 name="Componente integrativa 1")
                        self.plotsObjects[nplots][1].removeItem('Componente integrativa 1')
                        self.plotsObjects[nplots][1].addItem(temp, 'Componente integrativa 1')
                    if 'D' in plot:
                        for item in self.plotsObjects[nplots][0].listDataItems():
                            if item.name() == "Componente derivativa 1":
                                self.plotsObjects[nplots][0].removeItem(item)
                        temp = self.plotsObjects[nplots][0].plot(self.temp1D_x[:self.temp1Count], self.temp1D_y[:self.temp1Count], pen=(0, 0, 255),
                                                                 name="Componente derivativa 1")
                        self.plotsObjects[nplots][1].removeItem('Componente derivativa 1')
                        self.plotsObjects[nplots][1].addItem(temp, 'Componente derivativa 1')
                    if 'U' in plot:
                        for item in self.plotsObjects[nplots][0].listDataItems():
                            if item.name() == "Sinal de entrada 1":
                                self.plotsObjects[nplots][0].removeItem(item)
                        temp = self.plotsObjects[nplots][0].plot(self.temp1U_x[:self.temp1Count], self.temp1U_y[:self.temp1Count], pen=(191, 191, 0),
                                                                 name="Sinal de entrada 1")
                        self.plotsObjects[nplots][1].removeItem('Sinal de entrada 1')
                        self.plotsObjects[nplots][1].addItem(temp, 'Sinal de entrada 1')

                nplots = nplots + 1

            elif n == 3:
                if self.graph2_isUpdating:

                    for item in self.plotsObjects[nplots][0].listDataItems():
                        if item.name() == "Temperatura 2":
                            self.plotsObjects[nplots][0].removeItem(item)
                    temp = self.plotsObjects[nplots][0].plot(self.temp2T_x[:self.temp2Count], self.temp2T_y[:self.temp2Count], pen=(255, 0, 0),name="Temperatura 2")
                    self.plotsObjects[nplots][1].removeItem('Temperatura 2')
                    self.plotsObjects[nplots][1].addItem(temp, 'Temperatura 2')
                nplots = nplots + 1

            elif n == 4:
                if self.graph2_isUpdating:

                    if 'P' in plot:
                        for item in self.plotsObjects[nplots][0].listDataItems():
                            if item.name() == "Componente proporcional 2":
                                self.plotsObjects[nplots][0].removeItem(item)
                        temp = self.plotsObjects[nplots][0].plot(self.temp2P_x[:self.temp2Count], self.temp2P_y[:self.temp2Count], pen=(255, 0, 0),
                                                                 name="Componente proporcional 2")
                        self.plotsObjects[nplots][1].removeItem('Componente proporcional 2')
                        self.plotsObjects[nplots][1].addItem(temp, 'Componente proporcional 2')
                    if 'I' in plot:
                        for item in self.plotsObjects[nplots][0].listDataItems():
                            if item.name() == "Componente integrativa 2":
                                self.plotsObjects[nplots][0].removeItem(item)
                        temp = self.plotsObjects[nplots][0].plot(self.temp2I_x[:self.temp2Count], self.temp2I_y[:self.temp2Count], pen=(0, 255, 0),
                                                                 name="Componente integrativa 2")
                        self.plotsObjects[nplots][1].removeItem('Componente integrativa 2')
                        self.plotsObjects[nplots][1].addItem(temp, 'Componente integrativa 2')
                    if 'D' in plot:
                        for item in self.plotsObjects[nplots][0].listDataItems():
                            if item.name() == "Componente derivativa 2":
                                self.plotsObjects[nplots][0].removeItem(item)
                        temp = self.plotsObjects[nplots][0].plot(self.temp2D_x[:self.temp2Count], self.temp2D_y[:self.temp2Count], pen=(0, 0, 255),
                                                                 name="Componente derivativa 2")
                        self.plotsObjects[nplots][1].removeItem('Componente derivativa 2')
                        self.plotsObjects[nplots][1].addItem(temp, 'Componente derivativa 2')
                    if 'U' in plot:
                        for item in self.plotsObjects[nplots][0].listDataItems():
                            if item.name() == "Sinal de entrada 2":
                                self.plotsObjects[nplots][0].removeItem(item)
                        temp = self.plotsObjects[nplots][0].plot(self.temp2U_x[:self.temp2Count], self.temp2U_y[:self.temp2Count], pen=(191, 191, 0),
                                                                 name="Sinal de entrada 2")
                        self.plotsObjects[nplots][1].removeItem('Sinal de entrada 2')
                        self.plotsObjects[nplots][1].addItem(temp, 'Sinal de entrada 2')

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
        if not self.isCreatingModel1: #or self.isCreatingModel2:
            if plot == 1:
                self.temp1Count = 0
                self.temp1T_x = np.zeros(self.maxnumberofpoints1)
                self.temp1T_y = np.zeros(self.maxnumberofpoints1)
                self.temp1P_x = np.zeros(self.maxnumberofpoints1)
                self.temp1P_y = np.zeros(self.maxnumberofpoints1)
                self.temp1I_x = np.zeros(self.maxnumberofpoints1)
                self.temp1I_y = np.zeros(self.maxnumberofpoints1)
                self.temp1D_x = np.zeros(self.maxnumberofpoints1)
                self.temp1D_y = np.zeros(self.maxnumberofpoints1)
                self.temp1U_x = np.zeros(self.maxnumberofpoints1)
                self.temp1U_y = np.zeros(self.maxnumberofpoints1)
            if plot == 2:
                self.temp2Count = 0
                self.temp2T_x = np.zeros(self.maxnumberofpoints2)
                self.temp2T_y = np.zeros(self.maxnumberofpoints2)
                self.temp2P_x = np.zeros(self.maxnumberofpoints2)
                self.temp2P_y = np.zeros(self.maxnumberofpoints2)
                self.temp2I_x = np.zeros(self.maxnumberofpoints2)
                self.temp2I_y = np.zeros(self.maxnumberofpoints2)
                self.temp2D_x = np.zeros(self.maxnumberofpoints2)
                self.temp2D_y = np.zeros(self.maxnumberofpoints2)
                self.temp2U_x = np.zeros(self.maxnumberofpoints2)
                self.temp2U_y = np.zeros(self.maxnumberofpoints2)
        elif self.isCreatingModel1:
            self.temp1Count = 0
            self.temp1T_x = np.zeros(round(1200 * (1000.0 / self.temp1TA)))
            self.temp1T_y = np.zeros(round(1200 * (1000.0 / self.temp1TA)))

    def startGraph1Update(self):
        self.serialListenerThread.temperature1DeltaTime = self.temp1TA/1000.0
        self.serialListenerThread.getTemperature1.set()
        self.maxnumberofpoints1 = round(300 * (1000.0 / self.temp1TA))
        self.graphArraysSetup(1)
        if not self.guiupdate_qtimer.isActive():
            self.guiupdate_qtimer.start(self.guiupdate_qtimer_interval)

    def stopGraph1Update(self):
        self.serialListenerThread.getTemperature1.clear()
        if not self.graph1_isUpdating and not self.graph2_isUpdating:
            self.guiupdate_qtimer.stop()

    def startGraph2Update(self):
        self.serialListenerThread.temperature2DeltaTime = self.temp2TA / 1000.0
        self.serialListenerThread.getTemperature2.set()
        self.maxnumberofpoints2 = round(300 * (1000.0 / self.temp2TA))
        self.graphArraysSetup(2)
        if not self.guiupdate_qtimer.isActive():
            self.guiupdate_qtimer.start(self.guiupdate_qtimer_interval)

    def stopGraph2Update(self):
        self.serialListenerThread.getTemperature2.clear()
        if not self.graph1_isUpdating and not self.graph2_isUpdating:
            self.guiupdate_qtimer.stop()

    #Callbacks

    def connectCB(self):

        if not self.serialListenerThread.closeEvent.is_set():
            self.serialThreadStop()
            self.ui.conectarButton.setText("Connect")
            self.ui.connectionLabel.setText("Conexão: Desligada")
            self.ui.Controlo.setEnabled(False)
            self.ui.frame.setEnabled(False)
            self.ui.temp1TAEdit.setText('')
            self.temp1TA = None
            self.ui.temp2TAEdit.setText('')
            self.temp2TA = None
        elif(self.serialCOM != None):
            self.serialListenerThread.closeEvent.clear()
            self.serialThreadStart()
            if(self.serialListenerThread.isRunning()):
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

        if not self.isCreatingModel1:# or self.isCreatingModel2:

            if (self.temp1Count < self.maxnumberofpoints1):

                time = self.temp1Count * self.temp1TA / 1000.0
                self.temp1T_y[self.temp1Count] = self.temp1T
                self.temp1P_y[self.temp1Count] = self.temp1P
                self.temp1I_y[self.temp1Count] = self.temp1I
                self.temp1D_y[self.temp1Count] = self.temp1D
                self.temp1U_y[self.temp1Count] = self.temp1U

                self.temp1T_x[self.temp1Count] = time
                self.temp1P_x[self.temp1Count] = time
                self.temp1I_x[self.temp1Count] = time
                self.temp1D_x[self.temp1Count] = time
                self.temp1U_x[self.temp1Count] = time
                self.temp1Count = self.temp1Count + 1
            else:

                lasttime = self.temp1T_x[-1]
                time = lasttime + self.temp1TA / 1000.0
                self.temp1T_y = np.roll(self.temp1T_y, -1)
                self.temp1P_y = np.roll(self.temp1P_y, -1)
                self.temp1I_y = np.roll(self.temp1I_y, -1)
                self.temp1D_y = np.roll(self.temp1D_y, -1)
                self.temp1U_y = np.roll(self.temp1U_y, -1)

                self.temp1T_x = np.roll(self.temp1T_x, -1)
                self.temp1P_x = np.roll(self.temp1P_x, -1)
                self.temp1I_x = np.roll(self.temp1I_x, -1)
                self.temp1D_x = np.roll(self.temp1D_x, -1)
                self.temp1U_x = np.roll(self.temp1U_x, -1)

                self.temp1T_y[-1] = self.temp1T
                self.temp1P_y[-1] = self.temp1P
                self.temp1I_y[-1] = self.temp1I
                self.temp1D_y[-1] = self.temp1D
                self.temp1U_y[-1] = self.temp1U

                self.temp1T_x[-1] = time
                self.temp1P_x[-1] = time
                self.temp1I_x[-1] = time
                self.temp1D_x[-1] = time
                self.temp1U_x[-1] = time

        elif self.isCreatingModel1:
            time = self.temp1Count * self.temp1TA / 1000.0
            self.temp1T_y[self.temp1Count] = self.temp1T
            self.temp1T_x[self.temp1Count] = time


            #Check if last 30 seconds are stable
            if self.temp1T_x[self.temp1Count] > 30:
                ns = round(30*(1000.0/self.temp1TA))
                avrg = sum(self.temp1T_y[self.temp1Count-ns:self.temp1Count])/ns
                avrgerror = sum(abs(self.temp1T_y[self.temp1Count-ns:self.temp1Count] - avrg)) / ns
                print(self.temp1Count, avrgerror)
                if avrgerror < 0.02: # certeza superior a 99.98%
                    self.finishModel1(avrg)

            self.temp1Count = self.temp1Count + 1
            if self.temp1Count == round(1200 * (1000.0 / self.temp1TA)):
                self.finishModel1(avrg)

    def temperature2CB(self, temp):
        
        self.temp2T = temp

        if (self.temp2Count < self.maxnumberofpoints2):

            time = self.temp2Count * self.temp2TA / 1000.0
            self.temp2T_y[self.temp2Count] = self.temp2T
            self.temp2P_y[self.temp2Count] = self.temp2P
            self.temp2I_y[self.temp2Count] = self.temp2I
            self.temp2D_y[self.temp2Count] = self.temp2D
            self.temp2U_y[self.temp2Count] = self.temp2U

            self.temp2T_x[self.temp2Count] = time
            self.temp2P_x[self.temp2Count] = time
            self.temp2I_x[self.temp2Count] = time
            self.temp2D_x[self.temp2Count] = time
            self.temp2U_x[self.temp2Count] = time
            self.temp2Count = self.temp2Count + 1
        else:

            lasttime = self.temp2T_x[-1]
            time = lasttime + self.temp2TA / 1000.0
            self.temp2T_y = np.roll(self.temp2T_y, -1)
            self.temp2P_y = np.roll(self.temp2P_y, -1)
            self.temp2I_y = np.roll(self.temp2I_y, -1)
            self.temp2D_y = np.roll(self.temp2D_y, -1)
            self.temp2U_y = np.roll(self.temp2U_y, -1)

            self.temp2T_x = np.roll(self.temp2T_x, -1)
            self.temp2P_x = np.roll(self.temp2P_x, -1)
            self.temp2I_x = np.roll(self.temp2I_x, -1)
            self.temp2D_x = np.roll(self.temp2D_x, -1)
            self.temp2U_x = np.roll(self.temp2U_x, -1)

            self.temp2T_y[-1] = self.temp2T
            self.temp2P_y[-1] = self.temp2P
            self.temp2I_y[-1] = self.temp2I
            self.temp2D_y[-1] = self.temp2D
            self.temp2U_y[-1] = self.temp2U

            self.temp2T_x[-1] = time
            self.temp2P_x[-1] = time
            self.temp2I_x[-1] = time
            self.temp2D_x[-1] = time
            self.temp2U_x[-1] = time

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

def main():
    app = QtWidgets.QApplication(sys.argv)
    application = ApplicationWindow()
    application.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
