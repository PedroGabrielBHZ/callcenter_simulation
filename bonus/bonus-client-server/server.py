from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor, protocol
from collections import deque
import json


class RequestProtocol(protocol.Protocol):

    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        self.factory.clients.append(self)

    def connectionLost(self, reason):
        self.factory.clients.remove(self)

    def dataReceived(self, data, verbose=False):
        """Receive data, send a signal for the factory, i.e.
        the call center manager to handle the parsed request,
        and send back the response down the transport.
        """

        # Parse the incoming data, i.e. client's request.
        request = json.loads(data)
        command = request['command']
        identifier = request['id']
        
        if verbose:
            print("Received from client:", data)
            print("Parsed received data:")
            print("Command:", command)
            print("ID:", identifier)
            print()

        # Send the request to the factory.
        self.handleRequest(command, identifier)

        # Read the factory's response and send it
        # back to the client through the transport.
        self.transport.write(self.readResponse())

        if request['command'] != 'call':
            self.transport.loseConnection()

    def handleRequest(self, command, identifier):
        """Send a signal to the factory. The signal
        identifies the client's request, i.e. a function
        execution with the identifier as input.

        e.g. call <id> -> factory.call(id)
        """
        if command == "call":
            self.factory.call(identifier)
        if command == "answer":
            self.factory.answer(identifier)
        if command == "reject":
            self.factory.reject(identifier)
        if command == "hangup":
            self.factory.hangup(identifier)

    def readResponse(self):
        """Read the factory's response after the signal
        being sent and processed. After the response is
        read, it is overwritten to give place to a new
        response corresponding to a new request. The
        response is encoded in JSON format and sent
        back in bytes.
        """
        response = {"response": self.factory.response}
        self.factory.response = ''
        return bytes(json.dumps(response), 'utf-8')


class RequestFactory(Factory):

    # Call Center Variables
    clients = []
    unprocessed_calls = deque()
    operators = [{'id': 'A', 'state': 'available', 'call': None},
                 {'id': 'B', 'state': 'available', 'call': None}]
    response = ''

    def buildProtocol(self, addr):
        return RequestProtocol(self)

    # Call Center Functionality #
    def call(self, id):
        """make application receive a call whose id is <id>."""
        # Check if the call's id is already taken by some other
        # call being handled by the call center manager.
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
            self.response += f'Call {id} is already being processed.\n'
            return
        else:
            # if id is not taken, make the call using the auxiliary function.
            self.aux_call(id)

    def timeout(self, id):
        for operator in self.operators:
            if operator['call'] == id:
                if operator['state'] != 'busy':
                    operator['state'] = 'available'
                    message = f"Call {id} ignored by operator {operator['id']}"
                    for client in self.clients:
                        response = {"response": message}
                        response = bytes(json.dumps(response), 'utf-8')
                        client.transport.write(response)
                        break
                return

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

        self.response += f'There is no operator whose id is equal to {id}.\n'
        return

    def reject(self, id):
        """make operator <id> reject a call being delivered to it."""
        for operator in self.operators:
            if operator['id'] == id:
                operator['state'] = 'available'
                call = operator['call']
                if call == None:
                    self.response += f"There are no calls for operator {id} to reject.\n"
                    return
                else:
                    self.response += f"Call {call} rejected by operator {id}\n"
                    # call got rejected, but send it again for processing
                    self.aux_call(call, novel=False)
                    return

        self.response += f'There is no operator whose id is equal to {id}.\n'
        return

    def hangup(self, id):
        """make call whose id is <id> be finished."""
        # if call is unprocessed, print missed call
        if id in self.unprocessed_calls:
            self.unprocessed_calls.remove(id)
            self.response += f"Call {id} missed\n"
            return
        # else, look for operator responsible for that call
        else:
            for operator in self.operators:
                if operator['call'] == id:
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

        self.response += f"There are no calls with id equal to {id}\n"
        return
        

    def exit(self, arg):
        """close application"""
        print('Thank you for using Operator')
        return True

    def aux_call(self, id: int, novel=True) -> None:
        """auxiliary call function. It's use is to handle cases
        when another function makes a call. In that case, the <novel>
        argument is set to False. When equal to True, it signals that
        a new call is being received.
        """
        if novel:
            self.response += f'Call {id} received\n'
        # a new call has come in, look for an available operator.
        for operator in self.operators:
            if operator['state'] == 'available':
                operator['state'] = 'ringing'
                operator['call'] = id
                self.response += f"Call {id} ringing for operator {operator['id']}\n"
                self.timeout_call = reactor.callLater(10, self.timeout, id)
                return
        # there are no available operators, put the call in the queue.
        self.unprocessed_calls.append(id)
        self.response += f"Call {id} waiting in queue\n"
        return


reactor.listenTCP(5678, RequestFactory())
reactor.run()
