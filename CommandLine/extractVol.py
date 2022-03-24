import sys, os
from lxml import etree 

volList = []
solidList = []
positionList = []
rotationList = []

def processSolid(sname) :
   # Passed olid name volume, booleans
   global solidList, solids
   solid = oldSolids.find(f"*[@name='{sname}']")
   print('Adding : '+sname)
   print(solid.attrib)
   if sname not in solidList : solidList.append(sname)
   if solid.tag == 'subtraction' or solid.tag == 'union' or \
      solid.tag == 'intersection' :
      print('Found Boolean')
      first = solid.find('first')
      print('first : '+str(first.attrib))
      fname = first.attrib.get('ref')
      processSolid(fname)
      second = solid.find('second')
      print('second : '+str(second.attrib))
      sname = second.attrib.get('ref')
      processSolid(sname)

def processPhysVol(volasm):
   for pv in volasm.findall('physvol') :
      volref = pv.find('volumeref')
      pname = volref.attrib.get('ref')
      print('physvol : '+pname)
      processVolAsm(pname)
      posref = pv.find('positionref')
      if posref is not None :
         posname = posref.attrib.get('ref')
         print('Position ref : '+posname)
         if posname not in positionList : 
            positionList.append(posname)
      rotref = pv.find('rotationref')
      if rotref is not None :
         rotname = rotref.attrib.get('ref')
         print('Rotation ref : '+rotname)
         if rotname not in rotationList : rotationList.append(rotname)

def processVol(vol) :
   global volList, solidList, oldSolids
   print(vol)
   print(vol.attrib)
   # Need to process physvols first
   processPhysVol(vol)
   vname = vol.attrib.get('name')
   print('volume : ' + vname)
   if vname not in volList : volList.append(vname)
   solid = vol.find('solidref')
   sname = solid.attrib.get('ref')
   processSolid(sname)
   material = vol.find('materialref')
   if material is not None :
      #print('material : '+str(material.attrib))
      print('material : ' + material.attrib.get('ref'))

def processAssembly(assem) :
    aname = assem.attrib.get('name')
    print('Process Assembly ; '+aname)
    processPhysVol(assem)
    if aname not in volList : volList.append(aname)

def processVolAsm(vaname) :
    volasm = structure.find(f"*[@name='{vaname}']")
    if volasm.tag == 'volume' :
       processVol(volasm)
    elif volasm.tag == 'assembly' :
       processAssembly(volasm)
    else :
       print('Not Volume or Assembly : '+volasm.tag)

def exportElement(dirPath, elemName, elem) :
    import os
    global gdml, docString

    etree.ElementTree(elem).write(os.path.join(dirPath,elemName))
    docString += '<!ENTITY '+elemName+' SYSTEM "'+elemName+'">\n'
    gdml.append(etree.Entity(elemName))

def checkDirectory(path) :
    if not os.path.exists(path):
       print('Creating Directory : '+path)
       os.mkdir(path)

if len(sys.argv)<5:
  print ("Usage: sys.argv[0] <parms> <Volume> <in_file> <Out_directory> <materials>")
  print("/n For parms the following are or'ed together")
  print(" For future")
  sys.exit(1)

parms  = int(sys.argv[1])
gdml = etree.Element('gdml')

volume = sys.argv[2]
iName = sys.argv[3]
oName = sys.argv[4]

print('\nExtracting Volume : '+volume+' from : '+iName+' to '+oName)
tree = etree.parse(iName)
root = tree.getroot()
structure = tree.find('structure')
oldSolids = tree.find('solids')
#print(etree.fromstring(structure))
# Following works
#vol = structure.find('volume[@name="World"]')
# Test if Volume
vol = structure.find(f"volume[@name='{volume}']")
if vol is not None :
   processVol(vol)
else : 
   # Test if Assembly
   vol = structure.find(f"assembly[@name='{volume}']")
   if vol is not None :
      processAssembly(vol)
   else :
      print(volume+' :  Not found as Volume or Assembly')
      exit(0)
newDefine = etree.Element('define')
materials = tree.find('materials')
newSolids = etree.Element('solids')
newStructure = etree.Element('structure')
oldDefine = tree.find('define') 
oldSolids = tree.find('solids')
oldVols   = tree.find('structure')
for posName in positionList :
    p = oldDefine.find(f"position[@name='{posName}']")
    newDefine.append(p)
for rotName in rotationList :
    p = oldDefine.find(f"rotation[@name='{rotName}']")
    newDefine.append(p)
for solidName in solidList :
    print('Solid : '+solidName)
    s = oldSolids.find(f"*[@name='{solidName}']")
    #print(s.attrib)
    newSolids.append(s)
for vaName in volList :
    v = oldVols.find(f"*[@name='{vaName}']")
    newStructure.append(v)

print('Vol List')
print(volList)
print('Solid List')
print(solidList)
print('Position List')
print(positionList)
print('Rotation List')
print(rotationList)
setup = etree.Element('setup', {'name':'Default', 'version':'1.0'})
etree.SubElement(setup,'world', { 'ref' : volList[-1]})

print("Write GDML structure to Directory")
NS = 'http://www.w3.org/2001/XMLSchema-instance'
location_attribute = '{%s}noNameSpaceSchemaLocation' % NS
gdml = etree.Element('gdml',attrib={location_attribute: \
      'http://service-spi.web.cern.ch/service-spi/app/releases/GDML/schema/gdml.xsd'})

docString = '\n<!DOCTYPE gdml [\n'
checkDirectory(oName)
#exportElement(oName, 'constants',constants)
exportElement(oName, volume+'_define',newDefine)
exportElement(oName, volume+'_materials',materials)
exportElement(oName, volume+'_solids',newSolids)
exportElement(oName, volume+'_structure',newStructure)
exportElement(oName, volume+'_setup',setup)
docString += ']>\n'
#indent(gdml)
etree.ElementTree(gdml).write(os.path.join(oName,volume+'.gdml'), \
               doctype=docString.encode('UTF-8'))
