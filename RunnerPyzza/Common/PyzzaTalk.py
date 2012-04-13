#!/usr/bin/env python
"""
PyzzaTalk

Common Library

PyzzaTalk class
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
    def __init__(self, server='', port=''):
        self.server = server
        self.port = int(port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket = None
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
    
    def startServer(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.server, self.port))
            self.server_socket.listen(5)
        except Exception, e:
            logger.warning('Start server error! %s'
                            %(e))
            logger.warning('Could not start the server %s on port %s'
                            %(self.server, self.port))
            raise e
    
    def accept(self):
        if not self.server_socket:
            self.startServer()
        self.socket, self.address = self.server_socket.accept()
        logger.info("Server : Connection request from %s %s"%(self.address))
    
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
    
    def getExtendedMessage(self):
        '''
        Receive data from the server and the msg type
        Automatically converted with the PyzzaProtocol
        BLOCKING CALL
        '''
        try:
            msg = ''
            while True:
                data = self.socket.recv(1024)
                msg += data
                if msg[-2:] == '}\n' :
                    break
            obj = self.iprtcl.interpretate(msg)
            if hasattr(obj, 'body'):
                logger.warning('<-- %s'%obj.body)
            elif  self.iprtcl.type != 'system':
                logger.warning('<-- %s'%self.iprtcl.type)
            else:
                print obj
                print msg
            return obj, self.iprtcl.type
        except Exception, e:
            logger.warning('Receive error! %s'
                            %(e))
            raise e
    
    def getMessage(self):
        '''
        Receive data from the server
        Automatically converted with the PyzzaProtocol
        BLOCKING CALL
        '''
        try:
            msg = ''
            while True:
                data = self.socket.recv(1024)
                msg += data
                if msg[-2:] == '}\n' :
                    break
            obj = self.iprtcl.interpretate(msg)
            if hasattr(obj, 'body'):
                logger.warning('<-- %s'%obj.body)
            elif  'values' in msg:
                logger.warning('<-- %s'%msg.type)
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
