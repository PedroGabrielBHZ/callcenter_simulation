# Upon receiving a quote from a client, the server
# will send the client its current quote and store
# the client's quote to share with the next client.
# It also keeps track of the number of concurrent
# client connections.

from twisted.internet.protocol import Factory
from twisted.internet import reactor, protocol

class QuoteProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        self.factory.numConnections += 1

    def dataReceived(self, data):
        print("Number of active connections:", self.factory.numConnections)
        print("> Received: {}\n> Sending: {}".format(data, self.getQuote()))
        self.transport.write(self.getQuote())
        self.updateQuote(data)

    def connectionLost(self, reason):
        self.factory.numConnections -= 1

    def getQuote(self):
        return self.factory.quote

    def updateQuote(self, quote):
        self.factory.quote = quote

class QuoteFactory(Factory):
    numConnections = 0
    
    def __init__(self, quote=None):
        self.quote = quote or b"An apple a day keeps the DOC away."

    def buildProtocol(self, addr):
        return QuoteProtocol(self)

reactor.listenTCP(8000, QuoteFactory())
reactor.run()

