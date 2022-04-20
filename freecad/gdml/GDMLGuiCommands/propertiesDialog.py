import FreeCAD

from PySide import QtGui, QtCore


class propertyFloat(QtGui.QLineEdit):
    def __init__(self, value):
        super().__init__()
        self.insert(str(value))


class propertyPlacement(QtGui.QWidget):
    def __init__(self, name, value):
        super().__init__()
        self.hbox = QtGui.QHBoxLayout()
        self.hbox.addWidget(QtGui.QLabel(name))
        self.hbox.addWidget(propertyFloat(value))
        self.setLayout(self.hbox)


class propertyMaterial(QtGui.QWidget):
    def __init__(self, name, value):
        super().__init__()
        self.hbox = QtGui.QHBoxLayout()
        self.hbox.addWidget(QtGui.QLabel('Material'))
        self.hbox.addWidget(propertyFloat(value))
        self.setLayout(self.hbox)


class property_aunits(QtGui.QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QtGui.QHBoxLayout()
        self.layout.addWidget(QtGui.QLabel('aunit'))
        self.units = QtGui.QComboBox()
        self.units.addItems(["deg", "rad"])
        self.layout.addWidget(self.units)
        self.setLayout(self.layout)


class property_lunits(QtGui.QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QtGui.QHBoxLayout()
        self.layout.addWidget(QtGui.QLabel('lunit'))
        self.units = QtGui.QComboBox()
        self.units.addItems(["mm", "cm", "m", "um", "nm"])
        self.layout.addWidget(self.units)
        self.setLayout(self.layout)


class propertyUnits(QtGui.QWidget):
    def __init__(self, obj):
        super().__init__()
        self.unitsLayout = QtGui.QHBoxLayout()
        if 'lunit' in obj.PropertiesList:
            self.unitsLayout.addWidget(property_lunits())
        if 'aunit' in obj.PropertiesList:
            self.unitsLayout.addWidget(property_aunits())
        self.setLayout(self.unitsLayout)


class propertyEntry(QtGui.QWidget):

    def __init__(self, name, value):
        super().__init__()
        self.hbox = QtGui.QHBoxLayout()
        self.hbox.addWidget(QtGui.QLabel(name))
        self.hbox.addWidget(propertyFloat(value))
        self.setLayout(self.hbox)


class propertiesPanel(QtGui.QWidget):
    def __init__(self, obj):
        super().__init__()
        self.obj = obj
        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(propertyPlacement('Placement', 0), 1, 0)
        self.layout.addWidget(propertyMaterial('Material', 0), 2, 0)
        self.layout.addWidget(propertyUnits(self.obj), 3, 0)
        self.buildPropertiesPanel()
        self.setLayout(self.layout)

    def countProperties(self):
        print('Count Properties')
        # print(dir(self.obj))
        print(self.obj.PropertiesList)
        return len(self.obj.PropertiesList)-len(self.ignoreProperties())

    def ignoreProperties(self):
        return ['ExpressionEngine', 'Label', 'Label2', 'Proxy', 'Shape',
                'Visibility', 'Placement', 'material', 'aunit', 'lunit']

    def buildPropertiesPanel(self):
        ignoreLst = self.ignoreProperties()
        fullLst = self.obj.PropertiesList
        self.propertyList = [x for x in fullLst if x not in ignoreLst]
        self.unitList = [x for x in fullLst if x in ['lunit', 'aunit']]
        self.propLayout = QtGui.QGridLayout()
        self.layout.addLayout(self.propLayout, 4, 0)
        for i, o in enumerate(self.propertyList):
            # print(o)
            # print(type(o))
            self.propLayout.addWidget(QtGui.QLabel(o), i, 0)
            self.propLayout.addWidget(propertyFloat(getattr(self.obj, o)), i, 1)
            # print(f'{o} : {type(getattr(self.obj, o))}')


class infoActionPanel(QtGui.QWidget):
    def __init__(self,  propLayout):
        super().__init__()
        print('infoActionPanel')
        self.propLayout = propLayout
        self.layout = QtGui.QVBoxLayout()
        okayButton = QtGui.QPushButton('Okay')
        okayButton.clicked.connect(self.onOkay)
        cancelButton = QtGui.QPushButton('Cancel')
        cancelButton.clicked.connect(self.onCancel)
        #
        buttonBox = QtGui.QDialogButtonBox()
        buttonBox.setFixedWidth(400)
        # buttonBox = Qt.QDialogButtonBox(QtCore.Qt.Vertical)
        buttonBox.addButton(okayButton, QtGui.QDialogButtonBox.ActionRole)
        buttonBox.addButton(cancelButton, QtGui.QDialogButtonBox.ActionRole)
        #
        self.layout.addWidget(buttonBox)

    def onOkay(self):
        # self.obj.setPropertyValues()
        print("setPropertyValues")
        print('Okay')
        # Process Placement
        # Process Material
        # Process Units
        units = self.propLayout.itemAt(3).widget()
        for i in range(units.unitsLayout.count()):
            u = units.unitsLayout.itemAt(i).widget()
            prop = u.layout.itemAt(0).widget().text()
            value = u.layout.itemAt(1).widget().currentText()
            print(prop)
            print(value)
            setattr(self.obj, prop, value)
        # Process properties
        for y in range(0, self.propLayout.count(), 2):
            prop = self.propLayout.itemAt(y).widget().text()
            value = float(self.propLayout.itemAt(y+1).widget().text())
            print(prop)
            print(value)
            setattr(self.obj, prop, value)
        super.setRetCode(1)
        self.close()

    def onCancel(self):
        print('Cancel')
        super.setRetCode(2)
        self.close()


class propertiesDialog(QtGui.QDialog):
    def __init__(self, obj, name, image, *args):
        super(propertiesDialog, self).__init__()
        self.obj = obj
        self.name = name
        self.image = image
        self.initUI()

    def initUI(self):
        print(f'Label : {self.obj.Label}')
        self.mainLayout = QtGui.QHBoxLayout()
        pp = propertiesPanel(self.obj)
        self.mainLayout.addWidget(pp)
        self.mainLayout.addWidget(infoActionPanel(pp.layout))
        label = QtGui.QLabel(self)
        pixmap = QtGui.QPixmap(self.image)
        label.setPixmap(pixmap)
        label.resize(pixmap.width(), pixmap.height())
        self.mainLayout.addWidget(label)
        self.setLayout(self.mainLayout)
        # define window         xLoc,yLoc,xDim,yDim
        self.setGeometry(650, 650, 300, 50)
        self.setWindowTitle(self.name+":  Set Properties")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)

        self.buttonBox.accepted.connect(self.OK) # type: ignore
        self.buttonBox.rejected.connect(self.cancel) # type: ignore

        self.retStatus = 2

    def OK(self):
        self.setRetCode(1)

    def cancel(self):
        self.setRetCode(2)

    def setRetCode(self, code):
        self.retStatus = code

