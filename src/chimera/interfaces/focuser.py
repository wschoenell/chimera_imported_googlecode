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

from chimera.core.interface import Interface
from chimera.core.event import event

class IFocuser(Interface):

    # properties
    position = 0.0
    type = ""
    maxIncrement = 0
    maxStep = 0
    tepSize = 0
    temperature = 0

    # methods
    def abortMove(self):
        pass

    def move(self, position):
        pass

    # events
    @event
    def focusChanged(self, newPosition, lastPosition):
        pass

