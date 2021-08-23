from Stack import StackLinkedList


class Error(Exception):
    pass


class InvalidKeyError(Error):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message


class EmptyStackError(Error):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message

input_string = "[{a+(b-c)}]"
parans = {
    "{": "}",
    "[": "]",
    "(": ")"
}


def paran_validation(input_string, parans, sll):
    for letter in input_string:
        if letter in parans.keys():
            sll.push(letter)
        elif letter in parans.values():
            if sll.is_empty():
                raise EmptyStackError(letter, 'Stack is empty.')
                break
            popped_element = sll.pop()
            if letter != parans[popped_element]:
                raise InvalidKeyError(letter, 'Invalid key bro')

    if not sll.is_empty():
        raise EmptyStackError(letter, 'Stack is empty.')
    else:
        print("Validation Successfully Completed.")



if __name__ == '__main__':
    sll = StackLinkedList()
    paran_validation(input_string, parans, sll)