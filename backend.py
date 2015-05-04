#!/usr/bin/env python

"""
PeerTree
Spencer Liberto, Nick Knoebber
Heavily based off of http://ilab.cs.byu.edu/python/socket/echoserver.html
"""

import select
import socket
import sys
import threading

"""
class Server
this is the main loop of the program. It is in charge of handling
new socket requests by creating a new thread to handle that IP address
"""
class Server:
	def __init__(self,max_connections=2):
		self.host = '' #localhost
		self.port = 42200 #port to bind sockets on this machine. you can change it
		self.backlog = 5
		self.size = 1024 #max message size
		self.server = None
		self.threads = [] #list of Client threads that handle known IP addresses
		self.max_connections = max_connections #the amount of connections(threads) a server can make
		#creates new Client threads for the IP addresses passed as arguements
		try :
			self.connect(sys.argv[1])
		except :
			print "Creating a lonely node . . ."
	"""
	connect to a clients IP address, where the default is what was passed from command line
	"""
	def connect(self, address):
		print "Connecting to "+str(address)
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

			s.connect((address,self.port))
			c = Client((s,address), self)
			c.start()
			self.threads.append(c)
			c.send("JOIN")
		except socket.error, (value,message):
			print "In method Server.connect socket error: " + message

	#opens a socket that listens for unidentified requests.
	#i didn't write this I don't know much about it 
	def open_socket(self):
		try:
			self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.server.bind((self.host,self.port))
			self.server.listen(5)
		except socket.error, (value,message):
			if self.server:
				self.server.close()
			print "Could not open socket: " + message
			sys.exit(1)

	def sendToNaivePeers(self, messageToSend, publishingAddress) :
		for t in self.threads:
			if str(t.address) != publishingAddress:
				t.send(messageToSend)

	#main loop of main class
	def run(self):
		self.open_socket()
		input = [self.server,sys.stdin]
		running = 1
		while running:
			inputready,outputready,exceptready = select.select(input,[],[])

			for s in inputready:

				if s == self.server:
					# THIS IS WHERE NEW PEERS ARE CONNECTED
					c = Client(self.server.accept(), self)
					c.start()
					self.threads.append(c)


				elif s == sys.stdin:
					# handle standard input
					messagetosend = sys.stdin.readline()
					if messagetosend == "exit\n":
						print "Pruning self"
						running = 0
					else:
						for t in self.threads:
							t.send("MESG" + messagetosend)


	# close all threads
		self.server.close()
		for c in self.threads:
			c.join()
		exit(1)

class Client(threading.Thread):
	def __init__(self,(client,address), server):
		threading.Thread.__init__(self)
		self.client = client
		self.address = address
		self.size = 1024
		self.server=server

	def run(self):
		running = 1
		while running:
			data = self.client.recv(self.size)
			if data[:4] == "MESG":
				print data[4:]
				self.server.sendToNaivePeers(data,str(self.address))
			elif data[:4] == "JOIN":
				#check if connection is okay 
				if len(self.server.threads)>self.server.max_connections:
					new_adr = self.server.threads[-1].address
					rejection = "REJJ"+str(new_adr[0])
					print "in join clause"
					print rejection
					#for t in self.server.threads :
						#rejection+=str(t.address)
						#rejection+= " "
					self.send(rejection)
				else :
					print "joined " + str(self.address)

			elif data[:4] == "REJJ" :
				self.client.close()
				self.server.connect(data[4:])
				print "Connection rejected! trying: "+data[4:]
				running=0


			else:
				self.client.close()
				running = 0

	def send(self, messagetosend):
		self.client.send(messagetosend)

if __name__ == "__main__":
	s = Server()
	s.run() 
