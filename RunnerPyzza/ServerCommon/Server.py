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
# Imports

import logging
import socket
from getpass import getpass
import threading 	
import Queue
import paramiko
from Common.PyzzaProtocol import *

################################################################################
# Log setup

# create logger
# Name shown
logger = logging.getLogger('Server')


################################################################################

class Server():
    '''
    RunnerPyzza daemon server (RPdaemon)
    '''
    def __init__ (self,port):
	#self.hosts = []
	#self.queue = Queue.Queue()
	self.jobsList = {} # jobID:{"machine":[machinediz1, ..], "program":[programdiz1,...]}
	self.jobCounter = 0

	host = ""
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server_socket.bind((host, port))
	server_socket.listen(5)
	#logging.debug("Type 'Q' or 'q' to QUIT")
	logging.debug("Server - Waiting for client on port %s"%(port))
	#print "wait"
	quit=False
	while not quit:
	    	#Attendi la connessione del lanciatore...
	   	client_socket, address = server_socket.accept()
	    	logging.debug("Server - Connection from %s %s"%(address))
		####
		#
		# Create a new job
		#
		self.jobCounter+=1
		self.jobsList[self.jobCounter]={"machine":[],"program":[]}
		#
		####
		while 1:
			logging.debug("...waiting ")
		    	client_data = client_socket.recv(1024)
		
			###
			#
			# Inserire PyzzaProtocoll 
			# TEST
			PP=PyzzaProtocol(client_data)
			PPtype = PP.isType()
			PPdict = PP.toDict()
			#print PPtype
			#client_socket.send('{"values": {"msg" : "ok"}, "type" : "system"}')
			#
			###		
				
			if PPtype=="system":
				
				if PPdict["values"]["msg"]=="quit":
					logging.debug("\n Bye Bye !!\n")
					client_socket.close()
					break
				else:
					logging.debug("\n ?? \n%s"%(client_data))
				
			elif PPtype == "machine":	
				logging.debug("Machine :%s"%(client_data))
				self.jobsList[self.jobCounter]["machine"].append()
				client_socket.send('{"values": {"msg" : "ok"}, "type" : "system"}')

			elif PPtype == "program":	
				logging.debug("Program :%s"%(client_data))
				client_socket.send('{"values": {"msg" : "ok"}, "type" : "system"}')

			else:
				logging.debug("FAIL :%s"%(client_data))
				client_socket.send('{"values": {"msg" : "fail"}, "type" : "system"}')


					
			
			'''if client_data.lower() == 'quit_server':
				logging.info("QUIT")
				client_socket.close()
				quit=True
				break
			elif client_data.lower() == 'q':
				logging.info("Client disconnected")
				client_socket.close()
				break
			elif client_data.find("cmd:")==0:
				client_data=client_data.split(":")[1]
				self.queue.put("%s"%(client_data))
				#"cmd:<command>"
				logging.info("add command to queue %s"%(client_data))
				client_socket.send("ok")

			elif client_data.find("server:")==0:
				client_data=client_data.split(":")[1]
				self.hosts.append(client_data.split(','))
        			#server:hostip,user,password
				logging.info("add server to cluster%s"%(client_data))
				client_socket.send("ok")

			elif client_data.find("start")==0:
				queue_test=RPqueue(self.hosts,self.queue)
				queue_test.start()
				logging.info("Start queue")
				client_socket.send("ok")
				self.queue=Queue.Queue()

			elif client_data.find("debug")==0:
				print self.hosts,self.queue
				client_socket.send("ok")
			else:
				#print "--X server: ", server_data, "fail"
				#print "Allowed server commands: q, Q [Close client]; 
				#cmd:xxx [Add command to queue]; server:xxx [Add server to cluster]" 
				logging.info("fail")
				client_socket.send("fail")
				#print "fail"
			'''

################################################################################
# Methods

################################################################################
# Main

if __name__ == '__main__':
    pass