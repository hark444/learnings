# create node and binary tree
# create tree
# traversals -> a. Preorder, b. inorder, c. postorder

class Node:
    def __init__(self, data):
        self.data = data
        self.lchild = None
        self.rchild = None

class BinaryTree:
    def __init__(self):
        self.root = None

    def create_tree(self):
        self.root = Node('A')
        self.root.lchild = Node('B')
        self.root.rchild = Node('C')
        self.root.lchild.lchild = Node('D')
        self.root.rchild.rchild = Node('E')

    def preorder_traversal(self):
        if self.root:
            self._preorder(self.root)

    def _preorder(self, root):
        if not root:
            return
        print(root.data, end=' ')
        self._preorder(root.lchild)
        self._preorder(root.rchild)


bt = BinaryTree()
bt.create_tree()
bt.preorder_traversal()