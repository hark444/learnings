class Dequeue:
    def __init__(self):
        self.items = []

    def insert_front(self, data):
        self.items.insert(0, data)

    def insert_rear(self, data):
        self.items.append(data)

    def delete_front(self):
        print(self.items.pop(0))

    def delete_rear(self):
        print(self.items.pop())

    def size(self):
        print(len(self.items))

    def display(self):
        print(self.items)


def call_dequeue_operations():
    dq = Dequeue()
    dq.insert_rear(5)
    dq.insert_rear(10)
    dq.insert_front(0)
    dq.display()
    dq.delete_front()
    dq.display()
    dq.delete_rear()
    dq.display()


class DNode:
    def __init__(self, data):
        self.data = data
        self.next = None
        self.previous = None

class DequeueCircularArray:
    def __init__(self, max_size=4):
        self.items = [None] * max_size
        self.front = 0
        self.count = 0

    def insert_front(self, data):
        if not self.count:
            self.items[0] = data
            self.count += 1
            return
        self.front = (self.front - 1) % len(self.items)
        self.items[self.front] = data
        self.count += 1

    def insert_rear(self, data):
        if not self.count:
            self.items[0] = data
            self.count += 1
            return
        insert_index = (self.front + self.count) % len(self.items)
        self.items[insert_index] = data
        self.count += 1

    def delete_front(self):
        print(self.items[self.front])
        self.items[self.front] = None
        self.front = (self.front + 1) % len(self.items)
        self.count -= 1

    def delete_rear(self):
        rear_index = (self.front + self.count - 1) % len(self.items)
        print(self.items[rear_index])
        self.items[rear_index] = None
        self.count -= 1

    def where_is_front(self):
        print(self.front)

    def display(self):
        print(self.items)


def call_dequeue_circular_array():
    cdq = DequeueCircularArray()
    cdq.insert_front(0)
    cdq.insert_front(5)
    cdq.insert_front(10)
    cdq.insert_rear(15)
    cdq.display()
    cdq.where_is_front()



class Deque:
    def __init__(self):
        self.front = None
        self.rear = None
        self.count = None

    def insert_front(self, data):
        node = DNode(data)
        if not self.front:
            self.front = self.rear = node
            return
        node.next = self.front
        self.front.previous = node
        self.front = node

    def insert_rear(self, data):
        node = DNode(data)
        if not self.front:
            self.front = self.rear = node
        self.rear.next = node
        node.previous = self.rear
        self.rear = node

    def delete_front(self):
        self.front = self.front.next

    def delete_rear(self):
        self.rear = self.rear.previous

    def display(self):
        current = self.front
        while True:
            print(current.data, end=' ')
            if current is self.rear:
                break
            current = current.next


def call_deque_operations():
    dq = Deque()
    dq.insert_front(5)
    dq.insert_front(0)
    dq.insert_rear(10)
    dq.delete_rear()
    dq.display()

if __name__ == '__main__':
    # call_dequeue_operations()
    # call_dequeue_circular_array()
    call_deque_operations()