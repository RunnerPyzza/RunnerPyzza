#!/usr/bin/env python
"""
Protocol

Common package

Pyzza protocol interpreter
- Discards rubbish (fail-safe)
- Tells the user the type of message
- Returns the object or the body of the message

The client can istantiate the Protocol object just once and then use it as many
times as it likes
"""

__author__ = "Marco Galardini"
__copyright__ = "Copyright 2011, RunnerPyzza"
__credits__ = ["Emilio Potenza"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Marco Galardini"
__email__ = "marco.galardini@unifi.it"
__status__ = "Development"

################################################################################
# Imports

import logging

################################################################################
# Log setup

# create logger
# Name shown
logger = logging.getLogger('Protocol')

################################################################################
# Classes

class Protocol():
	'''
	Pyzza protocol interpreter
	'''
	def __init__(self, msg = ''):
		self._clean()
		from JSON import JSON
		self._msgHandler = JSON()
		if msg != '':
			self._interpretate(msg)
	def _getSystem(self):
		from System import System
		self.obj = System(self.d["msg"])
	def _getMachine(self):
		from Machine import Machine
		m = Machine(self.d["hostname"], self.d["user"])
		m.setPassword(self.d["password"], encode = False)
		self.obj = m
	def _getProgram(self):
		from Program import Program
		p = Program(self.d["name"], self.d["cmd"])
		p.setCpu(self.d["ncpu"])
		p.setOrder(self.d["order"])
		self.obj = p
	_conversions = {"system":_getSystem,
					"machine":_getMachine,
					"program":_getProgram}
	def _clean(self):
		self.msg = None
		self.type = None
		self.d = None
		self.obj = None
	def _convert(self):
		# Fail safe conversion
		try:
			self._conversions.get(self.type,self._clean())(self)
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
		'''
		self._clean()
		self._interpretate(msg)
	def getType(self):
		return self.type
	
################################################################################
# Main

if __name__ == '__main__':
	pass
