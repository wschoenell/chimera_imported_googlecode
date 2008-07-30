from chimera.core.location import Location

class ImageURI(Location):
    def __init__(self, imageServer, hash):
        Location.__init__(self)
        self._host = imageServer.getManager().getHostname()
        self._port = imageServer.getManager().getPort()
        isL = imageServer.getLocation()
        self._cls = isL.cls
        self._name = isL.name
        self.config = {'hash':hash}
        