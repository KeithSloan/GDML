from setuptools import setup
#from pygears import __version__
__version__ = '0.1'

import os

def mysetup(requires) :
   setup(name='FreeCad_GDML_Workbench',
      version=str(__version__),
      packages=['freecad','lxml']
      maintainer="keithsloan52",
      maintainer_email="keith@sloan-home.co.uk",
      url="https://github.com/KeithSloan/FreeCAD_GDML_Workbench",
      description="GDML Workbench for FreeCAD",
      install_requires=[requires],
      include_package_data=True
      include_package_data=True)

# Still not clear if under linux one can just install lxml with pip
# or sudo apt-get install python3-lxml

mysetup('lxml')
#import os
#if 'posix' in os.name:
#    mysetup('lxml')
#
#else:
#    mysetup('python3-lxml')

