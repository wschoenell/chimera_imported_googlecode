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
        
        self.imagesByID = {}
        self.imagesByPath = {}
    
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
        self.getDaemon().connect(image)
        self.imagesByID += {image.getID(): image}
        self.imagesByPath += {image.getPath(): image}
    
    def _isMyImage(self, imageURI):
        myMan = self.getManager()
        return ((imageURI.host == myMan.getHostname()) and (imageURI.port == myMan.getPort()))
    
    def getImageByURI(self, imageURI):
        if self._isMyImage(imageURI):
            return self.imagesByID[imageURI.config['hash']]
    
    def getImageByPath(self, path):
        if path in self.imagesByPath.keys():
            return self.imagesByPath[path]
        else:
            return None
        
    def __stop__(self):
        for image in self.images.values():
            self.getDaemon().disconnect(image)

    
    @staticmethod
    def getImageServer():
        #TODO: getting the current manager from "nothing"
        manager = Manager.getManagerProxy()
        try:
            toReturn = manager.getProxy('/ImageServer/0')
        except NameError:
            toReturn = manager.addLocation('/ImageServer/imageserver', ChimeraPath.controllers())
        if not toReturn:
            raise ClassLoaderException('Unable to create or find an ImageServer')
        




#If you create new Pyro objects on the server, and you want them to be accessed from the client, or vice versa (such as callback objects), you have to consider some things carefully. Make sure you:
#
#    * derive the class from Pyro.core.ObjBase, or use the delegation approach, and call Pyro.core.ObjBase.__init__(self) from your own __init__
#    * connect the new object to the Pyro Daemon (with or without a name). (This is needed to register the object as a Pyro object, and to set the daemon in the object for the next step.) It can be easily done from within the Pyro object that created the new object:
#
#         URI = self.getDaemon().connect(object)        # no name, not in NS
#         URI = self.getDaemon().connect(object,'name') # registered in NS with 'name'
#
#    * return a proxy for the object, not the object itself. Instead of the normal return object that you would otherwise use, you do:
#
#         return object.getProxy()      # regular dynamic proxy
#         return object.getAttrProxy()  # dynamic proxy with attribute support
#
#    * disconnect the object form the Pyro Daemon if you're done with it (don't just del it)
#
#         self.getDaemon().disconnect(object)
#         del object

