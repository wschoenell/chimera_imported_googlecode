from chimera.core.chimeraobject import ChimeraObject
from chimera.util.filenamesequence import FilenameSequence
from chimera.core.manager import Manager
import time
import os
import os.path

class ImageServer(ChimeraObject):
    __config__  = {'savedir':   '$HOME/images'}
    
    def __init__(self):
        ChimeraObject.__init__(self)
        
        self.images = {}
    
    def getFileName(self, filename='$DATE'):
        dest = os.path.expanduser(self['savedir'])
        dest = os.path.expandvars(dest)
        dest = os.path.realpath(dest)
        
        if not os.path.exists(dest):
            os.makedirs(dest)
        if not os.path.isdir(dest):
            raise OSError('A file with the same name as the desired dir already exists.')
        
        subs_dict = {"date": time.strftime(dateFormat, time.gmtime(obsTime))}

        filename = string.Template(filename).safe_substitute(subs_dict)
        
        seq_num = FilenameSequence(os.path.join(dest, filename), extension='fits').next()

        finalname = os.path.join(dest, "%s-%04d%s%s" % (filename, seq_num, os.path.extsep, ext))
        
        if os.path.exists(finalname):
            tmp = finalname
            finalname = os.path.join(dest, "%s-%04d%s%s" % (filename, int (random.random()*1000),
                                                            os.path.extsep, ext))

            self.log.debug ("Image %s already exists. Saving to %s instead." %  (tmp, finalname))

        return finalname
    
    def registerImage(self, image):
        Manager().adapter.connect
        #self.getManager().adapter.
        self.images += {image.getHash(): image}
    
    def _isMyImage(self, imageURI):
        myMan = self.getManager()
        return ((imageURI.host == myMan.getHostname()) and (imageURI.port == myMan.getPort()))
    
    def getImage(self, imageURI):
        if self._isMyImage(imageURI):
            return self.images[imageURI.config['hash']]

    
    pass



