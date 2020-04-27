import sys
from lxml import etree 

if len(sys.argv)<3:
  print ("Usage: sys.argv[0] <in_file> <out_file>")
  sys.exit(1)

iname = sys.argv[1]
oname = sys.argv[2]

print('Parsing : '+iname)
tree = etree.parse(iname)
root = tree.getroot()
