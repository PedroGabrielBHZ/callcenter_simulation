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
        reactor.callLater(20, self.transport.loseConnection)

    def dataReceived(self, data):
        """Print out the server's decoded response on
        stdout. After that, close the connection.
        """
        print(json.loads(data)['response'])


class RequestClientFactory(protocol.ClientFactory):
    protocol = RequestProtocol

    def __init__(self, request):
        self.request = request


class CenterShell(Cmd):

    def do_call(self, arg):
        """make application receive a call whose id is <id>."""
        if arg.isnumeric():
            reactor.callFromThread(call, arg)
        else:
            print("<id> must be a integer")

    def do_answer(self, arg):
        """make operator <id> answer a call being delivered to it."""
        if arg.isnumeric():
            print("<id> must be a character")
        else:
            reactor.callFromThread(answer, arg)

    def do_reject(self, arg):
        """make operator <id> reject a call being delivered to it."""
        if arg.isnumeric():
            print("<id> must be a character")
        else:
            reactor.callFromThread(reject, arg)

    def do_hangup(self, arg):
        """make call whose id is <id> be finished."""
        if arg.isnumeric():
            reactor.callFromThread(hangup, arg)
        else:
            print("<id> must be a integer")

    def do_EOF(self, arg):
        """brute force quit using ctrl+d"""
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
