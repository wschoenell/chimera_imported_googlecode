#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from chimera.core.cli import ChimeraCLI, action, parameter, Parameter, ParameterType, Action

class SimpleCli(ChimeraCLI):

    def __init__ (self):
        ChimeraCLI.__init__(self, "chimera-cli", "Chimera CLI Class", 0.1)
        
        self.addParameters(dict(name="telescope", help="Telescope instance to use", type=ParameterType.INSTRUMENT),
                           dict(name="driver", help="Telescope driver to use", type=ParameterType.DRIVER))        
        
    # pure attribute based parameter (require's name, as this couldn't be guessed as in the decorator case) 
    outro = Parameter(name="teste", help="Test option")
        
    @parameter(long="ra", default=None)
    def ra(self, value):
        """
        Right Ascension.
        """
        self.out("Validating DEC value=%s" % value)
        return value

    @parameter(long="dec", default=None)
    def dec(self, value):
        """
        Declination.
        """
        self.out("Validating DEC value=%s" % value)
        return value
        
    @action(short="s")
    def slew(self, options):
        """
        Help for slew.
        """
        self.out("slewing to RA=%s DEC=%s" % (options.ra, options.dec))
        self.out("using telescope=%s driver=%s" % (options.telescope, options.driver))

    @action(short="S")
    def sync(self, options):
        """
        Help for sync.
        """
        self.out("syncing")

    @action(short="i", help="Help for info.")
    def info(self, options):
        self.out("info")
        

class TestCLI(object):

    def test_run (self):
        s = SimpleCli()
        s.run("--slew --ra 10:10:10 --dec 20:20:20".split())
        
    def test_help(self):
        s = SimpleCli()
        s.run("--help".split())

if __name__ == '__main__':
    
    import sys
    
    cli = SimpleCli()
    ret = cli.run(sys.argv)
    sys.exit(ret)
     