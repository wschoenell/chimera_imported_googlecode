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


import threading
import os
import time


from chimera.core.chimeraobject import ChimeraObject
from chimera.interfaces.camerang import ICameraExpose, ICameraTemperature

from chimera.controllers.imageserver.constants import SHUTTER_LEAVE

from chimera.core.exceptions import OptionConversionException
from chimera.core.exceptions import ChimeraValueError
from chimera.core.exceptions import ChimeraException

from chimera.core.lock import lock


class CameraNG (ChimeraObject, ICameraExpose, ICameraTemperature):

    def __init__(self):
        ChimeraObject.__init__(self)

        self.abort = threading.Event()
        self.abort.clear()

    def getDriver(self):
        """
        Get a Proxy to the instrument driver. This function is necessary '
        cause Proxies cannot be shared among different threads.
        So, every time you need a driver Proxy you need to call this to
        get a Proxy to the current thread.
        """
        return self.getManager().getProxy(self['driver'], lazy=True)        
        
    def __start__ (self):

        drv = self.getDriver()

        # connect callbacks to driver events
        drv.exposeBegin       += self.getProxy()._exposeBeginDrvClbk        
        drv.exposeComplete    += self.getProxy()._exposeCompleteDrvClbk
        drv.readoutBegin      += self.getProxy()._readoutBeginDrvClbk
        drv.readoutComplete   += self.getProxy()._readoutCompleteDrvClbk        
        drv.abortComplete     += self.getProxy()._abortDrvClbk
        drv.temperatureChange += self.getProxy()._tempChangeDrvClbk

        return True

    def __stop__ (self):
        
        if self.isExposing():
            self.abortExposure(False)
            while self.isExposing():
                time.sleep(1)
        
        # disconnect our callbacks
        drv = self.getDriver()

        drv.exposeBegin       -= self.getProxy()._exposeBeginDrvClbk        
        drv.exposeComplete    -= self.getProxy()._exposeCompleteDrvClbk
        drv.readoutBegin      -= self.getProxy()._readoutBeginDrvClbk
        drv.readoutComplete   -= self.getProxy()._readoutCompleteDrvClbk        
        drv.abortComplete     -= self.getProxy()._abortDrvClbk
        drv.temperatureChange -= self.getProxy()._tempChangeDrvClbk

    def _exposeBeginDrvClbk (self, exp_time):
        self.exposeBegin(exp_time)
    
    def _exposeCompleteDrvClbk (self):
        self.exposeComplete()

    def _readoutBeginDrvClbk (self, filename):
        self.readoutBegin(filename)
    
    def _readoutCompleteDrvClbk (self, filename):
        self.readoutComplete(filename)

    def _abortDrvClbk (self):
        self.abortComplete()
    
    def _tempChangeDrvClbk (self, temp, delta):
        self.temperatureChange(temp, delta)

    @lock
    def expose (self, shepherd):
        """
        Unlike the old expose request, this one is for a single frame only so that 
        reductions can start sooner.
        
        @param shepherd: The imageserver shepherd
        @type shepherd: chimera.controllers.imageserver.shepherd.Shepherd 
        """

        # clear abort setting
        self.abort.clear()

        # config driver
        drv = self.getDriver()
        
        try:
            drv.expose(shepherd)
            return True
        except:
            return False
            pass
        
    def abortExposure (self, readout=True):
        drv = self.getDriver()
        drv.abortExposure(readout = True)

        return True
    
    def isExposing (self):
        drv = self.getDriver()
        return drv.isExposing()

    @lock
    def startCooling (self, tempC):
        drv = self.getDriver()
        
        drv += {"temp_setpoint": tempC}

        drv.startCooling()
        return True

    @lock
    def stopCooling (self):
        drv = self.getDriver()
        drv.stopCooling()
        return True

    def isCooling (self):
        drv = self.getDriver()
        return drv.isCooling()

    def getTemperature(self):
        drv = self.getDriver()
        return drv.getTemperature()

    def getSetpoint(self):
        drv = self.getDriver()
        return drv.getSetpoint()
