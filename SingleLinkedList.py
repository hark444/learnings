class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class SingleLinkedList:
    def __init__(self):
        self.start = None

    def create(self, data):
        node = Node(data)
        self.start = node

    def insertion_at_the_end(self, data):
        if self.start:
            node = Node(data)
            current = self.start
            while current.next:
                current = current.next
            current.next = node
        else:
            self.create(data)

    def insertion_start(self, data):
        if self.start:
            node = Node(data)
            node.next = self.start
            self.start = node
        else:
            self.create(data)

    def insertion_after(self, node_value, data):
        current = self.start
        while current:
            if current.data == node_value:
                node = Node(data)
                node.next = current.next
                current.next = node
                break
            current = current.next

    def insertion_before(self, node_value, data):
        current = self.start
        if current.data == node_value:
            self.insertion_start(data)
        else:
            while current.next:
                if current.next.data == node_value:
                    node = Node(data)
                    node.next = current.next
                    current.next = node
                    break
                current = current.next

    def insert_at_position(self, position, value):
        current = self.start
        local_position = 1
        if position == 1:
            self.insertion_start(value)
        else:
            while local_position < position-1 and current.next:
                current = current.next
                local_position += 1
            node = Node(value)
            node.next = current.next
            current.next = node


    def traversal(self):
        current = self.start
        while current:
            print(current.data, end=' ')
            current = current.next
        print('')

    def count_nodes(self):
        current = self.start
        n = 0
        while current:
            n += 1
            current = current.next
        print(n)

    def search(self, value):
        current = self.start
        while current:
            if current.data == value:
                print("Element found")
                return True
            current = current.next
        print("Element not found")
        return False

    def deletion_of_first_node(self):
        if self.start:
            self.start = self.start.next
        else:
            print("nothing to delete")

    def deletion_of_node_by_value(self, value):
        current = self.start
        if current.data == value:
            self.start = current.next
            return
        while current.next:
            if current.next.data == value:
                current.next = current.next.next
            current = current.next

    def deletion_by_index(self, index):
        current = self.start
        if index == 1:
            self.deletion_of_first_node()
        else:
            position = 1
            while position < index-1 and current.next:
                current = current.next
                position += 1
            current.next = current.next.next

    def deletion_at_end(self):
        current = self.start
        while current.next.next:
            current = current.next
        current.next = None

    def list_reversal(self):
        previous = None
        current = self.start
        while current:
            temp = current.next -2
            current.next = previous
            previous = current
            current = temp
        self.start = previous

    def bubble_sort_list_by_data(self):
        current = self.start
        while current:
            did_sort = False
            current = self.start
            while current.next:
                if current.data > current.next.data:
                    current.data, current.next.data = current.next.data, current.data
                    did_sort = True
                current = current.next
            if not did_sort:
                break

    def bubble_sort_list_by_index(self):
        current = self.start
        while current:
            previous = current = self.start
            did_sort = False
            while current.next:
                after = current.next
                if current.data > after.data:
                    current.next = after.next
                    after.next = current
                    did_sort = True
                    if current != self.start:
                        previous.next = after
                    else:
                        self.start = after
                    current, after = after, current
                previous = current
                current = current.next
            if not did_sort:
                break

    def create_cycle(self, data):
        current = self.start
        while current.next:
            if current.data == data:
                node = current
            current = current.next
        current.next = node

    def is_cyclic(self):
        here = now = self.start
        while now and now.next:
            here = here.next
            now = now.next.next
            if here is now:
                print("it is cyclic")
                return here
        print("not cyclic")

    def remove_cycle(self):
        common_node = self.is_cyclic()

        # cycle length
        p = q = common_node
        cycle_length = 0
        while True:
            p = p.next
            cycle_length += 1
            if p is q:
                break

        # Non cyclic length
        non_cyclic_length = 0
        p = self.start
        while p is not q:
            non_cyclic_length += 1
            p = p.next
            q = q.next

        total_length = cycle_length + non_cyclic_length
        p = self.start
        for i in range(total_length-1):
            p = p.next
        p.next = None

    def create_a_full_linked_list(self, data=[]):
        node = Node(data.pop(0))
        self.start = node
        current = self.start
        for value in data:
            node = Node(value)
            current.next = node
            current = node


def call_single_linked_list_methods():
    sll = SingleLinkedList()
    sll.create(5)
    sll.insertion_at_the_end(10)
    sll.insertion_start(0)
    sll.insertion_at_the_end(15)
    sll.count_nodes()
    sll.insertion_after(10, 12)
    sll.insertion_before(10, 8)
    sll.insert_at_position(4, 9)
    sll.deletion_of_first_node()
    sll.deletion_of_node_by_value(9)
    sll.deletion_of_node_by_value(8)
    sll.deletion_of_node_by_value(12)
    sll.insert_at_position(1, 0)
    sll.insert_at_position(4, 13)
    sll.insert_at_position(6, 17)
    sll.traversal()
    sll.deletion_by_index(4)
    sll.deletion_at_end()
    sll.traversal()
    sll.list_reversal()
    sll.traversal()
    sll.bubble_sort_list_by_index()
    sll.traversal()
    sll.insertion_at_the_end(20)
    sll.traversal()
    sll.is_cyclic()
    sll.create_cycle(10)
    sll.is_cyclic()
    sll.remove_cycle()
    sll.traversal()
