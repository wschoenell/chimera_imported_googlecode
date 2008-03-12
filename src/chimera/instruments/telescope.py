#! /usr/bin/python
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


from chimera.core.chimeraobject import ChimeraObject

from chimera.interfaces.telescope       import ITelescopeSlew, ITelescopeSync, ITelescopePark
from chimera.interfaces.telescopedriver import SlewRate

from chimera.core.lock import lock

from chimera.util.position import Position


__all__ = ["Telescope"]


class Telescope(ChimeraObject, ITelescopeSlew, ITelescopeSync, ITelescopePark):

    def __init__(self):
        ChimeraObject.__init__(self)
        
    def __start__(self):

        drv = self.getDriver()

        drv.parkComplete   += self.getProxy()._parkCompleteClbk
        drv.unparkComplete += self.getProxy()._unparkCompleteClbk
        drv.slewBegin      += self.getProxy()._slewBeginClbk
        drv.slewComplete   += self.getProxy()._slewCompleteClbk
        drv.syncComplete   += self.getProxy()._syncCompleteClbk
        drv.abortComplete  += self.getProxy()._abortCompleteClbk

    def __stop__(self):

        drv = self.getDriver()
        
        drv.parkComplete   -= self.getProxy()._parkCompleteClbk
        drv.unparkComplete -= self.getProxy()._unparkCompleteClbk
        drv.slewBegin      -= self.getProxy()._slewBeginClbk
        drv.slewComplete   -= self.getProxy()._slewCompleteClbk
        drv.syncComplete   -= self.getProxy()._syncCompleteClbk
        drv.abortComplete  -= self.getProxy()._abortCompleteClbk

    def _parkCompleteClbk (self):
        self.parkComplete()

    def _unparkCompleteClbk (self):
        self.unparkComplete()

    def _slewBeginClbk (self, target):
        if isinstance(target, tuple):
            target = Position.fromRaDec(*target)
        self.slewBegin(target)

    def _slewCompleteClbk (self, position):
        if isinstance(position, tuple):
            position = Position.fromRaDec(*position)
        self.slewComplete(position)

    def _abortCompleteClbk (self, position):
        if isinstance(position, tuple):
            position = Position.fromRaDec(*position)
        self.abortComplete()

    def _syncCompleteClbk (self, position):
        if isinstance(position, tuple):
            position = Position.fromRaDec(*position)
        self.syncComplete(position)

    @lock
    def getDriver(self, lazy=True):
        """
        Get a Proxy to the instrument driver. This function is necessary '
        cause Proxies cannot be shared among different threads.
        So, every time you need a driver Proxy you need to call this to
        get a Proxy to the current thread.
        """
        return self.getManager().getProxy(self['driver'], lazy=lazy)        
        

    def syncObject(self, name):
        return ITelescopeSync.syncObject(self, name)

    def syncRaDec(self, position):
         if not isinstance(position, Position):
             position = Position.fromRaDec(*position)
        
         drv = self.getDriver()
         drv.syncRaDec(position)
       
    def syncAzAlt(self, position):
        return ITelescopeSync.syncAzAlt(self, position)

    def slewToObject(self, name):
        return ITelescopeSlew.slewToObject(self, name)

    def slewToRaDec(self, position):
        # FIXME: validate limits?

        if not isinstance(position, Position):
            position = Position.fromRaDec(*position)
        
        drv = self.getDriver()
        drv.slewToRaDec(position)
       
        
    def slewToAzAlt(self, position):
        # FIXME: validate limits?        

        if not isinstance(position, Position):
            position = Position.fromAzAlt(*position)

        drv = self.getDriver()

        try:
            drv.slewToAzAlt(position)
        except Exception,e:
            self.log.exception("Houston")

    def abortSlew(self):
        drv = self.getDriver()
        if not self.isSlewing(): return
        return drv.abortSlew()

    def isSlewing(self):
        drv = self.getDriver()
        return drv.isSlewing()

    def moveEast(self, offset, rate=SlewRate.MAX):
        drv = self.getDriver()
        return drv.moveEast(offset, rate)

    def moveWest(self, offset, rate=SlewRate.MAX):
        drv = self.getDriver()
        return drv.moveWest(offset, rate)

    def moveNorth(self, offset, rate=SlewRate.MAX):
        drv = self.getDriver()
        return drv.moveNorth(offset, rate)

    def moveSouth(self, offset, rate=SlewRate.MAX):
        drv = self.getDriver()
        return drv.moveSouth(offset, rate)

    def getRa(self):
        drv = self.getDriver()
        return drv.getRa()

    def getDec(self):
        drv = self.getDriver()
        return drv.getDec()

    def getAz(self):
        drv = self.getDriver()
        return drv.getAz()

    def getAlt(self):
        drv = self.getDriver()
        return drv.getAlt()

    def getPositionRaDec(self):
        drv = self.getDriver()

        ret = drv.getPositionRaDec()

        if not isinstance(ret, Position):
            ret = Position.fromRaDec(*ret)
        return ret

    def getPositionAzAlt(self):
        drv = self.getDriver()

        ret = drv.getPositionAzAlt()

        if not isinstance(ret, Position):
            ret = Position.fromAzAlt(*ret)
        return ret

    def getTargetRaDec(self):
        drv = self.getDriver()

        ret = drv.getTargetRaDec()

        if not isinstance(ret, Position):
            ret = Position.fromRaDec(*ret)
        return ret

    def getTargetAzAlt(self):
        drv = self.getDriver()
        
        ret =  drv.getTargetAzAlt()

        if not isinstance(ret, Position):
            ret = Position.fromAzAlt(*ret)
        return ret

    def park(self):
        drv = self.getDriver()
        return drv.park()

    def unpark(self):
        drv = self.getDriver()
        return drv.unpark()

    def setParkPosition(self, position):
        drv = self.getDriver()
        return drv.setParkPosition(position)
