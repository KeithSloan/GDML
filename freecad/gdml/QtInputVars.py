# ***************************************************************************
# *																			*
# *   Copyright (c) 2024 Keith Sloan <ipad2@sloan-home.co.uk>				*
# *																			*
# *   This program is free software; you can redistribute it and/or modify	*
# *   it under the terms of the GNU Lesser General Public License (LGPL)	*
# *   as published by the Free Software Foundation; either version 2 of		*
# *   the License, or (at your option) any later version.					*
# *   for detail see the LICENCE text file.									*
# *																			*
# *   This program is distributed in the hope that it will be useful,		*
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of		*
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the			*
# *   GNU Library General Public License for more details					*
# *																			*
# *   You should have received a copy of the GNU Library General Public		*
# *   License along with this program; if not, write to the Free Software 	*
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307	*
# *   USA																	*
# *																			*
# *   Acknowledgements :													*     
#     Prompt for any undefined variables									*				
# 																			*
#		Create Dialog fo any undefiend varibles								*
#																			*
#			Passed a dictionary {'varName' : 'varType'}						*
#				valid types are 'int','float', 'decimal', 'bool', str		*
#																			*
# ***************************************************************************

#from PyQt5.QtWidgets import (
from PySide.QtWidgets import (
    QApplication, QDialog, QLabel, QLineEdit, QVBoxLayout, QDialogButtonBox,
    QScrollArea, QWidget, QCheckBox, QMessageBox, QHBoxLayout, QSizePolicy
)
#from PyQt5.QtCore import Qt
from PySide.QtCore import Qt

from decimal import Decimal
import sys


class VariableInputDialog(QDialog):
    def __init__(self, variable_types, existing_vars=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Provide Missing Variables")
        self.variable_types = variable_types
        self.variables = {}
        self.inputs = {}
        self.existing_vars = existing_vars or {}

        self.resize(500, 400)
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout(self)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        for name, vtype in self.variable_types.items():
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(5, 5, 5, 5)

            label = QLabel(name)
            label.setMinimumWidth(150)
            row_layout.addWidget(label)

            if vtype == 'bool':
                input_widget = QCheckBox()
                if name in self.existing_vars:
                    input_widget.setChecked(bool(self.existing_vars[name]))
            else:
                input_widget = QLineEdit()
                input_widget.setPlaceholderText(vtype)
                if name in self.existing_vars:
                    input_widget.setText(str(self.existing_vars[name]))

            row_layout.addWidget(input_widget)
            self.inputs[name] = input_widget
            scroll_layout.addWidget(row)

        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def validate_and_accept(self):
        for name, vtype in self.variable_types.items():
            widget = self.inputs[name]
            try:
                if vtype == 'int':
                    value = int(widget.text())
                elif vtype == 'float':
                    value = float(widget.text())
                elif vtype == 'decimal':
                    value = Decimal(widget.text())
                elif vtype == 'bool':
                    value = widget.isChecked()
                else:
                    raise ValueError(f"Unsupported type: {vtype}")
            except Exception as e:
                QMessageBox.warning(self, "Input Error", f"Invalid input for '{name}': {str(e)}")
                return
            self.variables[name] = value

        self.accept()


def checkVariablesSet(var_types: dict, scope_vars):
    missing_vars = {}
    present_vars = {}
    
    #scope_vars = dict(globals(), **locals()
    print(f"scope vars {scope_vars}")
    
    for name, vtype in var_types.items():
        print(f"name {name} vtype {vtype}")
        if name in scope_vars:
            present_vars[name] = vtype
        else:
            missing_vars[name] = vtype

    # All variables present
    print(f"missing {missing_vars}")
    if not missing_vars:
        return True

    # Prompt user for missing ones
    app = QApplication.instance() or QApplication(sys.argv)
    dialog = VariableInputDialog(missing_vars, existing_vars=present_vars)
    if dialog.exec_() == QDialog.Accepted:
        result = present_vars.copy()
        result.update(dialog.variables)
        return True
    else:
        raise RuntimeError("User cancelled variable input.")


