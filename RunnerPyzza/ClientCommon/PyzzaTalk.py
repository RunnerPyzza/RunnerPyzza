#!/usr/bin/env python
"""
PyzzaTalk

ClientCommon Library

PyzzaTalk classes for the clients
"""
from RunnerPyzza.Common.Protocol import iProtocol, oProtocol
from RunnerPyzza.Common.System import System
import logging
import socket
import time

__author__ = "Marco Galardini"
__credits__ = ["Emilio Potenza"]

################################################################################
# Log setup

logger = logging.getLogger('RunnerPyzza.PyzzaTalk')

################################################################################
# Classes

class PyzzaTalk(object):
    '''
    Base class for the PyzzaTalk protocol
    Opens the connection, sends messages
    Receives replies, closes the connections
    '''
    def __init__(self, server, port):
        self.server = server
        self.port = int(port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.iprtcl = iProtocol()
        self.oprtcl = oProtocol()
        
    def connect(self):
        '''
        Opens the connection with the desired server
        '''
        try:
            self.socket.connect( (self.server, self.port) )
        except Exception, e:
            logger.warning('Connection error! %s'
                            %(e))
            logger.warning('Could not connect to %s on port %s'
                            %(self.server, self.port))
            raise e
    
    def send(self, obj):
        '''
        Send a obj to the server
        Automatically converted with the PyzzaProtocol
        True if it worked, False otherwise
        '''
        if hasattr(obj, 'body'):
            logger.warning('--> %s'%obj.body)
        msg = self.oprtcl.interpretate(obj)
        try:
            self.socket.send( str(msg) )
        except Exception, e:
            logger.warning('Send error! %s'
                            %(e))
            raise e
    
    def getMessage(self):
        '''
        Receive data from the server
        Automatically converted with the PyzzaProtocol
        BLOCKING CALL
        '''
        try:
            msg = self.socket.recv(1024)
            obj = self.iprtcl.interpretate(msg)
            if hasattr(obj, 'body'):
                logger.warning('<-- %s'%obj.body)
            else:
                print obj
                print msg
            return obj
        except Exception, e:
            logger.warning('Receive error! %s'
                            %(e))
            raise e
    
    def close(self):
        '''
        Close the connection with the server
        Uses the quit message from the PyzzaProtocol
        '''
        obj = System("quit")
        self.send(obj)
        time.sleep(1)
        self.socket.close()

class OrderPyzza(PyzzaTalk):
    '''
    Initialize a new job
    Order a new pyzza
    '''
    def __init__(self, server, port, machines = [], programs = [],
                 tag = 'Generic', local = False):
        PyzzaTalk.__init__(self, server, port)
        self.connect()
        self.machines = machines
        self.programs = programs
        self.tag = tag
        self.local = local
        self.jobID = None
    
    def copyInputs(self):
        '''
        Copy my inputs using scp
        [STUB]
        '''
        time.sleep(10)
    
    def launchOrder(self):
        '''
        Perform all the steps to order a new pyzza
        '''
        self.send(System('init'))
        if self.getMessage().body == 'fail':
            return False
        
        self.send(System('tag',self.tag))
        if self.getMessage().body == 'fail':
            return False
        self.jobID = self.getMessage().ID
        self.send(System('ok'))
        
        if self.local:
            self.send(System('local',True))
            if self.getMessage().body == 'fail':
                return False
            self.copyInputs()
            self.send(System('copydone',self.jobID))
            if self.getMessage().body == 'fail':
                return False
        else:
            self.send(System('local',False))
            if self.getMessage().body == 'fail':
                return False
            
        for machine in self.machines:
            self.send(machine)
            if self.getMessage().body == 'fail':
                return False
            
        for program in self.programs:
            self.send(program)
            if self.getMessage().body == 'fail':
                return False
        
        self.send(System('save',self.jobID))
        
        if self.getMessage().body == 'fail':
            return False
        
        self.close()
        return True
        
class OvenPyzza(PyzzaTalk):
    '''
    Start the desired job
    Put the pyzza in the oven
    '''
    def __init__(self, server, port, jobID):
        PyzzaTalk.__init__(self, server, port)
        self.connect()
        self.jobID = jobID
    
    def putInTheOven(self):
        '''
        Perform all the steps to put the pyzza in the oven
        '''
        self.send(System('start',self.jobID))
        if self.getMessage().body == 'fail':
            return False
            
        self.close()
        return True
        
class CheckPyzza(PyzzaTalk):
    '''
    Check the desired job status
    Check the pyzza in the oven: is it ready or burned?
    '''
    def __init__(self, server, port, jobID):
        PyzzaTalk.__init__(self, server, port)
        self.connect()
        self.jobID = jobID
        
        self.status = None
        self.step = None
    
    def isReady(self):
        if self.status == 'done':
            return True
        else:
            return False
            
    def isCooking(self):
        if self.status == 'running':
            return True
        else:
            return False
            
    def isWaiting(self):
        if self.status == 'queued':
            return True
        else:
            return False
    
    def isBurned(self):
        if self.status == 'error':
            return True
        else:
            return False
            
    def getLastSlice(self):
        return self.step.split('||')
            
    def inspectErrors(self):
        errors = []
        for error in self.step.splitlines():
            errors.append(error.split('||'))
        return errors
            
    def checkTheOven(self):
        '''
        Perform all the steps to check the pyzza in the oven
        '''
        self.send(System('status',self.jobID))
        if self.getMessage().body == 'fail':
            return False
        statusmsg = self.getMessage()
        self.status = statusmsg.body
        self.step = statusmsg.ID
        self.send(System('ok'))

        self.close()
        return True

class EatPyzza(PyzzaTalk):
    '''
    Get the desired job results
    Eat the pyzza!
    '''
    def __init__(self, server, port, jobID):
        PyzzaTalk.__init__(self, server, port)
        self.connect()
        self.jobID = jobID
        
        self.results = {}
        
    def getSlices(self):
        '''
        Generate the pyzza slices
        '''
        for step in sorted(self.results.keys()):
            yield step
            
    def eatSlice(self,step):
        '''
        Return each bit of the slice
        '''
        for program in self.results[step]:
            yield program
        
    def eatThePyzza(self):
        '''
        Perfomr all the actions to eat a delicious pyzza
        '''
        self.send(System('results',self.jobID))
        if self.getMessage().body == 'fail':
            return False

        while True:
            msg = self.getMessage()
            if not msg:
                continue
            
            if msg.type == "program":
                if msg.order not in self.results:
                    self.results[msg.order] = []
                self.results[msg.order].append(msg)
                
                self.send(System('ok'))
            
            elif msg.type == "system":
                if msg.body == "save":
                    if len(self.results) == 0:
                        self.send(System('fail'))
                        self.close()
                        return False
                    else:
                        self.send(System('ok'))
                    break
                
            else:
                self.send(System('fail'))
        
        # Here scp
        
        self.close()
        return True
        
class CleanPyzza(PyzzaTalk):
    '''
    Clean the informations about a job
    Clean the table (and pay!)
    '''
    pass
        