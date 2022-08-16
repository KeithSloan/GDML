# GDML_Command_Line_Utils

This repository contains various GDML command line utilities and is a submodule for several other GDML related repositories

### extractVol.py

Extracts a volume or assembly from a gdml file and creates a directory which contains separate files for 

 * defines
 * materials
 * solids
 * structute
 * setup
 
 and a gdml file with includes for the above
 
 #### syntax
 
 python3 extract.py < parameter > < volume/assembly >  < directory_to_be_created >
  
### combineGDML.py

Combines a GDML with includes into a single GDML file

#### syntax

python3 combineGDML.py < input_file > < output_file >
  
### listVols.py

List the volumes and assemblies in a gdml file

#### syntax

python3 listVols < input_file >

### listSolids.py

List the solids in a gdml file

#### syntax

python3 listSolids.py < input_file >
  
