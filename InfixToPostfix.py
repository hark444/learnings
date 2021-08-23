from Stack import StackLinkedList


def precedence(symbol):
    if symbol in '(':
        return 0
    elif symbol in '+-':
        return 1
    elif symbol in '*/':
        return 2
    elif symbol in '^':
        return 3
    elif symbol in ')':
        return 5
    else:
        return 4


def infix_to_postfix(expression):
    postfix = ''
    sll = StackLinkedList()
    for term in expression:
        local_precedence = precedence(term)
        if local_precedence == 4:
            postfix += term
            continue
        else:
            if sll.is_empty():
                sll.push((local_precedence, term))
            elif local_precedence == 0:
                sll.push((local_precedence, term))
            elif local_precedence == 5:
                while sll.top.data[0] != 0:
                    postfix += sll.pop()[1]
                sll.pop()
            else:
                if local_precedence > sll.top.data[0]:
                    sll.push((local_precedence, term))
                else:
                    while not sll.is_empty() and local_precedence <= sll.top.data[0]:
                        postfix += sll.pop()[1]
                    sll.push((local_precedence, term))
    while not sll.is_empty():
        postfix += sll.pop()[1]
    return postfix


def evaluate_postfix(expression):
    sll = StackLinkedList()
    for letter in expression:
        if letter not in '+-*/^':
            sll.push(letter)
        else:
            y = sll.pop()
            x = sll.pop()
            if letter == '^':
                letter = '**'
            solution = eval('{}{}{}'.format(x, letter, y))
            sll.push(solution)
    print(sll.top.data)



if __name__ == '__main__':
    expression = '5+8*3^2/(8-2^2)+7*3'
    # expression = 'p-q*r^s/t+u*v'
    postfix = infix_to_postfix(expression)
    print(postfix)
    postfix = '532^+28*22+/-4+'
    evaluate_postfix(postfix)