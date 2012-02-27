#!/usr/bin/env python
"""
Program

Common package

Objects that represent commands of the ScriptChain
"""

__author__ = "Marco Galardini"
__credits__ = ["Emilio Potenza"]

import logging

################################################################################
# Log setup

# create logger
# Name shown
logger = logging.getLogger('RunnerPyzza.Program')

################################################################################
# Classes

class Program(object):
    '''
    Class Program
    Stores the raw command and the number of CPUs it should use
    '''
    def __init__(self,name,cmd,ncpu = 1,order = 1, canFail = False):
        self.name = name
        self._cmd = cmd
        self._ncpu = ncpu
        self._order = order
        self._canFail = canFail
        
        # Info about the results
        self._stdout = None
        self._stderr = None
        self._host = None
        self._exit = None
        
    def __str__(self):
        '''
        Returns the program command line
        '''
        return self._cmd
    
    def msg(self):
        '''
        Returns a dictionary representation of the object
        To be sent to the server
        '''
        d = {}
        d['type'] = 'program'
        # Values dictionary
        d1 = {}
        d1['name'] = self.name
        d1['cmd'] = self._cmd
        d1['ncpu'] = self._ncpu
        d1['order'] = self._order
        d1['canFail'] = self._canFail
        d1['stdout'] = self._stdout
        d1['stderr'] = self._stderr
        d1['host'] = self._host
        d1['exit'] = self._exit
        # Put all together
        d['values'] = d1
        
        return d
    
    def getCmd(self):
        return self._cmd
    
    def getCpu(self):
        return self._ncpu
    
    def setCpu(self,ncpu):
        self._ncpu = int(ncpu)
        
    def getOrder(self):
        return self._order
    
    def setOrder(self,order):
        self._order = int(order)
        
    def getCanFail(self):
        return self._canFail
        
    def setCanFail(self,canFail):
        self._canFail = bool(canFail)
        
    def getStdOut(self):
        return self._stdout
        
    def setStdOut(self,stdout):
        self._stdout = stdout
        
    def getStdErr(self):
        return self._stderr
        
    def setStdErr(self,stderr):
        self._stderr = stderr
        
    def getHost(self):
        return self._host
        
    def setHost(self,host):
        self._host = host
        
    def getExit(self):
        return self._exit
        
    def setExit(self,exitStatus):
        self._exit = exitStatus

################################################################################
# Methods

################################################################################
# Main

if __name__ == '__main__':
    pass
