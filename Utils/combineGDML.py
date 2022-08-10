import sys

print('Utility to combined a GDML files included XML files')
if len(sys.argv)<3:
  print ("Usage: sys.argv[0] <in_file> <out_file>")
  sys.exit(1)

iname=sys.argv[1]
oname=sys.argv[2]

from lxml import etree
parser = etree.XMLParser(resolve_entities=True)
root= etree.parse(iname, parser=parser)
root.docinfo.clear()
root.write(oname)

