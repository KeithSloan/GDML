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
    constantsGrp = doc.getObject('Constants')
    constants = {}
    for obj in constantsGrp.OutList:
        constants[obj.name] = obj.value

    var = loopElement.get("for")
    start = loopElement.get("from")
    if start in constants:
        start = int(constants[start])
    else:
        start = int(start)

    to = loopElement.get("to")
    if to in constants:
        to = int(constants[to])
    else:
        to = int(to)

    step = loopElement.get("step")
    if step in constants:
        step = int(constants[step])
    else:
        step = int(step)

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
    #
    for loop in root.getroot().iterdescendants(tag="loop"):
        # print(loop.getparent(), loop.tag, loop.attrib)
        stack.append(loop)
    #
    # process them one at a time
    #
    while len(stack) > 0:
        loop = stack.pop()
        processLoop(loop)
    # print(ET.tostring(root, pretty_print=True))
