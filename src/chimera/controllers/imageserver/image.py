from chimera.core.chimeraobject import ChimeraObject
from Pyro.errors import NamingError
from chimera.core.path import ChimeraPath
from chimera.interfaces.cameradriver import Bitpix
from chimera.controllers.imageserver.imageuri import ImageURI
from chimera.core.exceptions import ClassLoaderException

fits_date_format = "%Y-%m-%dT%H:%M:%S"

import pyfits
import numpy
#TODO: Python2.4 Compatible hashlib
try:
    import hashlib
    def hashFcn(filename):
        file = open(filename, 'rb')
        hash = hashlib.sha1(file.read()).hexdigest()
        file.close()
        return hash
except:
    import sha
    def hashFcn(filename):
        file = open(filename, 'rb')
        hash = sha.new(file.read()).hexdigest()
        file.close()
        return hash

class ImageURI(object):
    def __init__(self):
        object.__init__(self)
        

class Image(ChimeraObject):
    
    def __init__(self):
        ChimeraObject.__init__(self)
        
        self.imageServer = None
        
        try:
            self.imageServer = self.getManager().getProxy('/ImageServer/0')
        except NameError:
            self.imageServer = self.getManager().addLocation('/ImageServer/imageserver', ChimeraPath.controllers())
            if not self.imageServer:
                raise ClassLoaderException('Unable to create an ImageServer')
            
        self.path = None
        self.hdu = None
        self.hash = None
        pass
    
    def _registerMe(self):
        self.imageServer.registerImage(self)
    
    def getHash(self):
        if self.hash == None:
            self.hash = hashFcn(self.path) 
        return self.hash
    
    def getURI(self):
        return ImageURI(self.imageServer, self.getHash)
        
    @staticmethod
    def imageFromImg(img, imageRequest, dict = None):
        image = imageStart(imageRequest)
        
        hdu = pyfits.PrimaryHDU(img)
        
        if dict == None:
            dict = []
 
        file_date = time.strftime(fits_date_format, time.gmtime())
                                                                                            
        basic_headers = [("EXPTIME", float(exptime) or -1, "exposure time in seconds"),
                         ("DATE", file_date, "date of file creation"),
                         #("DATE-OBS", obs_date, "date of the start of observation"),       #From cameradriver
                         #("MJD-OBS", 0.0, "date of the start of observation in MJD"),      #Not needed
                         #("RA", "00:00:00", "right ascension of the observed object"),     #From telescope
                         #("DEC", "00:00:00", "declination of the observed object"),        #From telescope
                         ("EQUINOX", 2000.0, "equinox of celestial coordinate system"),
                         ("RADESYS", "FK5",  "reference frame"),
                         ("SECPIX", 0.0, "plate scale"),                                   #From telescope
                         ("WCSAXES", 2, "wcs dimensionality"),
                         ("CRPIX1", 0.0, "coordinate system reference pixel"),
                         ("CRPIX2", 0.0, "coordinate system reference pixel"),
                         ("CRVAL1", 0.0, "coordinate system value at reference pixel"),
                         ("CRVAL2", 0.0, "coordinate system value at reference pixel"),
                         ("CTYPE1", '', "name of the coordinate axis"),
                         ("CTYPE2", '', "name of the coordinate axis"),
                         ("CUNIT1", '', "units of coordinate value"),
                         ("CUNIT2", '', "units of coordinate value"),
                         ("CD1_1", 1.0, "transformation matrix element (1,1)"),
                         ("CD1_2", 0.0, "transformation matrix element (1,2)"),
                         ("CD2_1", 0.0, "transformation matrix element (2,1)"),
                         ("CD2_2", 1.0, "transformation matrix element (2,2)"),
                         ("CREATOR", _chimera_description_, ""),
                         #('OBJECT', 'UNKNOWN', 'Object observed'),                        #Added by scheduler
                         #('TELESCOP', 'UNKNOWN', 'Telescope used for observation'),        #Added by telescope
                         #('PI', 'Chimera User', 'Principal Investigator'),                #Added by scheduler
                         ('IMAGETYP', imageRequest['image_type'], 'Image type')
                         ]

        #TODO: Implement bitpix support
        #Should be done just before writing
        #if imageRequest['bitpix'] == Bitpix.uint16:
        hdu.scale('int16', '', bzero=32768, bscale=1)
        
        for header in basic_headers + dict:
            hdu.header.update(*header)
        
        image.path = image.imageServer.getFileName(imageRequest['filename'])
        
        hduList = pyfits.HDUList([hdu])
        
        hduList.writeto(image.path)
        
        del hdu
        del hduList
        
        image._registerMe()
        return image.getURI()
    
    @staticmethod
    def formatDate(date):
        return time.strftime(fits_date_format, date)
    