# Upon receiving a quote from a client, the server
# will send the client its current quote and store
# the client's quote to share with the next client.
# It also keeps track of the number of concurrent
# client connections.

from twisted.internet.protocol import Factory
from twisted.internet import reactor, protocol
from collections import deque

class RequestProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory

    def dataReceived(self, data):
        # Received the request
        print("PONG!", data)

        # Must receive not only id, but also the request.
        # Here comes json.

        self.transport.write(self.getRequest())
        self.updateRequest(data)

    def getRequest(self):
        return self.factory.quote

    def updateRequest(self, quote):
        self.factory.quote = quote

class RequestFactory(Factory):
    unprocessed_calls = deque()
    operators = [{'id': 'A', 'state': 'available', 'call': None},
                 {'id': 'B', 'state': 'available', 'call': None}]
    
    def __init__(self, quote=None):
        self.quote = quote or b"An apple a day keeps the DOC away."

    def buildProtocol(self, addr):
        return RequestProtocol(self)

    def call(self, arg):
        """make application receive a call whose id is <id>."""
        self.call(arg)

    def answer(self, id: chr) -> None:
        """make operator <id> answer a call being delivered to it."""
        for operator in self.operators:
            if operator['id'] == id:
                operator['state'] = 'busy'
                call = operator['call']
                print(f"Call {call} answered by operator {id}")
                break
        return

    def reject(self, id: chr) -> None:
        """make operator reject a call being delivered to it."""
        for operator in self.operators:
            if operator['id'] == id:
                operator['state'] = 'available'
                call = operator['call']
                print(f"Call {call} rejected by operator {id}")
                self.call(call, novel=False)
                break
        return

    def hangup(self, id: int) -> None:
        """make call whose id is <id> be finished."""
        # if call is unprocessed, print missed call
        if id in self.unprocessed_calls:
            self.unprocessed_calls.remove(id)
            print(f"Call {id} missed")
        else:
            for operator in self.operators:
                if operator['call'] == id:
                    if operator['state'] == 'busy':
                        operator['state'] = 'available'
                        operator['call'] = None
                        op_id = operator['id']
                        print(
                            f"Call {id} finished and operator {op_id} available")
                        break
                    if operator['state'] == 'ringing':
                        operator['state'] = 'available'
                        operator['call'] = None
                        print(f"Call {id} missed")
                        break
            # there is a new available operator, so dequeue a call if there is one
            if len(self.unprocessed_calls) != 0:
                self.call(self.unprocessed_calls.popleft(), novel=False)
        return

    def exit(self, arg):
        """close application"""
        print('Thank you for using Operator')
        return True

    def call(self, id: int, novel=True) -> None:
        """auxiliary call function."""
        # print to stdout
        if novel:
            print(f'Call {id} received')
        # get available operator
        available_operator_found = False
        for operator in self.operators:
            if operator['state'] == 'available':
                available_operator_found = True
                operator['state'] = 'ringing'
                operator['call'] = id
                print(f"Call {id} ringing for operator {operator['id']}")
                break
        if not available_operator_found:
            self.unprocessed_calls.append(id)
            print(f"Call {id} waiting in queue")
        return

reactor.listenTCP(8000, RequestFactory())
reactor.run()

