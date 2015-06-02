#!/usr/bin/python

"""
root.py
A basic p2p chat node written with the Twisted protocol
Intended as a backend for PeerTree
"""

from twisted.internet import stdio
from twisted.protocols import basic
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
from sys import argv
from os import _exit
import platform
import datetime

"""
Handles an individual connection
"""
class Peer(LineReceiver):

	def __init__(self, network, addr, port):
		self.network = network
		self.addr = addr
		self.port = port
		self.addrport = self.addr + ':' + str(self.port)
		self.listeningport = None

	def connectionMade(self):
		print "Peer.connectionMade " + self.addrport
		self.network.peers[self.addrport] = self
		self.network.root.databases.flushBuff()
	
		"""
		This initial exchange communicates a lot of helpful info
		PORT tells the peer what our listening port is
		IPAD gives a list of all our known addrports
		EVRY requests every Message they have
		"""	
		self.sendLine("PORT"+str(self.network.port))
		addressesinstringformat = "IPAD"
		for addr in self.network.root.databases.known_addrs :
			addressesinstringformat += " " + addr
		self.sendLine(addressesinstringformat)
		self.sendLine("EVRY")

	def connectionLost(self, reason):
		print "Peer.connectionLost " + self.addrport
		if self.addr in self.network.peers.keys():
			del self.network.peers[self.addrport]

	def lineReceived(self, line):
		self.network.recievedFromPeer(line,self.addrport)

"""
A factory for Peers
required by Twisted 
"""
class PeerFactory(Factory):

	def __init__(self, network):
		self.network = network
	def buildProtocol(self, conn):
		return Peer(self.network, conn.host, conn.port)

	def startedConnecting(self, connector):
		pass

	def clientConnectionLost(self, connector, reason):
		print "PeerFactory.clientConnectionLost"

"""
Used for storing the actual content
"""
class Message():
	def __init__(self,inputstring):
		splitstring = inputstring.split(chr(31))
		self.content = splitstring[0]
		if len(splitstring) > 1:
			self.parent = splitstring[1]
			self.datetime = splitstring[2]
			self.count = int(splitstring[3]) - 1
			if self.count <= 0:
				pass
				#request network maintenence
		else:
			self.parent = ""
			self.datetime = str(datetime.datetime.now())
			self.count = 0

	def toString(self):
		return self.content + chr(31) + self.parent + chr(31) + self.datetime + chr(31) + str(self.count)

	def toHash(self) :
		return hash(self.content + self.parent + self.datetime)

'''
A singleton class that stores network clients
	and methods
'''
class Network():
	def __init__(self, root):
		self.root = root
		self.peers = {}
		
		self.port = int(argv[1])
		self.f = PeerFactory(self)
		reactor.listenTCP(self.port, self.f)


	"""
	Connect to an addrport
	addrport - an ip address with a port 
	example: 192.168.1.130:8000
	"""
	def makeAPeerConnection(self, addrport):
		self.root.databases.newIP(addrport)
		addr, port = addrport.split(':')
		reactor.connectTCP(addr, int(port), self.f)

	"""
	Sends message to all connected peers, including publisher
	"""
	def broadcast(self, mesg):
		for _, peer in self.peers.iteritems():
			peer.sendLine(mesg + "\r\n")

	"""
	Sends message to everyone but publisher
	"""
	def propogate(self, mesg, publisher):
		for addrport, peer in self.peers.iteritems():
			if addrport is not publisher:
				peer.sendLine(mesg + "\r\n")

	"""
	Called whenever data is recieved from a peer
	message is a string containing the data recieved
	addrport is a string containing the publishing peers ip:sendingport
	Each message contains a protocol:
		MESG: a content message
		EVRY: The peer is requesting our entire content history
		IPAD: Another peers ip address and port number
		PORT: The publishing peer's listening port
	"""
	def recievedFromPeer(self, message, addrport):
		proto = message[:4]
		parameters = message [4:]
		if proto == "MESG" :
			m = Message(parameters)
			if self.root.databases.newMessage(m):
				print m.content 
				self.propogate(message, addrport)
		elif proto == "EVRY" :
			for _,c in self.root.databases.content_history.iteritems():
				self.peers[addrport].sendLine("MESG" + c.toString())
		elif proto == "IPAD" :
			addresses = parameters[4:].split(" ")
			for addr in addresses :
				if addr != '':
					self.root.databases.newIP(addr)
			self.propogate(message,addrport)
		elif proto == "PORT" :
			listeningAddrport = addrport.split(":")[0]+':'+parameters
			self.root.databases.newIP(listeningAddrport)
			self.broadcast("IPAD"+listeningAddrport)

'''
A singleton class that stores live database information
	and methods as well as streams to the logfiles
	and methods to read and write to the logfiles
'''
class Databases():
	def __init__(self, root):
		self.root = root
		self.content_history = {}
		self.known_addrs = []
		self.populateDatabasesFromFile()
		
		self.historyfile = open(".peertree-content-history.txt", "a+")
		self.ipfile = open(".peertree-known-ips.txt", "a+")
		
		

	def populateDatabasesFromFile(self):
		try :
			readhistoryfile = open(".peertree-content-history.txt", "r+")
			for line in readhistoryfile:
				if chr(31) in line:
					m = Message(line)
					self.content_history[m.toHash()] = m
			readhistoryfile.close()
		except :
			print "No history file found"
		try :
			readipfile = open(".peertree-known-ips.txt", "r+")
			for line in readipfile:
				line = line[:-1]
				self.known_addrs.append(line)
			readipfile.close()
			print "initial addrs: "+ str(self.known_addrs)
		except:
			print "No IP file found"


	"""
	Writes the buffer to the files
	"""
	def flushBuff(self, quitting=0):
		self.historyfile.close()
		self.ipfile.close()
		if quitting == 0 :
			self.ipfile = open(".peertree-known-ips.txt", "a+")
			self.historyfile = open(".peertree-content-history.txt", "a+")

	"""
	Saves a given addr:port to the known_ports
	list and the ipfile file
	"""
	def newIP(self,addrport):
		if addrport not in self.known_addrs:
			self.known_addrs.append(addrport)
			self.ipfile.write(addrport + "\n")

	"""
	Saves a given message object to content_history and messagefile
	Returns true if message has never been seen before. Otherwise false.
	"""
	def newMessage(self, mesg):
		if mesg is str:
			mesg = Message(mesg)
		elif mesg.toHash not in self.content_history.iteritems():
			self.content_history[mesg.toHash()] = mesg
			self.historyfile.write(mesg.toString())
			self.historyfile.flush()
			return True
		return False


"""
A singleton class that handles keyboard input
"""
class Keyboard(basic.LineReceiver):
	from os import linesep as delimiter

	def __init__(self, root):
		self.root = root
		stdio.StandardIO(self)

	def connectionMade(self):
		pass

	def lineReceived(self, line):
		if line == "":
			pass
		elif line[0] != "\\":
			m = Message(line)
			self.root.databases.newMessage(m)
			self.root.network.broadcast("MESG" + m.toString())
		elif line[1] == 'q' or line[1] == 'e':
			self.root.databases.flushBuff()
			_exit(0)
		elif line[1] == 'c':
			self.root.network.makeAPeerConnection(line[2:])
		elif line[1] == 'i' :
			print self.root.databases.known_addrs
		else:
			print "\\q quit\n\\e quit\n\\c255.255.255.255:8000"

"""
The root of the PeerTree
    (just think of an actual tree)
    (PeerTree is a tree. The content of the tree branches out from a central trunk)
    (But the roots of the tree feed the branches through the trunk)
    (The roots are the interfaces through which human users contribute content
        to the branches of PeerTree)
"""
class Root(object):
	def __init__(self):
		self.network = Network(self)
		self.databases = Databases(self)
		self.keyboard = Keyboard(self)

		for addrport in argv[2:]:
			self.databases.newIP(addrport)
			self.network.makeAPeerConnection(addrport)

		reactor.run()

if __name__ == '__main__':
	t = Root()

#eof 
