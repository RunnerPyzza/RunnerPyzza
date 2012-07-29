#!/usr/bin/env python
"""
Machine

Common package

Objects that represent a machine
"""

__author__ = "Marco Galardini"
__credits__ = ["Emilio Potenza"]

import logging

################################################################################
# Log setup

# create logger
# Name shown
logger = logging.getLogger('RunnerPyzza.Machine')

################################################################################
# Classes

class Machine(object):
    '''
    Class Machine
    Stores the raw command and the number of CPUs it should use
    Hostname, Username and Password are passed on creation
    '''
    def __init__(self,name,hostname,user='runnerpyzza'):
        self.name = name
        self._hostname = hostname
        self._user = user
        self._password = None
        
        # Used by the Server
        self._ncpu = None
        
    def __str__(self):
        '''
        Returns the machine string - if the password has not been set returns
        only hostname and user
        '''
        if not self._password:
            return ':'.join([self._hostname,self._user])
        else:
            return ':'.join([self._hostname,self._user,self._password])
        
    def msg(self):
        '''
        Returns a dictionary representation of the object
        To be sent to the server
        '''
        d = {}
        d['type'] = 'machine'
        # Values dictionary
        d1 = {}
        d1["name"] = self.name
        d1['hostname'] = self._hostname
        d1['user'] = self._user
        d1['password'] = self._password
        # Put all together
        d['values'] = d1
        
        return d
    
    def getHostname(self):
        return self._hostname
    
    def getUser(self):
        return self._user
    
    def getPassword(self,encode = True):
        '''
        Return the machine password
        If Encode is set to True it will be encoded
        If Encode is set to False it means that it's already encoded
        '''
        if encode:
            import base64
            return base64.b64decode(self._password)
        else:
            return self._password

    def hasPassword(self):
        if not self._password:
            return False
        else:
            return True
        
    def setPassword(self,pwd,encode = True):
        '''
        Add the password to the machine
        If Encode is set to True it will be encoded
        If Encode is set to False it means that it's already encoded
        '''
        if encode:
            import base64
            self._password = base64.b64encode(pwd)
        else:
            self._password = pwd
            
    def setCpu(self, ncpu):
        self._ncpu = int(ncpu)
        
    def getCpu(self):
        return self._ncpu
            
    
################################################################################
# Methods

################################################################################
# Main

if __name__ == '__main__':
    pass