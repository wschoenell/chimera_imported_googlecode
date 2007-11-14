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

class RegisterEntry (object):

    def __init__ (self):

        self._location = None
        self._created  = time.time ()
        self._uri      = None        

    location = property (lambda self: self._location, lambda self, value: setattr (self, '_location', value))
    created  = property (lambda self: self._created)
    uri      = property (lambda self: self._uri,      lambda self, value: setattr (self, '_uri', value))
    
    def __str__ (self):
        return "<%s at %s>" % (self.location, self.uri)


class Register (Pyro.core.ObjBase):

    def __init__(self, addr):

        Pyro.core.ObjBase.__init__ (self)        

        self.address = addr
        self.objects = {}

    def getAddress (self):
        return self.address

    def _serveFor (self, addr):
        return self.getAddress() == addr

    def register(self, item, uri):

        location = self._validLocation (item)

        if not location:
            return False

        if location in self:
            return False

        entry = RegisterEntry ()
        entry.location = location
        entry.uri = uri

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

REGISTER_COMMAND_LOCATION = "0x01"
REGISTER_COMMAND_SHUTDOWN = "0x02"

REGISTER_DEFAULT_HOST = 'localhost'
REGISTER_DEFAULT_PORT = 9876

class RegisterURI (object):
    host = REGISTER_DEFAULT_HOST
    port = REGISTER_DEFAULT_PORT

    def __init__ (self, addr):
        self.host = addr[0]
        self.port = addr[1]

    def __cmp__ (self, other):
        return self.host == other.host and self.port == other.port

    def __getitem__ (self, index):
        if index == 0:
            return self.host

        if index == 1:
            return self.port
    
        raise IndexError ("Index out of bounds")

class RegisterServer(SocketServer.ThreadingUDPServer):

    def __init__(self, addr, requestHandler, reuse = False):

        self.register_uri = ''

        (location, port) = addr

        SocketServer.ThreadingUDPServer.allow_reuse_address = reuse
        SocketServer.ThreadingUDPServer.__init__(self, (location,port), requestHandler)

    def setRegisterURI (self, uri):
        self.register_uri = uri

    def getRegisterURI (self):
        return self.register_uri


class RegisterRequestHandler(SocketServer.DatagramRequestHandler):
    def handle (self):
        cmd = self.request[0]

        if cmd == REGISTER_COMMAND_LOCATION:
            self.request[1].sendto(str(self.server.getRegisterURI()), 0, self.client_address)
            return
 
        if cmd == REGISTER_COMMAND_SHUTDOWN:
            self.server.shutdown = 1
            return

def RegisterLocator (addr = (REGISTER_DEFAULT_HOST, REGISTER_DEFAULT_PORT), timeout = 1):

    sk = socket.socket (socket.AF_INET, socket.SOCK_DGRAM)

    if '<broadcast>' in addr[0]:
        sk.setsockopt (socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    sk.sendto (REGISTER_COMMAND_LOCATION, 0, addr)

    ins, out, errs = select.select ([sk], [], [sk], timeout)

    if not ins:
        return False

    for s in ins:
        reply, recvfrom = s.recvfrom (1000)

        proxy = Pyro.core.getProxyForURI (reply)

        if not proxy:
            return False

        return proxy

    return False


def RegisterFactory (daemon, addr = (REGISTER_DEFAULT_HOST, REGISTER_DEFAULT_PORT)):

    try:
        server = RegisterServer (addr, RegisterRequestHandler)
    except socket.error, e:
        if e[0] == 98: # socket already in use
            logging.warning ("Couldn't start register server. Address already in use (%s:%d)." % addr)
        return False

    register = Register (addr)

    uri = daemon.connect (register)

    server.setRegisterURI (uri)

    getThreadPool().queueTask (server.serve_forever)

    return register

