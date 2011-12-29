#!/usr/bin/env python
"""
Server

Common mod test

Server object running on Runner Pyzza daemon (RPdaemon) 
"""

__author__ = "Emilio Potenza"
__copyright__ = "Copyright 2011, RunnerPyzza"
__credits__ = ["Marco Galardini"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Emilio Potenza"
__email__ = "emilio.potenza@iasma.it"
__status__ = "Development"

#################################################################################
# Imports ##

import logging
import socket
import sys
from getpass import getpass
import threading 	
import Queue
import paramiko
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
			client.connect(host.getHostname(), username=host.getUser(), password=host.getPassword())
			self.connections.append(client)
                        logging.info("Job %s: %s is now connected to user %s"%(self.name, host.getHostname(),host.getUser()))


	def _workFun(self,host, conn, queue):
		while True:
			try:
				command=queue.get()
				if command=="break":
					queue.task_done()
					break	
				#self.raw_notify("%s> Command in queue start"%(host[0]),command)
				with self.outlock:
					logging.info("... %s ==> %s"%(host.getHostname(),command))
				stdin, stdout, stderr = conn.exec_command(command)

				stdin.close()
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
				#self.raw_notify("%s> Command in queue done"%(host.getHostname()),command)
				queue.task_done()
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
                logging.info("Job %s: is now running"%(self.name))
                '''
                Connect
                '''
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
                                    t = threading.Thread(target=self._workFun, args=(host,conn, queue))
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
                
		
		

class Server():
	'''
    RunnerPyzza daemon server (RPdaemon)
    '''
	def __init__ (self,port):
		self.jobCounter = 0
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
		quit=False
		while not quit:
                        logging.info("Server is now waiting for client on port %s"%(port))
			#Attendi la connessione del lanciatore...
			client_socket, address = server_socket.accept()
			logging.info("Server : Connection requenst from %s %s"%(address))
			####
			# Create a new job
			self.jobCounter+=1
			job=Job(self.jobCounter)
                        logging.info("Server : Initialize Job %s"%(self.jobCounter))
                        ####
			####
			# PyzzaProtocol
			iPP=iProtocol()
			oPP=oProtocol()
                        ####
			ok = System("ok")
			ok = oPP.interpretate(ok)
                        #
			while 1:
				logging.debug("...waiting ")
				client_data = client_socket.recv(1024)
				###
				# PyzzaProtocoll IN
				iPP.interpretate(client_data)
				#
				###		
				if iPP.type=="system":
					if iPP.obj.body == "quit":
						client_socket.close()
                                                from time import sleep
                                                sleep(1)
                                                logging.info("Server : Connection close from %s %s"%(address))
						break
                                        elif iPP.obj.body == "result":
                                                client_socket.send(ok)
                                                jobID = client_socket.recv(1024)
                                                iPPjobID=iProtocol()
                                                iPPjobID.interpretate(jobID)
                                                job= self.manager.getJob( int(iPPjobID.obj.body) )
                                                stdout = '' 
                                                while not job.stdout.empty():
                                                    stdout = stdout + job.stdout.get()
                                                stderr = '' 
                                                while not job.stderr.empty():
                                                    stderr = stderr + job.stderr.get()
                                                
                                                
                                                
                                                client_socket.send( oPP.interpretate( System(stdout) ) )
                                                client_socket.send( oPP.interpretate( System(stderr) ) ) 
                                                
                                                client_socket.close()
                                                from time import sleep
                                                sleep(1)
                                                logging.info("Server : Connection close from %s %s"%(address))
                                                sys.exit()
					else:
						logging.warning("\n ?? \n%s"%(client_data))
					
				elif iPP.type == "machine":	
					logging.debug("Machine :%s"%(client_data))
					job.machines.append(iPP.obj)
					client_socket.send(ok)
	
				elif iPP.type == "program":	
					logging.debug("Program :%s"%(client_data))
					job.programs.append(iPP.obj)
					client_socket.send(ok)
	
				else:
					logging.debug("FAIL :%s"%(client_data))
					client_socket.send( oPP.interpretate( System("fail") ) )
			####
			# Append to the main queue and start the job
                        logging.info("Server : Append job %s to queue manager"%(self.jobCounter))
			self.manager.addJob(job)
			self.manager.startJob(job.name)
			#
			####
					
################################################################################
# Methods

################################################################################
# Main

if __name__ == '__main__':
	pass
