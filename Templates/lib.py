#!/usr/bin/env python
"""
XXXXXXXXXXXXX

Library

Description
"""

__author__ = "NAME"
__copyright__ = "Copyright 20XX, PROJECT"
__credits__ = ["NAME1", "NAME2", "NAME3",
                    "NAME4"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "NAME"
__email__ = ""
__status__ = "Development"

################################################################################
# Imports

import logging

################################################################################
# Log setup

# create logger
# Name shown
logger = logging.getLogger('XXXXXXXXXXXXX')

################################################################################
# Classes

class Spam(object):
    '''
    Class Spam
    blah blah blah
    '''
    def __init__(self):
        pass
    def _behindTheScenes(self):
        '''
        Internal method to be called ONLY inside the class
        '''
        pass
    def addEggs(self):
        '''
        Add some eggs to the spam
        '''
        pass

################################################################################
# Methods

def foo():
    '''
    Foo computes something
    Input: eggs
    Output: spam
    Exceptions: when spam > eggs
    '''
    pass

################################################################################
# Main

if __name__ == '__main__':
    pass
