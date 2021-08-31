from twisted.internet import reactor, protocol
from twisted.internet.stdio import StandardIO
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver

from cmd import Cmd

import json


class RequestProtocol(protocol.Protocol):

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
        wait signal is false.
        """
        print(json.loads(data)['response'])
        if json.loads(data)['wait']:
            reactor.callLater(15, self.transport.loseConnection)
        else:
            self.transport.loseConnection()


class RequestClientFactory(protocol.ClientFactory):
    protocol = RequestProtocol

    def __init__(self, request):
        self.request = request

    def clientConnectionFailed(self, connector, reason):
        print("Connection failed:", reason.getErrorMessage())


class CenterShell(Cmd):

    def do_call(self, arg):
        """make application receive a call whose id is <id>."""
        if arg.isnumeric():
            reactor.callFromThread(call, arg)
        else:
            print("error: <id> must be a integer")

    def do_answer(self, arg):
        """make operator <id> answer a call being delivered to it."""
        if arg.isnumeric():
            print("error: <id> must be a character")
        else:
            reactor.callFromThread(answer, arg)

    def do_reject(self, arg):
        """make operator <id> reject a call being delivered to it."""
        if arg.isnumeric():
            print("error: <id> must be a character")
        else:
            reactor.callFromThread(reject, arg)

    def do_hangup(self, arg):
        """make call whose id is <id> be finished."""
        if arg.isnumeric():
            reactor.callFromThread(hangup, arg)
        else:
            print("error: <id> must be a integer")

    def do_EOF(self, arg):
        """brute force quit using ctrl+d"""
        reactor.stop()
        return True

    def do_exit(self, arg):
        """cleanly quit the program and stop the reactor."""
        print("Goodbye!")
        reactor.stop()
        return True


class LineProcessor(LineReceiver):

    def __init__(self):
        self.processor = CenterShell()
        self.setRawMode()

    def rawDataReceived(self, data):
        self.processor.onecmd(data.decode('utf-8'))


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


StandardIO(LineProcessor())
reactor.run()
