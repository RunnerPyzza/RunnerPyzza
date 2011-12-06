#!/usr/bin/env python
"""
Machine

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
    Class System
    '''
    def __init__(self,cmd):
        self.cmd = cmd
 
    def msg(self):
        '''
        Returns a dictionary representation of the object
        To be sent to the server
        '''
        d = {}
        d['type'] = 'system'
        # Values dictionary
        d1 = {}
        d1['msg'] = self.cmd
        # Put all together
        d['values'] = d1

        return d
    

################################################################################
# Methods

################################################################################
# Main

if __name__ == '__main__':
    pass
