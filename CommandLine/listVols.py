import sys
from lxml import etree 

if len(sys.argv)<2:
  print ("Usage: sys.argv[0] <in_file>")
  sys.exit(1)

iname = sys.argv[1]

print('\nListing Volumes in : '+iname+'\n')
tree = etree.parse(iname)
root = tree.getroot()
s = root.find('structure')
#print(etree.tostring(s))
for v in s.findall('volume') :
    #print(etree.tostring(v))
    n = v.get('name')
    print(n)
