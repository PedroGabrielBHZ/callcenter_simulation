from twisted.internet.protocol import Factory
from twisted.internet import reactor, protocol
from collections import deque
import json


class RequestProtocol(protocol.Protocol):

    def __init__(self, factory):
        self.factory = factory

    def dataReceived(self, data):

        print("Received from client:", data)
        request = json.loads(data)
        command = request['command']
        identifier = request['id']

        print("Parsed received data:")
        print("Command:", command)
        print("ID:", identifier)
        print()

        self.handleRequest(command, identifier)
        self.transport.write(self.getRequest())
        self.factory.response = ''

    def handleRequest(self, command, identifier):
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
        return bytes(json.dumps(response), 'utf-8')


class RequestFactory(Factory):

    # Call Center Variables
    unprocessed_calls = deque()
    operators = [{'id': 'A', 'state': 'available', 'call': None},
                 {'id': 'B', 'state': 'available', 'call': None}]
    response = ""


    def buildProtocol(self, addr):
        return RequestProtocol(self)

    # Call Center Functionality #
    def call(self, id):
        """make application receive a call whose id is <id>."""

        # Check if the call's id already taken by some call
        # being handled by the call center manager.
        call_id_already_taken = False

        # Check for calls being handled by the operators.
        for operator in self.operators:
            if operator['call'] == id:
                call_id_already_taken = True

        # Check for calls in the waiting queue.
        for call in self.unprocessed_calls:
            if call == id:
                call_id_already_taken = True

        if call_id_already_taken:
            self.response += f"Call {id} is already being processed.\n"
            return
        else:
            # if id is not taken, make the call using the auxiliary function.
            self.aux_call(id)

    def answer(self, id):
        """make operator <id> answer a call being delivered to it."""
        for operator in self.operators:
            if operator['id'] == id:
                if operator['state'] == 'busy':
                    self.response += f"Operator {id} is already in a call.\n"
                    return
                else:
                    call = operator['call']
                    if call == None:
                        self.response += f"There are no calls for operator {id}.\n"
                        return
                    else:
                        operator['state'] = 'busy'
                        self.response += f"Call {call} answered by operator {id}.\n"
                        return
        return

    def reject(self, id):
        """make operator reject a call being delivered to it."""
        for operator in self.operators:
            if operator['id'] == id:
                operator['state'] = 'available'
                call = operator['call']
                if call == 'None':
                    self.response += f"There are no calls for operator {id} to reject.\n"
                    return
                else:
                    self.response += f"Call {call} rejected by operator {id}\n"
                    # call got rejected, but send it again for processing
                    self.aux_call(call, novel=False)
                    return
        return

    def hangup(self, id):
        """make call whose id is <id> be finished."""
        found_call = False
        # if call is unprocessed, print missed call
        if id in self.unprocessed_calls:
            found_call = True
            self.unprocessed_calls.remove(id)
            self.response += f"Call {id} missed\n"
            return
        # else, look for operator responsible for that call
        else:
            for operator in self.operators:
                if operator['call'] == id:
                    found_call = True
                    if operator['state'] == 'busy':
                        # operator has cleanly finished the call
                        operator['state'] = 'available'
                        operator['call'] = None
                        op_id = operator['id']
                        self.response += f"Call {id} finished and operator {op_id} available\n"
                        # there is a new available operator, so dequeue a call if there is one
                        if len(self.unprocessed_calls) != 0:
                            self.aux_call(self.unprocessed_calls.popleft(), novel=False)
                        return
                    if operator['state'] == 'ringing':
                        # operator missed the ringing call
                        operator['state'] = 'available'
                        operator['call'] = None
                        self.response += f"Call {id} missed\n"
                        # there is a new available operator, so dequeue a call if there is one
                        if len(self.unprocessed_calls) != 0:
                            self.aux_call(self.unprocessed_calls.popleft(), novel=False)
                        return
        # there is no call with id equal to <id>
        if not found_call:
            self.response += f"There are no calls with id equal to {id}\n"
        return
        

    def exit(self, arg):
        """close application"""
        print('Thank you for using Operator')
        return True

    def aux_call(self, id: int, novel=True) -> None:
        """auxiliary call function."""
        if novel:
            self.response += f'Call {id} received\n'
        available_operator_found = False
        # a new call has come in, look for an available operator
        for operator in self.operators:
            if operator['state'] == 'available':
                available_operator_found = True
                operator['state'] = 'ringing'
                operator['call'] = id
                self.response += f"Call {id} ringing for operator {operator['id']}\n"
                return
        if not available_operator_found:
            # there is no available operator, put it in the queue
            self.unprocessed_calls.append(id)
            self.response += f"Call {id} waiting in queue\n"
            return
        return


reactor.listenTCP(5678, RequestFactory())
reactor.run()
