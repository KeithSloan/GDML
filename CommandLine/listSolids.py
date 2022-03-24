import sys
from lxml import etree 

if len(sys.argv)<2:
  print ("Usage: sys.argv[0] <in_file>")
  sys.exit(1)

iname = sys.argv[1]

print('\nParsing : '+iname+'\n')
tree = etree.parse(iname)
root = tree.getroot()
solidList = []
for s in tree.xpath('//solids/*') :
    #print(s.tag)
    if s.tag not in solidList :
        solidList.append(s.tag)
l = 'List of Solids in : '+iname
print(l)
print('=' * len(l))
for i in solidList :
    print(i)        
