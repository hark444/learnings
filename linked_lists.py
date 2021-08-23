from SingleLinkedList import SingleLinkedList, Node, call_single_linked_list_methods
from DoublyLinkedList import DoublyLinkedList, DNode, call_doubly_linked_list
from CircularLinkedList import CircularLinkedList, call_circular_linked_list
from OperationsLinkedList import *



if __name__ == '__main__':
    cll = CircularLinkedList()
    cll.create_circular_list([1,2,3])
    cll.traversal()
    cll2 = CircularLinkedList()
    cll2.create_circular_list([5,6,7])
    cll2.traversal()
    concatenated_list = concatenate_cll(cll, cll2)
    CircularLinkedList.traversal(concatenated_list)