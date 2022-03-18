from PySide import QtGui, QtCore

class propertiesDialog(QtGui.QDialog):
    def __init__(self, obj, *args):
        super(propertiesDialog, self).__init__()
        self.obj = obj
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
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)
        # define window         xLoc,yLoc,xDim,yDim
        print(self.countProperties())
        self.setGeometry(650, 650, 0, 50)
        self.setWindowTitle("Choose an Option    ")
        self.buildPropertiesPanel()
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

    def ignoreProperties(self):
        return ['ExpressionEngine','Label','Label2','Proxy','Shape','Visibility']

    def enumProperties(self):
        return ['aunit','lunit','material']

    def countProperties(self):
        print('Count Properties')
        #print(dir(self.obj))
        print(self.obj.PropertiesList)
        return len(self.obj.PropertiesList)-len(self.ignoreProperties())

    def buildPropertiesPanel(self):
        ignore = self.ignoreProperties()
        enums = self.enumProperties()
        for o in self.obj.PropertiesList:
            if o not in ignore:
               print(o)
               if o in enums:
                  print('Enums')
               else: 
                  print(type(o))
                  print(f'{o} : {type(getattr(self.obj, o))}')

    def onOkay(self):
        #self.obj.setPropertyValues()
        print("setPropertyValues")
        print('Okay')

    def onCancel(self):
        print('Cancel')
        print('Delete Object & LV ???')
        self.close()
