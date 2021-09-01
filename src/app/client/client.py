from twisted.internet import reactor, protocol
from twisted.internet.stdio import StandardIO
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.application import service

from cmd import Cmd

import json


class RequestProtocol(protocol.Protocol):

    wait_call = None

    def connectionMade(self):
        """The connection has been made, send a request
        to the server through the transport. The request
        is stored in the factory and is equal to the last
        input processed by the command shell loop.
        """
        self.transport.write(self.factory.request)

    def dataReceived(self, data):
        """Print out the server's decoded response on
        stdout. After that, close the connection if 
        'wait' signal is false.
        """
        print(json.loads(data)['response'])

        if json.loads(data)['wait']:
            new_wait_call = reactor.callLater(15, self.transport.loseConnection)
            if self.wait_call != None:
                self.wait_call.cancel()
                self.wait_call = new_wait_call
            else:
                self.wait_call = new_wait_call
        else:
            self.transport.loseConnection()


class RequestClientFactory(protocol.ClientFactory):
    protocol = RequestProtocol

    def __init__(self, request):
        self.request = request

    def clientConnectionFailed(self, connector, reason):
        """Print out the reason if client failed to connect
        to the server.
        """
        print("Connection failed:", reason.getErrorMessage())


class CenterShell(Cmd):
    prompt = ''

    def do_call(self, arg):
        """Make application receive a call whose id is <id>.
        The id should be an integer.
        Usage: call <id>
        """
        if arg.isnumeric():
            reactor.callFromThread(call, arg)
        else:
            print("error: <id> must be a integer")

    def do_answer(self, arg):
        """Make operator <id> answer a call being delivered to it.
        The id should be a character.
        Usage: answer <id>
        """
        if arg.isnumeric():
            print("error: <id> must be a character")
        else:
            reactor.callFromThread(answer, arg)

    def do_reject(self, arg):
        """Make operator <id> reject a call being delivered to it.
        The id should be a character.
        Usage: reject <id>
        """
        if arg.isnumeric():
            print("error: <id> must be a character")
        else:
            reactor.callFromThread(reject, arg)

    def do_hangup(self, arg):
        """Make call whose id is <id> be finished.
        The id should should be an integer.
        Usage: hangup <id>
        """
        if arg.isnumeric():
            reactor.callFromThread(hangup, arg)
        else:
            print("error: <id> must be a integer")

    def do_EOF(self, arg):
        """Quit the program by pressing ctrl+d"""
        reactor.stop()
        return True

    def do_exit(self, arg):
        """Cleanly quit the program."""
        print("Goodbye!")
        reactor.stop()
        return True


class LineProcessor(LineReceiver):

    def __init__(self):
        self.processor = CenterShell()
        self.setRawMode()

    def rawDataReceived(self, data):
        """Send out the input to the command interpreter."""
        self.processor.onecmd(data.decode('utf-8'))

host = 'localhost'
#host = '0.0.0.0:5001'
port = 5678

def call(arg):
    """Create a protocol signaling an incoming call with id <arg>.
    This request is to be handled by the queue manager in the server."""
    request = {"command": "call", "id": arg}
    request = bytes(json.dumps(request), 'utf-8')
    reactor.connectTCP(host, port, RequestClientFactory(request))

def answer(arg):
    """Create a protocol signaling that operator with id <arg> 
    answered his assigned call. This request is to be handled
    by the queue manager in the server."""
    request = {"command": "answer", "id": arg}
    request = bytes(json.dumps(request), 'utf-8')
    reactor.connectTCP(host, port, RequestClientFactory(request))


def reject(arg):
    """Create a protocol signaling that operator with id <arg> 
    rejected his assigned call. This request is to be handled 
    by the queue manager in the server."""
    request = {"command": "reject", "id": arg}
    request = bytes(json.dumps(request), 'utf-8')
    reactor.connectTCP(host, port, RequestClientFactory(request))


def hangup(arg):
    """Create a protocol signaling that operator with id <arg> 
    hung up his assigned call. This request is to be handled by
    the queue manager in the server."""
    request = {"command": "hangup", "id": arg}
    request = bytes(json.dumps(request), 'utf-8')
    reactor.connectTCP(host, port, RequestClientFactory(request))

class ShellService(service.Service):

    def startService(self):
        StandardIO(LineProcessor())

        # Uncomment to use old IO method.
        # reactor.callInThread(CenterShell().cmdloop)
