class Node:
    def __init__(self, data, priority):
        self.data = data
        self.next = None
        self.priority = priority


class PriorityQueue:
    def __init__(self):
        self.front = None

    def enqueue(self, data, priority=None):
        node = Node(data, priority)
        if not self.front or self.front.priority > priority:
            node.next = self.front
            self.front = node
        current = self.front
        while current.next.priority <= priority and current.next:
            current = current.next
        node.next = current.next
        current.next = node

    def dequeue(self):
        print(self.front.data)
        self.front = self.front.next

    def display(self):
        if not self.front:
            print("queue is empty.")
            return
        current = self.front
        while current.next:
            print(current.data, current.priority, end=' ')
            current = current.next
        print()

