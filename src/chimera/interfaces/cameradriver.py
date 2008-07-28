#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

# chimera - observatory automation system
# Copyright (C) 2006-2007  P. Henrique Silva <henrique@astro.ufsc.br>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


from chimera.core.interface import Interface
from chimera.core.event import event

from chimera.interfaces.camera import Shutter, Binning, Window

from chimera.util.enum import Enum


Bitpix = Enum("char8", "uint16", "int16", "int32", "int64", "float32", "float64")

Device = Enum ("USB",
               "USB1",
               "USB2",
               "LPT"
               "LPT1",
               "LPT2")

CCD = Enum ("IMAGING",
            "TRACKING")


class ICameraDriver(Interface):

    # config
    __config__ = {"device"         : Device.USB,
                  "ccd"          : CCD.IMAGING,
                  
                  "temp_setpoint"    : 20.0,
                  "temp_delta"       : 1.0,

                  "camera_model"    : "Fake camera Inc.",
                  "ccd_model"       : "KAF XYZ 10",
                  "ccd_dimension_x" : 100,  # pixel
                  "ccd_dimension_y" : 100,  # pixel
                  "ccd_pixel_size_x": 10.0, # micrometer (without binning factors)
                  "ccd_pixel_size_y": 10.0  # micrometer (without binning factors)
                  }
                  
    # methods

    def open(self, device):
        pass

    def close(self):
        pass

    def ping(self):
        pass

    def isExposing(self):
        """
        @return:   Return the currently exposing shepherd, or false
        @rtype:    boolean or chimera.controllers.imageserver.shepherd.Shepherd
        """
        pass

    def expose(self, shepherd):
        pass

    def getBinnings(self):
        """Return the allowed binning settings for this camera
        
        @return: Dictionary with the keys being the English binning description (caption), and 
                 the values being a device-specific value needed to activate the described binning
        @rtype: dictionary
        """
        return {'1x1': 0}
    
    def getDeviceSize(self):
        return (0,0)

    def abortExposure(self, readout = False):
        pass

    def startCooling(self):
        pass

    def stopCooling(self):
        pass

    def isCooling(self):
        pass

    def getTemperature(self):
        pass

    def getSetpoint(self):
        pass

    # events
    @event
    def exposeBegin (self, exp_time):
        pass
    
    @event
    def exposeComplete (self):
        pass

    @event
    def readoutBegin (self, filename):
        pass

    @event
    def readoutComplete (self, filename):
        pass

    @event
    def abortComplete (self):
        pass

    @event
    def temperatureChange(self, newTemp, delta):
        pass
    
