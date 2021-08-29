from twisted.internet import reactor, protocol
from cmd import Cmd
import json

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
        message = data.decode('utf-8')
        print(message)
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
        reactor.callFromThread(call, arg)

    def do_answer(self, arg):
        reactor.callFromThread(answer, arg)

    def do_reject(self, arg):
        reactor.callFromThread(reject, arg)

    def do_hangup(self, arg):
        reactor.callFromThread(hangup, arg)

def call(arg):
    request = {"command": "call", "id": arg}
    request = bytes(json.dumps(request), 'utf-8')
    reactor.connectTCP('localhost', 8000, RequestClientFactory(request))
        
def answer(arg):
    request = {"command": "answer", "id": arg}
    request = bytes(json.dumps(request), 'utf-8')
    reactor.connectTCP('localhost', 8000, RequestClientFactory(request))

def reject(arg):
    request = {"command": "reject", "id": arg}
    request = bytes(json.dumps(request), 'utf-8')
    reactor.connectTCP('localhost', 8000, RequestClientFactory(request))

def hangup(arg):
    request = {"command": "hangup", "id": arg}
    request = bytes(json.dumps(request), 'utf-8')
    reactor.connectTCP('localhost', 8000, RequestClientFactory(request))

reactor.callInThread(CenterShell().cmdloop)
reactor.run()
