#!/usr/bin/env python
"""
PyzzaTalk

ClientCommon Library

PyzzaTalk classes for the clients
"""
from RunnerPyzza.Common.PyzzaTalk import PyzzaTalk
from RunnerPyzza.Common.System import System
import tarfile
import logging
import os
import shutil

# TODO: add more logs

__author__ = "Marco Galardini"
__credits__ = ["Emilio Potenza"]

################################################################################
# Log setup

logger = logging.getLogger('RunnerPyzza.PyzzaTalk')

################################################################################
# Classes

class OrderPyzza(PyzzaTalk):
    '''
    Initialize a new job
    Order a new pyzza
    '''
    def __init__(self, server, port, machines = [], programs = [],
                 tag = 'Margherita', local = False, localdir = '',
                 user = 'runnerpyzza', password = ''):
        PyzzaTalk.__init__(self, server, port)
        self.connect()
        self.machines = machines
        self.programs = programs
        self.tag = tag
        
        # "local" variables
        self.local = local
        self.localdir = localdir
        self.user = user
        self.password = password
        #
        
        self.jobID = None
    
    def copyInputs(self):
        '''
        Copy my inputs using sftp
        '''
        # Check if the stuff is there
        if not os.path.exists(self.localdir):
            logger.error('Cannot find the directory to be copied! (%s)'%self.localdir)
            return False
        
        if not os.path.isdir(self.localdir):
            logger.error('Expecting a directory! (%s)'%self.localdir)
            return False
        
        # Perform the directory compression
        startdir = os.path.abspath('.')
        # Move into the local directory
        os.chdir(self.localdir)
        tarname = '%s.tar.gz'%self.jobID
        tar = tarfile.open(tarname,'w:gz')
        for fname in os.listdir('.'):
            tar.add(fname)
        tar.close()
        
        # Move the tarfile into the start directoy
        shutil.move(tarname, startdir)
        
        # Return back
        os.chdir(startdir)
        
        # Send it
        sftp, client = self.getSFTP(self.user, self.password)
        sftp.put(tarname, '/home/%s/%s'%('runnerpyzza',
                                         os.path.split(tarname)[-1]))
        sftp.close()
        client.close()
        
        return True
    
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
            if not self.copyInputs():
                self.send(System('copyfail',self.jobID))
                self.getMessage()
                return False
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
    def __init__(self, server, port, jobID, local = False,
                 user = 'runnerpyzza', password = ''):
        PyzzaTalk.__init__(self, server, port)
        self.connect()
        self.jobID = jobID
        
        # "local" variables
        self.local = local
        self.user = user
        self.password = password
        #
        
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
            
    def copyResults(self):
        '''
        Copy my results using sftp
        '''
        # Get it
        sftp, client = self.getSFTP(self.user, self.password)
        tarname = self.jobID + '_results.tar.gz'
        sftp.get('/home/runnerpyzza/%s'%tarname, './%s'%tarname)
        sftp.close()
        client.close()
        
        return True
        
    def eatThePyzza(self):
        '''
        Perform all the actions to eat a delicious pyzza
        '''
        self.send(System('results',self.jobID))
        if self.getMessage().body == 'fail':
            self.close()
            return False

        while True:
            obj,type = self.getExtendedMessage()
            if not obj:
                continue
            
            if type == "program":
                if obj.getOrder() not in self.results:
                    self.results[obj.getOrder()] = []
                self.results[obj.getOrder()].append(obj)
                
                self.send(System('ok'))
            
            elif type == "system":
                if obj.body == "save":
                    if len(self.results) == 0:
                        self.send(System('fail'))
                        self.close()
                        return False
                    else:
                        self.send(System('ok'))
                    break
                
            else:
                self.send(System('fail'))
        
        if self.local:
            self.send(System('local',True))
            if self.getMessage().body == 'fail':
                return False
            if not self.copyResults():
                self.send(System('copyfail',self.jobID))
                self.getMessage()
                return False
            self.send(System('copydone',self.jobID))
            if self.getMessage().body == 'fail':
                return False
        else:
            self.send(System('local',False))
            if self.getMessage().body == 'fail':
                return False
        
        self.close()
        return True
        
class CleanPyzza(PyzzaTalk):
    '''
    Clean the informations about a job
    Clean the table (and pay!)
    '''
    def __init__(self, server, port, jobID):
        PyzzaTalk.__init__(self, server, port)
        self.connect()
        self.jobID = jobID
        
    def cleanAndPay(self):
        '''
        Perfomr all the actions to clean the table and pay your pyzza
        '''
        self.send(System('clean',self.jobID))
        if self.getMessage().body == 'fail':
            return False

        self.close()
        return True
        