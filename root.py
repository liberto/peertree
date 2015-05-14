from twisted.internet import stdio
from twisted.protocols import basic
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
from sys import argv
import platform
import datetime

"""
root.py
A basic p2p chat node written with the Twisted protocol
"""

class KeyboardClient(basic.LineReceiver):
	from os import linesep as delimiter

	def __init__(self, root):
		self.root = root
		stdio.StandardIO(self)

	def connectionMade(self):
		pass

	def lineReceived(self, line):
		self.root.recievedKeyboard(line)

class Peer(LineReceiver):

	def __init__(self, root, addr, port):
		self.root = root
		self.addr = addr
		self.port = port

	def connectionMade(self):
		print "Peer.connectionMade " + self.addr
		self.root.users[self.addr] = self

	def connectionLost(self, reason):
		print "Peer.connectionLost " + self.addr
		if self.addr in self.root.users.keys():
			del self.root.users[self.addr]

	def lineReceived(self, line):
		self.root.recievedConn(line,self.addr)


class PeerFactory(Factory):

	def __init__(self, root):
		self.root = root
	def buildProtocol(self, conn):
		return Peer(self.root, conn.host, conn.port)


	def startedConnecting(self, connector):
		pass



	def clientConnectionLost(self, connector, reason):
		print "PeerFactory.clientConnectionLost"


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
		return hash(self.content + self.datetime)


class Root(object):
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
				protocol.sendLine(mesg + "\r\n")

	def recievedConn(self, message, ip):
		#print 'recieved: ' + message

		if message[:4] == "MESG" :
			mesg = Message.decodeString(message[4:])
			mesgHash = mesg.toHash()
			if mesgHash in self.content_history :
				print "i already got this"
			else :
				print mesg.content 
				self.content_history[mesgHash] = mesg
				self.propogate(message,ip)
		else :
			proto=message[:4]
			param=message[4:]
			if proto is "ATMT" :
				for addr in param.split(" "):
					self.makeAPeerConnection(addr)

	def recievedKeyboard(self, line):
		if line[0] != "\\":
			m = Message(line)
			self.content_history[m.toHash()] = m
			self.broadcast("MESG" + m.toString())
		elif line[1] == 'e':
			reactor.stop()
			exit(0)
		else:
			print "did you mean \\e to exit?"

if __name__ == '__main__':
	t = Root()
	
