from PySide import QtGui, QtCore

class propertyFloat(QtGui.QLineEdit):
    def __init__(self, value):
        super().__init__()
        #self.insert(colhex)
        #self.setReadOnly(True)

class propertyPlacement(QtGui.QWidget):
    def __init__(self, name, value):
        super().__init__()
        self.hbox = QtGui.QHBoxLayout()
        self.hbox.addWidget(QtGui.QLabel(name))
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
        self.vbox = QtGui.QVBoxLayout()
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
        self.mainLayout = QtGui.QVBoxLayout()
        self.mainLayout.addWidget(buttonBox)
        self.setLayout(self.mainLayout)
        # define window         xLoc,yLoc,xDim,yDim
        print(self.countProperties())
        self.setGeometry(650, 650, 0, 50)
        self.setWindowTitle(self.name+":  Set Properties")
        self.buildPropertiesPanel()
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

    def ignoreProperties(self):
        return ['ExpressionEngine','Label','Label2','Proxy','Shape', \
                'Visibility','Placement','aunit','lunit']

    def enumProperties(self):
        #return ['aunit','lunit','material']
        return ['material']

    def countProperties(self):
        print('Count Properties')
        #print(dir(self.obj))
        print(self.obj.PropertiesList)
        return len(self.obj.PropertiesList)-len(self.ignoreProperties())

    def buildPropertiesPanel(self):
        self.propLayout = QtGui.QGridLayout()
        self.mainLayout.addLayout(self.propLayout)
        ignore = self.ignoreProperties()
        enums = self.enumProperties()
        self.propLayout.addWidget(propertyPlacement('Placement',0),0,0)
        self.propLayout.addWidget(propertyUnits(self.obj),0,1)
        for i, o in enumerate(self.obj.PropertiesList):
            if o not in ignore:
               print(o)
               if o in enums:
                  print('Enums')
               else: 
                  print(type(o))
                  self.propLayout.addWidget(propertyEntry(o, 10),i,0)
                  print(f'{o} : {type(getattr(self.obj, o))}')

    def onOkay(self):
        #self.obj.setPropertyValues()
        print("setPropertyValues")
        print('Okay')

    def onCancel(self):
        print('Cancel')
        print('Delete Object & LV ???')
        self.close()
