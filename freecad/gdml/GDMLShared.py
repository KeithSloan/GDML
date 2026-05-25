# Shared file
# single access to globals
# anything requiring access to globals needs to call a function in this file
# anything needing to call eval needs to be in this file
# **************************************************************************
# *                                                                        *
# *   Copyright (c) 2017 Keith Sloan <keith@sloan-home.co.uk>              *
# *             (c) Dam Lambert 2020                                       *
# *                                                                        *
# *   This program is free software; you can redistribute it and/or modify *
# *   it under the terms of the GNU Lesser General Public License (LGPL)   *
# *   as published by the Free Software Foundation; either version 2 of    *
# *   the License, or (at your option) any later version.                  *
# *   for detail see the LICENCE text file.                                *
# *                                                                        *
# *   This program is distributed in the hope that it will be useful,      *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of       *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the        *
# *   GNU Library General Public License for more details.                 *
# *                                                                        *
# *   You should have received a copy of the GNU Library General Public    *
# *   License along with this program; if not, write to the Free Software  *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 *
# *   USA                                                                  *
# *                                                                        *
# *   Acknowledgements :                                                   *
# *                                                                        *
# *                                                                        *
# **************************************************************************
from math import *
import FreeCAD, Part
from PySide import QtCore, QtGui

# from lxml import etree as ET

global define
global tracefp

global printverbose
printverbose = False


definesColumn = {
    "type" : 'A',  # type of item (constant, variab;e, quantity, etc
    "name": 'B',  # name of item
    "value": 'C',  # value=
    "quantity_type": 'C',
    "quantity_value": 'D',
    "quantity_unit": 'E',

    "pos_x": 'C',
    "pos_y": 'D',
    "pos_z": 'E',
    "pos_unit": 'F',

    "rot_x": 'C',
    "rot_y": 'D',
    "rot_z": 'E',
    "rot_unit": 'F'
}

gdmlSheetColumn = {'identifier': 'A', 'physvol_name': 'B',
                   'position_type': 'C', 'position_name': 'D', 'pos_x': 'E', 'pos_y': 'F', 'pos_z': 'G', 'pos_unit': 'H',
                   'rotation_type': 'I', 'rotation_name': 'J', 'rot_x': 'K', 'rot_y': 'L', 'rot_z': 'M', 'rot_unit': 'N'
                   }


def setTrace(flag):
    global tracefp
    print("Trace set to : " + str(flag))
    global printverbose
    printverbose = flag
    if flag is True:
        tracePath = FreeCAD.getUserAppDataDir()
        tracefp = open(tracePath + "FC-trace", "w")
        print("Trace path : " + tracePath)


def getTrace():
    global printverbose
    # print('Get Trace : '+str(printverbose))
    return printverbose


def trace(s):
    global tracefp
    if printverbose is True:
        print(s)
        print(s, file=tracefp)
        tracefp.flush()
    return


def errorDialog(msg, title="Warning", type=2):
    # Create a simple dialog QMessageBox
    # type indicates the icon used: one of QtGui.QMessageBox.{NoIcon, Information, Warning, Critical, Question}
    typeDict = {
        0: QtGui.QMessageBox.NoIcon,
        1: QtGui.QMessageBox.Information,
        2: QtGui.QMessageBox.Warning,
        3: QtGui.QMessageBox.Critical,
        4: QtGui.QMessageBox.Question,
    }
    diag = QtGui.QMessageBox(Dict(type), title, msg)
    diag.setWindowModality(QtCore.Qt.ApplicationModal)
    diag.exec_()


def getFloatVal(expr):
    try:
        ret = float(eval(expr))
    except:
        # eval might fail on constants with leading zeros in python3
        # so we try direct conversion
        try:
            ret = float(expr)
        except:
            ret = 0.0
            print("Illegal float value: {}".format(expr))
    return ret


def setDefine(val):
    # print("Set Define")
    global define
    define = val


global defineSpreadsheet
global gdmlSpreadsheet
defineSpreadsheet = None
gdmlSpreadsheet = None

def processDefines(doc):
    global defineSpreadsheet
    global gdmlSpreadsheet
    defineGrp = doc.getObject("Define")
    if defineGrp is None:
        defineGrp = doc.addObject("App::DocumentObjectGroupPython", "Define")
        defineSpreadsheet = defineGrp.newObject("Spreadsheet::Sheet", "defines")
        gdmlSpreadsheet = defineGrp.newObject("Spreadsheet::Sheet", "gdmlInfo")

    processConstants(doc)
    processQuantities(doc)
    processVariables(doc)
    processExpression(doc)
    processPositions(doc)
    processRotation(doc)
    defineSpreadsheet.recompute()

    # SheetHandler.saveInitialSheet()


def lastRow(sheet):
    usedRange = sheet.getNonEmptyRange()
    lastCell: str = usedRange[1]
    if lastCell == '@0':
        return 0
    else:
        if lastCell[1].isdigit():
            row = int(lastCell[1:])
        else:
            row = int(lastCell[2:])
        return row

def processConstants(doc):
    global defineSpreadsheet
    # all of math must be imported at global level
    # setTrace(True)
    col = 0
    row = lastRow(defineSpreadsheet)
    trace("Process Constants")
    constantGrp = doc.getObject("Constants")
    if constantGrp is None:
        constantGrp = doc.addObject(
            "App::DocumentObjectGroupPython", "Constants"
        )
    from .GDMLObjects import GDMLconstant

    for cdefine in define.findall("constant"):
        # print cdefine.attrib
        name = str(cdefine.attrib.get("name"))
        print(f"name :  + {name}")
        value = cdefine.attrib.get("value")
        print(f"value : {value}")
        cell = definesColumn['type'] + str(row+1)
        defineSpreadsheet.set(cell, 'constant')
        cell = definesColumn['name'] + str(row+1)  # variable name
        defineSpreadsheet.set(cell, name)
        cell = definesColumn['value'] + str(row+1)
        SheetHandler.set(cell, value)
        SheetHandler.setAlias(cell, name)  #  give the value an alias
        row += 1
        trace("value : " + value)
        # constDict[name] = value
        # trace(name)
        # print(dir(name))
        try:
            globals()[name] = eval(value)
        except:  # eg 5*cm
            globals()[name] = value
        constObj = constantGrp.newObject(
            "App::DocumentObjectGroupPython", name
        )
        GDMLconstant(constObj, name, value)

    # print("Globals")
    # print(str(globals()))


def processVariables(doc):
    global defineSpreadsheet
    # all of math must be imported at global level
    trace("Process Variables")
    variablesGrp = doc.getObject("Variables")
    if variablesGrp is None:
        variablesGrp = doc.addObject(
            "App::DocumentObjectGroupPython", "Variables"
        )
    from .GDMLObjects import GDMLconstant
    from .GDMLObjects import GDMLvariable
    col = 0
    row = lastRow(defineSpreadsheet)

    globals()["false"] = False
    globals()["true"] = True

    for cdefine in define.findall("variable"):
        # print cdefine.attrib
        name = str(cdefine.attrib.get("name"))
        trace("name : " + name)
        value = cdefine.attrib.get("value")
        trace("value : " + value)
        cell = definesColumn['type'] + str(row+1)
        defineSpreadsheet.set(cell, 'variable')
        cell = definesColumn['name'] + str(row+1)
        defineSpreadsheet.set(cell, name)
        cell = definesColumn['value'] + str(row+1)
        SheetHandler.set(cell, value)
        SheetHandler.setAlias(cell, name)
        row += 1

        # constDict[name] = value
        trace(name)
        # print(dir(name))
        # print('Name  : '+name)
        try:
            globals()[name] = eval(value)
            # print('Value : '+value)
        except:
            globals()[name] = value
            # print('Value String : '+value)
        variableObj = variablesGrp.newObject(
            "App::DocumentObjectGroupPython", name
        )
        GDMLvariable(variableObj, name, value)
    # print("Globals")
    # print(str(globals()))


def processQuantities(doc):
    global defineSpreadsheet

    # all of math must be imported at global level
    trace("Process Quantitities")
    quantityGrp = doc.getObject("Quantities")
    if quantityGrp is None:
        quantityGrp = doc.addObject(
            "App::DocumentObjectGroupPython", "Quantities"
        )
    from .GDMLObjects import GDMLquantity

    col = 0
    row = lastRow(defineSpreadsheet)
    for cdefine in define.findall("quantity"):
        # print cdefine.attrib
        name = str(cdefine.attrib.get("name"))
        trace("name : " + name)
        type = cdefine.attrib.get("type")
        trace("type : " + type)
        unit = cdefine.attrib.get("unit")
        trace("unit : " + unit)
        value = cdefine.attrib.get("value")
        trace("value : " + value)
        # constDict[name] = value
        trace(name)
        cell = definesColumn['type'] + str(row+1)
        defineSpreadsheet.set(cell, 'quantity')

        cell = definesColumn['name'] + str(row+1)
        defineSpreadsheet.set(cell, name)

        cell = definesColumn['quantity_type'] + str(row+1)
        # SheetHandler.set(cell, type)   # this is only for floats or expressions. type is a string
        defineSpreadsheet.set(cell, type)
        SheetHandler.setAlias(cell, name)

        cell = definesColumn['quantity_value'] + str(row+1)
        SheetHandler.set(cell, value)
        SheetHandler.setAlias(cell, name)

        # set unit column
        cell = definesColumn['quantity_unit'] + str(row+1)
        defineSpreadsheet.set(cell, unit)
        SheetHandler.setAlias(cell, name+"_unit")

        row += 1

        # print(dir(name))
        # print('Name  : '+name)
        try:
            globals()[name] = eval(value)
            # print('Value : '+value)
        except:
            globals()[name] = value
            # print('Value String : '+value)
        quantityObj = quantityGrp.newObject(
            "App::DocumentObjectGroupPython", name
        )
        GDMLquantity(quantityObj, name, type, unit, value)
    # print("Globals")
    # print(str(globals()))


def processPositions(doc):
    global defineSpreadsheet
    print("Process Positions")
    # need to be done ?
    global positions
    positions = {}
    row = lastRow(defineSpreadsheet)
    for elem in define.findall("position"):
        atts = elem.attrib
        if "unit" in atts:
            unit = atts["unit"]
        else:
            unit = "mm"
        if "x" in atts:
            x = getFloatVal(atts["x"])
        else:
            x = 0
        if "y" in atts:
            y = getFloatVal(atts["y"])
        else:
            y = 0
        if "z" in atts:
            z = getFloatVal(atts["z"])
        else:
            z = 0

        positions[atts["name"]] = {"unit": unit, "x": x, "y": y, "z": z}

        name = str(elem.attrib.get("name"))
        trace("name : " + name)

        # Add position info to the define
        cell = definesColumn['type'] + str(row+1)
        defineSpreadsheet.set(cell, 'position')
        cell = definesColumn['name'] + str(row+1)
        defineSpreadsheet.set(cell, name)

        for prop in ["x", "y", "z", "unit"]:
            cell = definesColumn['pos_' + prop] + str(row+1)
            if prop in atts:
                value = atts[prop]
                if prop == "unit":  # a little kludge because a unit is not an expression nor a float
                    defineSpreadsheet.set(cell, value)
                else:
                    SheetHandler.set(cell, value)
                SheetHandler.setAlias(cell, name+"_"+prop)

        row += 1



    trace("Positions processed")


def processExpression(doc):
    # need to be done ?
    trace("Expressions Not processed & Displayed")


def processRotation(doc):
    global defineSpreadsheet
    print("Process Rotations")
    # need to be done ?
    row = lastRow(defineSpreadsheet)
    for elem in define.findall("rotation"):
        atts = elem.attrib
        if "x" in atts:
            x = getFloatVal(atts["x"])
        else:
            x = 0
        if "y" in atts:
            y = getFloatVal(atts["y"])
        else:
            y = 0
        if "z" in atts:
            z = getFloatVal(atts["z"])
        else:
            z = 0

        name = str(elem.attrib.get("name"))
        trace("name : " + name)

        cell = definesColumn['type'] + str(row+1)
        defineSpreadsheet.set(cell, 'rotation')
        cell = definesColumn['name'] + str(row+1)
        defineSpreadsheet.set(cell, name)

        for prop in ["x", "y", "z", "unit"]:
            cell = definesColumn['rot_'+prop] + str(row+1)
            if prop in atts:
                value = atts[prop]
                if prop == "unit":
                    defineSpreadsheet.set(cell, value)  # a pure string
                else:
                    SheetHandler.set(cell, value)  # possibly an expression
                SheetHandler.setAlias(cell, name+"_"+prop)
        row += 1

    trace("Rotations processed")


import re

class SheetHandler:
    replacements: dict[str, str] = {}
    originals: dict[str, str] = {}
    aliasDict: dict[str,str] = {}

    initialSheet: dict[str, str] = {}

    function_names = ['pow',
                      'sqrt',
                      'sin',
                      'cos',
                      'tan',
                      'asin',
                      'acos',
                      'atan',
                      'atan2'
                      'sinh',
                      'cosh',
                      'tanh',
                      'exp',
                      'log',
                      'log10',
                      'abs',
                      'min',
                      'max']

    trig_funcs = ['sin',
                  'cos',
                  'tan']

    invtrig_funcs = ['asin',
                     'acos',
                     'atan',
                     'atan2']

    trig_pattern = None
    invtrig_pattern = None
    variable_pattern = None


    @staticmethod
    def getSheetDict() -> dict[str, str]:
        sheetDict = {}
        endRow = lastRow(defineSpreadsheet)
        for row in range(1,endRow+1):
            varType = defineSpreadsheet.get(definesColumn['type'] + str(row))
            varName = defineSpreadsheet.get(definesColumn['name'] + str(row))
            if varType == 'position' or varType == 'rotation':
                value = ''
                for column in [definesColumn['pos_x'], definesColumn['pos_y'], definesColumn['pos_z'], definesColumn['pos_unit']]:
                    try :
                        value += defineSpreadsheet.getContents(column + str(row))
                    except:
                        pass


            elif varType == "quantity":
                value = defineSpreadsheet.getContents(definesColumn['quantity_type'] + str(row))   # type
                value += defineSpreadsheet.getContents(definesColumn['quantity_value'] + str(row))  # value
                value += defineSpreadsheet.getContents(definesColumn['quantity_unit'] + str(row))  # unit

            else:
                value = defineSpreadsheet.getContents(definesColumn['value'] + str(row))
            sheetDict[varName] = value

        return sheetDict

    @staticmethod
    def init_reg_exprs():
        pat = r'\b(sin)|(cos)|(tan)\b'
        SheetHandler.trig_pattern = re.compile(pat)

        pat = r'\b(asin)|(acos)|(atan)|(atan2)\b'
        SheetHandler.invtrig_pattern = re.compile(pat)

        # Regular expression to match variable names (sequences of letters and underscores)
        # \b asserts a word boundary, so we don't match parts of words
        # Join function names into a regex pattern
        function_pattern = r'\b(?:' + '|'.join(map(re.escape, SheetHandler.function_names)) + r')\b'

        # Pattern to match variables (words that are not functions)
        SheetHandler.variable_pattern = r'\b(?!' + function_pattern + r')\b[a-zA-Z_][a-zA-Z0-9_]*\b'
        # pattern = r'\b[a-zA-Z_]\w*\b'

    @staticmethod
    def hasTrig(expr):
        if SheetHandler.trig_pattern is None:
            SheetHandler.init_reg_exprs()

        return re.search(SheetHandler.trig_pattern, expr)

    @staticmethod
    def hasInvTrig(expr):
        if SheetHandler.invtrig_pattern is None:
            SheetHandler.init_reg_exprs()

        return re.search(SheetHandler.invtrig_pattern, expr)

    @staticmethod
    def setAlias(cell, name: str) -> str:
        global defineSpreadsheet
        pattern = r'[^A-Za-z0-9_]'   # allowed chars are [A-Za-z0-9_]
        m = re.findall(pattern, name)  # find charcaters NOT in allowed characters
        s = str(name)
        if len(m) > 0:
            for c in m:
                s = s.replace(c, '_')
        try:
            defineSpreadsheet.setAlias(cell, s)
        except Exception as e:
            s = s + '__'
            defineSpreadsheet.setAlias(cell, s)
        if s != name:
            SheetHandler.replacements[name] = s
            SheetHandler.originals[s] = name
        SheetHandler.aliasDict[name] = s

    @staticmethod
    def set(cell, value):
        global defineSpreadsheet
        try:
            val = float(value)
            defineSpreadsheet.set(cell, str(val))
        except Exception as e:
            value = adjust_floats(value)
            value = SheetHandler.replace_illegal_aliases(value)
            print(f"after replacing illegals: {value}")
            if SheetHandler.hasInvTrig(value):
                print("has invtrig")
                value = SheetHandler.gdml_invtrig_to_FC(value)
            if SheetHandler.hasTrig(value):
                print("has trig")
                value = SheetHandler.gdml_trig_to_FC(value)
            print(f" after dealing with trig function: {value}")
            defineSpreadsheet.set(cell, '='+value)

    @staticmethod
    def alias(name) -> str:
        return SheetHandler.aliasDict[name]


    @staticmethod
    def replace_illegal_aliases(expr: str) -> str:
        variables = extract_variables(expr)
        for var in variables:
            if var in SheetHandler.replacements:
                expr = re.sub(r'\b' + var + r'\b', SheetHandler.replacements[var], expr)
        return expr

    @staticmethod
    def find_matching_parenthesis(expr):
        stack = []
        matches = []

        # Traverse the expression
        for i, char in enumerate(expr):
            if char == '(':
                # Push index of the opening parenthesis onto the stack
                stack.append(i)
            elif char == ')':
                if stack:
                    # Pop the most recent unmatched opening parenthesis
                    opening_index = stack.pop()
                    # Store the matching pair (opening, closing)
                    matches.append((opening_index, i))

        if len(stack) > 0:
            print(f"unmatched parentheses in: {expr}")

        return matches


    @staticmethod
    def gdml_trig_to_FC(expr):
        matching_paren = SheetHandler.find_matching_parenthesis(expr)
        if len(matching_paren) == 0:
            return expr

        # Check if any of the trig functions are in the expression
        # breakpoint()
        trig_parenthesis = []
        for func in SheetHandler.trig_funcs:
            pattern = r'\b' + func + r'\b'
            matches = re.finditer(pattern, expr)
            for match in matches:
                # print(f"Match: {match.group()} at index {match.start()}-{match.end()}")
                # find which parentheses pair matches the enclosing arguments of the trig function
                for paren_pair in matching_paren:
                    if paren_pair[0] == match.end():
                        trig_parenthesis.append(paren_pair)

        paren_dict = {}
        # sort the parenthesis in the order of their indexes
        for paren in trig_parenthesis:
            paren_dict[paren[0]] = '('
            paren_dict[paren[1]] = ')'

        sorted_dict = dict(sorted(paren_dict.items()))

        out_expr = []
        src_pos = 0
        for index in sorted_dict:
            out_expr += expr[src_pos:index+1]
            if sorted_dict[index] == '(':
                out_expr += '180/pi*('
            else:
                out_expr += ')'
            src_pos = index+1
        out_expr += expr[src_pos:]   # copy remaining part of expression

        return ''.join(out_expr)

    @staticmethod
    def FC_expression_to_gdml(expr):
        expr = expr.replace(' ', '')
        if SheetHandler.hasInvTrig(expr):
            print("has invtrig")
            expr = SheetHandler.FC_invtrig_to_gdml(expr)
        if SheetHandler.hasTrig(expr):
            print("has trig")
            expr = SheetHandler.FC_trig_to_gdml(expr)

        expr = SheetHandler.replaceAliases(expr)

        return expr

    @staticmethod
    def replaceAliases(expr) -> str:
        sheet = FreeCAD.ActiveDocument.getObject("defines")
        if sheet is None:  # an old doc, with no definesSpreadSheet
            return expr

        variables = extract_variables(expr)
        for var in variables:
            # the var in the expression is the alias of the cell
            cell = sheet.getCellFromAlias(var)
            if cell is None:
                continue
            row = cell[1:]
            nameCell = definesColumn['name'] + row
            name = sheet.get(nameCell)
            expr = expr.replace(var, name)

        return expr

    @staticmethod
    def FC_trig_to_gdml(expr):
        expr = expr.replace(' ', '')  # remove spaces that FreeCAD adds to expressions
        matching_paren = SheetHandler.find_matching_parenthesis(expr)
        if len(matching_paren) == 0:
            return expr

        # Check if any of the trig functions are in the expression
        # breakpoint()
        trig_parenthesis = []
        for func in SheetHandler.trig_funcs:
            pattern = r'\b' + func + r'\b'
            matches = re.finditer(pattern, expr)
            for match in matches:
                # print(f"Match: {match.group()} at index {match.start()}-{match.end()}")
                # find which parentheses pair matches the enclosing arguments of the trig function
                for paren_pair in matching_paren:
                    if paren_pair[0] == match.end():
                        trig_parenthesis.append(paren_pair)

        out_expr = list(expr)
        replacement0 = '180/pi*'  # FreeCAD has a habit of removing unneeded parenthesis, so it may have removed the '('
        replacement1 = ')'
        n = len(replacement0)
        for paren_pair in trig_parenthesis:
            istart = paren_pair[0]
            iend = paren_pair[1]
            out_expr[istart+1 : istart+1+n] = ' ' * n  # replace the '180/pi*' with spaces

        out_expr = "".join(out_expr)  # back to string
        out_expr = out_expr.replace(' ', '')  # remove the spaces we put in

        return out_expr

    @staticmethod
    def gdml_invtrig_to_FC(expr):
        for func in SheetHandler.invtrig_funcs:
            pattern = r'\b' + func + r'\b'
            if re.search(pattern, expr):
                expr = re.sub(pattern, '1/deg*pi/180*'+func, expr)

        return expr

    @staticmethod
    def FC_invtrig_to_gdml(expr):
        expr = expr.replace(' ', '')  # remove spaces that FreeCAD adds to expressions
        # breakpoint()
        for func in SheetHandler.invtrig_funcs:
            pattern = r'\b' + '1/deg[*]pi/180[*]'+func + r'\b'
            if re.search(pattern, expr):
                expr = re.sub(pattern, func, expr)

        return expr


def getPositionRow(name) -> int| None:
    endRow = lastRow(defineSpreadsheet)
    for row in range(endRow):
        cell = chr(ord("A")) + str(row+1)
        if defineSpreadsheet.get(str(cell)) == 'position':
            posName = defineSpreadsheet.get('B' + str(row+1))
            if posName == name:  # found the row with that position name
                return row+1

    return None


def getRotationRow(name) -> int| None:
    endRow = lastRow(defineSpreadsheet)
    for row in range(endRow):
        cell = chr(ord("A")) + str(row+1)
        if defineSpreadsheet.get(str(cell)) == 'rotation':
            rotName = defineSpreadsheet.get('B' + str(row+1))
            if rotName == name:  # found the row with that position name
                return row+1

    return None


def extract_variables(expression):
    if SheetHandler.variable_pattern is None:
        SheetHandler.init_reg_exprs()

    # Find all matches in the expression
    variables = re.findall(SheetHandler.variable_pattern, expression)

    # Return unique variables (set removes duplicates) while preserving order
    return sorted(set(variables), key=variables.index)


def adjust_floats(expression) -> str:
    # change floats of the form d[dd..]. to d.0
    pattern = r'\b\d+[.]\w*'

    # Find all matches in the expression
    floats = re.findall(pattern, expression)
    floats = sorted(set(floats), key=floats.index)

    for f in floats:
        expression = expression.replace(f, f+"0")

    return expression

def getSheetExpression(ptr, var) -> str | None:
    # all of math must be imported at global level
    # print ptr.attrib
    # is the variable defined in passed attribute
    sheet = defineSpreadsheet.Label
    if var in ptr.attrib:
        # if yes get its value
        vval = ptr.attrib.get(var)
        trace(var + " : " + str(vval))
        if vval[0] == "&":  # Is this referring to an HTML entity constant
            chkval = vval[1:]
        else:
            chkval = vval
        trace("chkval : " + str(chkval))

        variables = extract_variables(chkval)
        if len(variables) == 0:
            return None

        for var in variables:
            varAlias = SheetHandler.alias(var)
            if defineSpreadsheet.getCellFromAlias(varAlias) is None:
                return None
            else:
                repl = f"<<{sheet}>>.{varAlias}"
                chkval = chkval.replace(var, repl)
        return chkval

    return None


def getPropertyValue(obj, property: str) -> float | None:
    '''' Get the VALUE of a property of the form 'A.B.C'
    e.g., Placement.Base.x
    '''
    propertyComponents = property.split('.')
    # skip first '.', if any
    if propertyComponents[0] == '':
        propertyComponents = propertyComponents[1:]
    propObj = obj
    i = 0
    while i < len(propertyComponents):
        # should really test with hasattrib first
        propObj = getattr(propObj, propertyComponents[i])
        i += 1

    return propObj


def getPropertyExpression(obj, property) -> str | float | None:
    # If the variables in the expression are all defined in the define spreadsheet
    # return the expression minus references to the spreadsheet,
    # otherwise just evaluate the expression and return its value
    sheet = FreeCAD.ActiveDocument.getObject("defines")

    # breakpoint()
    if sheet is None:  # an old doc, with no definesSpreadSheet
        return getPropertyValue(obj, property)

    defineLabel = sheet.Label
    expressions = obj.ExpressionEngine
    expression = None
    for pair in expressions:
        if pair[0] == property:
            expression = pair[1]
            break

    if expression is None:
        return getPropertyValue(obj, property)

    sheetstr = f"<<{defineLabel}>>."
    if expression.find(sheetstr) == -1:  # no defines spreadsheet  variables, just return the value
        return getPropertyValue(obj, property)

    expr1 = expression.replace(sheetstr, '')
    expr1 = SheetHandler.FC_expression_to_gdml(expr1)
    variables = extract_variables(expr1)
    for var in variables:
        # the var in the expression is the alias of the cell
        cell = sheet.getCellFromAlias(var)
        if cell is None:
            return getPropertyValue(obj, property)  # the variable is not an alias, just return the value of the property
        # the actual gdml variable name is in cell B+row
        row = cell[1:]
        nameCell = definesColumn['name'] + row
        name = sheet.get(nameCell)
        expr1 = expr1.replace(var, name)

    return expr1


def getVal(ptr, var, default=0):
    # all of math must be imported at global level
    # print ptr.attrib
    # is the variable defined in passed attribute
    if var in ptr.attrib:
        # if yes get its value
        vval = ptr.attrib.get(var)
        trace(var + " : " + str(vval))
        if vval[0] == "&":  # Is this referring to an HTML entity constant
            chkval = vval[1:]
        else:
            chkval = vval
        trace("chkval : " + str(chkval))
        try:
            ret = float(eval(chkval))
        except:
            try:
                ret = float(chkval)
            except:
                print("Illegal float: {}" % chkval)
                ret = 0.0

        trace("return value : " + str(ret))
        return ret
    return default


# get ref e.g name world, solidref, materialref
def getRef(ptr, name):
    wrk = ptr.find(name)
    if wrk is not None:
        ref = wrk.get("ref")
        trace(name + " : " + ref)
        return ref
    return wrk


def getMult(fp):
    unit = "mm"  # set default
    # Watch for unit and lunit
    # print('getMult : '+str(fp))
    if hasattr(fp, "lunit"):
        trace("lunit : " + fp.lunit)
        unit = fp.lunit
    elif hasattr(fp, "unit"):
        trace("unit : " + fp.unit)
        unit = fp.unit
    elif hasattr(fp, "attrib"):
        if "unit" in fp.attrib:
            unit = fp.attrib["unit"]
        elif "lunit" in fp.attrib:
            unit = fp.attrib["lunit"]
    else:
        return 1

    unitsDict = {
        "mm": 1,
        "cm": 10,
        "m": 1000,
        "um": 0.001,
        "nm": 0.000001,
        # "dm": 100,   decimeter not recognized by geant
        "m": 1000,
        "km": 1000000,
    }
    if unit in unitsDict:
        return unitsDict[unit]

    print("unit not handled : " + unit)


def getDegrees(flag, r):
    import math

    if flag is True:
        return r * 180 / math.pi
    else:
        return r


def getRadians(flag, r):
    import math

    if flag is True:
        return r
    else:
        return r * math.pi / 180


def getPhysVolName(name) -> str | None:
    ''' return phys_vol name of part or none if not in the gdmlInfo sheet '''
    # TODO test, for WB version in the doc, rather than spreadsheet name
    # TODO put part_names in a dictionary for quick access to row number
    sheet = FreeCAD.ActiveDocument.getObject("gdmlInfo")
    if sheet is None:  # an old doc, with no definesSpreadSheet
        return None

    last_row = lastRow(sheet)

    # slow search to find if the volume name is contained in column A
    # first is header, so start at 2
    for row in range(2, last_row + 1):
        cell = gdmlSheetColumn['identifier'] + str(row)
        part_name = sheet.get(cell)
        if part_name == name:
            # The name exists. Does it have a position reference?
            cell = gdmlSheetColumn['physvol_name'] + str(row)
            try:
                name = sheet.get(cell)
            except:
                name = None
            return name

    return None

def getPositionName(name) -> tuple[str|None,str|None]:
    ''' return (position_type, position_name) name of the part with name 'name. or none if not in the gdmlInfo sheet '''
    # TODO test, for WB version in the doc, rather than spreadsheet name
    sheet = FreeCAD.ActiveDocument.getObject("gdmlInfo")
    if sheet is None:  # an old doc, with no definesSpreadSheet
        return None, None

    last_row = lastRow(sheet)

    # slow search to find if the volume name is contained in column A
    # first is header, so start at 2
    for row in range(2, last_row + 1):
        cell = gdmlSheetColumn['identifier'] + str(row)
        part_name = sheet.get(cell)
        if part_name == name:
            # The name exists. Does it have a position reference?
            cell = gdmlSheetColumn['position_type'] + str(row)
            try:
                pos_type = sheet.get(cell)
            except:
                pos_type = None

            cell = gdmlSheetColumn['position_name'] + str(row)
            try:
                name = sheet.get(cell)
            except:
                name = None
            return pos_type, name

    return None, None

def getRotationName(name) -> tuple[str|None,str|None]:
    ''' return rotation_type, rotation_name name of the part with name 'name. or none if not in the gdmlInfo sheet '''
    # TODO test, for WB version in the doc, rather than spreadsheet name
    sheet = FreeCAD.ActiveDocument.getObject("gdmlInfo")
    if sheet is None:  # an old doc, with no definesSpreadSheet
        return None, None

    last_row = lastRow(sheet)

    # slow search to find if the volume name is contained in column A
    for row in range(1, last_row + 1):
        cell = gdmlSheetColumn['identifier'] + str(row)
        part_name = sheet.get(cell)
        if part_name == name:
            # The name exists. Does it have a position reference?
            cell = gdmlSheetColumn['rotation_type'] + str(row)
            try:
                rot_type = sheet.get(cell)
            except:
                rot_type = None

            cell = gdmlSheetColumn['rotation_name'] + str(row)
            try:
                name = sheet.get(cell)
            except:
                name = None
            return rot_type, name

    return None, None


def getPositionExpressions(solid, property):
    '''
    return expression from the define section for a position with name property
    '''

    posName = solid.get(property)
    pos = define.find("position[@name='%s']" % posName)
    # TODO deal with unit
    xexpr = yexpr = zexpr = None
    if posName is not None:
        row = getPositionRow(posName)
        if row is not None:
            xAlias = defineSpreadsheet.getAlias(definesColumn['pos_x'] + str(row))
            if xAlias is not None:
                xexpr = f"<<defines>>.{xAlias}"

            yAlias = defineSpreadsheet.getAlias(definesColumn['pos_y'] + str(row))
            if yAlias is not None:
                yexpr = f"<<defines>>.{yAlias}"

            zAlias = defineSpreadsheet.getAlias(definesColumn['pos_z'] + str(row))
            if zAlias is not None:
                zexpr = f"<<defines>>.{zAlias}"

    return xexpr, yexpr, zexpr


def setPlacement(obj, xml, invertRotation=True):
    ''' Set the placement of FreeCAD object obj from the position/positionref
    and rotation/rotationref given in the xml element
    invertRotation: invert rotation from that given in the xml
    '''


    obj.Placement.Base = FreeCAD.Vector(0, 0, 0)
    posName = getRef(xml, "positionref")

    if posName is not None:
        row = getPositionRow(posName)
        if row is not None:
            unit_alias = defineSpreadsheet.getAlias(definesColumn['pos_unit'] + str(row))
            default_unit = True
            if unit_alias is not None:
                unit = defineSpreadsheet.get(unit_alias)
                default_unit = False
            xAlias = defineSpreadsheet.getAlias(definesColumn['pos_x'] + str(row))
            if xAlias is not None:
                if default_unit:
                    expr = f"<<defines>>.{xAlias}"
                else:
                    expr = f"<<defines>>.{xAlias}*1{unit}"
                obj.setExpression('.Placement.Base.x', expr)

            yAlias = defineSpreadsheet.getAlias(definesColumn['pos_y'] + str(row))
            if yAlias is not None:
                if default_unit:
                    expr = f"<<defines>>.{yAlias}"
                else:
                    expr = f"<<defines>>.{yAlias}*1{unit}"
                obj.setExpression('.Placement.Base.y', expr)

            zAlias = defineSpreadsheet.getAlias(definesColumn['pos_z'] + str(row))
            if zAlias is not None:
                if default_unit:
                    expr = f"<<defines>>.{zAlias}"
                else:
                    expr = f"<<defines>>.{zAlias}*1{unit}"
                obj.setExpression('.Placement.Base.z', expr)

    else:
        pos = xml.find("position")
        if pos is not None:
            px, py, pz = getPositionFromAttrib(pos)
            obj.Placement.Base = FreeCAD.Vector(px, py, pz)

            # set expression for components that have one
            for prop in ["x", "y", "z"]:
                expr = getSheetExpression(pos, prop)
                if expr is not None:
                    if SheetHandler.hasTrig(expr):
                        expr = SheetHandler.gdml_invtrig_to_FC(expr)
                    if SheetHandler.hasTrig(expr):
                        expr = SheetHandler.gdml_trig_to_FC(expr)

                    obj.setExpression(f".Placement.Base.{prop}", expr)

    # Now set Rotation
    obj.Placement.Rotation = FreeCAD.Rotation(0, 0, 0, 1)
    rotName = getRef(xml, "rotationref")
    if rotName is not None:
        row = getRotationRow(rotName)
        radianFlg = True   # default is radians
        angMult = 1.0
        if row is not None:
            try:
                unit = defineSpreadsheet.get('F' + str(row))
                if unit=="deg" or unit=="degree":
                    radianFlg = False
                elif unit=="mrad":
                    angMult = 0.001
            except:
                pass

            x = y = z = 0
            xAlias = defineSpreadsheet.getAlias(definesColumn['rot_x'] + str(row))
            if xAlias is not None:
                x = defineSpreadsheet.get(xAlias)
                x = angMult * getDegrees(radianFlg, x)

            yAlias = defineSpreadsheet.getAlias(definesColumn['rot_y'] + str(row))
            if yAlias is not None:
                y = defineSpreadsheet.get(yAlias)
                y = angMult * getDegrees(radianFlg, y)

            zAlias = defineSpreadsheet.getAlias(definesColumn['rot_z'] + str(row))
            if zAlias is not None:
                z = defineSpreadsheet.get(zAlias)
                z = angMult * getDegrees(radianFlg, z)

            if invertRotation:
                x = -x
                y = -y
                z = -z
            rotX = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), x)
            rotY = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), y)
            rotZ = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), z)

            rot = rotX * rotY * rotZ
            obj.Placement.Rotation = rot

    else:
        rot = xml.find("rotation")
        x = y = z = 0
        if rot is not None:
            if "name" in rot.attrib:
                rotName = rot.attrib["name"]

            radianFlg = True
            if "unit" in rot.attrib:
                # print(rot.attrib['unit'][:3])
                if rot.attrib["unit"][:3] == "deg":
                    radianFlg = False

            if "x" in rot.attrib:
                x = getDegrees(radianFlg, float(eval(rot.attrib["x"])))

            if "y" in rot.attrib:
                y = getDegrees(radianFlg, float(eval(rot.attrib["y"])))

            if "z" in rot.attrib:
                z = getDegrees(radianFlg, float(eval(rot.attrib["z"])))

            if invertRotation:
                x = -x
                y = -y
                z = -z

            rotX = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), x)
            rotY = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), y)
            rotZ = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), z)

            rot = rotX * rotY * rotZ
            obj.Placement.Rotation = rot

    createGdmlSheetEntry(obj, xml)

def createGdmlSheetEntry(obj, xml):
    ''' Create entry in gdmlSpreadsheet to keep track of original gdml parameters '''
    global gdmlSpreadsheet
    from .exportGDML import getIdentifier

    if gdmlSpreadsheet is None:
        return

    identifier = getIdentifier(obj)

    row = lastRow(gdmlSpreadsheet)
    row += 1
    if row == 1:
        for heading in gdmlSheetColumn:
            cell = gdmlSheetColumn[heading] + str(row)
            gdmlSpreadsheet.set(cell, heading)
            gdmlSpreadsheet.setStyle(cell, 'bold')
        row += 1

    cell = gdmlSheetColumn['identifier'] + str(row)
    gdmlSpreadsheet.set(cell, identifier)

    # we don't need this anymore. identifier should give us the name
    # if "name" in xml.attrib:
    #    cell = gdmlSheetColumn['identifier'] + str(row)
    #    gdmlSpreadsheet.set(cell, xml.attrib["name"])

    cell = gdmlSheetColumn['position_type'] + str(row)

    pos = xml.find("position")
    if pos is not None:
        gdmlSpreadsheet.set(cell, 'position')
        if "name" in pos.attrib:
            cell = gdmlSheetColumn['position_name'] + str(row)
            gdmlSpreadsheet.set(cell, pos.attrib["name"])
        for prop in ["x", "y", "z", "unit"]:
            if prop in pos.attrib:
                cell = gdmlSheetColumn["pos_" + prop] + str(row)
                gdmlSpreadsheet.set(cell, pos.attrib[prop])

    else:
        pos = xml.find("positionref")
        if pos is not None:
            gdmlSpreadsheet.set(cell, 'positionref')
            cell = gdmlSheetColumn['position_name'] + str(row)
            gdmlSpreadsheet.set(cell, pos.attrib["ref"])

    cell = gdmlSheetColumn['rotation_type'] + str(row)
    rot = xml.find("rotation")
    if rot is not None:
        gdmlSpreadsheet.set(cell, 'rotation')
        if "name" in rot.attrib:
            cell = gdmlSheetColumn['rotation_name'] + str(row)
            gdmlSpreadsheet.set(cell, rot.attrib["name"])
        for prop in ["x", "y", "z", "unit"]:
            if prop in rot.attrib:
                cell = gdmlSheetColumn["rot_"+prop] + str(row)
                gdmlSpreadsheet.set(cell, rot.attrib[prop])

    else:
        rot = xml.find("rotationref")
        if rot is not None:
            gdmlSpreadsheet.set(cell, 'rotationref')
            cell = gdmlSheetColumn['rotation_name'] + str(row)
            gdmlSpreadsheet.set(cell, rot.attrib["ref"])


def processPlacement(base, rot):
    # setTrace(True)
    # trace('processPlacement')
    # Different Objects will have adjusted base GDML-FreeCAD
    # rot is rotation or None if default
    # set rotation matrix
    # print('process Placement : '+str(base))
    if rot is None:
        return FreeCAD.Placement(base, FreeCAD.Rotation(0, 0, 0, 1))

    else:
        trace("Rotation : ")
        trace(rot.attrib)
        x = y = z = 0

        if "name" in rot.attrib:
            if rot.attrib["name"] == "identity":
                trace("identity")
                return FreeCAD.Placement(base, FreeCAD.Rotation(0, 0, 0, 1))

            if rot.attrib["name"] == "center":
                trace("center")
                return FreeCAD.Placement(base, FreeCAD.Rotation(0, 0, 0, 1))

        radianFlg = True
        if "unit" in rot.attrib:
            # print(rot.attrib['unit'][:3])
            if rot.attrib["unit"][:3] == "deg":
                radianFlg = False

        if "x" in rot.attrib:
            trace("x : " + rot.attrib["x"])
            # print(eval('HALFPI'))
            trace(eval(rot.attrib["x"]))
            x = getDegrees(radianFlg, float(eval(rot.attrib["x"])))
            trace("x deg : " + str(x))

        if "y" in rot.attrib:
            trace("y : " + rot.attrib["y"])
            y = getDegrees(radianFlg, float(eval(rot.attrib["y"])))
            trace("y deg : " + str(y))

        if "z" in rot.attrib:
            trace("z : " + rot.attrib["z"])
            z = getDegrees(radianFlg, float(eval(rot.attrib["z"])))
            trace("z deg : " + str(z))

        rotX = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), -x)
        rotY = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), -y)
        rotZ = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), -z)

        rot = rotX * rotY * rotZ
        # rot = rotX.multiply(rotY).multiply(rotZ)
        # rot = rotX
        # c_rot =  FreeCAD.Vector(0,0,0)  # Center of rotation
        # print('base : '+str(base))
        # print('rot  : '+str(rot))
        # return FreeCAD.Placement(base, rot,  c_rot)

        # placement = FreeCAD.Placement(base, FreeCAD.Rotation(-x,-y,-z))
        # placement = FreeCAD.Placement(base, FreeCAD.Rotation(-z,-y,-x), \
        #            base)
        placement = FreeCAD.Placement(base, FreeCAD.Rotation(rot))
        # print('placement : '+str(placement))
        return placement


def getPositionFromAttrib(pos):
    # print('getPositionFromAttrib')
    # print('pos : '+str(ET.tostring(pos)))
    # print(pos.attrib)
    # if hasattr(pos.attrib, 'unit') :        # Note unit NOT lunit
    # if hasattr(pos.attrib,'name') :
    #   name = pos.get('name')
    #   if name == 'center' :
    #      return(0,0,0)
    mul = getMult(pos)
    px = mul * getVal(pos, "x")
    py = mul * getVal(pos, "y")
    pz = mul * getVal(pos, "z")
    return px, py, pz


def getPositionFromDict(pos):
    # print('getPositionFromAttrib')
    # print('pos : '+str(ET.tostring(pos)))
    # print(pos.attrib)
    # if hasattr(pos.attrib, 'unit') :        # Note unit NOT lunit
    # if hasattr(pos.attrib,'name') :
    #   name = pos.get('name')
    #   if name == 'center' :
    #      return(0,0,0)
    unit = pos["unit"]
    mul = 1

    unitsDict = {
        "mm": 1,
        "cm": 10,
        "m": 1000,
        "um": 0.001,
        "nm": 0.000001,
        "dm": 100,
        "m": 1000,
        "km": 1000000,
    }

    if unit in unitsDict:
        mul = unitsDict[unit]

    try:
        px = mul * float(pos["x"])
        py = mul * float(pos["y"])
        pz = mul * float(pos["z"])
    except:
        px = py = pz = 0

    return px, py, pz


# Return x,y,z from position definition
def getElementPosition(xmlElem):
    # get Position from local element
    # setTrace(True)
    trace("Get Element Position : ")
    pos = xmlElem.find("position")
    if pos is not None:
        trace(pos.attrib)
        return getPositionFromAttrib(pos)
    else:
        return 0, 0, 0


def getDefinedPosition(name):
    # get Position from define section
    # pos = define.find("position[@name='%s']" % name )
    if name == "identity":
        print("Identity Position")
        return 0, 0, 0
    elif name == "center":
        print("Center Position")
        return 0, 0, 0
    else:
        pos = positions[name]
        if pos is not None:
            # print('Position : '+str(pos))
            trace(pos)
            # return(getPositionFromAttrib(pos))
            return getPositionFromDict(pos)
        else:
            return 0, 0, 0


def getPosition(xmlEntity):
    # Get position via reference
    # setTrace(True)
    trace("GetPosition via Reference if any")
    posName = getRef(xmlEntity, "positionref")
    if posName is not None:
        trace("positionref : " + posName)
        return getDefinedPosition(posName)
    else:
        return getElementPosition(xmlEntity)


def testPosition(xmlEntity, px, py, pz):
    posName = getRef(xmlEntity, "positionref")
    if posName is not None:
        trace("positionref : " + posName)
        return getDefinedPosition(posName)
    pos = xmlEntity.find("position")
    if pos is not None:
        trace(pos.attrib)
        return getPositionFromAttrib(pos)
    else:
        return px, py, pz


def getDefinedRotation(name):
    # Just get definition - used by parseMultiUnion passed to create solids
    return define.find("rotation[@name='%s']" % name)


def getRotation(xmlEntity):
    trace("GetRotation")
    rotref = getRef(xmlEntity, "rotationref")
    trace("rotref : " + str(rotref))
    if rotref is not None:
        rot = define.find("rotation[@name='%s']" % rotref)
    else:
        rot = xmlEntity.find("rotation")
    if rot is not None:
        trace(rot.attrib)
    return rot


def getRotFromRefs(ptr):
    printverbose = True
    trace("getRotFromRef")
    rot = define.find("rotation[@name='%s']" % getRef(ptr, "rotationref"))
    if rot is not None:
        trace(rot.attrib)
    return rot


def getDefinedVector(solid, v):
    global define
    # print('get Defined Vector : '+v)
    name = solid.get(v)
    pos = define.find("position[@name='%s']" % name)
    # print(pos.attrib)
    x = getVal(pos, "x")
    y = getVal(pos, "y")
    z = getVal(pos, "z")
    return FreeCAD.Vector(x, y, z)


def getPlacement(pvXML):
    base = FreeCAD.Vector(getPosition(pvXML))
    # print('base: '+str(base))
    rot = getRotation(pvXML)
    return processPlacement(base, rot)


def getScale(pvXML):
    # print(ET.tostring(pvXML))
    scale = pvXML.find("scale")
    x = y = z = 1.0
    if scale is not None:
        # print(ET.tostring(scale))
        x = getVal(scale, "x")
        y = getVal(scale, "y")
        z = getVal(scale, "z")
    return FreeCAD.Vector(x, y, z)


def getVertex(v):
    global define
    trace("Vertex")
    # print(dir(v))
    pos = define.find("position[@name='%s']" % v)
    # print("Position")
    # print(dir(pos))
    x = getVal(pos, "x")
    trace("x : " + str(x))
    y = getVal(pos, "y")
    trace("y : " + str(y))
    z = getVal(pos, "z")
    trace("z : " + str(z))
    return FreeCAD.Vector(x, y, z)


def facet(f):
    # vec = FreeCAD.Vector(1.0,1.0,1.0)
    # print(f"Facet {f}")
    # print(f.Points)
    if len(f.Points) == 3:
        return triangle(f.Points[0], f.Points[1], f.Points[2])
        # if f.Normal.dot(vec) > 0 :
        #   return(triangle(f.Points[0],f.Points[1],f.Points[2]))
        # else :
        #   return(triangle(f.Points[2],f.Points[1],f.Points[0]))
    else:
        return quad(f.Points[0], f.Points[1], f.Points[2], f.Points[3])
        # if f.Normal.dot(vec) > 0 :
        #   return(quad(f.Points[0],f.Points[1],f.Points[2],f.Points[3]))
        # else :
        #   return(quad(f.Points[3],f.Points[2],f.Points[1],f.Points[0]))


def triangle(v1, v2, v3):
    # passed vertex return face
    # print('v1 : '+str(v1)+' v2 : '+str(v2)+' v3 : '+str(v3))
    try:
        w1 = Part.makePolygon([v1, v2, v3, v1])
        f1 = Part.Face(w1)
        return f1
    except:
        return None


def quad(v1, v2, v3, v4):
    # passed vertex return face
    w1 = Part.makePolygon([v1, v2, v3, v4, v1])
    try:
        f1 = Part.Face(w1)
        return f1
    except:
        # Non-planar quad — caller counts and reports the total
        return None
