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
def doXMLfile(nameFile, listElem, listMaterialSingle, listMaterialMulti):
    suffixDef = "GF_"

    fileW = open(nameFile, 'w')
    fileW.write('<xml>\n')
    fileW.write('  <define>\n')
    fileW.write('    <constant name="HALFPI" value="pi/2." />\n')
    fileW.write('    <constant name="PI" value="1.*pi" />\n')
    fileW.write('    <constant name="TWOPI" value="2.*pi" />\n')
    fileW.write('    </define>\n')


    fileW.write('  <materials>\n')

    for indiceM in range(len(listElem)):
        fileW.write('      <element Z="'+str(listElem[indiceM][1]))
	fileW.write('" formula="' +str(listElem[indiceM][0].replace('G4_','')))
	fileW.write('" name="'+str(listElem[indiceM][0].replace('G4_',''))+'_element" >\n')
        fileW.write('        <atom value="'+str(listElem[indiceM][3])+'" />\n')
        fileW.write('      </element>\n')
    

	
    listeZ = []
    for indiceM in range(len(listElem)):
    	listeZ.append(listElem[indiceM][1])
    print listeZ
	
    for indiceM in range(len(listMaterialMulti)):
        name = listMaterialMulti[indiceM][0].replace('G4_',suffixDef)
        fileW.write('      <material formula="'+str(name)+'" name="'+str(name)+'" >\n')
        fileW.write('        <D unit="g/cm3" value="'+str(listMaterialMulti[indiceM][1])+'" />\n')
        type = lmaterialNist[indiceM][4]
        for indiceSubM in range(len(listMaterialMulti[indiceM][5][0])):
            Z = listMaterialMulti[indiceM][5][0][indiceSubM]	
            indiceZ = listeZ.index(Z)
            thisname = listElem[indiceZ][0].replace('G4_','')+'_element'	
            fileW.write('        <'+type+' n="'+ str(listMaterialMulti[indiceM][5][1][indiceSubM])+'" ref="'+str(thisname)+'"/>\n')
        fileW.write('      </material>\n')	
	


    for indiceM in range(len(listMaterialSingle)):
        name = listMaterialSingle[indiceM][0].replace('G4_','')
        fileW.write('      <material formula="'+str(name)+'" name="'+suffixDef+str(name)+'" >\n')
        fileW.write('        <D unit="g/cm3" value="'+str(listMaterialSingle[indiceM][2])+'" />\n')
        fileW.write('        <composite n="1" ref="'+str(name)+'_element"/>\n')
        fileW.write('      </material>\n')

      
    fileW.write('  </materials>\n')
    fileW.write('</xml>\n')
    fileW.close()




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


lmaterialNist = loadFileNcomp('nist.dat')

doXMLfile("dataBaseSingleElementsl.xml", lmaterial, lmaterial, [])
doXMLfile("dataBaseMaterialNist.xml", lmaterial, [], lmaterialNist)
doXMLfile("dataBaseNistAndSingleElementsl.xml", lmaterial, lmaterial, lmaterialNist)

