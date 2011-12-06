#!/usr/bin/env python
"""
Server

Common

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
		self.name=job.name
		self.thread_stop=False
		self.programs=job.programs
		###TEST CONVERSION###
		self.queue=Queue.Queue()
		for p in job.programs:
			self.queue.put(p.getCmd())
			
		#####################
		self.machines=job.machines
		self.connections=[]
		self.threads = []
		self.outlock = threading.Lock()

	def _connect(self):
		"""Connect to all hosts in the hosts list"""
		for host in self.machines:
			client = paramiko.SSHClient()
			client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
			client.connect(host.getHostname(), username=host.getUser(), password=host._password)
			self.connections.append(client)


	def _workFun(self,host, conn, queue):
		while True:
			try:
				command=queue.get()
				if command=="break":
					queue.task_done()
					break	
				#self.raw_notify("%s> Command in queue start"%(host[0]),command)
				with self.outlock:
					print "... %s ==> %s"%(host.getHostname(),command)
				stdin, stdout, stderr = conn.exec_command(command)

				stdin.close()
				for line in stdout.read().splitlines():
					with self.outlock:
						print """\033[1;32m[%s - out]\033[0m : %s""" % (host.getHostname(), line) 
				for line in stderr.read().splitlines():
					with self.outlock:
						"""\033[1;31m[%s - err]\033[0m : %s""" % (host.getHostname(), line) 		
				#self.raw_notify("%s> Command in queue done"%(host.getHostname()),command)
				queue.task_done()
			except KeyboardInterrupt:
				print "do quit thread"
				self.do_quit(None)
				break
			except Exception as e:
				print e	

	def _quit(self):
		"""Close all the connections and exit"""
		for conn in self.connections:
			conn.close()
		return 

	def run(self):
		'''Connect'''
		self._connect()
		#print self.hosts
		#print self.connections
		#print self.queue
		"""start Execute commands queue on all hosts in the list"""
		try:		
			for host, conn in zip(self.machines, self.connections):
				self.queue.put("break")
				t = threading.Thread(target=self._workFun, args=(host,conn, self.queue))
				t.setDaemon(True)		
				t.start()
				self.threads.append(t)
			self.queue.join()
		except KeyboardInterrupt:
			print "do quit"
			self._quit()
		self._quit()		

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
		print job.name
		print job.machines
		print job.programs
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
		host = ""
		server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		server_socket.bind((host, port))
		server_socket.listen(5)
		#
		####
		logging.debug("Server - Waiting for client on port %s"%(port))
		quit=False
		while not quit:
			#Attendi la connessione del lanciatore...
			client_socket, address = server_socket.accept()
			logging.debug("Server - Connection from %s %s"%(address))
			####
			# Create a new job
			self.jobCounter+=1
			job=Job(self.jobCounter)
			#
			####
			###
			# PyzzaProtocol
			iPP=iProtocol()
			oPP=oProtocol()
			#
			###
			ok = System("ok")
			ok = oPP.interpretate(ok)
			print ok
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
						logging.debug("\n Bye Bye !!\n")
						client_socket.close()
						break
					else:
						logging.debug("\n ?? \n%s"%(client_data))
					
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
