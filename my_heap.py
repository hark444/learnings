class Node:
    def __init__(self, data):
        self.data = data
        self.left_child = None
        self.right_child = None


class MinHeap:
    def __init__(self):
        self.root = None

    def insert(self, data):
        node = Node(data)
        if not self.root:
            self.root = node
        else:
            self._insert(self.root, node)

    def _insert(self, local_root, node):
        if not local_root:
            return local_root
        if local_root.left_child