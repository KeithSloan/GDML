import sys, os
from lxml import etree 

def checkDirectory(path) :
    if not os.path.exists(path):
       print('Creating Directory : '+path)
       os.mkdir(path)

class gdmlStacks :
   def __init__(self, iName, oName) :
       self.tree = etree.parse(iName)
       self.root = self.tree.getroot()
       self.oName = oName
       self.gdml = etree.Element('gdml')
       self.docString = '\n<!DOCTYPE gdml [\n'
       self.structure = self.tree.find('structure')
       self.oldSolids = self.tree.find('solids')
       #print(etree.fromstring(structure))
       self.newDefine = etree.Element('define')
       self.materials = self.tree.find('materials')
       self.newSolids = etree.Element('solids')
       self.newStructure = etree.Element('structure')
       self.oldDefine = self.tree.find('define') 
       #oldSolids = self.tree.find('solids')
       self.oldVols   = self.tree.find('structure')
       self.solidList = []
       self.positionList = []
       self.rotationList = []
       self.volList = []

   def processSolid(self, sname) :
       # Passed solid name volume, booleans
       solid = self.oldSolids.find(f"*[@name='{sname}']")
       print('Adding : '+sname)
       print(solid.attrib)
       if sname not in self.solidList : self.solidList.append(sname)
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

   def processPhysVol(self, volasm, vname):
       pvs = volasm.findall('physvol')
       splitCount = 0
       splitSet   = 0
       splitSize  = 75
       for pv in pvs :
           volref = pv.find('volumeref')
           pname = volref.attrib.get('ref')
           print('physvol : '+pname)
           self.processVolAsm(pname)
           posref = pv.find('positionref')
           if posref is not None :
              posname = posref.attrib.get('ref')
              print('Position ref : '+posname)
           if posname not in self.positionList : 
              self.positionList.append(posname)
           rotref = pv.find('rotationref')
           if rotref is not None :
              rotname = rotref.attrib.get('ref')
              print('Rotation ref : '+rotname)
           if rotname not in self.rotationList :
              self.rotationList.append(rotname)
           splitCount += 1
           if splitCount == splitSize :
              newName = vname + '_' +str(splitSet).zfill(3)
              print('Export gdml and structure : '+newName)
              self.exportGDML(os.path.join(oName, newName), newName) 
              print('splitCount : '+str(splitCount))
              splitCount = 0
              splitSet +=  1

   def processVol(self, vol) :
       print(vol)
       print(vol.attrib)
       # Need to process physvols first
       vname = vol.attrib.get('name')
       print('volume : ' + vname)
       self.processPhysVol(vol, vname)
       if vname not in self.volList : self.volList.append(vname)
       solid = vol.find('solidref')
       sname = solid.attrib.get('ref')
       self.processSolid(sname)
       material = vol.find('materialref')
       if material is not None :
          #print('material : '+str(material.attrib))
          print('material : ' + material.attrib.get('ref'))

   def processAssembly(self, assem) :
       aname = assem.attrib.get('name')
       print('Process Assembly ; '+aname)
       processPhysVol(assem, aname)
       if aname not in volList : volList.append(aname)

   def processVolAsm(self, vaname) :
       volasm = self.structure.find(f"*[@name='{vaname}']")
       if volasm.tag == 'volume' :
          self.processVol(volasm)
       elif volasm.tag == 'assembly' :
          self.processAssembly(volasm)
       else :
          print('Not Volume or Assembly : '+volasm.tag)

   def process(self) :
       # Following works
       #vol = structure.find('volume[@name="World"]')
       # Test if Volume
       checkDirectory(self.oName)
       vol = self.structure.find(f"volume[@name='{volume}']")
       if vol is not None :
          self.processVol(vol)
       else : 
          # Test if Assembly
          vol = structure.find(f"assembly[@name='{volume}']")
          if vol is not None :
             self.processAssembly(vol)
          else :
             print(volume+' :  Not found as Volume or Assembly')
             exit(0)

   def processLists(self) :
       for posName in self.positionList :
           p = self.oldDefine.find(f"position[@name='{posName}']")
           self.newDefine.append(p)
       for rotName in  self.rotationList :
           p = self.oldDefine.find(f"rotation[@name='{rotName}']")
           self.newDefine.append(p)
       for solidName in self.solidList :
           print('Solid : '+solidName)
           s = self.oldSolids.find(f"*[@name='{solidName}']")
           #print(s.attrib)
           self.newSolids.append(s)
       for vaName in self.volList :
           v = self.oldVols.find(f"*[@name='{vaName}']")
           self.newStructure.append(v)

   def printLists(self) :
       print('Vol List')
       print(self.volList)
       print('Solid List')
       print(self.solidList)
       print('Position List')
       print(self.positionList)
       print('Rotation List')
       print(self.rotationList)

   def exportElement(self, dirPath, elemName, elem) :
       etree.ElementTree(elem).write(os.path.join(dirPath,elemName))
       self.docString += '<!ENTITY '+elemName+' SYSTEM "'+elemName+'">\n'
       self.gdml.append(etree.Entity(elemName))

   def exportGDML(self, oName, volume) :
       self.setup = etree.Element('setup', {'name':'Default', 'version':'1.0'})
       etree.SubElement(self.setup,'world', { 'ref' : self.volList[-1]})
       print("Write GDML structure to Directory")
       NS = 'http://www.w3.org/2001/XMLSchema-instance'
       location_attribute = '{%s}noNameSpaceSchemaLocation' % NS
       gdml = etree.Element('gdml',attrib={location_attribute: \
            'http://service-spi.web.cern.ch/service-spi/app/releases/GDML/schema/gdml.xsd'})

       self.docString = '\n<!DOCTYPE gdml [\n'
       checkDirectory(oName)
       #self.exportElement(oName, 'constants',constants)
       self.exportElement(oName, volume+'_define',self.newDefine)
       self.exportElement(oName, volume+'_materials',self.materials)
       self.exportElement(oName, volume+'_solids',self.newSolids)
       self.exportElement(oName, volume+'_structure',self.newStructure)
       self.exportElement(oName, volume+'_setup',self.setup)
       self.docString += ']>\n'
       #indent(gdml)
       etree.ElementTree(gdml).write(os.path.join(oName,volume+'.gdml'), \
               doctype=self.docString.encode('UTF-8'))

if len(sys.argv)<5:
  print ("Usage: sys.argv[0] <parms> <Volume> <in_file> <Out_directory> <materials>")
  print("/n For parms the following are or'ed together")
  print(" For future")
  sys.exit(1)

parms  = int(sys.argv[1])
volume = sys.argv[2]
iName = sys.argv[3]
oName = sys.argv[4]

print('\nExtracting Volume : '+volume+' from : '+iName+' to '+oName)
gs = gdmlStacks(iName, oName)
gs.process()
gs.processLists()
gs.printLists()
gs.exportGDML(oName,volume)
