class DNode:

    def __init__(self, data=None):
        self.previous = None
        self.data = data
        self.next = None


class DoublyLinkedList:

    def __init__(self):
        self.start = None

    def insertion_at_beginning(self, data):
        node = DNode(data)
        node.next = self.start
        self.start.previous = node
        self.start = node

    def insertion_in_empty_list(self, data):
        node = DNode(data)
        self.start = node

    def insertion_at_end(self, data):
        node = DNode(data)
        current = self.start
        while current.next:
            current = current.next
        node.previous = current
        current.next = node

    def insertion_after_value(self, value, data):
        node = DNode(data)
        current = self.start
        while current.next:
            if current.data == value:
                node.previous = current
                node.next = current.next
                current.next = node
                break
            current = current.next

    def insertion_before_value(self, value, data):
        node = DNode(data)
        current = self.start
        while current.next:
            if current.data == value:
                node.previous = current.previous
                node.next = current
                node.previous.next = node
            current = current.next

    def traversal(self):
        current = self.start
        while current:
            print(current.data, end=' ')
            current = current.next
        print()

    def delete_first_node(self):
        self.start = self.start.next

    def delete_entire_list(self):
        self.start = None

    def delete_after_value(self, value):
        current = self.start
        while current.next:
            if current.data == value:
                current.next = current.next.next
                current.next.previous = current
            current = current.next

    def delete_before_value(self, value):
        current = self.start

        if current.next.data == value:
            self.start = current.next
            self.start.previous = None
            return
        while current.next:
            if current.data == value:
                current.previous = current.previous.previous
                current.previous.next = current

    def delete_last(self):
        current = self.start
        while current.next:
            current = current.next
        current.previous.next = None

    def list_reversal(self):
        current = self.start
        while current.next:
            current = current.next
            current.previous.next, current.previous.previous = current.previous.previous, current.previous.next
        current.next = current.previous
        current.previous = None
        self.start = current


def call_doubly_linked_list():
    dll = DoublyLinkedList()
    dll.insertion_in_empty_list(5)
    dll.insertion_at_beginning(0)
    dll.insertion_at_end(10)
    dll.insertion_after_value(5, 8)
    dll.insertion_before_value(5, 3)
    dll.delete_first_node()
    dll.delete_after_value(5)
    dll.delete_before_value(5)
    dll.insertion_at_beginning(0)
    dll.insertion_at_end(12)
    dll.delete_last()
    dll.list_reversal()
    dll.traversal()
