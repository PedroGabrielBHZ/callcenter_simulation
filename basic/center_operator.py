from collections import deque


class CenterOperator():
    """simple call-center simulator"""

    def __init__(self):
        self.__unprocessed_calls: deque = deque()
        self.__operators: List = [
            {'id': 'A', 'state': 'available', 'call': None},
            {'id': 'B', 'state': 'available', 'call': None}]
        return

    def call(self, id: int, novel=True) -> None:
        """make application receive a call whose id is <id>."""
        # print to stdout
        if novel:
            print(f'Call {id} received')
        # get available operator
        available_operator_found = False
        for operator in self.__operators:
            if operator['state'] == 'available':
                available_operator_found = True
                operator['state'] = 'ringing'
                operator['call'] = id
                print(f"Call {id} ringing for operator {operator['id']}")
                break
        if not available_operator_found:
            self.__unprocessed_calls.append(id)
            print(f"Call {id} waiting in queue")
        return

    def answer(self, id: chr) -> None:
        """make operator <id> answer a call being delivered to it."""
        for operator in self.__operators:
            if operator['id'] == id:
                operator['state'] = 'busy'
                call = operator['call']
                print(f"Call {call} answered by operator {id}")
                break
        return

    def reject(self, id: chr) -> None:
        """make operator reject a call being delivered to it."""
        for operator in self.__operators:
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
        if id in self.__unprocessed_calls:
            self.__unprocessed_calls.remove(id)
            print(f"Call {id} missed")
        else:
            for operator in self.__operators:
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
            if len(self.__unprocessed_calls) != 0:
                self.call(self.__unprocessed_calls.popleft(), novel=False)
        return


if __name__ == "__main__":
    c = CenterOperator()
    c.call(1)
    input()
    c.answer('A')
    input()
    c.hangup(1)
    input()
    c.call(2)
    input()
    c.call(3)
    input()
    c.answer('A')
    input()
    c.answer('B')
    input()
    c.call(4)
    input()
    c.call(5)
    input()
    c.hangup(3)
    input()
    c.hangup(2)
    input()
    c.answer('B')
    input()
    c.reject('A')
    input()
    c.call(6)
    input()
    c.hangup(5)
    input()
    c.call(7)
    input()
    c.hangup(7)
    input()
    c.hangup(6)
    input()
    c.hangup(4)
