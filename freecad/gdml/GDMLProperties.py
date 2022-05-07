import FreeCAD

from PySide import QtGui, QtCore

from .GDMLMaterials import GDMLMaterials, GDMLMaterialWidget

class propertyFloat(QtGui.QLineEdit):
    def __init__(self, value):
        super().__init__()
        self.insert(str(value))

class propertyPlacement(QtGui.QWidget):
    def __init__(self, x, y, z):
        super().__init__()
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        self.group = QtGui.QGroupBox("Placement")
        self.layout.addWidget(self.group)
        self.vbox = QtGui.QVBoxLayout()
        self.group.setLayout(self.vbox)
        self.vbox.addWidget(propertyEntry('x', x))
        self.vbox.addWidget(propertyEntry('y', y))
        self.vbox.addWidget(propertyEntry('z', z))

class propertyMaterial(QtGui.QWidget):
    def __init__(self, widget):
        super().__init__()
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        self.group = QtGui.QGroupBox("Material")
        self.layout.addWidget(self.group)
        self.vboxLayout = QtGui.QHBoxLayout()
        self.group.setLayout(self.vboxLayout)
        self.vboxLayout.addWidget(widget)

class property_aunits(QtGui.QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QtGui.QHBoxLayout()
        self.layout.addWidget(QtGui.QLabel('aunit'))
        self.units = QtGui.QComboBox()
        self.units.addItems(["deg","rad"])
        self.layout.addWidget(self.units)
        self.setLayout(self.layout)

class property_lunits(QtGui.QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QtGui.QHBoxLayout()
        self.layout.addWidget(QtGui.QLabel('lunit'))
        self.units = QtGui.QComboBox()
        self.units.addItems(["mm","cm","m","um","nm"])
        self.layout.addWidget(self.units)
        self.setLayout(self.layout)

class propertyUnits(QtGui.QWidget):
    def __init__(self, obj):
        super().__init__()
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        self.group = QtGui.QGroupBox("Units")
        self.layout.addWidget(self.group)
        self.unitsLayout = QtGui.QHBoxLayout()
        self.group.setLayout(self.unitsLayout)
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

class solidInfo(QtGui.QWidget):
    def __init__(self, image):
        super().__init__()
        print('solidInfo : '+image)
        self.label = QtGui.QLabel(self)
        self.pixmap = QtGui.QPixmap('./Resources/solidsInfo/'+image)
        self.label.setPixmap(self.pixmap)
        self.resize(self.pixmap.width(), self.pixmap.height())
        self.show()
 

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
        self.mainLayout.addWidget(propertyPlacement(0, 0, 0),1,0)
        self.mainLayout.addWidget(propertyMaterial(GDMLMaterialWidget(GDMLMaterials)),2,0)
        #self.mainLayout.addWidget(propertyUnits(self.obj),3,0)
        #self.mainLayout.addWidget(solidInfo(self.image),3,1)
        self.mainLayout.addWidget(solidInfo(self.image),3,0)
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
        self.unitList = [x for x in fullLst if x in ['lunit','aunit']]
        self.layout = QtGui.QGridLayout()
        self.mainLayout.addLayout(self.layout,4,0)
        self.group = QtGui.QGroupBox("Properties")
        self.layout.addWidget(self.group)
        #self.propLayout = QtGui.QHBoxLayout()
        self.propLayout = QtGui.QGridLayout()
        self.group.setLayout(self.propLayout)
        for i, o in enumerate(self.propertyList):
            #print(o)
            #print(type(o))
            self.propLayout.addWidget(QtGui.QLabel(o),i,0)
            self.propLayout.addWidget(propertyFloat(getattr(self.obj,o)),i,1)
            #print(f'{o} : {type(getattr(self.obj, o))}')

    def onOkay(self):
        #self.obj.setPropertyValues()
        print("setPropertyValues")
        print('Okay')
        # Process Placement
        # Process Material
        #material = self.mainLayout.itemAt(2).widget()
        #print(material.mainLayout.itemAt(1).widget().text())
        #setattr(self.obj, material, value)
        # Process Units
        units = self.mainLayout.itemAt(3).widget()
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
        self.retStatus = 1
        self.close()

    def onCancel(self):
        print('Cancel')
        lvObj = self.obj.InList[0]
        print(lvObj.Label)
        doc = FreeCAD.ActiveDocument
        doc.removeObject(lvObj.Label)
        doc.removeObject(self.obj.Label)
        self.retStatus = 2
        self.close()
