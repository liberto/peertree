from twisted.internet import stdio
from twisted.protocols import basic
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
from sys import argv

"""
trunk.py
A basic p2p chat node written with the Twisted protocol
"""

class KeyboardClient(basic.LineReceiver):
    from os import linesep as delimiter

    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        pass

    def lineReceived(self, line):
        for name, protocol in self.factory.users.iteritems():
            protocol.sendLine(line + "\r\n")

class Peer(LineReceiver):

    def __init__(self, users, addr, port):
        self.users = users
        self.addr = addr
        self.port = port

    def connectionMade(self):
        print "Peer.connectionMade " + self.addr
        self.users[self.addr] = self

    def connectionLost(self, reason):
        if self.addr in self.users:
            del self.users[self.addr]

    def lineReceived(self, line):
        print "Chat.lineReceived"  + line


class PeerFactory(Factory):

    def __init__(self):
        self.users = {} # maps user names to Chat instances
        for addr in initialAddresses:
            self.makeAPeerConnection(addr)

    def buildProtocol(self, conn):
        return Peer(self.users, conn.host, conn.port)

    def makeAPeerConnection(self, addr):
        reactor.connectTCP(addr, 8123, self)

    def startedConnecting(self, connector):
        pass


if __name__ == '__main__':
    port = 8123
    f = PeerFactory(argv[1:])
    k = KeyboardClient(f)
    stdio.StandardIO(k)
    reactor.listenTCP(port, f)
    reactor.run()
