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

import sys
import os.path
import traceback
import logging
from types import StringType, TupleType

from chimera.core.register import RegisterLocator, RegisterFactory, RegisterURI, REGISTER_DEFAULT_HOST, REGISTER_DEFAULT_PORT
from chimera.core.proxy import Proxy
from chimera.core.location import Location
from chimera.core.threads import getThreadPool

import Pyro.core

# manager singleton
# FIXME: better implementation needed

__manager_instance = None

def Manager (*args, **kwargs):

    global __manager_instance
    
    if __manager_instance is None:
        __manager_instance = _Manager (*args, **kwargs)

    return __manager_instance


class _Manager (object):

    includePath = {}
    registers = []
    _objects = {}
    cache = { }
    daemon = None

    def __init__(self, addr = None, add_system_path = True):

        logging.info("Starting manager.")

        self.includePath = {"instrument": [],
                             "controller": [],
                             "driver"    : []}

        if add_system_path:
            self._addSystemPath ()

        # get our registry
        if not addr:
            addr = (REGISTER_DEFAULT_HOST, REGISTER_DEFAULT_PORT)

        self._addr = addr

        register = RegisterFactory (self._getDaemon(), self._addr)
        
        if register == False:
            raise SystemError ("Couldn't start manager without a valid register.")

        self._addRegister (register)

    def shutdown(self):
        pass

    def _getDaemon (self):

        if not self.daemon:
            Pyro.core.initServer (banner=0)
            self.daemon = Pyro.core.Daemon ()
            getThreadPool().queueTask (self.daemon.requestLoop)            

        return self.daemon
    
    def _addRegister (self, register):
        # FIXME: resolve names?

        # check if any other register serve this host/port pair
        ret = filter (lambda reg: reg._serveFor (register.getAddress()), self.registers)
        if ret:
            logging.debug ("There is other register for %s:%d already. You cannot have two registers for the same host/port pair." % register.getAddress())
            return False

        self.registers.append(register)
    
        return True

    def _getRegister (self, addr=None):

        # UGLY HACK
        if not addr:
            addr = self._addr

        ret = filter (lambda reg: reg._serveFor (addr), self.registers)

        if ret:
            return ret[0]

        # looks for register using RegisterLocator
        reg = RegisterLocator (addr, timeout = 10)

        if not reg:
            logging.warning ("Couldn't found a register at %s:%d." % addr)
            return False

        self._addRegister (reg)

        return reg

    def _addSystemPath (self):
        
        prefix = os.path.realpath(os.path.join(os.path.abspath(__file__),
                                               '../../'))
        
        self.appendPath ("instrument", os.path.join(prefix, 'instruments'))
        self.appendPath ("controller", os.path.join(prefix, 'controllers'))
        self.appendPath ("driver", os.path.join(prefix, 'drivers'))

    def appendPath(self, kind, path):

        if not os.path.isabs(path):
            path = os.path.abspath(path)
            
        logging.debug("Adding %s to %s include path." % (path, kind))

        self.includePath[kind].append(path)

    def _getClass(self, name, kind):
        """
        Based on this recipe
        http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52241
        by Jorgen Hermann
        """

        # TODO: - add a reload method

        if name in self.cache:
            return self.cache[name]

        try:
            logging.debug("Looking for module %s." % name.lower())

            # adjust sys.path accordingly to kind
            tmpSysPath = sys.path
            sys.path = self.includePath[kind] + sys.path

            module = __import__(name.lower(), globals(), locals(), [name])

            # turns sys.path back
            sys.path = tmpSysPath

            if not name in vars(module).keys():
                logging.error("Module found but there are no class named %s on module %s (%s)." %
                              (name, name.lower(), module.__file__))
                return False

            self.cache[name] = vars(module)[name]

            logging.debug("Module %s found (%s)" % (name.lower(),
                                                    module.__file__))

            return self.cache[name]

        except Exception, e:

            # Python trick: An ImportError exception catched here
            # could came from both the __import__ above or from the
            # module imported by the __import__ above... So, we need a
            # way to know the difference between those exceptions.  A
            # simple (reliable?) way is to use the lenght of the
            # exception traceback as a indicator If the traceback had
            # only 1 entry, the exceptions comes from the __import__
            # above, more than one the exception comes from the
            # imported module

            tb_size = len(traceback.extract_tb(sys.exc_info()[2]))

            if tb_size == 1:

                if type (e) == ImportError:
                    logging.error("Couldn't found module %s." % name)

                else:
                    logging.error("Module %s found but couldn't be loaded. Exception follows..." % name)
                    logging.exception("")
                    
            else:
                logging.error("Module %s found but couldn't be loaded. Exception follows..." % name)
                logging.exception("")

            return False

    
    def get(self, location, addr, proxy = True):

        if type(location) == StringType:
            location = Location(location)

        if not addr:
            addr = (REGISTER_DEFAULT_HOST, REGISTER_DEFAULT_PORT)

        register = self._getRegister(addr)

        if not register:
            return None

        entry = register.get(location)

        if not entry:
            # not found on register, try to add
            if not self.init (location):
                entry = None
            else:
                entry = register.get(location)

        if entry != None:
            if proxy:
                return Pyro.core.getProxyForURI (entry.uri)
            else:
                return self._objects[entry.location]
        else:
            return None

    def add(self, location):

        if type(location) == StringType:
            location = Location(location)

        # get the class
        cls = self._getClass(location._class, location.namespace)

        if not cls:
            return False

        # run object __init__
        # it runs on the same thread, so be a good boy
        # and don't block manager's thread
        try:
            obj = cls()

            # connect to the daemon
            uri = self._getDaemon().connect (obj)
            self._getRegister().register(location, uri)

            self._objects[location] = obj
            
            return True
        except Exception:
            logging.exception("Error in %s __init__. Exception follows..." % location)
            return False
    
    def remove(self, location):

        if type(location) == StringType:
            location = Location(location)
        
        return self._getRegister().unregister(location)

    def start(self, location):

        if type(location) == StringType:
            location = Location(location)

        logging.debug ("Trying to start module %s." % location)
        
        if location not in self._getRegister():
            logging.debug ("Module %s was not found... will try to add it..." % location)
            
            if not self.add(location):
                logging.debug ("Couldn't add module %s... giving up..." % location)
                return False

        logging.debug("Starting %s." % location)

        # run object init
        # it runs on the same thread, so be a good boy and don't block manager's thread
        entry = self._getRegister()[location]

        try:        
            ret = self._objects[location].__start__()

            if not ret:
                logging.warning ("%s __start__ returned an error. Removing %s from register." % (location, location))
                return False
        except Exception:
            logging.exception("Error running %s __start__ method. Exception follows..." % location)
            return False

        try:
            # FIXME: thread exception handling
            # ok, now schedule object main in a new thread
            getThreadPool().queueTask(self._objects[location].__main__)
        except Exception:
            logging.exception("Error running %s __main__ method. Exception follows..." % location)
            return False

        return True

    def stop(self, location):

        if type(location) == StringType:
            location = Location(location)

        if location not in self._getRegister():
            return False

        try:
            logging.debug("Stopping %s." % location)

            # run object __stop__ method
            # again: runs on the same thread, so don't block it
            self._objects[location].__stop__()
            self.remove(location)
            return True

        except Exception:
            logging.exception("Error running %s __stop__ method. Exception follows..." % location)
            return False

    # helpers

#     def getLocation(self, obj):
#         # FIXME: buggy by definition
#         kinds = [self._controllers, self._instruments, self._drivers]

#         def _get (kind):
#             return kind.getLocation (obj)

#         ret = map(_get, kinds)

#         for item in ret:
#             if item != None:
#                 return item

#         return None
            

    # instruments

    def getInstrument(self, location, addr = None, proxy = True):
        return self.get('/instrument/'+location, addr, proxy)
    
    def addInstrument(self, location):
        return self.add('/instrument/'+location)

    def removeInstrument(self, location):
        return self.remove('/instrument/'+location)

    def startInstrument(self, location):
        return self.start('/instrument/'+location)

    def stopInstrument(self, location):
        return self.stop('/instrument/'+location)

    # controllers
    
    def getController(self, location, host = None, proxy = True):
        return self.get('/controller/'+location, host, proxy)

    def addController(self, location):
        return self.add('/controller/'+location)

    def removeController(self, location):
        return self.remove('/controller/'+location)

    def startController(self, location):
        return self.start('/controller/'+location)

    def stopController(self, location):
        return self.stop('/controller/'+location)

    # drivers

    def getDriver(self, location, host = None, proxy = True):
        return self.get('/driver/'+location, host, proxy)

    def addDriver(self, location):
        return self.add('/driver/'+location)

    def removeDriver(self, location):
        return self.remove('/driver/'+location)

    def startDriver(self, location):
        return self.start('/driver/'+location)

    def stopDriver(self, location):
        return self.stop('/driver/'+location)
