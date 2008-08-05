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

from chimera.util.enum import Enum

Bitpix = Enum("char8", "uint16", "int16", "int32", "int64", "float32", "float64")

# this makes sense for non-SBIG cameras?
# how to handle multiple USB cameras? USB1, USBn...?
# remove LPT support? (only works for SBIG on 2.4.x Linux kernel.
Device = Enum ("USB",
               "USB1",
               "USB2",
               "LPT"
               "LPT1",
               "LPT2")

# keep this just as a way to force common names for the first two CCD?
# (most cameras won't have more than 2 CCDs anyway).
CCD = Enum ("IMAGING",
            "TRACKING")

# Special features parameters can be passed as ImageRequest
# parameters. The ICameraDriver.supports(feature) method can be used
# to ask if the current camera support a given feature (useful for
# interfaces, to decides when to display options to the user).

CameraFeature = Enum("TEMPERATURE_CONTROL",
                     "PROGRAMMABLE_GAIN",
                     "PROGRAMMABLE_OVERSCAN",
                     "PROGRAMMABLE_FAN",
                     "PROGRAMMABLE_LEDS",
                     "PROGRAMMABLE_BIAS_LEVEL")

class ICameraDriver(Interface):

    __config__ = {"device"            : Device.USB,
                  "readout_aborted" : True,
                  "temp_delta"      : 1.0,
                  "temp_setpoint"   : 10.0}

    #
    # device handling
    #
    
    def open(self, device):
        pass

    def close(self):
        pass

    def ping(self):
        pass

    #
    # exposure request and control
    #

    def isExposing(self):
        """Ask if camera is exposing right now.

        @return: The currently exposing ImageRequest if the camera is exposing, False otherwise.
        @rtype: bool or chimera.controllers.imageserver.imagerequest.ImageRequest
        """
        pass

    def expose(self, request):
        pass

    def abortExposure(self):
        pass

    #
    # temperature control
    #

    def startCooling(self, setpoint):
        pass

    def stopCooling(self):
        pass

    def isCooling(self):
        pass

    def getTemperature(self):
        pass

    def getSetPoint(self):
        pass

    def startFan(self, rate=None):
        pass

    def isFanning(self):
        pass


    #
    # geometry and readout
    #

    # for getCCDs, getBinnings and getADCs, the driver should returns a
    # list of Human readable strings, which could be later passed as a
    # ImageRequest and be recognized by the driver. Those strings can
    # be use as key to an internal hashmap.
    # example:
    # ADCs = {'12 bits': SomeInternalValueWhichMapsTo12BitsADC,
    #         '16 bits': SomeInternalValueWhichMapsTo16BitsADC}

    def getCCDs(self):
        pass

    def getBinnings(self):
        pass

    def getADCs(self):
        pass

    def getPhysicalSize(self, ccd=None):
        pass

    def getPixelSize(self, ccd=None):
        pass

    def getOverscanSize(self, ccd=None):
        pass

    #
    # special features support
    #
    
    def supports(self, feature=None):
        pass

    #
    # events
    #
    
    @event
    def exposeBegin (self, request):
        pass
    
    @event
    def exposeComplete (self, request):
        pass

    @event
    def readoutBegin (self, request):
        pass

    @event
    def readoutComplete (self, request):
        pass

    @event
    def abortComplete (self):
        pass

    @event
    def temperatureChange(self, newTemp, delta):
        pass
    
