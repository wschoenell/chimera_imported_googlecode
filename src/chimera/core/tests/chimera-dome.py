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
from chimera.util.coord import Coord


class ChimeraDome (ChimeraCLI):
    
    def __init__ (self):
        ChimeraCLI.__init__(self, "chimera-dome", "Dome controller", 0.1)
    

        self.addHelpGroup("DOME", "Dome")
        self.addInstrument(name="dome", cls="Dome", help="Dome instrument to be used", helpGroup="DOME")
        self.addDriver(instrument="dome", name="driver", short="d", help="Dome driver to be used", helpGroup="DOME")

        self.addHelpGroup("TELESCOPE", "Telescope Tracking Configuration")
        self.addParameters(dict(name="telescope", helpGroup="TELESCOPE",
                                help="Tell the dome to follow TELESCOPE when tracking (only "
                                "utilized when calling --track"))
        
        self.addHelpGroup("COMMANDS", "Commands")
        
        self.addActionGroup("SLIT")
        self.addActionGroup("TRACKING")
        self.addActionGroup("INFO")     
        self.addActionGroup("SLEW")        

    @action(help="Open dome slit", helpGroup="COMMANDS", actionGroup="SLIT")
    def open(self, options):
        self.out("Opening dome slit ... ")
        options.dome.openSlit()
        self.out("OK\n")
    
    @action(help="Close dome slit", helpGroup="COMMANDS", actionGroup="SLIT")
    def close(self, options):
        self.out("Closing dome slit ... ")
        options.dome.closeSlit()
        self.out("OK\n")

    @action(help="Track the telescope", helpGroup="COMMANDS", actionGroup="TRACKING")
    def track(self, options):
        self.out("Activating tracking ... ")

        if options.telescope:
            options.dome["telescope"] = options.telescope
            
        options.dome.track()
        self.out("OK\n")

    @action(help="Stop tracking the telescope (stand)", helpGroup="COMMANDS", actionGroup="TRACKING")
    def stand(self, options):
        self.out("Deactivating tracking ... ")
        options.dome.stand()
        self.out("OK\n")

    @action(long="to", type="string",
            help="Move dome to AZ azimuth", metavar="AZ", helpGroup="COMMANDS", actionGroup="SLEW")
    def moveTo(self, options):
        
        try:
            target = Coord.fromDMS(options.moveTo)
        except ValueError, e:
            self.exit("Invalid azimuth (%s)" % e)

        self.out("Moving dome to %s ... " % target)
        options.dome.slewToAz(target)
        self.out("OK\n")
    
    @action(help="Print dome information", helpGroup="COMMANDS", actionGroup="INFO")
    def info(self, options):

        self.out("Dome: %s (%s).\n" % (options.dome["driver"], options.dome.getDriver()["device"]))
        self.out("Current dome azimuth: %s.\n" % options.dome.getAz())
        if options.dome.isSlitOpen():
            self.out("Dome slit is open.\n")
        else:
            self.out("Dome slit is closed.\n")

if __name__ == '__main__':
    
    import sys
    
    cli = ChimeraDome()
    ret = cli.run(sys.argv)
    sys.exit(ret)

