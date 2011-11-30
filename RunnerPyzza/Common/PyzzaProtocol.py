# Classes
class PyzzaProtocol():
	'''
	posizione temporanea 
	test protocollo 1
	'''
	def __init__(self, msg):
		from JSON import JSON
		self.msgHandler = JSON()
		self.msg=msg
		self.d=self.msgHandler.decode(self.msg)
		
	def isType(self):
		return self.d["type"]
	def toDict(self):
		return self.d
