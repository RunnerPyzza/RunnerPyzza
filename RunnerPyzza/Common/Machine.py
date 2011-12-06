#!/usr/bin/env python
"""
Machine

Common package

Objects that represent a machine
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
logger = logging.getLogger('Machine')

################################################################################
# Classes

class Machine(object):
    '''
    Class Machine
    Stores the raw command and the number of CPUs it should use
    Hostname, Username and Password are passed on creation
    '''
    def __init__(self,name,hostname,user):
        self.name = name
        self._hostname = hostname
        self._user = user
        self._password = None
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

################################################################################
# Methods

################################################################################
# Main

if __name__ == '__main__':
    pass