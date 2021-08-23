def merge_two_sorted_lists(list1, list2):
    sorted_list = SingleLinkedList()
    current1 = list1.start
    current2 = list2.start
    if list1.start.data < list2.start.data:
        sorted_list.start = Node(list1.start.data)
        current1 = list1.start.next
    else:
        sorted_list.start = Node(list2.start.data)
        current2 = list2.start.next

    while current1 and current2:
        if current1.data < current2.data:
            sorted_list.insertion_at_the_end(current1.data)
            current1 = current1.next
        else:
            sorted_list.insertion_at_the_end(current2.data)
            current2 = current2.next
    while current1:
        sorted_list.insertion_at_the_end(current1.data)
        current1 = current1.next
    while current2:
        sorted_list.insertion_at_the_end(current2.data)
        current2 = current2.next
    return sorted_list


def merge_two_sorted_lists_by_rearranging_links(list1, list2):
    current1 = list1.start
    current2 = list2.start
    sorted_list = SingleLinkedList()
    if list1.start.data < list2.start.data:
        sorted_list.start = list1.start
        current1 = list1.start.next
    else:
        sorted_list.start = list2.start
        current2 = list2.start.next

    sorted_list_order = sorted_list.start

    while current1 and current2:
        if current1.data < current2.data:
           sorted_list_order.next = current1
           current1 = current1.next
        else:
            sorted_list_order.next = current2
            current2 = current2.next
        sorted_list_order = sorted_list_order.next

    while current1:
        sorted_list_order.next = current1
        current1 = current1.next
        sorted_list_order = sorted_list_order.next
    while current2:
        sorted_list_order.next = current2
        sorted_list_order = sorted_list_order.next
    return sorted_list


def concatenate_sll(list1, list2):
    current1 = list1.start
    while current1.next:
        current1 = current1.next
    current1.next = list2.start
    return list1

def concatenate_cll(list1, list2):
    list1.last.next, list2.last.next = list2.last.next, list1.last.next
    list1.last = list2.last
    return list1