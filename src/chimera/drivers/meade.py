#! /usr/bin/python
# -*- coding: iso8859-1 -*-

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

import time
import serial
import signal
import threading
import logging

from chimera.core.lifecycle import BasicLifeCycle
from chimera.interfaces.telescope import ITelescopeDriver

from chimera.util.coord import Coord, Ra, Dec, Lat, Long, Point

class Meade (BasicLifeCycle, ITelescopeDriver):

    altazAlign = "A"
    polarAlign = "P"
    landAlign  = "L"

    alignModes = {"A": "altaz",
                  "P": "polar",
                  "L": "land"}



    def __init__(self, manager):

        BasicLifeCycle.__init__ (self, manager)

        self.tty = None
        self.alignMode = Meade.altazAlign
        self.abort = threading.Event ()
        self.slewing = False

        self._errorNo = 0
        self._errorString = ""

    # -- IBasicLifeCycle implementation --
    
    def init (self, config):

        self.config += config

        if not self.open ():
            return False

        return True

    def shutdown (self):

        if not self.close ():
            return False

        return True

    def main (self):
        pass


    # -- ITelescopeDriver implementation
        
    def _checkMeade (self):

        tmp = self.tty.timeout
        self.tty.timeout = 10

        self._write (":GVP#")

        name = self._readline ()

        self.tty.timeout = tmp

        if not name:
            return False
      
        if "LX200" in name:
            return True
        else:
            self.setError (-1, "Couldn't found a Meade telescope on %s." % self.device)
            return False

    def _autoAlign (self):

        self._write (":Aa#")

        while not self.tty.inWaiting ():
            time.sleep (1)

        # FIXME: bad LX200 behavious
        tmp = self._read (1)

        return True
            
    def open(self):

        self.tty = serial.Serial()
        self.device = self.config.device

        self.tty.port = self.device
        self.tty.timeout = self.config.timeout

        try:
            self.tty.open()

            if not self._checkMeade():
                logging.warning ("Couldn't found a Meade telescope on %s." %  self.config.device)
                return False

            if self.config.auto_align:
                self._autoAlign ()
            
            return True

        except serial.SerialException, e:
            self.setError (-1, str(e))
            logging.debug ("Error while opening %s. Exception follows..." % self.config.device)
            logging.exception ()
            return False
            
        except IOError,e:
            self.setError(e)
            logging.debug ("Error while opening %s. Exception follows..." % self.config.device)
            logging.exception ()
            return False

    def close(self):
        if self.tty.isOpen():
            self.tty.close()
            return True
        else:
            self.setError(-1, "Device not open")
            return False

    def getAlignMode(self):

        self._write(chr(0x06))

        self.alignMode = Meade.alignModes[self._read(1)]

        return self.alignMode

    def slewToRaDec(self, ra, dec):

        # FIXME: validate limits?

        target = Point(ra, dec)

        if not self.setRa(target.ra):
            return False
        
        if not self.setDec(target.dec):
            return False

        if not self._slew():
            return False

        return True

    def _slew(self):

        self.slewing = True
        self.abort.clear ()

        # slew
        self._write(':MS#')

        # to handle timeout
        start_time = time.time()

        err = self._readbool()
        
        if err:
            # check error message
            msg = self._readline()
            self.setError(-1, msg[:-1])
            self.slewing = False
            return False

        # slew possible
        target = self.getTarget()

        while True:

            # check slew abort event
            if self.abort.isSet ():
                self.setError (-1, "Slew aborted")
                self.slewing = False                
                return False

            # check timeout
            if time.time () >= (start_time + self.config.max_slew_time):
                self.abortSlew ()
                self.setError (-1, "Slew aborted. Max slew time reached.")
                self.slewing = False
                return False

            position = self.getPosition()

            if target.near (position, "00 01 00"):
                time.sleep (self.config.stabilization_time)
                self.slewing = False
                return True
            
            time.sleep (self.config.slew_idle_time)


    def slewToAltAz(self, alt, az):
        pass

    def abortSlew(self):

        if not self.slewing:
            return False

        err = self._write (":MQ")

        if err:
            self.setError (-1, "Error aborting.")
            return False

        self.abort.set()

    def moveEast(self, duration):
        pass

    def moveWest(self, duration):
        pass

    def moveNorth(self, duration):
        pass

    def moveSouth(self, duration):
        pass

    def getRa(self):

        self._write(":GR#")
        ret = self._readline()

        return Ra(ret[:-1])

    def getDec(self):
        self._write(":GD#")
        ret = self._readline()

        ret = ret.replace('\xdf', ':')

        return Dec(ret[:-1])

    def getPosition(self):
        return Point(self.getRa(), self.getDec())

    def getTarget(self):
        return Point(self.getTargetRa(), self.getTargetDec())     

    def getTargetRa(self):

        self._write(":Gr#")
        ret = self._readline()

        return Ra(ret[:-1])

    def getTargetDec(self):
        self._write(":Gd#")
        ret = self._readline()

        ret = ret.replace('\xdf', ':')

        return Dec(ret[:-1])

    def getAz(self):
        self._write(":GZ#")
        ret = self._readline()
        ret = ret.replace('\xdf', ':')

        return Coord(ret[:-1])

    def getAlt(self):
        self._write(":GA#")
        ret = self._readline()
        ret = ret.replace('\xdf', ':')

        return Coord(ret[:-1])

    def getLat(self):
        self._write(":Gt#")
        ret = self._readline()
        ret = ret.replace('\xdf', ':')

        return Lat(ret[:-1])

    def getLong(self):
        self._write(":Gg#")
        ret = self._readline()
        ret = ret.replace('\xdf', ':')

        return Long(ret[:-1])

    def getDate(self):
        self._write(":GC#")
        ret = self._readline()
        return ret[:-1]

    def getTime(self):
        self._write(":GL#")
        ret = self._readline()
        return ret[:-1]
                
    def getSiderealTime(self):
        self._write(":GS#")
        ret = self._readline()
        return ret[:-1]

    def getUTCOffset(self):
        self._write(":GG#")
        ret = self._readline()
        return ret[:-1]

    def setRa(self, ra):
        self._write(":Sr %s#" % ra.hor(":"))

        ret = self._readbool()

        if not ret:
            self.setError(-1, "Invalid ra %s" % ra)
            return False

        return True

    def setDec(self, dec):
        self._write(":Sd %s#" % dec.sexagesimal("*", ":"))

        ret = self._readbool()

        if not ret:
            self.setError(-1, "Invalid dec %s" % dec)
            return False

        return True

    # low-level 

    def _read(self, n = 1):
        if not self.tty.isOpen():
            self.setError(-1, "Device not open")
            return ""

        self.tty.flushInput()

        return self.tty.read(n)

    def _readline(self, eol='#'):
        if not self.tty.isOpen():
            self.setError(-1, "Device not open")
            return ""
        
        return self.tty.readline(None, eol)

    def _readbool(self, n = 1):
        ret = int(self._read(1))

        if not ret:
            return False

        return True

    def _write(self, data):
        if not self.tty.isOpen():
            self.setError(-1, "Device not open")
            return ""

        self.tty.flushOutput()
        
        return self.tty.write(data)


    def setError(self, errorNo, errorString):
        self._errorNo = errorNo
        self._errorString = errorString

    def getError(self):
        if self._errorNo:
            ret = (self._errorNo, self._errorString)
        else:
            ret = 0

        self._errorNo = 0
        self._errorString = ""

        return ret

# if __name__ == '__main__':

#     import sys

#     m = Meade()

#     if not m.open('/dev/ttyS0'):
#         print "Error (%s)." % m.getError ()[1]
#         sys.exit (2)

#     #m._autoAlign ()

#     def printInfo():
#         print "align mode:", m.getAlignMode()

#         print "ra :", m.getRa()
#         print "dec:", m.getDec()

#         print "az :", m.getAz()
#         print "alt:", m.getAlt()
        
#         print "lat :", m.getLat()
#         print "long:", m.getLong()
        
#         print "date:" , m.getDate()
#         print "time:" , m.getTime()
#         print "to utc:", m.getUTCOffset()
#         print "ts:", m.getSiderealTime()

#     def printCoord():
#         print m.getRa(), m.getDec()

#     printInfo()

#     if not m.slewToRaDec ("12 00 00", "-40 00 00"):
#         print m.getError ()
        
#     #printInfo()

                   
#     #m._write (":Aa#")
#     #print
#     #printInfo()

#     #if not m.slewToRaDec('20:00:00', '-20:00:00'):
#     #    print m.getError()[1]

    
