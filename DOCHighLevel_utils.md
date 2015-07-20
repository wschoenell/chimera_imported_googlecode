The idea of this document is to show how to create a utility type class in chimera.

# Introduction #

How to write a utility using chimera framework.

This kind of program does not need chimera objects.

It does not need the chimera daemon to be running.

It is basically like any other python class,

However, it does use chimera classes and is written to be used  by other chimera objects, particularly while chimera is running.

I show here the implementation of the astrometrynet class used to call solve-field (from astrometry.net) to find the WCS for a given image.

# Details #

```
from subprocess import Popen
from chimera.util.sextractor import SExtractor
from chimera.core.exceptions import ChimeraException
from chimera.util.image import Image

import os
import shutil
from pyraf import iraf

import logging
import chimera.core.log
log = logging.getLogger(__name__)
```

**Note some of these are chimera classes, some are standard python classes.** The astrometrynet class starts down here.  The goal is to run the solve-field program  from astrometrynet (as a system call) on a given image and to create a copy of the  **original image with a modified header reflecting the WCS found by solve-field:**


```
class AstrometryNet:
    
    # staticmethod allows to use a single method of a class
    @staticmethod
    def solveField(fullfilename, findstarmethod="astrometry.net"):
        """
        @param: fullfilename entire path to image
        @type: str

        @param: findstarmethod (astrometry.net, sex) 
        @type: str

        Does astrometry to image=fullfilename
        Uses either astrometry.net or sex(tractor) as its star finder

        """

        pathname, filename = os.path.split(fullfilename)
        pathname = pathname + "/"
        basefilename,file_xtn = os.path.splitext(filename)
        # *** enforce .fits extension
        if (file_xtn != ".fits"):
            raise ValueError("File extension must be .fits it was = %s\n" %file_xtn)

        # *** check whether the file exists or not
        if ( os.path.exists(fullfilename) == False ):
            raise IOError("You selected image %s  It does not exist\n" %fullfilename)

        # version 0.23 changed behavior of --overwrite
        # I need to specify an output filename with -o
        outfilename = basefilename + "-out"
```

**Here I use a chimera class for the first time.  I am using the image class    :**

```

        image = Image.fromFile(fullfilename)
        try:
            ra = image["CRVAL1"]    # expects to see this in image
        except:
            raise AstrometryNetException("Need CRVAL1 and CRVAL2 and CD1_1 on header")
        try:
            dec = image["CRVAL2"]
        except:
            raise AstrometryNetException("Need CRVAL1 and CRVAL2 and CD1_1 on header")
        width = image["NAXIS1"]
        height = image["NAXIS2"] 
        radius = 5.0 * abs(image["CD1_1"]) * width

```


## Now, I ask whether I am using astrometrynet internal star finder or sexrtactor. ##
## I build a command line to run solve-field based on this information: ##


```
        if findstarmethod == "astrometry.net":
            #line = "solve-field --guess-scale %s --overwrite -o %s" %(fullfilename, outfilename)
            line = "solve-field %s --overwrite -o %s --ra %f --dec %f --radius %f"  %(fullfilename, outfilename, ra, dec, radius)
            print line

        elif findstarmethod == "sex":
            sexoutfilename = pathname + outfilename + ".xyls"
            line = "solve-field %s --overwrite -o %s --x-column X_IMAGE --y-column Y_IMAGE --sort-column MAG_ISO --sort-ascending --width %d --height %d --ra %f --dec %f --radius %f"  %(sexoutfilename, outfilename, width, height, ra, dec, radius)
            print "Sextractor command line %s" %line
            # using --guess-scale
            # line = "solve-field %s --overwrite -o %s --x-column X_IMAGE --y-column Y_IMAGE --sort-column MAG_ISO --sort-ascending --width %d --height %d --guess-scale"  %(sexoutfilename, outfilename, width, height)

            sex = SExtractor()
            sex.config['BACK_TYPE']   = "AUTO"
            sex.config['DETECT_THRESH'] = 3.0
            sex.config['DETECT_MINAREA'] = 18.0
            sex.config['VERBOSE_TYPE'] = "QUIET"
            sex.config['CATALOG_TYPE'] = "FITS_1.0"
            #sex.config['CATALOG_TYPE'] = "ASCII"
            sex.config['CATALOG_NAME'] = sexoutfilename
            sex.config['PARAMETERS_LIST'] = ["X_IMAGE","Y_IMAGE","MAG_ISO"]
            sex.run(fullfilename)

        else:
            log.error("Unknown option used in astrometry.net")
```

**check to see if astrometry.net found a solution**

```
        # when there is a solution astrometry.net creates a file with .solved
        # added as extension.  
        is_solved = pathname + outfilename + ".solved"
        # if it is already there, make sure to delete it 
        if ( os.path.exists(is_solved)):
            os.remove(is_solved)
	print "SOLVE"  , line
        solve = Popen(line.split()) # ,env=os.environ)
        solve.wait()
        # if solution failed, there will be no file .solved
        if ( os.path.exists(is_solved) == False ):
            raise NoSolutionAstrometryNetException("Astrometry.net could not find a solution for image: %s %s" %(fullfilename, is_solved))

        # wcs_imgname will be the old fits file with the new header
        # wcs_solution is the solve-field solution file
        wcs_imgname = pathname + outfilename + "-wcs" + ".fits"
        wcs_solution = pathname + outfilename + ".wcs"
        shutil.copyfile(wcs_solution,wcs_solution+".fits")
        if ( os.path.exists(wcs_imgname) == True ):
            iraf.imdelete(wcs_imgname)

        # create a separate image with new header
        iraf.artdata()
        iraf.imcopy(fullfilename,wcs_imgname)
        iraf.mkheader(images=wcs_imgname,headers=wcs_solution+".fits",
                      append="no",verbose="no",mode="al")
        return(wcs_imgname)
```

**Exceptions**

```
class AstrometryNetException(ChimeraException):
    pass        

class NoSolutionAstrometryNetException(ChimeraException):
    pass 

```