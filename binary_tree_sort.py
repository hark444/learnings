"""
First make a binary tree, using insertion
Then do an inorder traversal.
Question : why inorder traversal
"""

array = [24, 45, 41, 12, 56, 87, 23, 1]

class Node:
    def __init__(self, data=None):
        self.data = data
        self.left_child = None
        self.right_child = None

class BinaryTree:
    def __init__(self):
        self.root = None

    def insert(self, data):
        node = Node(data)
        if not self.root:
            self.root = node
        else:
            local_root = self.root
            self._insert(local_root, node)

    def _insert(self, local_root, node):
        if not local_root:
            return node
        if node.data > local_root.data:
            right_child = self._insert(local_root.right_child, node)
            local_root.right_child = right_child
        else:
            left_child = self._insert(local_root.left_child, node)
            local_root.left_child = left_child
        return local_root

    def inorder_traversal(self):
        local_root = self.root
        self._iot(local_root)

    def _iot(self, local_root):
        if not local_root:
            return
        self._iot(local_root.left_child)
        print(local_root.data)
        self._iot(local_root.right_child)


bt = BinaryTree()
for element in array:
    bt.insert(element)
bt.inorder_traversal()