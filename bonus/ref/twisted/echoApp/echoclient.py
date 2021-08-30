# connect to the server, send it a message,
# receive a response, and terminate connection.
from twisted.internet import reactor, protocol
import json

class EchoClient(protocol.Protocol):
    def connectionMade(self):
        message = {"command": "call", "id": "<id>"}
        self.transport.write(bytes(json.dumps(message), 'utf-8'))

    def dataReceived(self, data):
        print("Server said:", data)
        self.transport.loseConnection()

class EchoFactory(protocol.ClientFactory):
    def buildProtocol(self, addr):
        print("You wanna a protocol? Take it!")
        return EchoClient()

    def clientConnectionFailed(self, connector, reason):
        print("Connection failed.")
        reactor.stop()
    
    def clientConnectionLost(self, connector, reason):
        print("Connection lost.")
        reactor.stop()

reactor.connectTCP("localhost", 8000, EchoFactory())
reactor.run()
