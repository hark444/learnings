class StackArray:

    def __init__(self, max_size=10):
        self.items = [None] * max_size
        self.count = 0

    def is_full(self):
        return self.count == len(self.items)

    def push(self, data):
        if self.is_full():
            print("Stack is already full")
            return
        self.items[self.count] = data
        self.count += 1

    def is_empty(self):
        if self.count:
            print(False)
        else:
            print(True)

    def pop(self):
        if self.is_empty():
            print("Stack is empty.")
            return
        popped_element = self.items[self.count-1]
        self.items[self.count-1] = None
        return popped_element

    def size(self):
        print(self.count)
        return self.count

    def peak(self):
        print(self.items[self.count - 1])

    def display(self):
        print(self.items)

def call_stack_array_operations():
    astack = StackArray()
    astack.is_empty()
    astack.push(0)
    astack.push(5)
    astack.push(10)
    astack.size()
    astack.pop()
    astack.display()


class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


class StackLinkedList:

    def __init__(self):
        self.top = None

    def push(self, data):
        node = Node(data)
        node.next = self.top
        self.top = node

    def is_empty(self):
        return (self.top == None)

    def size(self):
        current = self.top
        size = 0
        while current:
            size += 1
            current = current.next
        print(size)
        return size

    def display(self):
        current = self.top
        while current:
            print(current.data, end=' ')
            current = current.next
        print()

    def pop(self):
        if not self.top:
            print("empty stack")
            return
        popped_element = self.top.data
        self.top = self.top.next
        return popped_element

def call_stack_linked_list_operations():
    astack = StackLinkedList()
    astack.is_empty()
    astack.push(0)
    astack.push(5)
    astack.push(10)
    astack.display()
    astack.size()
    astack.pop()
    astack.display()

if __name__ == '__main__':
    # call_stack_array_operations()
    call_stack_linked_list_operations()