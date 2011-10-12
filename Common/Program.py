#!/usr/bin/env python
"""
Program

Common package

Objects that represent commands of the ScriptChain
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

################################################################################
# Log setup

# create logger
# Name shown
logger = logging.getLogger('Program')

################################################################################
# Classes

class Program(object):
    '''
    Class Program
    Stores the raw command and the number of CPUs it should use
    '''
    def __init__(self,name,cmd):
        self.name = name
        self._cmd = cmd
        self._ncpu = 1
        self._order = 1
    def __str__(self):
        '''
        Returns the program command line
        '''
        return self._cmd
    def getCpu(self):
        return self._ncpu
    def setCpu(self,ncpu):
        self._ncpu = int(ncpu)
    def getOrder(self):
        return self._order
    def setOrder(self,order):
        self._order = int(order)

################################################################################
# Methods

################################################################################
# Main

if __name__ == '__main__':
    pass