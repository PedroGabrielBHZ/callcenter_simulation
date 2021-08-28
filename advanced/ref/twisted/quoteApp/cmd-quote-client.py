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

quotes = ["You snooze, you lose.", "The early bird gets the worm.", "Carpe diem." ]
quote_counter = len(quotes)

class CommandProcessor(Cmd):
    def do_EOF(self, line):
        return True

    def do_Q1(self, line):
        """Print quote 1."""
        reactor.callFromThread(on_main_thread, "Q1")

    def do_Q2(self, line):
        """Print quote 1."""
        reactor.callFromThread(on_main_thread, "Q2")

    def do_Q3(self, line):
        """Print quote 1."""
        reactor.callFromThread(on_main_thread, "Q3")

def on_main_thread(item):
    if item == "Q1":
        print("You want quote 1? Here it is!")
        reactor.connectTCP('localhost', 8000, QuoteClientFactory(bytes(quotes[0], 'utf-8')))
    elif item == "Q2":
        print("You want quote 2? Here it is!")
        reactor.connectTCP('localhost', 8000, QuoteClientFactory(bytes(quotes[1], 'utf-8')))
    elif item == "Q3":
        print("You want quote 3? Here it is!")
        reactor.connectTCP('localhost', 8000, QuoteClientFactory(bytes(quotes[2], 'utf-8')))


reactor.callInThread(CommandProcessor().cmdloop)
reactor.run()
