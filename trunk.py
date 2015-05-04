from twisted import *

print "I'm twisted!"

class Server() :
	def __init__(max_connections=2) :
		self.max_connections = max_connections


class Client() :
	def __init__(address) :
		self.address = address 