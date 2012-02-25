#!/usr/bin/env python
"""
System

Common package

Objects that represent a System message
"""

__author__ = "Emilio Potenza"
__credits__ = ["Marco Galardini"]

import logging

################################################################################
# Log setup

# create logger
# Name shown
logger = logging.getLogger('RunnerPyzza.System')

################################################################################
# Classes

class System(object):
    '''
    System messages
    '''
    def __init__(self,body,ID = None):
        self.body = body
        self.ID = ID
        
    def __str__(self):
        return self.body
    
    def msg(self):
        '''
        Returns a dictionary representation of the object
        To be sent to the server
        '''
        d = {}
        d['type'] = 'system'
        # Values dictionary
        d1 = {}
        d1['msg'] = self.body
        d1['ID'] = self.ID
        # Put all together
        d['values'] = d1

        return d
    

################################################################################
# Methods

################################################################################
# Main

if __name__ == '__main__':
    pass
