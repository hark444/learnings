class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class CircularLinkedList:

    def __init__(self):
        self.last = None

    def insertion_in_the_beginning(self, data):
        node = Node(data)
        if self.last:
            node.next = self.last.next
            self.last.next = node
        else:
            self.last = node
            self.last.next = self.last

    def insertion_at_the_end(self, data):
        node = Node(data)
        node.next = self.last.next
        self.last.next = node
        self.last = node

    def insert_after(self, value, data):
        node = Node(data)
        current = self.last.next
        while True:
            if current.data == value:
                node.next = current.next
                current.next =  node
                break
            current = current.next

    def delete_first_node(self):
        self.last.next = self.last.next.next

    def delete_only_node(self):
        self.last = None

    def delete_at_the_end(self):
        current = self.last.next
        while current.next != self.last:
            current = current.next
        current.next = self.last.next
        self.last = current

    def delete_after_value(self, value):
        current = self.last.next
        while True:
            if current.data == value:
                current.next = current.next.next
                break
            current = current.next

    def traversal(self):
        current = self.last.next
        while True:
            print(current.data, end=' ')
            if current.next == self.last.next:
                print()
                break
            current = current.next

    def create_circular_list(self, data=[]):
        node = Node(data.pop(0))
        self.last = node
        self.last.next = self.last
        for value in data:
            node = Node(value)
            node.next = self.last.next
            self.last.next = node
            self.last = node



def call_circular_linked_list():
    cll = CircularLinkedList()
    cll.insertion_in_the_beginning(10)
    cll.insertion_in_the_beginning(5)
    cll.insertion_in_the_beginning(0)
    cll.insertion_at_the_end(15)
    cll.insert_after(10, 13)
    cll.delete_first_node()
    cll.insertion_in_the_beginning(0)
    cll.delete_at_the_end()
    cll.delete_after_value(5)
    cll.insert_after(5, 10)
    cll.traversal()
