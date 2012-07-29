#!/usr/bin/env python
"""
Server

Common mod test

Server object running on Runner Pyzza daemon (RPdaemon) 
"""

__author__ = "Emilio Potenza"
__credits__ = ["Marco Galardini"]

from RunnerPyzza.Common.PyzzaTalk import PyzzaTalk
from RunnerPyzza.Common.System import System
from RunnerPyzza.ServerCommon.Job import Job, WorkerJob
from RunnerPyzza.Common.Machine import Machine
from time import sleep
import Queue
import logging
import time
import ConfigParser

################################################################################
# Log setup

# create logger
# Name shown
logger = logging.getLogger('RunnerPyzza.Server')


################################################################################

class WorkerManager():
    '''
    Manager for multiple jobs
    '''
    def __init__(self):
        self._jobs = {} # jobID:{"machine":[machinediz1, ..], "program":[programdiz1,...]}

    def getJob(self,name):
        if name not in self._jobs:
            return None
        return self._jobs[name]
    
    def rmJob(self,name):
        del self._jobs[name]
        
    def addJob(self,job):
        self._jobs[job.name] = job
        
        #START-JOB
    def startJob(self,name):
        job=self._jobs[name]
        logger.debug("Starting - JOB %s"%(job.name))
        j=WorkerJob(job)
        j.start()
        job.running = True
            
class Server():
    '''
    RunnerPyzza daemon server (RPdaemon)
    '''
    def __init__(self,port,config='/etc/runnerpyzza/RPdaemon.conf'):
        logger.info("Start RunnerPyzza Server")
        self.host = ""
        self.port = port
        self.manager = WorkerManager()
        self.PyzzaOven = PyzzaTalk(server = self.host, port=self.port)
        
        self.coutRestart = 0
        self.maxRestart = 5
        self.restartTime = 5 #in secs
        
        # Default machines
        self.defaultMachines = []
        cparser = ConfigParser.ConfigParser()
        cparser.read(config)
        if cparser.has_section('machines'):
            dMach = {}
            for machine in cparser.items('machines'):
                dMach[machine[0]] = machine[1]
            if cparser.has_section('users'):
                dUsr = {}
                for user in cparser.items('users'):
                    dUsr[user[0]] = user[1]
            for mach in dMach:
                if mach in dUsr:
                    user = dUsr[mach]
                else:
                    user = 'runnerpyzza'
                self.defaultMachines.append(Machine(mach, dMach[mach], user))
                logger.debug('Added default machine %s, %s, %s'%(mach, dMach[mach], user))
        
        while self.coutRestart < self.maxRestart:
            try:
                self.PyzzaOven.startServer()
                self.run()
            except Exception, e:
                self.coutRestart += 1
                logger.warning('Server error! %s'
                                %(e))
                logger.warning('Could not start the server on port %s'
                                %(self.port))
                logger.warning('Server Error number %s/%s ... Try again in %s sec'
                                %(self.coutRestart, self.restartTime, self.restartTime))
                sleep(self.restartTime)
            else:
                break
        
        logger.info("Stop RunnerPyzza Server")
        
        
    def run(self):
        self.ok = System("ok")
        self.fail = System("fail")
        self.queued = System("queued")
        self.done = System("done")
        
        self.quit=False
        
        while not self.quit:
            logger.info("Server is now waiting for client on port %s"%(self.port))
            # Attendi la connessione del lanciatore...
            self.PyzzaOven.accept()
            obj, mtype = self.PyzzaOven.getExtendedMessage()
            if mtype=="system":
                if obj.body == "init":
                    self.PyzzaOven.send(self.ok)
                    sleep(0.5)
                    self._initJob()
                        
                elif obj.body == "start":
                    try:
                        self._startJob(obj.ID)
                        sleep(0.5)
                        self.PyzzaOven.send(self.ok)
                    except Exception, e:
                        logger.error("Start Job Error: %s"%e)
                        self.PyzzaOven.send(self.fail)
                        continue
                        
                elif obj.body == "status":
                    try:
                        self.PyzzaOven.send(self.ok)
                        sleep(0.5)
                        self._statusJob(obj.ID)
                        
                    except Exception, e:
                        logger.error("Status Job Error: %s"%e)
                        self.PyzzaOven.send(self.fail)
                        continue
                            
                elif obj.body == "results":
                    sleep(0.5)
                    self._resultsJob(obj.ID)
                        
                elif obj.body == "clean":
                    self.PyzzaOven.send(self.ok)
                    sleep(0.5)
                    self._cleanJob(obj.ID)
                        
                else:
                    self.PyzzaOven.send(self.fail)
                    continue
            else:
                self.PyzzaOven.send(self.fail)
                continue
                
            obj, mtype = self.PyzzaOven.getExtendedMessage()        
            if mtype=="system":
                if obj.body == "quit":
                    self.PyzzaOven.socket.close()
                    sleep(1)
                    logger.info("Server : Connection close from %s %s"%(self.PyzzaOven.address))
                else:
                    self.PyzzaOven.socket.close()
                    sleep(1)
                    logger.info("Server : FORCE Connection close from %s %s"%(self.PyzzaOven.address))
            else:
                self.PyzzaOven.socket.close()
                sleep(1)
                logger.info("Server : FORCE Connection close from %s %s"%(self.PyzzaOven.address))
                #
                ####
    
    def _recvAKW(self):
        obj, mtype = self.PyzzaOven.getExtendedMessage()
        if mtype=="system":
            if obj.body == "ok":
                pass
            else:
                pass
    
    def _resultsJob(self, jid):
        job = self.manager.getJob(jid)
        
        if job and job.done:
            self.PyzzaOven.send(self.ok)
            copyqueue = Queue.Queue()
            while not job.programsResult.empty():
                p = job.programsResult.get()
                copyqueue.put(p)
                self.PyzzaOven.send(p)
                
                obj, mtype = self.PyzzaOven.getExtendedMessage()
                if mtype=="system":
                    if obj.body == "fail":
                        return
            
            job.programsResult = copyqueue
            self.PyzzaOven.send(System("save", id))
            
            obj, mtype = self.PyzzaOven.getExtendedMessage()
            if mtype=="system":
                if obj.body == "ok":
                    pass
                else:
                    logger.warning("Fail to close results connection")
            
            ###
            #set local
            obj, mtype = self.PyzzaOven.getExtendedMessage()
            if mtype == "system":
                if obj.body == "local":
                    self.PyzzaOven.send(self.ok)
                    if obj.ID == True:
                        obj, mtype = self.PyzzaOven.getExtendedMessage()
                        if mtype == "system":
                            if obj.body == "copydone":
                                self.PyzzaOven.send(self.ok)
                            else:
                                self.PyzzaOven.send(self.fail)
                        else:
                            self.PyzzaOven.send(self.fail)
                    else:
                        pass 
                else:
                    self.PyzzaOven.send(self.fail)
            else:
                self.PyzzaOven.send(self.fail)
            
        else:
            if job:
                logger.info("Job %s uncomplete... Try status"%job.name)
            else:
                logger.warning("Job %s doesn't exist"%id)
            self.PyzzaOven.send(self.fail)
        return 
    
    def _startJob(self, ID):
        
        logger.info("Start Job %s data"%(ID))
        try:
            self.manager.startJob(ID)
        except Exception, e:
            logger.warning("Cannot start Job %s"%(ID))
            logger.warning(e)
            raise e
                
    def _statusJob(self, jid):
        job = self.manager.getJob(jid)
        logger.info(job.name)
        
        if not job.running:
            logger.info("%s is queued"%job.name)
            self.PyzzaOven.send(self.queued)
        else:
            if job.status_error:
                logger.info("%s Exited with error"%job.name)
                stderr = ""
                replace_queue = Queue.Queue()
                while True:
                    line = job.error.get()
                    stderr = stderr + line + "\n"
                    replace_queue.put(line)
                    if job.error.empty():
                        break
                job.error = replace_queue
                error = System("error", stderr)
                logger.error(error)
                self.PyzzaOven.send(error)
            elif job.done:
                logger.info("%s is DONE!"%job.name)
                self.PyzzaOven.send(self.done)
            else:
                logger.info("%s is Running"%job.name)
                
                try:
                    tmp = job.status.get(False)
                    running = System("running", tmp)
                    job.status.put(tmp)
                except:
                    str_zero = "OK|| 0 || -- || 0"
                    running = System("running", str_zero)
                    
                self.PyzzaOven.send(running)
        self._recvAKW()
        
    def _cleanJob(self, ID):
        logger.info("Remove Job %s data"%(ID))
        try:
            self.manager.rmJob(ID)
        except Exception, e:
            logger.warning("Cannot remove Job %s"%(ID))
            logger.warning(e)
        
    def _initJob(self):
        ###
        #set jobID
        jobID = time.strftime('%Y%m%d_%H%M%S')
        obj, mtype = self.PyzzaOven.getExtendedMessage()
        if mtype=="system":
            if obj.body == "tag":
                self.PyzzaOven.send(self.ok)
                jobID = obj.ID + "_" + jobID
                self.PyzzaOven.send(System("jobID",jobID))
                self._recvAKW()
            else:
                self.PyzzaOven.send(self.fail)
        else:
            self.PyzzaOven.send(self.fail)
        
        job=Job(jobID)
        logger.info("Server : Initialize Job %s"%(jobID))
        
        # If we have default machines just ad them!
        if len(self.defaultMachines) > 0:
            job.defaultMachine(self.defaultMachines)
        
        ###
        #set local
        obj, mtype = self.PyzzaOven.getExtendedMessage()
        if mtype == "system":
            if obj.body == "local":
                self.PyzzaOven.send(self.ok)
                if obj.ID == True:
                    logger.info('Expecting an input upload on job %s'%jobID)
                    job.isNFS = False
                    
                    obj, mtype = self.PyzzaOven.getExtendedMessage()
                    if mtype == "system":
                        if obj.body == "copydone":
                            self.PyzzaOven.send(self.ok)
                            
                            job.extractInputs()
                        else:
                            self.PyzzaOven.send(self.fail)
                    else:
                        self.PyzzaOven.send(self.fail)
                else:
                    pass 
            else:
                self.PyzzaOven.send(self.fail)
        else:
            self.PyzzaOven.send(self.fail)
        #
        ###
        ###
        # machine program -->save = break while
        while 1:
            obj, mtype = self.PyzzaOven.getExtendedMessage()
            if mtype == "machine":
                logger.debug("Machine : %s"%(obj))
                job.addMachine(m)
                self.PyzzaOven.send(self.ok)

            elif mtype == "program":    
                logger.debug("Program :%s"%(obj))
                job.addProgram(obj)
                self.PyzzaOven.send(self.ok)
            
            elif mtype == "system":
                if obj.body == "save":
                    logger.debug("Save %s"%(jobID))
                    self.PyzzaOven.send(self.ok)
                    break
            else:
                logger.debug("FAIL client data = %s"%(obj))
                self.PyzzaOven.send(self.fail)
        #
        ###
        ####
        # Append to the main queue and start the job
        logger.info("Server : Append job %s to queue manager"%(jobID))
        self.manager.addJob(job)
                
        #
        ####        
        
    

                    
################################################################################
# Methods

################################################################################
# Main

if __name__ == '__main__':
    pass
