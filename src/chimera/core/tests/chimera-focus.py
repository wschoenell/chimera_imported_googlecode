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


from chimera.core.cli import ChimeraCLI, action


class ChimeraFocus (ChimeraCLI):
    
    def __init__ (self):
        ChimeraCLI.__init__(self, "chimera-focus", "Focuser controller", 0.1)
        
        self.addHelpGroup("ACTIONS", "Actions")
        
        self.addInstrument(name="focuser", cls="Focuser", help="Focuser instrument to be used")
        self.addDriver(instrument="focuser", name="driver", short="d", help="Focuser driver to be used")        
        
    @action(long="in", type="int", help="Move N steps IN", metavar="N", group="ACTIONS")
    def move_in (self, options):
        self.out("Moving %d steps IN ... " % options.move_in)
        options.focuser.moveIn(options.move_in)
        self.out("OK\n")
        
        self._currentPosition(options)
        
    @action(long="out", type="int", help="Move N steps OUT", metavar="N", group="ACTIONS")
    def move_out (self, options):
        self.out("Moving %d steps OUT ... " % options.move_out)
        options.focuser.moveOut(options.move_out)
        self.out("OK\n")
        
        self._currentPosition(options)

    @action(long="to", type="int",help="Move to POSITION", metavar="POSITION", group="ACTIONS")
    def move_to (self, options):
        self.out("Moving to %d ... " % options.move_to)
        options.focuser.moveTo(options.move_to)
        self.out("OK\n")
        
    @action(short="i", help="Print focuser current information", group="ACTIONS")
    def info(self, options):
        
        drv = options.focuser.getDriver()
        
        self.out("Focuser: %s (%s)\n" % (options.focuser["driver"], drv["device"]))
        self._currentPosition(options)

    def _currentPosition(self, options):
        return self.out("Current focuser position: %s\n" % options.focuser.getPosition())

if __name__ == '__main__':
    
    import sys
    
    cli = ChimeraFocus()
    ret = cli.run(sys.argv)
    sys.exit(ret)
    