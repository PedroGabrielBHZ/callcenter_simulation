# This, allegedly, is our client.
from cmd import Cmd
from twisted.internet import reactor, protocol

class QuoteProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        self.sendQuote()

    def sendQuote(self):
        self.transport.write(self.factory.quote)

    def dataReceived(self, data):
        print("Received quote:", data)
        self.transport.loseConnection()

class QuoteClientFactory(protocol.ClientFactory):
    def __init__(self, quote):
        self.quote = quote

    def buildProtocol(self, addr):
        return QuoteProtocol(self)

    def clientConnectionFailed(self, connector, reason):
        print("connection failed:", reason.getErrorMessage())
        maybeStopReactor()

    def clientConnectionLost(self, connector, reason):
        print("connection lost:", reason.getErrorMessage())
        maybeStopReactor()

def maybeStopReactor():
    global quote_counter
    quote_counter -= 1
    if not quote_counter:
        reactor.stop()

quotes = ["You snooze, you lose.",
          "The early bird gets the worm.",
          "Casa de ferreiro, espeto de pau",
          "Carpe diem." ]
quote_counter = len(quotes)

class CommandProcessor(Cmd):
    def do_EOF(self, arg):
        return True

    def do_call(self, arg):
        """make application receive a call whose id is <id>."""
        reactor.callFromThread(call, arg)

    def do_answer(self, arg):
        """make operator <id> answer a call being delivered to it."""
        reactor.callFromThread(answer, arg)

    def do_reject(self, arg):
        """make operator reject a call being delivered to it."""
        reactor.callFromThread(reject, arg)

    def do_hangup(self, arg):
        """make call whose id is <id> be finished."""
        reactor.callFromThread(hangup, arg)

def call(arg):
    print("Making a call with id {}".format(arg))
    reactor.connectTCP('localhost', 8000, QuoteClientFactory(bytes(quotes[0], 'utf-8')))
        
def answer(arg):
    print("Answering a call with id {}".format(arg))
    reactor.connectTCP('localhost', 8000, QuoteClientFactory(bytes(quotes[1], 'utf-8')))

def reject(arg):
    print("Rejecting a call with id {}".format(arg))
    reactor.connectTCP('localhost', 8000, QuoteClientFactory(bytes(quotes[2], 'utf-8')))

def hangup(arg):
    print("Hangup'ing a call with id {}".format(arg))
    reactor.connectTCP('localhost', 8000, QuoteClientFactory(bytes(quotes[3], 'utf-8')))

reactor.callInThread(CommandProcessor().cmdloop)
reactor.run()
