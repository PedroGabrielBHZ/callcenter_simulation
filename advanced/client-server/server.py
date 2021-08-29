from twisted.internet.protocol import Factory
from twisted.internet import reactor, protocol
from collections import deque
import json

class RequestProtocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory

    def dataReceived(self, data):
        # Received the request
        print("Received from client:", data)
        request = json.loads(data)
        command = request['command']
        identifier = request['id']
        
        print("Parsed received data:")
        print("Command:", command)
        print("ID:", identifier)
        print()

        self.updateRequest(command, identifier)
        self.transport.write(self.getRequest())
        self.factory.response = ''

    def updateRequest(self, command, identifier):
        if command == "call":
            self.factory.call(identifier)
        if command == "answer":
            self.factory.answer(identifier)
        if command == "reject":
            self.factory.reject(identifier)
        if command == "hangup":
            self.factory.hangup(identifier)

    def getRequest(self):
        response = {"response": self.factory.response}
        print(json.dumps(response))
        return bytes(json.dumps(response), 'utf-8')

        # return bytes(self.factory.response, 'utf-8')


class RequestFactory(Factory):

    # Call Center Variables
    unprocessed_calls = deque()
    operators = [{'id': 'A', 'state': 'available', 'call': None},
                 {'id': 'B', 'state': 'available', 'call': None}]
    response = ""
    
    # legacy
    def __init__(self, quote=None):
        self.quote = quote or b"An apple a day keeps the DOC away."
    # legacy

    def buildProtocol(self, addr):
        return RequestProtocol(self)

    # Call Center Functionality #
    def call(self, arg):
        """make application receive a call whose id is <id>."""
        self.aux_call(arg)

    def answer(self, id: chr) -> None:
        """make operator <id> answer a call being delivered to it."""
        for operator in self.operators:
            if operator['id'] == id:
                operator['state'] = 'busy'
                call = operator['call']
                self.response += f"Call {call} answered by operator {id}\n"
                break
        return

    def reject(self, id: chr) -> None:
        """make operator reject a call being delivered to it."""
        for operator in self.operators:
            if operator['id'] == id:
                operator['state'] = 'available'
                call = operator['call']
                self.response += f"Call {call} rejected by operator {id}\n"
                self.aux_call(call, novel=False)
                break
        return

    def hangup(self, id: int) -> None:
        """make call whose id is <id> be finished."""
        # if call is unprocessed, print missed call
        if id in self.unprocessed_calls:
            self.unprocessed_calls.remove(id)
            self.response += f"Call {id} missed\n"
        else:
            for operator in self.operators:
                if operator['call'] == id:
                    if operator['state'] == 'busy':
                        operator['state'] = 'available'
                        operator['call'] = None
                        op_id = operator['id']
                        self.response += f"Call {id} finished and operator {op_id} available\n"
                        break
                    if operator['state'] == 'ringing':
                        operator['state'] = 'available'
                        operator['call'] = None
                        self.response += f"Call {id} missed\n"
                        break
            # there is a new available operator, so dequeue a call if there is one
            if len(self.unprocessed_calls) != 0:
                self.aux_call(self.unprocessed_calls.popleft(), novel=False)
        return

    def exit(self, arg):
        """close application"""
        print('Thank you for using Operator')
        return True

    def aux_call(self, id: int, novel=True) -> None:
        """auxiliary call function."""
        # print to stdout
        if novel:
            self.response += f'Call {id} received\n'
        # get available operator
        available_operator_found = False
        for operator in self.operators:
            if operator['state'] == 'available':
                available_operator_found = True
                operator['state'] = 'ringing'
                operator['call'] = id
                self.response += f"Call {id} ringing for operator {operator['id']}\n"
                break
        if not available_operator_found:
            self.unprocessed_calls.append(id)
            self.response += f"Call {id} waiting in queue\n"
        return

reactor.listenTCP(5678, RequestFactory())
reactor.run()

