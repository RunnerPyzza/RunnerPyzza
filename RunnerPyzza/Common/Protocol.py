#!/usr/bin/env python
"""
Protocol

Common package

Pyzza protocol interpreter

Incoming:
- Discards rubbish (fail-safe)
- Tells the user the type of message
- Returns the object or the body of the message

Outcoming:
- Handles only the right kind of messages
- Returns the JSON ready-to-be-sent string

The client can istantiate the Protocol object just once and then use it as many
times as it likes
"""

__author__ = "Marco Galardini"
__credits__ = ["Emilio Potenza"]

import logging

################################################################################
# Log setup

# create logger
# Name shown
logger = logging.getLogger('RunnerPyzza.Protocol')

################################################################################
# Classes

class Protocol(object):
	'''
	Base class for the PyzzaProtocol
	'''
	def __init__(self):
		self._clean()
		from JSON import JSON
		self._msgHandler = JSON()
		
	def _clean(self):
		'''
		Ensures no rubbish is preserved between messages
		'''
		self.msg = None
		self.type = None
		self.d = None
		self.obj = None
		
	def _convert(self):
		self._clean()
		
	def _interpretate(self,obj):
		# If it fails just keep the object clean
		self._clean()
		
	def interpretate(self,obj):
		'''
		Push and translate a new message/object
		(depending if this is InProtocol or OutProtocol)
		'''
		self._clean()
		self._interpretate(obj)
		
	def getType(self):
		return self.type

class iProtocol(Protocol):
	'''
	PyzzaProtocol interpreter for incoming messages
	'''
	def __init__(self, msg = ''):
		Protocol.__init__(self)
		if msg != '':
			self._interpretate(msg)
			
	def _getSystem(self):
		from System import System
		dval = self.d["values"]
		self.obj = System(dval["msg"],dval["ID"])
		
	def _getMachine(self):
		from Machine import Machine
		dval = self.d["values"]
		m = Machine(dval["name"],dval["hostname"], dval["user"])
		m.setPassword(dval["password"], encode = False)
		self.obj = m
		
	def _getProgram(self):
		from Program import Program
		dval = self.d["values"]
		p = Program(dval["name"], dval["cmd"])
		p.setCpu(dval["ncpu"])
		p.setOrder(dval["order"])
		p.setCanFail(dval['canFail'])
		p.addStdOut(dval['stdout'])
		p.addStdErr(dval['stderr'])
		p.setHost(dval['host'])
		p.setExit(dval['exit'])
		self.obj = p
	
	_conversions = {"system":_getSystem,
					"machine":_getMachine,
					"program":_getProgram}
	
	def _convert(self):
		# Fail safe conversion
		try:
			self._conversions.get(self.type,self._clean)(self)
		except:self._clean()
		
	def _interpretate(self,msg):
		# If it fails just keep the object clean
		try:
			self.msg = msg
			self.d = self._msgHandler.decode(self.msg)
			self.type = self.d["type"]
			self._convert()
		except:self._clean()
		
	def interpretate(self,msg):
		'''
		Push and translate a new message
		Returns the object
		'''
		self._clean()
		self._interpretate(msg)
		return self.obj
	
class oProtocol(Protocol):
	'''
	PyzzaProtocol interpreter for outcoming messages
	'''
	def __init__(self, obj = None):
		Protocol.__init__(self)
		if obj:
			self._interpretate(obj)
			
	def _convert(self):
		# Fail safe conversion
		try:
			self.d = self.obj.msg()
		except:self._clean()
		
	def _interpretate(self,obj):
		# If it fails just keep the object clean
		try:
			self.obj = obj
			self._convert()
			self.type = self.d["type"]
			self.msg = self._msgHandler.encode(self.d)
		except:self._clean()
		
	def interpretate(self,obj):
		'''
		Push and translate a new object
		Returns the ready-to-be-sent message
		'''
		self._clean()
		self._interpretate(obj)
		return self.msg + '\n'
	
################################################################################
# Main

if __name__ == '__main__':
	pass
