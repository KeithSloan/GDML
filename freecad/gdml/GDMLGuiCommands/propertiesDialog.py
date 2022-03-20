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
        self.vbox = QtGui.QHBoxLayout()
        self.vbox.addWidget(QtGui.QLabel('aunits'))
        self.units = QtGui.QComboBox()
        self.units.addItems(["deg","rad"])
        self.vbox.addWidget(self.units)
        self.setLayout(self.vbox)

class property_lunits(QtGui.QWidget):
    def __init__(self):
        super().__init__()
        self.vbox = QtGui.QHBoxLayout()
        self.vbox.addWidget(QtGui.QLabel('lunits'))
        self.units = QtGui.QComboBox()
        self.units.addItems(["mm","cm","m","um","nm"])
        self.vbox.addWidget(self.units)
        self.setLayout(self.vbox)

class propertyUnits(QtGui.QWidget):
    def __init__(self, obj):
        super().__init__()
        self.vbox = QtGui.QHBoxLayout()
        if 'lunit' in obj.PropertiesList:
           self.vbox.addWidget(property_lunits())
        if 'aunit' in obj.PropertiesList:
           self.vbox.addWidget(property_aunits())
        self.setLayout(self.vbox)

class propertyEntry(QtGui.QWidget):

    def __init__(self, name, value):
        super().__init__()
        self.hbox = QtGui.QHBoxLayout()
        self.hbox.addWidget(QtGui.QLabel(name))
        self.hbox.addWidget(propertyFloat(value))
        self.setLayout(self.hbox)

class propertiesDialog(QtGui.QDialog):
    def __init__(self, obj, name, image, *args):
        super(propertiesDialog, self).__init__()
        self.obj = obj
        self.name = name
        self.image = image
        self.initUI()

    def initUI(self):
        print(f'Label : {self.obj.Label}')
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
        self.mainLayout = QtGui.QGridLayout()
        self.mainLayout.addWidget(buttonBox,0,0)
        self.setLayout(self.mainLayout)
        # define window         xLoc,yLoc,xDim,yDim
        print(self.countProperties())
        self.setGeometry(650, 650, 0, 50)
        self.setWindowTitle(self.name+":  Set Properties")
        self.mainLayout.addWidget(propertyPlacement('Placement',0),1,0)
        self.mainLayout.addWidget(propertyMaterial('Material',0),2,0)
        self.mainLayout.addWidget(propertyUnits(self.obj),3,0)
        self.buildPropertiesPanel()
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

    def ignoreProperties(self):
        return ['ExpressionEngine','Label','Label2','Proxy','Shape', \
                'Visibility','Placement','material','aunit','lunit']

    def countProperties(self):
        print('Count Properties')
        #print(dir(self.obj))
        print(self.obj.PropertiesList)
        return len(self.obj.PropertiesList)-len(self.ignoreProperties())

    def buildPropertiesPanel(self):
        ignoreLst = self.ignoreProperties()
        fullLst = self.obj.PropertiesList
        self.propertyList = [x for x in fullLst if x not in ignoreLst]
        self.propLayout = QtGui.QGridLayout()
        self.mainLayout.addLayout(self.propLayout,4,0)
        for i, o in enumerate(self.propertyList):
            print(o)
            print(type(o))
            self.propLayout.addWidget(QtGui.QLabel(o),i,0)
            self.propLayout.addWidget(propertyFloat(10),i,1)
            print(f'{o} : {type(getattr(self.obj, o))}')

    def onOkay(self):
        #self.obj.setPropertyValues()
        print("setPropertyValues")
        print('Okay')
        # Process Placement
        # Process Material
        # Process Units
        # Process properties
        for y in range(0, self.propLayout.count(), 2):
            prop = self.propLayout.itemAt(y)
            value = self.propLayout.itemAt(y+1)
            print(prop.widget().text())
            print(value.widget().text())
            setattr(self.obj,prop.widget().text(), \
                    float(value.widget().text()))
        self.close()

    def onCancel(self):
        print('Cancel')
        print('Delete Object & LV ???')
        self.close()
