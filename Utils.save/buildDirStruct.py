import sys, os
from lxml import etree

class gdml_lxml() :
   def __init__(self, filename) :
      try:
         from lxml import etree
         print('Running with lxml.etree\n')
         print(filename)
         parser = etree.XMLParser(resolve_entities=True)
         self.root = etree.parse(filename, parser=parser)

      except ImportError :
         try :
             import xml.etree.ElementTree as etree
             print("Rnning with etree.ElementTree (import limitations)\n")
             self.tree = etree.parse(filename)
             self.root = self.tree.getroot()
         except :
             print('No lxml or xml')

      self.define    = self.root.find('define')
      self.materials = self.root.find('materials')
      self.solids    = self.root.find('solids')
      self.structure = self.root.find('structure')

   def getPosition(self,posName) :
       return self.define.find(f"position[@name='{posName}']")

   def getRotation(self,rotName) :
       return self.define.find(f"rotation[@name='{rotName}']")

   def getSolid(self, sname) :
       return self.solids.find(f"*[@name='{sname}']")

   def getMaterials(self) :
       return(self.materials)

   def getVolAsm(self, vaname) :
       return self.structure.find(f"*[@name='{vaname}']")

   def addElement(self, elemName) :
       self.docString += '<!ENTITY '+elemName+' SYSTEM "'+elemName+'">\n'
       self.gdml.append(etree.Entity(elemName))

   def closeElements(self) :
       self.docString += ']\n'

   def writeGDML(self, path,vname) :
       #indent(iself.gdml)
       etree.ElementTree(self.gdml).write(os.path.join(path,vname+'.gdml'), \
               doctype=self.docString.encode('UTF-8'))

class VolAsm() :

   def __init__(self, vaname) :
       from lxml import etree

       self.vaname    = vaname
       NS = 'http://www.w3.org/2001/XMLSchema-instance'
       location_attribute = '{%s}noNameSpaceSchemaLocation' % NS
       self.gdml = etree.Element('gdml',attrib={location_attribute: \
      'http://service-spi.web.cern.ch/service-spi/app/releases/GDML/schema/gdml.xsd'})
       self.newDefine = etree.SubElement(self.gdml,'define')
       self.newSolids = etree.SubElement(self.gdml,'solids')
       self.posList   = []
       self.rotList   = []
       self.solidList = []

   def addDefine(self, d) :
       if d is not None  :
          self.newDefine.append(d)
       else :
          print('==== Problem with define')
          exit(1)
  
   def processPosition(self, lxml, posName) :
       if posName not in self.posList :
          self.posList.append(posName)
          p = lxml.getPosition(posName)
          self.newDefine.append(p)

   def processRotation(self,lxml, rotName) :
       if rotName not in self.rotList :
          self.rotList.append(rotName)
          p = lxml.getPosition(rotName)
          self.newDefine.append(p)
   
   def processSolid(self, lxml, sname) :
       if sname not in self.solidList :
          self.solidList.append(sname)
          s = lxml.getSolid(sname)
          if s is not None :
             self.newSolids.append(s)
          else :
             print('Solid : '+sname+' Not Found')
             exit(1)

   def processPhysVols(self, lxml, volasm, path) :
       vaname = volasm.attrib.get('name')
       print('Process Phys Vols of : '+vaname)
       for pv in volasm.findall('physvol') :
           volref = pv.find('volumeref')
           pname = volref.attrib.get('ref')
           print('physvol : '+pname)
           npath = os.path.join(path,pname)
           print('New path : '+npath)
           checkDirectory(npath)
           new_pa = VolAsm(pname)
           new_pa.processVolAsm(lxml, npath, pname)
           posref = pv.find('positionref')
           if posref is not None :
              posname = posref.attrib.get('ref')
              print('Stack Position ref : '+posname)
              if posname not in self.posList :
                 self.posList.append(posname)
           rotref = pv.find('rotationref')
           if rotref is not None :
              rotname = rotref.attrib.get('ref')
              print('Stack Rotation ref : '+rotname)
              if rotname not in self.rotList : self.rotList.append(rotname)
       print('Number of positions in : '+vaname+' : '+str(len(self.posList)))
       print(self.posList)
       for posName in self.posList :
           print('Pull Position '+posName)
           p = lxml.getPosition(posName)
           self.addDefine(p)
       for rotName in self.rotList :
           p = lxml.getRotation(rotName)
           self.addDefine(p)
       writeElement(path, vaname, 'defines', self.newDefine)
       writeElement(path, vaname, 'solids', self.newSolids)
  
   def processVolume(self, lxml, path, vol) :
       print('Process Volume')
       print(vol)
       print(vol.attrib)
       # Need to process physvols first
       vname = vol.attrib.get('name')
       print('volume : ' + vname)
       self.processPhysVols(lxml, vol, path)
       solid = vol.find('solidref')
       sname = solid.attrib.get('ref')
       print('Process Solid : '+sname)
       self.processSolid(lxml, sname)
       material = vol.find('materialref')
       if material is not None :
          #print('material : '+str(material.attrib))
          print('material : ' + material.attrib.get('ref'))
       materials = lxml.getMaterials()
       writeElement(path, vname, 'materials', materials)

   def processAssembly(self, lxml, path, assem) :
       aname = assem.attrib.get('name')
       print('Process Assembly ; '+aname)
       self.processPhysVols(lxml, assem, path)

   def processVolAsm(self, lxml, path, vaname) :
       print('Processing VolAsm : '+vaname)
       volasm = lxml.getVolAsm(vaname)
       print(volasm)
       print(str(volasm))
       if volasm is not None :
          writeElement(path, vaname, 'struct', volasm)
          if volasm.tag == 'volume' :
             self.processVolume(lxml, path, volasm)
          elif volasm.tag == 'assembly' :
             self.processAssembly(lxml, path, volasm)
          else :
             print('Not Volume or Assembly : '+volasm.tag)
       else :
          print(vaname+ ' : Not Found')

def checkDirectory(path) :
    if not os.path.exists(path):
       print('Creating Directory : '+path)
       os.mkdir(path)

def writeElement(path, sname, type, elem) :
    import os

    fpath = os.path.join(path,sname+'_'+type)
    print('writing file : '+fpath)
    etree.ElementTree(elem).write(fpath)

def exportElement(dirPath, elemName, elem) :
    import os
    global gdml, docString

    etree.ElementTree(elem).write(os.path.join(dirPath,elemName))
    docString += '<!ENTITY '+elemName+' SYSTEM "'+elemName+'">\n'
    gdml.append(etree.Entity(elemName))

if len(sys.argv)<5:
  print ("Usage: sys.argv[0] <parms> <Volume> <in_file> <Out_directory> <materials>")
  print("/n For parms the following are or'ed together")
  print(" For future")
  sys.exit(1)

parms  = int(sys.argv[1])
vName = sys.argv[2]
iName = sys.argv[3]
oName = sys.argv[4]

print('\nExtracting Volume : '+vName+' from : '+iName+' to '+oName)
checkDirectory(oName)
path = os.path.join(oName,vName)
checkDirectory(path)
lxml = gdml_lxml(iName)
volasm = VolAsm(vName)
volasm.processVolAsm(lxml, path, vName)
#setup = etree.Element('setup', {'name':'Default', 'version':'1.0'})
#etree.SubElement(setup,'world', { 'ref' : volList[-1]})
