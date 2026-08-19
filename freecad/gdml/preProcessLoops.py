import sys
import FreeCAD
import copy
import re

try:
    import lxml.etree as ET

    FreeCAD.Console.PrintMessage("running with lxml.etree\n")
    XML_IO_VERSION = "lxml"
except ImportError:
    try:
        import xml.etree.ElementTree as ET

        FreeCAD.Console.PrintMessage("running with xml.etree.ElementTree\n")
        XML_IO_VERSION = "xml"
    except ImportError:
        FreeCAD.Console.PrintMessage("pb xml lib not found\n")
        sys.exit()


def processLoop(loopElement):
    """
    Expand loop element in situ:
    - first get the loop variable and the from, to, step 
    - for each value of the loop:
        copy all the child elements
        add the copy to the parent of the loop element
        replace the variable in the element with the current loop value
        for each descendant of the copied child element, replace
        the variable with its loop value
    - remove the loop element from its parent
    """
    doc = FreeCAD.ActiveDocument
    # The loop bounds may reference a constant OR a variable by name, so gather
    # both groups (the loop variable itself is usually a <variable>).
    values = {}
    for grpName in ('Constants', 'Variables'):
        grp = doc.getObject(grpName)
        if grp is None:
            continue
        for obj in grp.OutList:
            # skip the spreadsheet for now. TODO read values from the spreadsheet
            if obj.TypeId == "Spreadsheet::Sheet":
                continue
            if hasattr(obj, "value"):
                values[obj.name] = obj.value

    def loopInt(raw, default=None):
        # Resolve a loop bound that may be missing (None -> default), a
        # constant/variable name, or a numeric literal.
        if raw is None:
            return default
        if raw in values:
            raw = values[raw]
        return int(float(raw))

    var = loopElement.get("for")
    # In GDML 'from' and 'step' are optional. A missing 'from' starts at the loop
    # variable's current value (Geant4 semantics); 'step' defaults to 1.
    try:
        varStart = int(float(values.get(var, 1)))
    except (TypeError, ValueError):
        varStart = 1
    start = loopInt(loopElement.get("from"), default=varStart)
    to = loopInt(loopElement.get("to"))
    step = loopInt(loopElement.get("step"), default=1)
    if to is None:
        print(f"GDML Warning: <loop for='{var}'> has no 'to' value - loop skipped")
        loopElement.getparent().remove(loopElement)
        return

    # print(f'var {var} from {start} to {to} step {step}')

    def substitueVar(element, var, value):
        if element.attrib is None:
            # print(f'{element.tag} has no attributes - no substituions')
            return
        pattern = "\[ *"+var+" *\]"
        for key, value in element.items():
            if len(re.findall(pattern, value)):
                value = re.sub(pattern, f'_{str(i)}_', value)
                value = value.replace('__', '_')
                if value[-1] == '_':
                    s = list(value)
                    s[-1] = ""
                    value = "".join(s)
            elif var in value:
                value = value.replace(var, f'{i}')
            element.set(key, value)

    parent = loopElement.getparent()
    for i in range(start, to+1, step):
        for child in loopElement.iterchildren():
            newchild = copy.copy(child)
            # print(newchild, newchild.getparent())
            substitueVar(newchild, var, i)
            for desc in newchild.iterdescendants():
                # print(desc, desc.tag, desc.attrib)
                substitueVar(desc, var, i)
            parent.append(newchild)

    parent.remove(loopElement)


def preprocessLoops(root):
    stack = []
    #
    # get all loop elements
    # root may be an lxml _ElementTree (from etree.parse) or an _Element;
    # iterdescendants lives on _Element, so unwrap if needed.
    element = root.getroot() if hasattr(root, 'getroot') else root
    print(f"PreProcess Loops - root {root}")
    for loop in element.iterdescendants(tag="loop"):
    
        # print(loop.getparent(), loop.tag, loop.attrib)
        stack.append(loop)
    #
    # process them one at a time
    #
    while len(stack) > 0:
        loop = stack.pop()
        processLoop(loop)
    # print(ET.tostring(root, pretty_print=True))
