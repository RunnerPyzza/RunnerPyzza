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
import time
from time import sleep
from RunnerPyzza.Common.JSON import JSON
from RunnerPyzza.Common.System import System
from RunnerPyzza.Common.Protocol import iProtocol, oProtocol

################################################################################
# Log setup

# create logger
# Name shown
logger = logging.getLogger('Server')


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
                    queue.put(p.getCmd())
            if queue.empty():
                break
            else:
                self.listOFqueue.append(queue)
            order += 1
        print self.listOFqueue
                    
            
        #####################
        self.job=job
        self.machines=job.machines
        self.connections=[]
        self.threads = []
        self.outlock = threading.Lock()

    def _connect(self):
        """Connect to all hosts in the hosts list"""
        for host in self.machines:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            #print host.getHostname(), host.getUser(), host.getPassword()
            client.connect(host.getHostname(), username=host.getUser(), password=host.getPassword())
            self.connections.append(client)
            logging.info("Job %s: %s is now connected to user %s"%(self.name, host.getHostname(),host.getUser()))


    def _workFun(self,host, conn, queue, step):
        while True:
            try:
                command=queue.get()
                if command=="break":
                    queue.task_done()
                    break    
                #self.raw_notify("%s> Command in queue start"%(host[0]),command)
                with self.outlock:
                    logging.info("... %s ==> %s"%(host.getHostname(),command))
                                
                    chan = conn.get_transport().open_session()
                    chan.exec_command(command)
                    stdout = chan.makefile("rb", 1024)
                    stderr = chan.makefile_stderr("rb", 1024)
                    #stdin, stdout, stderr = conn.exec_command(command)
                    #stdin.close()
                    for line in stdout.read().splitlines():
                        with self.outlock:
                            logging.info("""\033[1;32m[%s - out]\033[0m : %s""" % (host.getHostname(), line))
                                                #self.job.stdout=self.job.stdout+"""\033[1;32m[%s - out]\033[0m : %s\n""" % (host.getHostname(), line)
                            self.job.stdout.put("""\033[1;32m[%s - out]\033[0m : %s\n""" % (host.getHostname(), line))
                            print """\033[1;32m[%s - out]\033[0m : %s\n""" % (host.getHostname(), line)
                for line in stderr.read().splitlines():
                    with self.outlock:
                        logging.info("""\033[1;31m[%s - err]\033[0m : %s""" % (host.getHostname(), line))
                        #self.job.stderr=self.job.stderr+"""\033[1;31m[%s - err]\033[0m : %s\n""" % (host.getHostname(), line)
                        self.job.stderr.put("""\033[1;31m[%s - err]\033[0m : %s\n""" % (host.getHostname(), line))
                        print """\033[1;31m[%s - err]\033[0m : %s\n""" % (host.getHostname(), line)
                        exit_status = chan.exit_status
                        chan.close() 
                queue.task_done()
                                
                with self.outlock:
                    self.job.status.put("%s||"%step + command + "||%s"%exit_status)
                    print "%s||"%step + command + "||%s"%exit_status
                    if exit_status != 0:
                        self.job.status_error = True
                        self.job.error.put("%s||"%step + command + "||%s"%exit_status)
                                
            except KeyboardInterrupt:
                print "do quit thread"
                self._quit(None)
                break
            except Exception as e:
                print e    

    def _quit(self):
        """Close all the connections and exit"""
        for conn in self.connections:
            conn.close()
        return 

    def run(self):
        '''
        Connect
        '''
        logging.info("Job %s: is now running"%(self.name))
        self._connect()
        logging.debug("Job %s: all the machine is now correctly connected"%(self.name))
        """
        Execute commands queue on all hosts in the list
        """
        for step,queue in enumerate(self.listOFqueue):
            print step , queue
            # update global queue
            try:        
                for host, conn in zip(self.machines, self.connections):
                    queue.put("break")
                    t = threading.Thread(target=self._workFun, args=(host, conn, queue, step))
                    t.setDaemon(True)        
                    t.start()
                    self.threads.append(t)
                    logging.info("Job %s: start thread on %s"%(self.name,host))
                queue.join()
            except KeyboardInterrupt:
                logging.info("Job %s: KeyboardInterrupt"%(self.name))
                self._quit()
        self._quit()
        self.job.done=True
        logging.info("Job %s: Done!"%(self.name))

class WorkerManager():
    '''
    Manager for multiple jobs
    '''
    def __init__(self):
        self._jobs = {} # jobID:{"machine":[machinediz1, ..], "program":[programdiz1,...]}

    def getJob(self,name):
        return self._jobs[name]
    def addJob(self,job):
        self._jobs[job.name] = job
        #START-JOB
    def startJob(self,name):
        self.test(name)
                
    def test(self,name):
        job=self._jobs[name]
        logging.debug("TEST - JOB %s"%(job.name))
        logging.debug("TEST - JOB %s"%(job.machines))
        logging.debug("TEST - JOB %s"%(job.programs))
        j=WorkerJob(job)
        j.start()

class Job():
    '''
    Job structure (and record??) running in WorkerManager
    '''
    def __init__(self,jobID):
        self.name = jobID
        self.machines = []
        self.programs = []
        self.done = False
        self.stdout = Queue.Queue()
        self.stderr = Queue.Queue()
        self.isNFS = True
        self.status = Queue.Queue()
        self.error = Queue.Queue()
        self.status_error = False
        
        

class Server():
    '''
    RunnerPyzza daemon server (RPdaemon)
    '''
    def __init__ (self,port):
        #try:
        # run server
        #except:
        # restart server
        self.manager = WorkerManager()
        self.msgHandler = JSON()
        ####
        # Create a server
        logging.info("Start RunnerPyzza Server")
        host = ""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen(5)
        #
        ####
        
        self.iPP=iProtocol()
        self.oPP=oProtocol()
        self.ok = self.oPP.interpretate(System("ok"))
        self.fail = self.oPP.interpretate(System("fail"))
        
        
        quit=False
        while not quit:
            logging.info("Server is now waiting for client on port %s"%(port))
            # Attendi la connessione del lanciatore...
            client_socket, address = server_socket.accept()
            logging.info("Server : Connection requenst from %s %s"%(address))
            ####
            # Connection Mode [init,status,results,clean]
            # read
            client_data = client_socket.recv(1024)
            self.iPP.interpretate(client_data)
            if self.iPP.type=="system":
                if self.iPP.obj.body == "init":
                    client_socket.send(self.ok)
                    self._initJob(client_socket)
                        
                elif self.iPP.obj.body == "start":
                    
                    try:
                        self._startJob(self.iPP.obj.ID)
                        client_socket.send(self.ok)
                    except Exception, e:
                        logging.error("Start Job Error: %s"%e)
                        client_socket.send(self.fail)
                        raise e
                    
                elif self.iPP.obj.body == "status":
                    try:
                        client_socket.send(self.ok)
                        sleep(0.5)
                        self._statusJob(self.iPP.obj.ID, client_socket)
                        
                    except Exception, e:
                        logging.error("Status Job Error: %s"%e)
                        client_socket.send(self.fail)
                        raise e
                            
                elif self.iPP.obj.body == "results":
                    client_socket.send(self.ok)
                    self._resultsJob(client_socket)
                        
                elif self.iPP.obj.body == "clean":
                    client_socket.send(self.ok)
                    self._cleanJob(client_socket)
                        
                else:
                    client_socket.send(self.fail)
            else:
                client_socket.send(self.fail)
            
            client_data = client_socket.recv(1024)        
            if self.iPP.type=="system":
                if self.iPP.obj.body == "quit":
                    client_socket.close()
                    sleep(1)
                    logging.info("Server : Connection close from %s %s"%(address))
                else:
                    client_socket.close()
                    sleep(1)
                    logging.info("Server : FORCE Connection close from %s %s"%(address))
            else:
                client_socket.close()
                sleep(1)
                logging.info("Server : FORCE Connection close from %s %s"%(address))
                #
                ####
                
    def _statusJob(self, id, client_socket):
        print "---"
        
        job = self.manager.getJob(id)
        print job.name
        if job.status.empty():
            print "empty"
            queued = self.oPP.interpretate(System("queued"))
            client_socket.send(queued)
        else:
            print "not empty"
            if job.status_error:
                print "error"
                stderr = ""
                tmp = Queue.Queue()
                while True:
                    line = job.error.get()
                    stderr = stderr + line + "\n"
                    tmp.put(line)
                    if job.error.empty():
                        break
                job.error = tmp
                error = self.oPP.interpretate( System("error", stderr))
                print error
                client_socket.send(error)
                print "errordone"
            elif job.done:
                print "done"
                done = self.oPP.interpretate(System("done"))
                client_socket.send(done)
            else:
                print "runnig"
                running = self.oPP.interpretate(System("running", job.status.get()))
                client_socket.send(running)
        print "ok"
        self._recvAKW(client_socket)
            
            
    def _startJob(self, id):
        self.manager.startJob(id)
        
    
    def _recvAKW(self, client_socket):
        client_data = client_socket.recv(1024)
        self.iPP.interpretate(client_data)
        if self.iPP.type=="system":
            if self.iPP.obj.body == "ok":
                pass
            else:
                pass
        
    def _initJob(self, client_socket):
        ###
        #set jobID
        jobID = time.strftime('%Y%m%d_%H%M%S')
        client_data = client_socket.recv(1024)
        self.iPP.interpretate(client_data)
        if self.iPP.type=="system":
            if self.iPP.obj.body == "tag":
                client_socket.send(self.ok)
                jobID = self.iPP.obj.ID + "_" + jobID
                client_socket.send(self.oPP.interpretate(System("jobID",jobID)))
                self._recvAKW(client_socket)
            else:
                client_socket.send(self.fail)
        else:
            client_socket.send(self.fail)
        job=Job(jobID)
        logging.info("Server : Initialize Job %s"%(jobID))
        #
        ###
        
        ###
        #set local
        client_data = client_socket.recv(1024)
        self.iPP.interpretate(client_data)
        if self.iPP.type == "system":
            if self.iPP.obj.body == "local":
                client_socket.send(self.ok)
                if self.iPP.obj.ID == True:
                    client_data = client_socket.recv(1024)
                    self.iPP.interpretate(client_data)
                    if self.iPP.type == "system":
                        if self.iPP.obj.body == "Copydone":
                            client_socket.send(self.ok)
                            pass
                        else:
                            client_socket.send(self.fail)
                    else:
                        client_socket.send(self.fail)
                else:
                    pass 
            else:
                client_socket.send(self.fail)
        else:
            client_socket.send(self.fail)
        #
        ###
        ###
        # machine program -->save = break while
        while 1:
            client_data = client_socket.recv(1024)
            self.iPP.interpretate(client_data)
            if self.iPP.type == "machine":    
                logging.debug("Machine :%s"%(client_data))
                job.machines.append(self.iPP.obj)
                client_socket.send(self.ok)

            elif self.iPP.type == "program":    
                logging.debug("Program :%s"%(client_data))
                job.programs.append(self.iPP.obj)
                client_socket.send(self.ok)
            
            elif self.iPP.type == "system":
                if self.iPP.obj.body == "save":
                    logging.debug("Save %s"%(jobID))
                    client_socket.send(self.ok)
                    break
            else:
                logging.debug("FAIL :%s"%(client_data))
                client_socket.send(self.fail)
        #
        ###
        ####
        # Append to the main queue and start the job
        logging.info("Server : Append job %s to queue manager"%(jobID))
        self.manager.addJob(job)
                
        #
        ####        
        
    

                    
################################################################################
# Methods

################################################################################
# Main

if __name__ == '__main__':
    pass
