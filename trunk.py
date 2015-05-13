from twisted.internet import stdio
from twisted.protocols import basic
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
from sys import argv
import platform
import datetime

"""
trunk.py
A basic p2p chat node written with the Twisted protocol
"""

class KeyboardClient(basic.LineReceiver):
	from os import linesep as delimiter

	def __init__(self, trunk):
		self.trunk = trunk
		stdio.StandardIO(self)

	def connectionMade(self):
		pass

	def lineReceived(self, line):
		m = Message(line)
		self.trunk.content_history[m.toHash()] = m
		self.trunk.broadcast("MESG" + m.toString())
			#protocol.host_name+":

class Peer(LineReceiver):

	def __init__(self, trunk, addr, port):
		self.trunk = trunk
		self.addr = addr
		self.port = port

	def connectionMade(self):
		print "Peer.connectionMade " + self.addr
		self.trunk.users[self.addr] = self

	def connectionLost(self, reason):
		if self.addr in self.trunk.users.keys():
			del self.trunk.users[self.addr]

	def lineReceived(self, line):
		self.trunk.recieved(line,self.addr)



class PeerFactory(Factory):

	def __init__(self, trunk):
		self.trunk = trunk
	def buildProtocol(self, conn):
		return Peer(self.trunk, conn.host, conn.port)


	def startedConnecting(self, connector):
		pass

class Message():
	def __init__(self,content,parent="", datetime=str(datetime.datetime.now()), count=0):
		self.content = content
		self.parent = parent
		self.datetime = datetime
		self.count = count

	def toString(self):
		return self.content + chr(31) + self.parent + chr(31) + self.datetime

	@staticmethod
	def decodeString(mesg) :
		parts = mesg.split(chr(31))
		return Message(parts[0],parts[1],parts[2])

	def toHash(self) :
		return hash(self.content)


class Trunk(object):
	def __init__(self):
		self.content_history = {}
		self.users = {}
		port = 8123
		self.f = PeerFactory(self)
		self.k = KeyboardClient(self)
		reactor.listenTCP(port, self.f)
		for addr in argv[1:]:
			self.makeAPeerConnection(addr)
		reactor.run()

	def makeAPeerConnection(self, addr):
		reactor.connectTCP(addr, 8123, self.f)

	def broadcast(self, mesg):
		for _, protocol in self.users.iteritems():
			protocol.sendLine(mesg + "\r\n")

	def propogate(self, mesg, publisher):
		for ip, protocol in self.users.iteritems():
			if ip is not publisher:
				protocol.sendLine("MESG"+mesg + "\r\n")

	def recieved(self, message, ip):
		#print 'recieved: ' + message

		if message[:4] == "MESG" :
			mesg = Message.decodeString(message[4:])
			mesgHash = mesg.toHash()
			if mesgHash in self.content_history :
				print "i already got this"
			else :
				print mesg.content 
				self.content_history[mesgHash] = mesg
				self.propogate(mesg.toString(),ip)
		else :
			proto=message[:4]
			param=message[4:]
			if proto is "ATMT" :
				for addr in param.split(" "):
					self.makeAPeerConnection(addr)

if __name__ == '__main__':
	t = Trunk()
	
