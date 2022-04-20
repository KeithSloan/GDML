import sys
from lxml import etree 

def processPhysVol(v) :
   print('process physvols')
   #print(etree.tostring(v))
   for pv in v.findall('physvol') :
      volref = pv.find('volumeref')
      pname = volref.attrib.get('ref')
      print(pname)


if len(sys.argv)<2:
  print ("Usage: sys.argv[0] <depth> <in_file>")
  sys.exit(1)

depth  = int(sys.argv[1])
iName  = sys.argv[2]

print('\nListing Physvols in filename : '+iName+'\n')
tree = etree.parse(iName)
root = tree.getroot()
setup = root.find('setup')
world = setup.find('world')
vName = world.attrib.get('ref')
print("Main Volume : "+vName)
struct = root.find('structure')
if depth == 1 :
   vol = struct.find(f"*[@name='{vName}']")
   pvol = vol.find('physvol')
   volref = pvol.find('volumeref')
   vName = volref.attrib.get('ref')
   print("First level Volume : "+str(vName))

#print(etree.tostring(s))
va = struct.find(f"*[@name='{vName}']")
if va is None :
   va = struct.find('assembly')
if va is not None :
   processPhysVol(va)
else :
   print('No Volume or Assembly') 
