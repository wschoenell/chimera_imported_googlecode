# Scripts are used on the command line to interact with a given chimera class.

# Introduction #

We show here the chimera-pverify script to show how


# Details #


### Start importing goodies: ###

```
from chimera.core.cli import ChimeraCLI, action, parameter
from chimera.core.callback import callback
from chimera.core.exceptions import ChimeraException
from chimera.interfaces.pointverify import CantPointScopeException, CanSetScopeButNotThisField, CantSetScopeException, PointVerify
from chimera.util.sextractor import SExtractorException

from chimera.util.ds9 import DS9

import sys
import time
import os

```

To really understand this one needs to read the documentation on ChimeraCLI, this is a quick and dirty guide.

What I am doing here is informing the running chimera daemon of the existence of chimera-pverify and that chimera-pverify will connect to the daemon and send info.

```
class ChimeraPointVerify (ChimeraCLI):

    def __init__ (self):
        ChimeraCLI.__init__(self, "chimera-pverify", "Point Verifier", 0.1)
```


Every chimera script has a --help option.  Options come grouped under "help groups", one can add as many groups as wished, then when defining methods we can assign the methods to given groups and they will appear in that group when help is asked for.

```
        self.addHelpGroup("PVERIFY", "PVerify")
```

We are now adding the "pverify" controller (could be any name) which is related to the existing class PointVerify.

It belongs to the help group "PVERIFY" (just added in the above line) and the help message shown by --help is "Pointing verification controller to be used"

```
        self.addController(name="pverify", cls="PointVerify", required=True, helpGroup="PVERIFY", help="Pointing verification controller to be used")
```

Add another help group:
```
        self.addHelpGroup("COMMANDS", "Commands")
```


@action establishes that the following method is some action performed by this script

so, one can type:

chimera-pverify --check

and the script will execute action "check" below.  One can define as many actions as needed.
```
    @action(long="check",
            help="Chooses a field to point the scope to, moves the scope, takes an image and verifies the pointing",
           helpGroup="PVERIFY")
    def checkPointing (self,options):
        self.out("Choosing a field in the sky, moving scope and taking images")
        try:
            self.pverify.checkPointing()
        # what is this e for ???
        except CantSetScopeException, e:
            self.exit("Can't set scope")
        self.out("OK")
```


This is needed to run it from the command line:
```
def main():
    cli = ChimeraPointVerify()
    return cli.run(sys.argv)

if __name__ == '__main__':
    main()
```