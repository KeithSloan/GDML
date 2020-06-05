#!/usr/bin/python

#    
#
import os


########################################################
#
#
#
########################################################
def loadFileCol(nomFileReaded):
    if os.path.isfile(nomFileReaded) == False :
        print(nomFileReaded + ' is not a file')
        return []
    else:
        tab =[]
        print(nomFileReaded)
        fileR = open(nomFileReaded, 'r')
        while 1:
            data=fileR.readline()
            if not data:
               break
            else:
               if data[0]=='#':
                  print 'not readen: ' + data  
               elif data[0] =='\n':
                  pass
               else:
                  data = data.replace(',', '.')
                  data = data.replace('\n', '')
                  data = data.replace('\t', ' ')
                  ldata = data.split(' ')
                  if(len(tab)<1):
                      for indice in range(len(ldata)):
                          tab.append([])   
                  for indice in range(len(ldata)):
                      tab[indice].append(ldata[indice])

        fileR.close()
    
        return tab
###############################################################


########################################################
#
#
#
########################################################
def loadFileNcomp(nomFileReaded):
    if os.path.isfile(nomFileReaded) == False :
        print(nomFileReaded + ' is not a file')
        return []
    else:
        tab =[]
        print(nomFileReaded)
        fileR = open(nomFileReaded, 'r')
        while 1:
            data=fileR.readline()
            if not data:
               break
            else:
               if data[0]=='#':
                  print 'not readen: ' + data  
               elif data[0] =='\n':
                  pass
               else:
                  data = data.replace(',', '.')
                  data = data.replace('\n', '')
                  data = data.replace('\t', ' ')
                  ldata = data.split(' ')
		  while( '' in ldata ): ldata.remove('')
		  		  
                  print ldata  

		  Ncomp = int(ldata[0])
		  Name = ldata[1]
		  density_gpcm3 = ldata[2]
		  I_eV = ldata[3]
		  formula = ''
		   
                  thisInfo = [Name, density_gpcm3, I_eV, formula] 
		  latomRep=[[],[]]
                  for indice in range(Ncomp):
                      data=fileR.readline()
		      data = data.replace(',', '.')
                      data = data.replace('\n', '')
                      data = data.replace('\t', ' ')
                      ldata = data.split(' ')
		      while( '' in ldata ): ldata.remove('')
		      latomRep[0].append(ldata[0])
                      latomRep[1].append(ldata[1])
		  
		  
		  dotindata=False
		  for indiceT in range(len(latomRep[1])):
		      if '.' in latomRep[1][indiceT]:
		          dotindata=True
                  if dotindata: thisInfo.append("fraction")
		  else: thisInfo.append("composite")
		  thisInfo.append(latomRep)		  
		  
                  tab.append(thisInfo)
        fileR.close()
    
        return tab
###############################################################



listZSymboleNameA = loadFileCol('list-Z-Symbol-Name-A.dat')
listZNameDensityI = loadFileCol('list-Z-Name-Density-I.dat')
print(listZNameDensityI)
print(listZSymboleNameA)


lmaterial = []
for indiceMat in range(len(listZNameDensityI[0])):
    thisname = listZNameDensityI[1][indiceMat]
    thisZ    = listZNameDensityI[0][indiceMat]
    thisDensity = listZNameDensityI[2][indiceMat] 
    print(listZSymboleNameA)
    print listZSymboleNameA[0]
    indiceThisZ = (listZSymboleNameA[0]).index(thisZ)
    thisA       = listZSymboleNameA[3][indiceThisZ] 
    lmaterial.append( [thisname, thisZ,thisDensity,  thisA])




## <material name="G4_He" Z="2">
##      <D unit="g/cm3" value="0.000166322" />
##      <atom unit="g/mole" value="4.002602" />

fileW = open("dataBaseSingleMaterial.xml", 'w')
fileW.write('<xml>\n')
fileW.write('  <define>\n')
fileW.write('    <constant name="HALFPI" value="pi/2." />\n')
fileW.write('    <constant name="PI" value="1.*pi" />\n')
fileW.write('    <constant name="TWOPI" value="2.*pi" />\n')
fileW.write('    </define>\n')
fileW.write('  <materials>\n')
       
for indiceM in range(len(lmaterial)):
    fileW.write('      <material formula="'+str(lmaterial[indiceM][0])+'" name="'+str(lmaterial[indiceM][0])+'" />\n')
    fileW.write('        <D unit="g/cm3" value="'+str(lmaterial[indiceM][1])+'" />\n')
    fileW.write('        <atom unit="g/mole" value="'+str(lmaterial[indiceM][3])+'" />\n')
    fileW.write('      </material>\n')
      
fileW.write('  </materials>\n')
fileW.write('</xml>\n')
fileW.close()



lmaterialNist = loadFileNcomp('nist.dat')


fileW = open("dataBaseMaterialNist.xml", 'w')
fileW.write('<xml>\n')
fileW.write('  <define>\n')
fileW.write('    <constant name="HALFPI" value="pi/2." />\n')
fileW.write('    <constant name="PI" value="1.*pi" />\n')
fileW.write('    <constant name="TWOPI" value="2.*pi" />\n')
fileW.write('    </define>\n')
fileW.write('  <materials>\n')
       
for indiceM in range(len(lmaterialNist)):
    fileW.write('      <material formula="'+str(lmaterialNist[indiceM][0])+'" name="'+str(lmaterialNist[indiceM][0])+'" >\n')
    fileW.write('        <D unit="g/cm3" value="'+str(lmaterialNist[indiceM][1])+'" />\n')
    type = lmaterialNist[indiceM][4]
    for indiceSubM in range(len(lmaterialNist[indiceM][5][0])):
        Z = lmaterialNist[indiceM][5][0][indiceSubM]
	
	
        indiceZ = listZNameDensityI[0].index(Z)
        thisname = listZNameDensityI[1][indiceZ]	
        fileW.write('        <'+type+' n="'+ str(lmaterialNist[indiceM][5][1][indiceSubM])+'" ref="'+str(thisname)+'"/>\n')
    fileW.write('      </material>\n')
      
fileW.write('  </materials>\n')
fileW.write('</xml>\n')
fileW.close()


print lmaterialNist


fileW = open("dataBaseNistAndSingleMaterial.xml", 'w')

fileW.write('<xml>\n')
fileW.write('  <define>\n')
fileW.write('    <constant name="HALFPI" value="pi/2." />\n')
fileW.write('    <constant name="PI" value="1.*pi" />\n')
fileW.write('    <constant name="TWOPI" value="2.*pi" />\n')
fileW.write('    </define>\n')
fileW.write('  <materials>\n')
      
for indiceM in range(len(lmaterialNist)):
    fileW.write('      <material formula="'+str(lmaterialNist[indiceM][0])+'" name="'+str(lmaterialNist[indiceM][0])+'" >\n')
    fileW.write('        <D unit="g/cm3" value="'+str(lmaterialNist[indiceM][1])+'" />\n')
    type = lmaterialNist[indiceM][4]
    for indiceSubM in range(len(lmaterialNist[indiceM][5][0])):
        Z = lmaterialNist[indiceM][5][0][indiceSubM]
	
	
        indiceZ = listZNameDensityI[0].index(Z)
        thisname = listZNameDensityI[1][indiceZ]	
        fileW.write('        <'+type+' n="'+ str(lmaterialNist[indiceM][5][1][indiceSubM])+'" ref="'+str(thisname)+'"/>\n')
    fileW.write('      </material>\n')
       
for indiceM in range(len(lmaterial)):
    fileW.write('      <material formula="'+str(lmaterial[indiceM][0])+'" name="'+str(lmaterial[indiceM][0])+'" >\n')
    fileW.write('        <D unit="g/cm3" value="'+str(lmaterial[indiceM][1])+'" />\n')
    fileW.write('        <atom unit="g/mole" value="'+str(lmaterial[indiceM][3])+'" />\n')
    fileW.write('      </material>\n')
      
fileW.write('  </materials>\n')
fileW.write('</xml>\n')
fileW.close()
