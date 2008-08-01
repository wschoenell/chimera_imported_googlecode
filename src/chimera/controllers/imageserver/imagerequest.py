from chimera.core.chimeraobject import ChimeraObject
from chimera.interfaces.cameradriver import Bitpix
from chimera.interfaces.camera import SHUTTER_LEAVE

import logging
import chimera.core.log
log = logging.getLogger(__name__)

class ImageRequest(ChimeraObject):
    __config__ =  {'exp_time':              1.0,
                   'frames':                1,
                   'interval':              0.0,
                   'shutter':               ('Leave', SHUTTER_LEAVE),
                   'binning':               ('None', None),                 #Based upon camera.getBinnings
                                                # (('1x1', 3), ('2x2', 323))
                   #'filter':                ('Clear', 'CLEAR'),             #Based upon filter.getFilters
                   'window':                ('Full', (0.5, 0.5, 1.0, 1.0)), #Ignored if hardware cannot handle
                   'chip':                  ('Default', None),              #Based upon camera.getChips
                   'readOnAbort':           False,
                   'bitpix':                Bitpix.uint16,
                   'filename':              '$date',
                   'headers':               [],
                   'image_type':             'object',
                   'metadatapre':           [],                             #URLs of proxies from which to get metadata before taking each image
                   'metadatapost':          [],                             #URLs of proxies from which to get metadata after taking each image
                   'accum_headers':         [],                             #Headers accumulated during processing of each frame (=headers+metadatapre+metadatapost)
                   }
    
    def __init__(self, **kwargs):
        
        ChimeraObject.__init__()
        
        self += kwargs
        
        forceArgsValid           = kwargs.get('forceArgsValid', False)

        if self['exp_time'] < 0.0:
            if forceArgsValid:
                self.exp_time = 0.0
            else:
                raise ChimeraValueError('Invalid exposure length (<0 seconds).')
        
        if self['frames'] < 1:
            if forceArgsValid:
                self.frames = 1
            else:
                raise ChimeraValueError('Invalid number of frames (<1 frame).')
        
        if self['interval'] < 0.0:
            if forceArgsValid:
                self.interval = 0.0
            else:
                raise ChimeraValueError('Invalid interval between exposures (<0 seconds)')

        if self['shutter'] not in Shutter.values():
            if forceArgsValid:
                self.shutter = SHUTTER_LEAVE
            else:
                raise ChimeraValueError('Invalid shutter value')

    
    def addPreHeaders(self, manager):
        self['accum_headers']=[]
        self['accum_headers']+=self['headers']
        for proxyurl in self['metadatapre']:
            try:
                proxy = manager.getProxy(proxyurl)
                self['accum_headers']+=proxy.getMetadata()
            except:
                log.warning('Unable to get metadata from ' + proxyurl)

    
    def addPostHeaders(self, manager):
        for proxyurl in self['metadatapost']:
            proxy = manager.getProxy(proxyurl)
            try:
                proxy = manager.getProxy(proxyurl)
                self['accum_headers']+=proxy.getMetadata()
            except:
                log.warning('Unable to get metadata from ' + proxyurl)
            