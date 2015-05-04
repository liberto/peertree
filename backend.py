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
    def __init__(self):
        self.host = '' #localhost
        self.port = 442200 #port to bind sockets on this machine. you can change it
        self.backlog = 5
        self.size = 1024 #max message size
        self.server = None
        self.threads = [] #list of Client threads that handle known IP addresses
        #creates new Client threads for the IP addresses passed as arguements
        for arg in sys.argv[1:]:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((arg,50000))
                c = Client((s,arg), self)
                c.start()
                self.threads.append(c)
            except socket.error, (value,message):
                print "Connection Error line 31: " + message
	
    #opens a socket that listens for unidentified requests.
    #i didn't write this I don't know much about it 
    def open_socket(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind((self.host,self.port))
            self.server.listen(5)
        except socket.error, (value,message):
            if self.server:
                self.server.close()
            print "Could not open socket: " + message
            sys.exit(1)

    #main loop of main class
    def run(self):
        self.open_socket()
        input = [self.server,sys.stdin]
        running = 1
        while running:
            inputready,outputready,exceptready = select.select(input,[],[])

            for s in inputready:

                if s == self.server:
                    # creates a new Client thread 
                    c = Client(self.server.accept(), self)
                    c.start()
                    self.threads.append(c)

                elif s == sys.stdin:
                    # handle standard input
                    messagetosend = sys.stdin.readline()
                    for t in self.threads:
                        t.send(messagetosend)

        
	# close all threads
        self.server.close()
        for c in self.threads:
            c.join()

class Client(threading.Thread):
    def __init__(self,(client,address), server):
        threading.Thread.__init__(self)
        self.client = client
        self.address = address
        self.size = 1024

    def run(self):
        running = 1
        while running:
            data = self.client.recv(self.size)
            if data:
                print data
            else:
                self.client.close()
                running = 0

    def send(self, messagetosend):
        self.client.send(messagetosend)

if __name__ == "__main__":
    s = Server()
    s.run() 
