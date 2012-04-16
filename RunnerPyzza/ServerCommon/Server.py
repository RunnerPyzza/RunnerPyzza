#!/usr/bin/env python
"""
Server

Common mod test

Server object running on Runner Pyzza daemon (RPdaemon) 
"""

__author__ = "Emilio Potenza"
__credits__ = ["Marco Galardini"]

import logging
import socket
import sys
from getpass import getpass
import threading     
import Queue
import paramiko
from time import sleep
import time
from RunnerPyzza.Common.JSON import JSON
from RunnerPyzza.Common.System import System
from RunnerPyzza.Common.Protocol import iProtocol, oProtocol
from RunnerPyzza.Common.PyzzaTalk import PyzzaTalk

################################################################################
# Log setup

# create logger
# Name shown
logger = logging.getLogger('RunnerPyzza.Server')


################################################################################

#Tread del manager code
class WorkerJob(threading.Thread):
    def __init__ (self,job):
        threading.Thread.__init__(self)
        self.name = job.name
        self.thread_stop = False
        self.programs = job.programs
        self.listOFqueue = []
                
        ###TEST CONVERSION###
        #order from 0 to infinite
        order = 0
        while True:
            queue = Queue.Queue()
            for p in job.programs:
                if int(p.getOrder()) == order:
                    queue.put(p)
            if queue.empty():
                break
            else:
                self.listOFqueue.append(queue)
            order += 1
        logger.debug(self.listOFqueue)
                    
            
        #####################
        self.job=job
        #print job.name
        self.machines=job.machines
        self.bigMachine = 0
        # Ask the total number of cpus for each machine
        self.setTotalCpus()
        
        self.connections=[]
        self.threads = []
        self.outlock = threading.Lock()

    def _connect(self, host):
        """Connect to all hosts in the hosts list"""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host.getHostname(), username=host.getUser(), password=host.getPassword())
        #self.connections.append(client)
        logger.info("Job %s: %s is now connected to user %s"%(self.name, host.getHostname(),host.getUser()))
        return client

    def _workFun(self, host, conn, program, step):
        try:    
            command = program.getCmd()

            with self.outlock:
                logger.info("... %s ==> %s"%(host.getHostname(),command))
                
            chan = conn.get_transport().open_session()
            chan.exec_command(command)
            stdout = chan.makefile("rb", 1024)
            stderr = chan.makefile_stderr("rb", 1024)
            
            for line in stdout.read().splitlines():
                with self.outlock:
                    program.addStdOut(line)
                    logger.info("""\033[1;32m[%s - out]\033[0m : %s""" % (host.getHostname(), line))
                    self.job.stdout.put("""\033[1;32m[%s - out]\033[0m : %s\n""" % (host.getHostname(), line))
            for line in stderr.read().splitlines():
                with self.outlock:
                    program.addStdErr(line)
                    logger.info("""\033[1;31m[%s - err]\033[0m : %s""" % (host.getHostname(), line))
                    self.job.stderr.put("""\033[1;31m[%s - err]\033[0m : %s\n""" % (host.getHostname(), line))
                    
            exit_status = chan.exit_status
            program.setHost(host.getHostname())
            program.setExit(exit_status)
            self.job.programsResult.put(program)
            chan.close()
                            
            with self.outlock:
                if  exit_status == 0:
                    # If cmd exit correctly
                    self.job.status.put("OK||%s||"%step + command + "||%s"%exit_status)
                    logger.info("OK||%s||"%step + command + "||%s"%exit_status)
                elif (exit_status != 0 and program.getCanFail()):
                    # If cmd exit correctly or Can Fail
                    self.job.status.put("PASS||%s||"%step + command + "||%s"%exit_status)
                    self.job.error.put("PASS||%s||"%step + command + "||%s"%exit_status)
                    logger.info("PASS||%s||"%step + command + "||%s"%exit_status)
                elif (exit_status != 0 and not program.getCanFail()):
                    # If cmd fail and Can't Fail
                    self.job.status_error = True
                    self.job.error.put("FAIL||%s||"%step + command + "||%s"%exit_status)
                    logger.info("FAIL||%s||"%step + command + "||%s"%exit_status)   
                else:
                    # else--- error
                    self.job.status_error = True
                    self.job.error.put("ELSE||%s||"%step + command + "||%s"%exit_status)
                             
        except KeyboardInterrupt:
            logger.error("do quit thread")
            #self._quit(None)
        except Exception as e:
            logger.error(e)    

    def _quit(self):
        """Close all the connections and exit"""
        for conn in self.connections:
            conn.close()
        return 

    def setTotalCpus(self):
        '''
        Cycle over the machines and get the total number of CPUs
        '''
        
        for machine in self.machines:
            conn = self._connect(machine)
            # cat /proc/cpuinfo | grep processor | wc -l
            stdin, stdout, stderr = conn.exec_command("cat /proc/cpuinfo | grep processor | wc -l")
            stdin.close()
            stderr.close()
            ncpu = int(stdout.read().splitlines()[0])
            logger.info("Machine %s has %d CPUs"%(machine.getHostname(),ncpu))
            machine.setCpu(ncpu)
            if ncpu > self.bigMachine:
                self.bigMachine = ncpu
            conn.close()

    def getFreeMachine(self, ncpu):
        '''
        Get the suitable machine for this command
        If return None no machine is free at the moment
        '''
        if ncpu > self.bigMachine:
            ncpu = self.bigMachine
        free_list = []
        for machine in self.machines:
            logger.info('Asking free CPU for %s'%machine.getHostname())
            conn = self._connect(machine)
            stdin, stdout, stderr = conn.exec_command("ps -eo pcpu | sort -h -r")
            stdin.close()
            stderr.close()
            mach_load = 0.0
            for line in stdout.read().splitlines():
                try:
                    line = line.strip()
                    mach_load += float(line)
                except:
                    pass
            free_mach = (machine.getCpu() * 100.0) - mach_load
            if free_mach < 100 and free_mach > 77:
                free_mach = 100.0
            free_list.append(free_mach)
            conn.close()
            logger.info('Machine %s has %f free CPU space'%(machine.getHostname(), free_mach))
            
        maxLoad = max(free_list)
        for mach,mach_load in zip(self.machines, free_list):
            if mach_load == maxLoad:
                logger.info('Machine %s is the most free'%mach.getHostname())
                reqLoad = (ncpu - 1) * 100
                logger.info('Manager asking for %s CPU space'%reqLoad)
                if mach_load > reqLoad:
                    return mach
        
        logger.warning('No free machine was found!')
        return None

    def run(self):
        '''
        Connect
        '''
        logger.info("Job %s: is now running"%(self.name))
        #self._connect()
        logger.info("Job %s: all the machine is now correctly connected"%(self.name))
        """
        Execute commands queue on all hosts in the list
        """
        for step,queue in enumerate(self.listOFqueue):
            try:
                while not queue.empty():
                    program = queue.get()
                    ncpu = program.getCpu()
                    machine = self.getFreeMachine(ncpu)
                    if not machine:
                        queue.put(program)
                        sleep(3.3)
                        continue
                    # connect
                    conn = self._connect(machine)
                    t = threading.Thread(target=self._workFun, args=(machine, conn, program, step))
                    t.setDaemon(True)        
                    t.start()
                    self.threads.append(t)
                    logger.info("Job %s: start thread on %s"%(self.name, machine))
                
                for t in self.threads:
                    t.join()
                self.threads = []
            
            except KeyboardInterrupt:
                logger.info("Job %s: KeyboardInterrupt"%(self.name))
                self._quit()
                
        #self._quit()
        self.job.done=True
        logger.info("Job %s: Done!"%(self.name))
        
#        for step,queue in enumerate(self.listOFqueue):
#            print step , queue
#            # update global queue
#            try:        
#                for host, conn in zip(self.machines, self.connections):
#                    queue.put("break")
#                    t = threading.Thread(target=self._workFun, args=(host, conn, queue, step))
#                    t.setDaemon(True)        
#                    t.start()
#                    self.threads.append(t)
#                    logger.info("Job %s: start thread on %s"%(self.name,host))
#                queue.join()
#            except KeyboardInterrupt:
#                logger.info("Job %s: KeyboardInterrupt"%(self.name))
#                self._quit()
#        self._quit()
#        self.job.done=True
#        logger.info("Job %s: Done!"%(self.name))

class WorkerManager():
    '''
    Manager for multiple jobs
    '''
    def __init__(self):
        self._jobs = {} # jobID:{"machine":[machinediz1, ..], "program":[programdiz1,...]}

    def getJob(self,name):
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

class Job():
    '''
    Job structure (and record??) running in WorkerManager
    '''
    def __init__(self,jobID):
        self.name = jobID
        self.machines = []
        self.programs = []
        self.programsResult = Queue.Queue() # with program obj
        self.done = False
        self.stdout = Queue.Queue()
        self.stderr = Queue.Queue()
        self.isNFS = True
        self.status = Queue.LifoQueue()
        self.error = Queue.Queue()
        self.status_error = False
        self.running = False
        


class Server():
    '''
    RunnerPyzza daemon server (RPdaemon)
    '''
    def __init__(self,port):
        logger.info("Start RunnerPyzza Server")
        self.host = ""
        self.port = port
        self.manager = WorkerManager()
        self.PyzzaOven = PyzzaTalk(server = self.host, port=self.port)
        
        self.coutRestart = 0
        self.maxRestart = 5 # try to restart a server after a crash for X time
        self.restartTime = 5 #in sec
        
        
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
            obj, type = self.PyzzaOven.getExtendedMessage()
            if type=="system":
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
                    self.PyzzaOven.send(self.ok)
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
                
            obj, type = self.PyzzaOven.getExtendedMessage()        
            if type=="system":
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
        obj, type = self.PyzzaOven.getExtendedMessage()
        if type=="system":
            if obj.body == "ok":
                pass
            else:
                pass
    
    def _resultsJob(self, id):
        job = self.manager.getJob(id)
        logger.info(job.name)
        if job.done:
            copyqueue = Queue.Queue()
            while not job.programsResult.empty():
                p = job.programsResult.get()
                copyqueue.put(p)
                self.PyzzaOven.send(p)
                
                obj, type = self.PyzzaOven.getExtendedMessage()
                if type=="system":
                    if obj.body == "fail":
                        return
            
            job.programsResult = copyqueue
            self.PyzzaOven.send(System("save", id))
            
            obj, type = self.PyzzaOven.getExtendedMessage()
            if type=="system":
                if obj.body == "ok":
                    return 
                else:
                    logger.warning("Fail to close results connection")
        else:
            logger.info("Job %s uncomplete ...Try status"%job.name)
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
                
    def _statusJob(self, id):
        job = self.manager.getJob(id)
        logger.info(job.name)
        
        if not job.running:
            logger.info("%s is queued"%job.name)
            self.PyzzaOven.send(self.queued)
        else:
            if job.status_error:
                logger.info("%s Exit with error"%job.name)
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
            looger.warning(e)
        
    def _initJob(self):
        ###
        #set jobID
        jobID = time.strftime('%Y%m%d_%H%M%S')
        obj, type = self.PyzzaOven.getExtendedMessage()
        if type=="system":
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
        ###
        #set local
        obj, type = self.PyzzaOven.getExtendedMessage()
        if type == "system":
            if obj.body == "local":
                self.PyzzaOven.send(self.ok)
                if obj.ID == True:
                    obj, type = self.PyzzaOven.getExtendedMessage()
                    if type == "system":
                        if obj.body == "Copydone":
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
        #
        ###
        ###
        # machine program -->save = break while
        while 1:
            obj, type = self.PyzzaOven.getExtendedMessage()
            if type == "machine":
                logger.debug("Machine : %s"%(obj))
                job.machines.append(obj)
                self.PyzzaOven.send(self.ok)

            elif type == "program":    
                logger.debug("Program :%s"%(obj))
                job.programs.append(obj)
                self.PyzzaOven.send(self.ok)
            
            elif type == "system":
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
