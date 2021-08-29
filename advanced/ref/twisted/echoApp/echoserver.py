# list for TCP connections on a particular port and echo
# back anything it receives.
from twisted.internet import protocol, reactor
import json

class Echo(protocol.Protocol):
    def dataReceived(self, data):
        print("I am a protocol, the factory has given me life!")
        print("Someone sent down the line:", data)
        print()
        message = json.loads(data)
        print("After decoding:", message)
        print("Command:", message['command'])
        print("ID:", message['id'])
        print("That's the way to handle JSON. Gonna echo that!")
        print()
        self.transport.write(data)

class EchoFactory(protocol.Factory):
    print("I have come to life. I am a server!")
    connections = 0
    
    def buildProtocol(self, addr):
        print("Somebody wants to talk with me, building a protocol.")
        print("So far I've served {} connections.".format(self.connections))
        self.connections += 1
        return Echo()

reactor.listenTCP(8000, EchoFactory())
reactor.run()
