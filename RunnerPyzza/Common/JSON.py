#!/usr/bin/env python
"""
JSON

Common package

Objects used to encode/decode messages between client(s) and server(s)
"""

__author__ = "Marco Galardini"
__copyright__ = "Copyright 2011, RunnerPyzza"
__credits__ = ["Emilio Potenza"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Marco Galardini"
__email__ = "marco.galardini@unifi.it"
__status__ = "Development"

################################################################################
# Imports

import logging
import json

################################################################################
# Log setup

# create logger
# Name shown
logger = logging.getLogger('JSON')

################################################################################
# Classes

class JSON(object):
    '''
    Class JSON
    Really really simple class implementing the json encoder/decoder
    '''
    def __init__(self):
        pass
    def encode(self,obj):
        '''
        Returns the JSON encoded version of the object
        '''
        logging.debug('Encoding: %s'%obj)
        return json.dumps(obj)
    def decode(self,msg):
        '''
        Returns the JSON deecoded version of the object
        '''
        logging.debug('Decoding: %s'%msg)
        return json.loads(msg)

################################################################################
# Methods

################################################################################
# Main

if __name__ == '__main__':
    pass
