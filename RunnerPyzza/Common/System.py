#!/usr/bin/env python
"""
System

Common package

Objects that represent a System message
"""

__author__ = "Emilio Potenza"
__copyright__ = "Copyright 2011, RunnerPyzza"
__credits__ = ["Marco Galardini"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Marco Galardini"
__email__ = "emilio.potenza@iasma.it"
__status__ = "Development"

################################################################################
# Imports

import logging

################################################################################
# Log setup

# create logger
# Name shown
logger = logging.getLogger('System')

################################################################################
# Classes

class System(object):
    '''
    System messages
    '''
    def __init__(self,msg):
        self.cmd = msg
    def __str__(self):
        return self.msg
    def msg(self):
        '''
        Returns a dictionary representation of the object
        To be sent to the server
        '''
        d = {}
        d['type'] = 'system'
        # Values dictionary
        d1 = {}
        d1['msg'] = self.msg
        # Put all together
        d['values'] = d1

        return d
    

################################################################################
# Methods

################################################################################
# Main

if __name__ == '__main__':
    pass
