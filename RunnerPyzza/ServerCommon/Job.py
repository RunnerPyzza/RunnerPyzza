#!/usr/bin/env python
"""
Server

Common mod test

Server object running on Runner Pyzza daemon (RPdaemon) 
"""
from RunnerPyzza.Common.Program import Program
from time import sleep
import Queue
import logging
import os
import paramiko
import subprocess
import sys
import tarfile
import threading

__author__ = "Emilio Potenza"
__credits__ = ["Marco Galardini"]


################################################################################
# Log setup
# Name shown
logger = logging.getLogger('RunnerPyzza.Server.Job')
################################################################################

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
        #self.stdout = Queue.Queue()
        #self.stderr = Queue.Queue()
        self.isNFS = True
        self.localFolder = None
        self.status = Queue.LifoQueue()
        self.error = Queue.Queue()
        self.status_error = False
        self.running = False
    
    def __del__(self):
        if not self.isNFS:
            logger.info('Removing the input folder and the related archives')
            
            try:
                tarname = '%s_results.tar.gz'%self.name
                tarname = os.path.join('/home/runnerpyzza',tarname)
                os.remove(tarname)
                
                for fname in os.listdir(self.localFolder):
                    fname = os.path.join(self.localFolder, fname)
                    os.remove(fname)
                
                os.rmdir(self.localFolder)
            except Exception, e:
                logger.warning('Could not remove the input/output files (%s)'%e)          
        
    def extractInputs(self):
        '''
        Extracts the user provided compressed folder
        '''
        
        logger.info('Unpacking inputs in /home/runnerpyzza')
        # Creating the JOBID directory
        jobDir = os.path.join('/home/runnerpyzza', self.name)
        self.localFolder = jobDir
        try:
            os.mkdir(jobDir)
        except OSError, e:
            logger.debug('Got error %s on directory creation'%e)
        # Move the Archive there
        tarName = os.path.join('/home/runnerpyzza',
                               '%s.tar.gz'%self.name)
        try:
            tarjob = tarfile.open(tarName, 'r:gz')
            tarjob.extractall(jobDir)
            os.remove(tarName)
        except Exception, e:
            logger.warning('Could not handle the inputs (%s)'%e)
        
    def compressResults(self):
        '''
        Creates a compressed tar file for the job results
        '''
        logger.info('Creating results tar file (%s)'%self.name)
            
        try:
            tarname = '%s_results.tar.gz'%self.name
            tarname = os.path.join('/home/runnerpyzza',tarname)
            tar = tarfile.open(tarname,'w:gz')
            for fname in os.listdir(self.localFolder):
                longname = os.path.join(self.localFolder, fname)
                shortname = os.path.join(os.path.split(self.localFolder)[-1], fname)
                tar.add(longname, arcname=shortname)
            tar.close()
        except Exception, e:
            logger.warning('Could not create the results archive (%s)'%e)
    
    def addMachine(self, m):
        """Append a Machine specific for this job """
        self.machines.append(m)
    
    def defaultMachine(self, machines):
        """Set default machines if no there's no specific machine"""
        if not self.machines:
            self.machines = machines
            
    def addProgram(self, p):
        """Append a Program specific for this job """
        self.programs.append(p)
    
    def iterResults(self):
        copyqueue = Queue.Queue()
        while not self.programsResult.empty():
            p = self.programsResult.get()
            copyqueue.put(p)
            yield p
        self.programsResult = copyqueue
        return
        
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
        
        self.connections=[]
        self.threads = []
        self.outlock = threading.Lock()
        
        self.tryAgent = False

    def _startAgent(self):
        '''
        Try once to start the ssh-agent
        An exception is raised if it's the second time this method has been tried
        '''
        if self.tryAgent:
            raise OSError('We have already tried to start ssh-agent!')
        
        cmd = 'eval $(ssh-agent -a ~/.ssh/agent.socket)'
        proc = subprocess.Popen(cmd,shell=(sys.platform!="win32"),
                    stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
        out = proc.communicate()
        self.tryAgent = True

    def _connect(self, host):
        """Connect to the host"""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(host.getHostname(), username=host.getUser())
        except Exception, e:
            # It didn't work, we give up?
            # We should try a little bit more
            self.machines.remove(host)
            logger.warning('Could not connect to %s (%s)'%(host.getHostname(), e))
            raise RuntimeError('Could not connect to %s (%s)'%(host.getHostname(), e))
        logger.info("Job %s: %s is now connected to user %s"%(self.name, host.getHostname(),host.getUser()))
        return client

    def _workFun(self, host, conn, program, step):
        try:
            command = program.getCmd()

            if not self.job.isNFS:
                # Move to the job directory
                command = 'cd %s; '%self.job.localFolder + command
    
            with self.outlock:
                logger.info("%s ==> %s"%(host.getHostname(),command))
                
            program.setHost(host.getHostname())
                
            chan = conn.get_transport().open_session()
            chan.exec_command(command)
            stdout = chan.makefile("rb", 1024)
            stderr = chan.makefile_stderr("rb", 1024)
            
            for line in stdout.read().splitlines():
                with self.outlock:
                    program.addStdOut(line)
                    logger.info("""\033[1;32m[%s - out]\033[0m : %s""" % (host.getHostname(), line))
            for line in stderr.read().splitlines():
                with self.outlock:
                    program.addStdErr(line)
                    logger.info("""\033[1;31m[%s - err]\033[0m : %s""" % (host.getHostname(), line))
            
            exit_status = chan.exit_status
            chan.close()
            
            program.setExit(exit_status)
            self.job.programsResult.put(program)
    
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

        except Exception, e:
            logger.error('Command %s error (%s)'%(command,e))
            
            program.setExit(999)
            self.job.programsResult.put(program)
    
            with self.outlock:
                self.job.status_error = True
                self.job.error.put("FAIL||%s||"%step + command + "||999")
                logger.info("FAIL||%s||"%step + command + "||999")   

    def _quit(self):
        """Close all the connections and exit"""
        for conn in self.connections:
            try:
                conn.close()
            except Exception, e:
                logger.warning('Could not close a connection %s'%e)
        return 
    
    def setErrJobs(self,prg=None,step=0,err='Generic error'):
        '''
        Put an error flag on the jobs tail
        '''
        if prg:
            command = prg.getCmd()
                    
            prg.addStdErr(err)
            prg.setExit(999)
            self.job.programsResult.put(prg)
                
            self.job.status.put("FAIL||%s||"%step + command + "||999")
            logger.info("FAIL||%s||"%step + command + "||999")
        
        for step,queue in enumerate(self.listOFqueue):
            while not queue.empty():
                with self.outlock:
                    program = queue.get()
                    command = program.getCmd()
                    
                    program.addStdErr(err)
                    program.setExit(999)
                    self.job.programsResult.put(program)
                    
                    self.job.status.put("FAIL||%s||"%step + command + "||999")
                    logger.info("FAIL||%s||"%step + command + "||999")
    
    def checkMachines(self):
        '''
        Check how many machines we have left
        Raises an exception otherwise
        '''
        if len(self.machines) == 0:
            logger.error('No online machines are left')
            return False
        return True

    def setTotalCpus(self):
        '''
        Cycle over the machines and get the total number of CPUs
        '''
        
        for machine in self.machines:
            if not self.checkMachines():
                return False
            try:
                conn = self._connect(machine)
            except:continue
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
        return True

    def getFreeMachine(self, ncpu):
        '''
        Get the suitable machine for this command
        If return None no machine is free at the moment
        '''
        if ncpu > self.bigMachine:
            ncpu = self.bigMachine
        free_list = []
        for machine in self.machines:
            if not self.checkMachines():
                return None
            logger.info('Asking free CPU for %s'%machine.getHostname())
            try:
                conn = self._connect(machine)
            except:continue
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
        """
        Execute commands queue on all hosts in the list
        """
        logger.info("Job %s will now run"%(self.name))
        
        # Ask the total number of cpus for each machine
        if not self.setTotalCpus():
            self.setErrJobs(self, err='No more online machines')
    
        bQuit = False
        for step,queue in enumerate(self.listOFqueue):
            while not queue.empty():
                program = queue.get()
                ncpu = program.getCpu()
                
                # Cycle until we got a working machine
                while True:
                    if not self.checkMachines():
                        self.setErrJobs(program, step, 'No more online machines')
                        bQuit = True
                        break
                    
                    machine = self.getFreeMachine(ncpu)
                    if not machine:
                        queue.put(program)
                        sleep(3.3)
                        continue
                    try:
                        conn = self._connect(machine)
                        break
                    except:pass
                    
                if bQuit:
                    break
                
                t = threading.Thread(target=self._workFun, args=(machine, conn, program, step))
                t.setDaemon(True)        
                t.start()
                self.threads.append(t)
                logger.info("Job %s: start thread on %s"%(self.name, machine))
            
            for t in self.threads:
                t.join()
            self.threads = []
                
        # Do we have to create a compressed results folder?
        if not self.job.isNFS:
            self.job.compressResults()
        
        self.job.done=True
        if self.job.status_error:
            logger.info("Job %s: Error!"%(self.name))
        else:
            logger.info("Job %s: Done!"%(self.name))