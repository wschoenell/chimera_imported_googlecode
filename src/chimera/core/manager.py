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
from types import StringType

from chimera.core.register import RegisterLocator, RegisterFactory
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

    def __init__(self, add_system_path = True):
        logging.info("Starting manager.")

        self._includePath = {"instrument": [],
                             "controller": [],
                             "driver"    : []}

        if add_system_path:
            self._addSystemPath ()

        self._cache = { }

        register_uri = RegisterLocator ()

        if register_uri:
            Pyro.core.initClient (banner=0)
            self.register = Pyro.core.getProxyForURI (register_uri)
        else:
            self.register = RegisterFactory ()

    def shutdown(self):
        pass

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

        self._includePath[kind].append(path)

    def _getClass(self, name, kind):
        """
        Based on this recipe
        http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52241
        by Jorgen Hermann
        """

        # TODO: - add a reload method

        if name in self._cache:
            return self._cache[name]

        try:
            logging.debug("Looking for module %s." % name.lower())

            # adjust sys.path accordingly to kind
            tmpSysPath = sys.path
            sys.path = self._includePath[kind] + sys.path

            module = __import__(name.lower(), globals(), locals(), [name])

            # turns sys.path back
            sys.path = tmpSysPath

            if not name in vars(module).keys():
                logging.error("Module found but there are no class named %s on module %s (%s)." %
                              (name, name.lower(), module.__file__))
                return False

            self._cache[name] = vars(module)[name]

            logging.debug("Module %s found (%s)" % (name.lower(),
                                                    module.__file__))

            return self._cache[name]

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

    
    def get(self, location, proxy = True):

        if type(location) == StringType:
            location = Location(location)

        entry = self.register.get(location)

        if not entry:
            # not found on register, try to add
            if not self.init (location):
                entry = None
            else:
                entry = self.register.get(location)

        if entry != None:
            if proxy:
                return Pyro.core.getProxyForURI (entry.uri)
            else:
                return entry.instance
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
            return self.register.register(location, obj)
                        
        except Exception:
            logging.exception("Error in %s __init__. Exception follows..." % location)
            return False
    
    def remove(self, location):

        if type(location) == StringType:
            location = Location(location)
        
        return self.register.unregister(location)

    def init(self, location):

        if type(location) == StringType:
            location = Location(location)
        
        if location not in self.register:
            if not self.add(location):
                return False

        logging.debug("Starting %s." % location)

        # run object init
        # it runs on the same thread, so be a good boy and don't block manager's thread
        entry = self.register[location]

        try:        
            ret = entry.instance.__start__()

            if not ret:
                logging.warning ("%s __start__ returned an error. Removing %s from register." % (location, location))
                return False
        except Exception:
            logging.exception("Error running %s __start__ method. Exception follows..." % location)
            return False

        try:
            # FIXME: thread exception handling
            # ok, now schedule object main in a new thread
            getThreadPool().queueTask(entry.instance.__main__)
        except Exception:
            logging.exception("Error running %s %s __main__ method. Exception follows..." % location)
            return False

        return True

    def shutdown(self, location):

        if type(location) == StringType:
            location = Location(location)

        if location not in self.register:
            return False

        try:
            logging.debug("Stopping %s." % location)

            # run object __stop__ method
            # again: runs on the same thread, so don't block it
            self.register[location].instance.__stop__()
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

    def getInstrument(self, location, proxy = True):
        return self.get('/instrument/'+location, proxy)
    
    def addInstrument(self, location):
        return self.add('/instrument/'+location)

    def removeInstrument(self, location):
        return self.remove('/instrument/'+location)

    def initInstrument(self, location):
        return self.init('/instrument/'+location)

    def shutdownInstrument(self, location):
        return self.shutdown('/instrument/'+location)

    # controllers
    
    def getController(self, location, proxy = True):
        return self.get('/controller/'+location, proxy)

    def addController(self, location):
        return self.add('/controller/'+location)

    def removeController(self, location):
        return self.remove('/controller/'+location)

    def initController(self, location):
        return self.init('/controller/'+location)

    def shutdownController(self, location):
        return self.shutdown('/controller/'+location)

    # drivers

    def getDriver(self, location, proxy = True):
        return self.get('/driver/'+location, proxy)

    def addDriver(self, location):
        return self.add('/driver/'+location)

    def removeDriver(self, location):
        return self.remove('/driver/'+location)

    def initDriver(self, location):
        return self.init('/driver/'+location)

    def shutdownDriver(self, location):
        return self.shutdown('/driver/'+location)
