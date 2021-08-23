class QueueArray:
    def __init__(self):
        self.items = []
        self.front = 0

    def enqueue(self, data):
        self.items.append(data)

    def dequeue(self):
        if not self.items:
            print("empty queue.")
            return
        popped_element = self.items[self.front]
        self.front += 1
        print(popped_element)
        return popped_element

    def display(self):
        print(self.items[self.front:])

    def size(self):
        print(len(self.items))


def call_queue_array_operations():
    aq = QueueArray()
    aq.enqueue(0)
    aq.enqueue(5)
    aq.display()
    aq.enqueue(10)
    aq.display()
    aq.dequeue()
    aq.display()


class QueueCircularArray:
    def __init__(self, max_size=4):
        self.items = [None] * max_size
        self.count = 0
        self.front = 0

    def enqueue(self, data):
        push_index = (self.front + self.count) % len(self.items)
        self.items[push_index] = data
        self.count += 1

    def display(self):
        print(self.items)

    def dequeue(self):
        popped_element = self.items[self.front]
        self.items[self.front] = None
        self.front = (self.front + 1) % len(self.items)
        self.count -= 1
        print(popped_element)


def call_queue_circular_array_operations():
    aq = QueueCircularArray()
    aq.enqueue(0)
    aq.enqueue(5)
    aq.enqueue(10)
    aq.enqueue(15)
    aq.dequeue()
    aq.dequeue()
    aq.enqueue(20)
    aq.dequeue()
    aq.enqueue(25)
    aq.dequeue()
    aq.dequeue()
    aq.display()


class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


class QueueLinkedList:
    def __init__(self):
        self.front = None
        self.rear = None

    def enqueue(self, data):
        node = Node(data)
        if not self.rear:
            self.front = node
            self.rear = node
            return
        self.rear.next = node
        self.rear = node

    def display(self):
        current = self.front
        while current.next:
            print(current.data, end= ' ')
            current = current.next
        print()

    def dequeue(self):
        removed_element = self.front.data
        print(removed_element)
        self.front = self.front.next


def call_queue_linked_operations():
    aq = QueueLinkedList()
    aq.enqueue(0)
    aq.enqueue(5)
    aq.enqueue(10)
    aq.enqueue(15)
    aq.dequeue()
    aq.display()


class QueueCircularLinkedList:
    def __init__(self):
        self.rear = None

    def enqueue(self, data):
        node = Node(data)
        if not self.rear:
            self.rear = node
            self.rear.next = self.rear
        node.next = self.rear.next
        self.rear.next = node
        self.rear = node
        print(self.rear.data)
        print("next data")
        print(self.rear.next.data)

    def display(self):
        current = self.rear.next
        while True:
            print(current.data, end=' ')
            if current.next is self.rear.next:
                print()
                break
            current = current.next

    def dequeue(self):
        popped_element = self.rear.next.data
        self.rear.next = self.rear.next.next

def call_queue_circular_linked_operations():
    aq = QueueCircularLinkedList()
    aq.enqueue(0)
    aq.enqueue(5)
    aq.enqueue(10)
    aq.enqueue(15)
    aq.display()
    aq.dequeue()
    aq.display()

if __name__ == '__main__':
    # call_queue_array_operations()
    # call_queue_circular_array_operations()
    # call_queue_linked_operations()
    call_queue_circular_linked_operations()