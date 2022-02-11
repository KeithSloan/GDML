
import FreeCAD,FreeCADGui
from PySide import QtGui, QtCore


class importPrompt(QtGui.QDialog):
    def __init__(self, *args):
        super(importPrompt, self).__init__()
        self.initUI()

    def initUI(self):
        importButton = QtGui.QPushButton('Import')
        importButton.clicked.connect(self.onImport)
        scanButton = QtGui.QPushButton('Scan Vol')
        scanButton .clicked.connect(self.onScan)
        #
        buttonBox = QtGui.QDialogButtonBox()
        buttonBox.setFixedWidth(400)
        # buttonBox = Qt.QDialogButtonBox(QtCore.Qt.Vertical)
        buttonBox.addButton(importButton, QtGui.QDialogButtonBox.ActionRole)
        buttonBox.addButton(scanButton, QtGui.QDialogButtonBox.ActionRole)
        #
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)
        # self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        # define window         xLoc,yLoc,xDim,yDim
        self.setGeometry(650, 650, 0, 50)
        self.setWindowTitle("Choose an Option    ")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.retStatus = 0

    def onImport(self):
        self.retStatus = 1
        self.close()

    def onScan(self):
        self.retStatus = 2
        self.close()


class showInvalidWorldVol(QtGui.QWidget):

    def __init__(self):
        super().__init__()
        self.title = 'Invalid World messagebox'
        self.left = 200
        self.top = 200
        self.width = 320
        self.height = 200
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        box = QtGui.QMessageBox.information(self, 'Invalid World Volume',
                                            'World Vol must only contain one GDML Object, correct and try again',
                                            #QtGui.QMessageBox.Yes | QtGui.QMessageBox.Ok)
                                            QtGui.QMessageBox.Ok)
        self.show()
