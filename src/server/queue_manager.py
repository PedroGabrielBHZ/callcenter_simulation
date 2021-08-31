from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor, protocol

from collections import deque

import json


class RequestProtocol(protocol.Protocol):

    def connectionMade(self):
        self.factory.clients.append(self)

    def connectionLost(self, reason):
        self.factory.clients.remove(self)

    def dataReceived(self, data, verbose=False):
        """Receive data, send a signal for the factory, i.e.
        the call center manager to handle the parsed request,
        and send back the response down the transport.
        If verbose is set to True, print incoming data on
        stdout.
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

        # Handle the request, sending the appropriate
        # command to the factory.
        self.handleRequest(command, identifier)

        # Read the factory's response and send it
        # back to the client through the transport.
        self.transport.write(self.readResponse())


    def handleRequest(self, command, identifier):
        """Send a signal to the factory. The signal
        identifies the client's request, i.e. a function
        execution along with the identifier as input.

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
        read, it is overwritten to give place to a future
        response corresponding to a new request. The
        response is encoded in JSON format and sent
        back in bytes. If there are pending timeouts,
        send a wait signal along with the response
        telling the client to hold the connection.
        """
        response = {"response": self.factory.response,
                    "wait": self.factory.timeout_calls != []}
        self.factory.response = ''
        return bytes(json.dumps(response), 'utf-8')


class RequestFactory(protocol.Factory):
    protocol = RequestProtocol

    # Call Center Variables

    # The factory's response to be sent back to client.
    response = ''

    # A list of current connected clients.
    clients = []

    # A list of current timeout objects representing calls
    # that will be potentially ignored by the operator.
    timeout_calls = []

    # A queue data structure responsible for storing calls
    # that are currently waiting for an available operator.
    unprocessed_calls = deque()

    # A list of the call center's operators. Each operator is
    # represented by a dictionary with keys mapping to the
    # operator current state and current assigned call.
    operators = [{'id': 'A', 'state': 'available', 'call': None},
                 {'id': 'B', 'state': 'available', 'call': None}]


    def call(self, id):
        """Process an incoming call from the client.
        If there are calls with the same id being processed
        by the call center, send back a response telling
        client that this call is being handled. Else, invoke
        the aux_call function, responsible for checking if 
        there are available operators to handle the call. If
        not, the call is sent to the queue.
        """
        if self.id_already_taken(id):
            self.response += f'Call {id} is already being processed.\n'
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
                        self.remove_timeout(call)
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
                    self.remove_timeout(call)
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
        """auxiliary call function. Used to handle cases
        when another function makes a call. In that case, the <novel>
        argument is set to False. When equal to True, it signals that
        a new call is being received from the client.
        """
        if novel:
            self.response += f'Call {id} received\n'

        # a new, pending or rejected call has come in, look for an available operator.
        for operator in self.operators:
            if operator['state'] == 'available':
                operator['state'] = 'ringing'
                operator['call'] = id
                self.response += f"Call {id} ringing for operator {operator['id']}\n"
                self.add_timeout(id)
                return

        # there are no available operators, put the call in the queue.
        self.unprocessed_calls.append(id)
        self.response += f"Call {id} waiting in queue\n"
        return

    def add_timeout(self, call):
        """Add a timeout of 10 seconds for a call
        that is ringing for an operator. Update
        factory's list of counting timeouts.
        """
        timeout_call = reactor.callLater(10, self.on_timeout, call)
        self.timeout_calls.append({'id': call, 'call': timeout_call})

    def remove_timeout(self, call):
        """Remove a timeout from the factory's list
        and cancel the timeout in the reactor. 
        """
        for timeout_call in self.timeout_calls:
            if timeout_call['id'] == call:
                timeout_call['call'].cancel()
                self.timeout_calls.remove(timeout_call)
                return
        return

    def on_timeout(self, id):
        """Send back a signal to listening clients that the
        operator responsible for call <id> has ignored it.
        """
        for operator in self.operators:
            if operator['call'] == id:
                for timeout_call in self.timeout_calls:
                    if timeout_call['id'] == id:
                        self.timeout_calls.remove(timeout_call)
                        operator['state'] = 'available'
                        operator['call'] = None
                        message = f"Call {id} ignored by operator {operator['id']}"
                        # Try to deque a call - untested
                        # CODE GOES HERE
                        #
                        for client in self.clients:
                            client.transport.write(bytes(
                                json.dumps({"response": message, "wait": False}), 'utf-8'))
                            return
        return

    def id_already_taken(self, id):
        """ Check if the call's id is already taken by some other
        call being handled by the call center manager.
        """
        call_id_already_taken = False

        # Check for calls being handled by the operators.
        for operator in self.operators:
            if operator['call'] == id:
                call_id_already_taken = True

        # Check for calls in the waiting queue.
        for call in self.unprocessed_calls:
            if call == id:
                call_id_already_taken = True
        
        return call_id_already_taken


reactor.listenTCP(5678, RequestFactory())
reactor.run()
