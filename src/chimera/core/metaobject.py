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



from chimera.core.methodwrapper import MethodWrapper
from chimera.core.eventwrapper  import EventWrapperDispatcher
from chimera.core.async         import BeginDispatcher, EndDispatcher

from chimera.core.constants     import EVENT_ATTRIBUTE_NAME, CONFIG_ATTRIBUTE_NAME

from types import DictType


__all__ = ['MetaObject']

    
class MetaObject (type):

    def __new__ (meta, clsname, bases, _dict):

        # join __config__ dicts, class configuration override base classes configs
        config = {}

        for base in bases:
            if CONFIG_ATTRIBUTE_NAME in base.__dict__ and type(base.__dict__[CONFIG_ATTRIBUTE_NAME]) == DictType:
                config = dict(config, **base.__dict__[CONFIG_ATTRIBUTE_NAME])

        # update our class with all configs got from bases, if none defined, our config will be equal to the sum from the bases
        _dict[CONFIG_ATTRIBUTE_NAME] = dict(config, **_dict.get(CONFIG_ATTRIBUTE_NAME, {}))

        # callables and events
        for name, obj in _dict.iteritems():
            
            if hasattr(obj, '__call__') and not name.startswith('_'):
                # events
                if hasattr(obj, EVENT_ATTRIBUTE_NAME):
                    _dict[name] = MethodWrapper(obj, dispatcher=EventWrapperDispatcher)
                else:
                    # normal objects
                    _dict[name] = MethodWrapper(obj, specials = {"begin": BeginDispatcher, "end": EndDispatcher})

        return super(MetaObject, meta).__new__(meta, clsname, bases, _dict)

