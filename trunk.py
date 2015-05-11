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

    def __init__(self):
        self.factory = None

    def modifyFactory(self, factory):
        self.factory = factory

    def connectionMade(self):
        self.transport.write('> ')

    def lineReceived(self, line):
        self.transport.write('> ')
        for name, protocol in self.factory.users.iteritems():
            protocol.sendLine(line + "\r\n")

class Peer(LineReceiver):

    def __init__(self, users):
        self.users = users
        self.name = None
        self.state = "GETNAME"

    def connectionMade(self):
        self.sendLine("connectionMade")
        print "connectionMade"
        self.users["1"] = self

    def connectionLost(self, reason):
        if self.name in self.users:
            del self.users[self.name]

    def lineReceived(self, line):
        print "Chat.lineReceived"  + line


class PeerFactory(Factory):

    def __init__(self, KeyboardClient, initialAddresses):
        self.users = {} # maps user names to Chat instances
        KeyboardClient.modifyFactory(self)
        for addr in initialAddresses:
            self.makeAPeerConnection(addr)

    def buildProtocol(self, addr):
        return Peer(self.users)

    def makeAPeerConnection(self, addr):
        reactor.connectTCP(addr, 8123, self)

    def startedConnecting(self, connector):
        pass


if __name__ == '__main__':
    port = 8123
    k = KeyboardClient()
    stdio.StandardIO(k)
    reactor.listenTCP(port, PeerFactory(k, argv[1:]))
    reactor.run()
