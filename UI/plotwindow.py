# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'UI\plotwindow.ui'
#
# Created by: PyQt5 UI code generator 5.14.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_PlotWindow(object):
    def setupUi(self, PlotWindow):
        PlotWindow.setObjectName("PlotWindow")
        PlotWindow.resize(712, 454)
        self.centralwidget = QtWidgets.QWidget(PlotWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.graphWidget = PlotWidget(self.centralwidget)
        self.graphWidget.setObjectName("graphWidget")
        self.gridLayout.addWidget(self.graphWidget, 0, 0, 1, 1)
        PlotWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(PlotWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 712, 21))
        self.menubar.setObjectName("menubar")
        PlotWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(PlotWindow)
        self.statusbar.setObjectName("statusbar")
        PlotWindow.setStatusBar(self.statusbar)

        self.retranslateUi(PlotWindow)
        QtCore.QMetaObject.connectSlotsByName(PlotWindow)

    def retranslateUi(self, PlotWindow):
        _translate = QtCore.QCoreApplication.translate
        PlotWindow.setWindowTitle(_translate("PlotWindow", "Plot"))


from pyqtgraph import PlotWidget
