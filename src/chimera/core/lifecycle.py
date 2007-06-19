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
import threading

import Pyro.core

from chimera.interfaces.lifecycle import ILifeCycle
from chimera.core.event import EventsProxy
from chimera.core.config import Config


class BasicLifeCycle (ILifeCycle, Pyro.core.ObjBase):

    def __init__(self):

        Pyro.core.ObjBase.__init__ (self)

        # event handling
        self.__events_proxy__ = EventsProxy (self)

        # configuration handling
        self.__config_proxy__ = Config (self)

    # config
    def __getitem__ (self, item):
        return self.__config_proxy__.__getitem__ (item)
    
    def __setitem__ (self, item, value):
        return self.__config_proxy__.__setitem__ (item, value)

    # event
    def publish (self, event, *args, **kwargs):

        if event in self.__events_proxy__:
            self.__events_proxy__[event] (*args, **kwargs)

    def subscribe (self, event, clbk):

        if event in self.__events_proxy__:
            self.__events_proxy__[event].__iadd__ (clbk)
            return True

        return False
    
    def unsubscribe (self, event, clbk):

        if event in self.__events_proxy__:
            self.__events_proxy__[event].__isub__ (clbk)
            return True

        return False
    
    # lifecycle
    def __start__ (self):
        pass

    def __stop__ (self):
        pass

    def __control__ (self):
        pass

    def __main__ (self):
            
        try:

            while True:

                # run control function
                self.__control__()

                time.sleep(self.timeslice)

        except KeyboardInterrupt, e:
            return

#     def __getattr__(self, attr):
#         if attr in self.__eventsProxy__:
#             return self.__eventsProxy__[attr]
#         else:
#             raise AttributeError
