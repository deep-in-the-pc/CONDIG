# -*- coding: latin-1 -*-


from operator import itemgetter
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

        #Graph
        self.temp1TA = None
        self.temp2TA = None
        self.plots = []
        self.plotsObjects = []


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
        #TODO add limit to stretch tool bar
        #TODO plot data on 1 or 2 plots depending on amount to temperature sensor data received
        #TODO link serial event for receiving data to graph update
        #TODO add options to graph info area (start temperature get timer; set temperature#DeltaTime; set analogReference)
        #TODO search library for making transfer functions
        #TODO clear graph and data lists when creating new model
        #TODO store model in file
        #TODO Load models on startup
        #TODO search library to calibrate PID to model
        #TODO add options to graph info area (P, I, D componentes to new plot; input value to new plot;)


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
    #Graph

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


    def graphArraysSetup(self):

        for n, plot in self.plots:
            if n == 1:
                maxnumberofpoints = round(300*(1000.0/self.temp1TA))
                self.temp1T_x = np.zeros(maxnumberofpoints)
                self.temp1T_y = np.zeros(maxnumberofpoints)


            elif n == 2:
                maxnumberofpoints = round(300 * (1000.0 / self.temp1TA))
                if 'P' in plot:
                    self.temp1P_x = np.zeros(maxnumberofpoints)
                    self.temp1P_y = np.zeros(maxnumberofpoints)
                if 'I' in plot:
                    self.temp1I_x = np.zeros(maxnumberofpoints)
                    self.temp1I_y = np.zeros(maxnumberofpoints)
                if 'D' in plot:
                    self.temp1D_x = np.zeros(maxnumberofpoints)
                    self.temp1D_y = np.zeros(maxnumberofpoints)
                if 'U' in plot:
                    self.temp1U_x = np.zeros(maxnumberofpoints)
                    self.temp1U_y = np.zeros(maxnumberofpoints)
            elif n == 3:
                maxnumberofpoints = round(300*(1000.0/self.temp2TA))
                self.temp2T_x = np.zeros(maxnumberofpoints)
                self.temp2T_y = np.zeros(maxnumberofpoints)
            elif n == 4:
                maxnumberofpoints = round(300 * (1000.0 / self.temp2TA))
                if 'P' in plot:
                    self.temp2P_x = np.zeros(maxnumberofpoints)
                    self.temp2P_y = np.zeros(maxnumberofpoints)
                if 'I' in plot:
                    self.temp2I_x = np.zeros(maxnumberofpoints)
                    self.temp2I_y = np.zeros(maxnumberofpoints)
                if 'D' in plot:
                    self.temp2D_x = np.zeros(maxnumberofpoints)
                    self.temp2D_y = np.zeros(maxnumberofpoints)
                if 'U' in plot:
                    self.temp2U_x = np.zeros(maxnumberofpoints)
                    self.temp2U_y = np.zeros(maxnumberofpoints)

    #Callbacks

    def connectCB(self):

        if not self.serialListenerThread.closeEvent.is_set():
            self.serialThreadStop()
            self.ui.conectarButton.setText("Connect")
            self.ui.connectionLabel.setText("Conexão: Desligada")
        elif(self.serialCOM != None):
            self.serialListenerThread.closeEvent.clear()
            self.serialThreadStart()
            if(self.serialListenerThread.isRunning()):
                self.ui.connectionLabel.setText("Conexão: Ligado")
                # If connection is established set text as disconnect
                self.ui.conectarButton.setText("Disconnect")

    def t1EnviarCB(self):
        if self.is_connected:
            self.serialListenerThread.transistor1 = self.ui.t1SBox.value()
            self.serialListenerThread.setTransistor1.set()
    def t2EnviarCB(self):
        if self.is_connected:
            self.serialListenerThread.transistor2 = self.ui.t2SBox.value()
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

        self.graphWindowSetup()

    def temp2TcheckboxCB(self, state):
        if state==2:
            self.plots.append((3, 'temp2T'))
        if(state==0):
            self.plots.remove((3, 'temp2T'))
        if len(self.plots):
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



def main():
    app = QtWidgets.QApplication(sys.argv)
    application = ApplicationWindow()
    application.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
