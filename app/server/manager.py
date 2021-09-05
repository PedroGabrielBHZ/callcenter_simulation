from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor, protocol
from twisted.application import service, internet

from collections import deque

import os
import sys

import json


class RequestProtocol(protocol.Protocol):

    def connectionMade(self):
        self.factory.clients.append(self)

    def connectionLost(self, reason):
        self.factory.clients.remove(self)

    def dataReceived(self, data, verbose=True):
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
            print("> Command:", command)
            print("> ID:", identifier)
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

    # Call Center Manager variables

    # The factory's response to be sent back to client.
    response = ''

    # A list of current connected clients.
    clients = []

    # A list of current timeout objects representing calls
    # that could be ignored by the operator.
    timeout_calls = []

    # A queue data structure responsible for storing calls
    # that are currently waiting for an available operator.
    calls_on_wait = deque()

    # The call center's operators. Each operator is
    # represented by a dictionary with keys mapping to the
    # operator current state and current assigned call.
    operators = {
        'A': {'state': 'available', 'call': None},
        'B': {'state': 'available', 'call': None}
    }

    def call(self, id):
        """Process an incoming call from the client.
        If there are calls with the same id being processed
        by the call center, send back a response telling the
        client that this call is being handled. Else, invoke
        the aux_call function, responsible for checking if 
        there are available operators to handle the call. If
        not, the call is sent to the queue.
        """
        if self.id_already_taken(id):
            self.response += f'Call {id} is already being processed.\n'
        else:
            # If id is not taken, make the call using the auxiliary function.
            self.aux_call(id)

    def answer(self, id):
        """Make operator <id> answer a call being delivered to it.
        If operator <id> is already in a call, if there are no calls
        to be answered, or there is no operator <id>, send back a
        response accordingly. If operator is available, set his state
        to busy and remove the call's timeout.
        """
        # Try to find operator <id>. If there is no operator <id>, except.
        try:
            operator = self.operators[id]
        except:
            self.response += f'There is no operator whose id is equal to {id}.\n'
            return
        if operator['state'] == 'busy':
            self.response += f"Operator {id} is already in a call.\n"
        else:
            call = operator['call']
            if call == None:
                self.response += f"There are no calls for operator {id}.\n"
            else:
                # Set the operator as busy, update response and remove timeout.
                operator['state'] = 'busy'
                self.response += f"Call {call} answered by operator {id}.\n"
                self.remove_timeout(call)

    def reject(self, id):
        """Make operator <id> reject a call being delivered to it.
        If there are no calls to be rejected or there is no operator
        <id>, send back a response accordingly. Else, send back the
        response that operator <id> rejected the call, remove the call's
        timeout and send the rejected call through aux_call() to be
        handled again by the call center.
        Attention: This function allows an operator to reject an answered call.
        """
        # Try to find operator <id>. If there is no operator <id>, except.
        try:
            operator = self.operators[id]
        except:
            self.response += f'There is no operator whose id is equal to {id}.\n'
            return
        call = operator['call']
        if call == None:
            self.response += f"There are no calls for operator {id} to reject.\n"
        else:
            # Free the operator, update response and remove timeout.
            operator['state'] = 'available'
            self.response += f"Call {call} rejected by operator {id}\n"
            self.remove_timeout(call)
            # Call got rejected, but it must be sent again for processing.
            self.aux_call(call, novel=False)

    def hangup(self, id):
        """Make call whose id is <id> be finished. If the call being hung up
        is in the queue, remove it from the queue and tell the client that this
        call was missed. If the operator was handling call <id>, set the operator
        as available and try to dequeue a call. If the call was ringing, tell the
        client that call <id> was missed and try to dequeue a call."""
        # if call is on wait, print that call was missed
        if id in self.calls_on_wait:
            self.calls_on_wait.remove(id)
            self.response += f"Call {id} missed\n"
        # else, look for operator responsible for that call
        else:
            operator, operator_id = self.get_operator_by_call(id)
            if operator != None:
                if operator['state'] == 'busy':
                    # operator has cleanly finished his/her call
                    operator['state'] = 'available'
                    operator['call'] = None
                    self.response += f"Call {id} finished and operator {operator_id} available\n"
                    # there is a new available operator, so dequeue a call if there is one
                    self.try_dequeueing_call()
                    return
                if operator['state'] == 'ringing':
                    # operator missed the ringing call
                    operator['state'] = 'available'
                    operator['call'] = None
                    self.response += f"Call {id} missed\n"
                    # there is a new available operator, so dequeue a call if there is one
                    self.try_dequeueing_call()
                    return

        self.response += f"There are no calls with id equal to {id}\n"
        return

    def try_dequeueing_call(self):
        """Dequeue a call if there are any in queue."""
        if len(self.calls_on_wait) != 0:
            self.aux_call(self.calls_on_wait.popleft(), novel=False)
            return True
        return False

    def aux_call(self, id: int, novel=True) -> None:
        """Auxiliary call function. Used to handle cases when
        another function makes a call. In that case, the <novel>
        argument is set to False. When equal to True, it signals
        that a new call is being received from the client.
        """
        if novel:
            self.response += f'Call {id} received\n'

        # a new, pending or rejected call has come in, look for an available operator.
        for operator_id in self.operators:
            if self.operators[operator_id]['state'] == 'available':
                self.operators[operator_id]['state'] = 'ringing'
                self.operators[operator_id]['call'] = id
                self.response += f"Call {id} ringing for operator {operator_id}\n"
                self.add_timeout(id)
                return

        # there are no available operators, put the call in the queue.
        self.calls_on_wait.append(id)
        self.response += f"Call {id} waiting in queue\n"
        return

    def add_timeout(self, id):
        """Add a timeout of 10 seconds for a call
        that is ringing for an operator. Update
        manager's list of counting timeouts.
        """
        timeout_call = reactor.callLater(60, self.on_timeout, id)
        self.timeout_calls.append({'id': id, 'call': timeout_call})

    def remove_timeout(self, id):
        """Remove a timeout from the manager's list by the
        call's id and cancel the timeout in the reactor. 
        """
        for timeout_call in self.timeout_calls:
            if timeout_call['id'] == id:
                timeout_call['call'].cancel()
                self.timeout_calls.remove(timeout_call)
                return
        return

    def on_timeout(self, id):
        """Send back a signal to listening clients that the
        operator responsible for call <id> has ignored it.
        """
        operator, operator_id = self.get_operator_by_call(id)
        if operator != None:
            for timeout_call in self.timeout_calls:
                if timeout_call['id'] == id:
                    self.timeout_calls.remove(timeout_call)
                    operator['state'] = 'available'
                    operator['call'] = None
                    self.response = f"Call {id} ignored by operator {operator_id}\n"
                    self.try_dequeueing_call()

                    # This may break if there are different client-programs.
                    # It only sends to the first listening client found.
                    wait = self.timeout_calls != []
                    for client in self.clients:
                        client.transport.write(bytes(json.dumps(
                            {"response": self.response, "wait": wait}), 'utf-8'))
                        self.response = ''
                        return
        return

    def get_operator_by_call(self, id):
        """Return the operator's object and id for the
        operator responsible for call <id>.
        If there are no operators assigned to that call,
        return a None tuple.
        """
        for operator_id in self.operators:
            if self.operators[operator_id]['call'] == id:
                return self.operators[operator_id], operator_id

        # operator not found, return a None tuple.
        return None, None

    def id_already_taken(self, id):
        """ Check if the call's id is already taken by some other
        call being handled by the call center manager.
        """
        call_id_already_taken = False

        # Check for calls being handled by the operators.
        for operator_id in self.operators:
            if self.operators[operator_id]['call'] == id:
                call_id_already_taken = True

        # Check for calls in the waiting queue.
        for call in self.calls_on_wait:
            if call == id:
                call_id_already_taken = True

        return call_id_already_taken
