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

import logging
import time
import socket
import SocketServer
import select
from types import TupleType, ListType, StringType
import copy

import Pyro.core

from chimera.core.location import Location
from chimera.core.threads import getThreadPool

class RegisterEntry (Pyro.core.ObjBase):

    def __init__ (self):

        Pyro.core.ObjBase.__init__ (self)

        self._location = None
        self._instance = None
        self._uri      = None
        self._created  = time.time ()

    location = property (lambda self: self._location, lambda self, value: setattr (self, '_location', value))
    instance = property (lambda self: self._instance, lambda self, value: setattr (self, '_instance', value))
    uri      = property (lambda self: self._uri,      lambda self, value: setattr (self, '_uri', value))
    created  = property (lambda self: self._created)

    def __str__ (self):
        return "<%s %s at %s>" % (self.location, self.instance, self.uri)


class Register (Pyro.core.ObjBase):

    def __init__(self):

        Pyro.core.ObjBase.__init__ (self)

        self.objects = {}

        # the underlying Pyro daemon used to register instances
        Pyro.core.initServer (banner=False)
        self.daemon = Pyro.core.Daemon ()

    def _getDaemon (self):
        return self.daemon

    def register(self, item, instance):

        location = self._validLocation (item)

        if not location:
            return False

        if location in self:
            return False

        entry = RegisterEntry ()
        entry.location = location
        entry.instance = instance

        # connect instance to the daemon
        entry.uri = self.daemon.connect (instance)

        self.objects[location] = entry

        return True

    def unregister(self, item):

        location = self._validLocation (item)

        if not location:
            return False

        if not location in self:
            return False

        ret = self.get(location)

        del self.objects[ret.location]

        return True

    def __contains__(self, item):

        location = self._validLocation (item)

        if not location:
            return False

        ret = filter(lambda x: x == location, self.keys())

        if ret:
            return True
        else:
            return False

    def __len__(self):
        return self.objects.__len__()

    def __iter__(self):
        return self.objects.__iter__()

    def items(self):
        return self.objects.items()

    def keys(self):
        return self.objects.keys()

    def values(self):
        return self.objects.values()

    def __getitem__(self, item):

        ret = self.get(item)

        if not ret:
            raise KeyError
        else:
            return ret

    def get (self, item):

        location = self._validLocation (item)

        if not location:
            return False

        try:
            index = int(location.name)
            return self._getByIndex(location, index)
        except ValueError:
            # not a numbered instance
            pass

        return self._get (location)

    def getByClass(self, cls):
        
        entries = filter(lambda location: location.cls == cls, self.keys())

        ret = []
        for entry in entries:
            ret.append (self.get (entry))

        ret.sort (key=lambda entry: entry.created)

        return ret

 
    def _get (self, item):

        location = self._validLocation (item)

        if not location:
            return False

        if location in self:
            ret = filter(lambda x: x == location, self.keys())
            return self.objects[ret[0]]
        else:
            return False


    def _getByIndex(self, item, index):

        location = self._validLocation (item)

        if not location:
            return False

        insts = self.getByClass(location.cls)

        if insts:
            try:
                return self.objects[insts[index].location]
            except IndexError:
                return False
        else:
            return False

    def _validLocation (self, item):
       
        ret = item

        if not isinstance (item, Location):
            ret = Location (item)

        if not ret.isValid():
            ret = False

        return ret

REGISTER_COMMAND_LOCATION = "chimera_register_location"
REGISTER_COMMAND_SHUTDOWN = "chimera_register_shutdown"

REGISTER_DEFAULT_HOST = '<broadcast>'
REGISTER_DEFAULT_PORT = 9876

class RegisterBroadcastServer(SocketServer.ThreadingUDPServer):

    def __init__(self, addr, requestHandler, reuse = False):

        self.register_uri = ''

        (location, port) = addr

        try:
            SocketServer.ThreadingUDPServer.allow_reuse_address = reuse
            SocketServer.ThreadingUDPServer.__init__(self, (location,port), requestHandler)
        except socket.error:
            raise

    def setRegisterURI (self, uri):
        self.register_uri = uri

    def getRegisterURI (self):
        return self.register_uri


class RegisterRequestHandler(SocketServer.DatagramRequestHandler):
    def handle (self):
        cmd = self.request[0]

        if cmd == REGISTER_COMMAND_LOCATION:
            self.request[1].sendto(self.server.getRegisterURI(), 0, self.client_address)
            return

        if cmd == REGISTER_COMMAND_SHUTDOWN:
            self.server.shutdown = 1
            return

def RegisterLocator (addr = (REGISTER_DEFAULT_HOST, REGISTER_DEFAULT_PORT), timeout = 1):

    sk = socket.socket (socket.AF_INET, socket.SOCK_DGRAM)

    if '<broadcast>' in addr[0]:
        sk.setsockopt (socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    sk.sendto (REGISTER_COMMAND_LOCATION, 0, (addr))

    ins, out, errs = select.select ([sk], [], [sk], timeout)

    if not ins:
        return False

    for s in ins:
        reply, recvfrom = s.recvfrom (1000)
        return reply

    return False

def RegisterFactory (addr = (REGISTER_DEFAULT_HOST, REGISTER_DEFAULT_PORT)):

    server = RegisterBroadcastServer (addr, RegisterRequestHandler, reuse=True)

    register = Register ()

    daemon = register.getDaemon ()
    daemon.connect (register)

    getThreadPool().queueTask (register.getDaemon().requestLoop)

    server.setRegisterURI (str(register.getProxy().URI))

    getThreadPool().queueTask (server.serve_forever)

    return register

