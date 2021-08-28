from cmd import Cmd
from twisted.internet import reactor, protocol

class RequestProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        self.sendRequest()

    def sendRequest(self):
        """Send a request to the server."""
        self.transport.write(self.factory.request)

    def dataReceived(self, data):
        """Prints out the server's response."""
        print(data)
        self.transport.loseConnection()

class RequestClientFactory(protocol.ClientFactory):
    def __init__(self, request):
        self.request = request

    def buildProtocol(self, addr):
        return RequestProtocol(self)

class CenterShell(Cmd):
    intro = 'Welcome to the Operator shell.   Type help or ? to list commands.\n'
    prompt = '(center) '

    def do_EOF(self, arg):
        return True

    def do_call(self, arg):
        """make application receive a call whose id is <id>."""
        reactor.callFromThread(call, str(arg))

def call(arg):
    print("Making a call with id {}".format(arg))
    reactor.connectTCP('localhost', 8000, RequestClientFactory(bytes(arg, 'utf-8')))
        

reactor.callInThread(CenterShell().cmdloop)
reactor.run()
