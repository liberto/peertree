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
Handles keyboard input
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

"""
Handles an individual connection
"""
class Peer(LineReceiver):

	def __init__(self, root, addr, port):
		self.root = root
		self.addr = addr
		self.port = port
		self.addrport = self.addr + ':' + str(self.port)

	def connectionMade(self):
		print "Peer.connectionMade " + self.addrport
		self.root.users[self.addrport] = self
		self.root.flushBuff()
		self.sendLine("EVRY")
		self.sendLine("PORT"+str(self.root.port))
		addressesinstringformat = "IPAD"
		for addr in self.root.known_addrs :
			addressesinstringformat += " " + addr
		self.sendLine(addressesinstringformat)

	def connectionLost(self, reason):
		print "Peer.connectionLost " + self.addrport
		if self.addr in self.root.users.keys():
			del self.root.users[self.addrport]

	def lineReceived(self, line):
		self.root.recievedConn(line,self.addrport)

"""
A factory for Peers
required by Twisted 
"""
class PeerFactory(Factory):

	def __init__(self, root):
		self.root = root
	def buildProtocol(self, conn):
		return Peer(self.root, conn.host, conn.port)

	def startedConnecting(self, connector):
		pass

	def clientConnectionLost(self, connector, reason):
		print "PeerFactory.clientConnectionLost"

"""
Used for storing the actual content
"""
class Message():
	def __init__(self,content,parent="", count=0):
		self.content = content
		self.parent = parent
		self.datetime = str(datetime.datetime.now())
		self.count = count

	def toString(self):
		return self.content + chr(31) + self.parent + chr(31) + self.datetime

	@staticmethod
	def decodeString(mesg) :
		parts = mesg.split(chr(31))
		return Message(parts[0],parts[1],parts[2])

	def toHash(self) :
		#print hash(self.content+self.datetime)
		#print self.datetime
		return hash(self.content + self.datetime)

"""
The root of the PeerTree
    (just think of an actual tree)
"""
class Root(object):
	def __init__(self):
		self.content_history = {}
		self.known_addrs = []
		self.users = {}
		try :
			self.readhistoryfile = open(".peertree-content-history.txt", "r+")
			for line in self.readhistoryfile:
				splitline = line.split(chr(31)) 
				if len(splitline)==3:
					m = Message(splitline[0],splitline[1],splitline[2])
					self.content_history[m.toHash()] = m
			self.readhistoryfile.close()
		except :
			print "No history file found"
		try :
			self.readipfile = open(".peertree-known-ips.txt", "r+")
			for line in self.readipfile:
				line = line[:-1]
				self.known_addrs.append(line)
			self.readipfile.close()
			print "initial addrs: "+ str(self.known_addrs)
		except:
			print "No IP file found"
		self.port = int(argv[1])
		self.f = PeerFactory(self)
		self.k = KeyboardClient(self)
		reactor.listenTCP(self.port, self.f)
		self.historyfile = open(".peertree-content-history.txt", "a+")
		self.ipfile = open(".peertree-known-ips.txt", "a+")
		for addrport in argv[2:]:
			self.saveIP(addrport)
			self.makeAPeerConnection(addrport)
		reactor.run()

	"""
	Writes the buffer to the files
	"""
	def flushBuff(self):
		self.historyfile.close()
		self.historyfile = open(".peertree-content-history.txt", "a+")
		self.ipfile.close()
		self.ipfile = open(".peertree-known-ips.txt", "a+")

	"""
	Saves a given addr:port to the known_ports
	list and the ipfile file
	"""
	def saveIP(self,addrport):
		#print "addr port: " + addrport
		#print "known " + str(self.known_addrs)
		if addrport not in self.known_addrs:
			self.known_addrs.append(addrport)
			self.ipfile.write(addrport + "\n")

	"""
	Connect to a another peers
	addrport - an ip address with a port 
	example: 192.168.1.130:8000
	"""
	def makeAPeerConnection(self, addrport):
		addr, port = addrport.split(':')
		port = int(port)
		reactor.connectTCP(addr, port, self.f)

	"""
	Sends message to all connected peers, including publisher
	"""
	def broadcast(self, mesg):
		for _, protocol in self.users.iteritems():
			protocol.sendLine(mesg + "\r\n")

	"""
	Sends message to everyone but publisher
	"""
	def propogate(self, mesg, publisher):
		for ip, protocol in self.users.iteritems():
			if ip is not publisher:
				protocol.sendLine(mesg + "\r\n")

	"""
	Called whenever data is recieved
	Each message contains a protocol:
		MESG: an actual message with content.
		EVRY: Sends the content history to every peer
		IPAD: Another peers ip address and port number
		ATMT: Attempt to connect to this address 
	"""
	def recievedConn(self, message, ip):
		proto = message[:4]
		if proto == "MESG" :
			mesg = Message.decodeString(message[4:])
			mesgHash = mesg.toHash()
			if mesgHash not in self.content_history :
				print mesg.content 
				self.content_history[mesgHash] = mesg
				self.historyfile.write(mesg.toString())
				self.historyfile.flush()
				self.propogate(message,ip)
		elif proto == "EVRY" :
			for k,c in self.content_history.iteritems():
				self.users[ip].sendLine("MESG" + c.toString())
		elif proto == "IPAD" :
			addresses = message[4:].split(" ")
			for addr in addresses :
				if addr != '':
					self.saveIP(addr)
			self.propogate(message,ip)
		elif proto == "PORT" :
			recievedAddr = ip.split(":")[0]+':'+message[4:]
			self.saveIP(recievedAddr)
			self.broadcast("IPAD"+recievedAddr)

		elif proto is "ATMT" :
			for addr in param.split(" "):
				self.makeAPeerConnection(addr)
	"""
	its a method thats called whenever a line from the
	the keyboard is inputted
	"""
	def recievedKeyboard(self, line):
		if line == "":
			pass
		elif line[0] != "\\":
			m = Message(line)
			self.content_history[m.toHash()] = m
			self.historyfile.write(m.toString())
			self.historyfile.flush()
			self.broadcast("MESG" + m.toString())
		elif line[1] == 'q' or line[1] == 'e':
			self.historyfile.close()
			self.ipfile.close()
			_exit(0)
		elif line[1] == 'c':
			self.saveIP(line[2:])
			self.makeAPeerConnection(line[2:])
		elif line[1] == 'i' :
			print self.known_addrs
		else:
			print "\\q quit\n\\e quit\n\\c255.255.255.255:8000"

if __name__ == '__main__':
	t = Root()

#eof 