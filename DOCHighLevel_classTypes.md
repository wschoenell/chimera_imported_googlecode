#The types of classes you define in chimera

# Introduction #

This document describes the types of chimera classes.  There shall be one document for each type of class.

There are five divisions:

  1. util
  1. controllers
  1. instruments
  1. scripts
  1. interfaces
  1. core

An overview of chimera classes can be found in http://chimera.sourceforge.net/getting-started/

Install instructions in http://chimera.sourceforge.net/

# Details #

  1. util - these classes will be used by chimera and its objects, they are not chimera objects but they do use chimera classes.
  1. controllers - these are classes that control other chimera classes.  For instance, the autofocus class is a controller.  It controls instruments (camera and telescope) and takes decisions based on what it sees on the instruments.  It does not actually control any instrument directly.
  1. instruments - these classes control hardware.  Examples are, camera, telescope, focuser, dome, etc.  Here one needs to do real action on the hardware.
  1. scripts - used to control instruments and controllers from the command line
  1. interfaces - they describe the methods of a class that need to be exposed to other chimera classes, the methods defined in interfaces are empty, they simply show what attributes the exposed methods have
  1. core - the communications classes based on pyro