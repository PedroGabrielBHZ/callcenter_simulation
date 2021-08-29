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
        """Prints out the server's decoded response on stdout,
        and close connection.
        """
        response = json.loads(data)
        print(response["response"])
        self.transport.loseConnection()

class RequestClientFactory(protocol.ClientFactory):
    def __init__(self, request):
        self.request = request

    def buildProtocol(self, addr):
        return RequestProtocol(self)

class CenterShell(Cmd):
    intro = 'Welcome to the Operator shell. Type help or ? to list commands.\n'
    #prompt = '(center) '
    prompt = ''

    def do_EOF(self, arg):
        """brute force quit using ctrl+d"""
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
    request = {"command": "call", "id": arg}
    request = bytes(json.dumps(request), 'utf-8')
    reactor.connectTCP('localhost', 5678, RequestClientFactory(request))
        
def answer(arg):
    request = {"command": "answer", "id": arg}
    request = bytes(json.dumps(request), 'utf-8')
    reactor.connectTCP('localhost', 5678, RequestClientFactory(request))

def reject(arg):
    request = {"command": "reject", "id": arg}
    request = bytes(json.dumps(request), 'utf-8')
    reactor.connectTCP('localhost', 5678, RequestClientFactory(request))

def hangup(arg):
    request = {"command": "hangup", "id": arg}
    request = bytes(json.dumps(request), 'utf-8')
    reactor.connectTCP('localhost', 5678, RequestClientFactory(request))

reactor.callInThread(CenterShell().cmdloop)
reactor.run()
