from setuptools import setup
#from pygears import __version__
__version__ = '0.1'

setup(name='FreeCad_GDML_Workbench',
      version=str(__version__),
      packages=['freecad','lxml']
      #,
      #          'freecad.gears',
      #  		'pygears'],
      maintainer="keithsloan52",
      maintainer_email="keith@sloan-home.co.uk",
      url="https://github.com/KeithSloan/FreeCAD_GDML_Workbench",
      description="GDML Workbench for FreeCAD",
      install_requires=['lxml'],
      include_package_data=True
include_package_data=True)
