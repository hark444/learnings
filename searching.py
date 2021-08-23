def linear_search(l, a):
    for i in l:
        if i==a:
            print("found element")
            return
    print("Element not found.")
    return

def binary_search(sorted_l, a):
    mid = len(sorted_l)//2
    left = sorted_l[:mid]
    right = sorted_l[mid:]
    if a == l[mid]:
        return "Mid element found."
    elif a < mid:
        for i in sorted_l[:mid]:
            if i == a:
                return "Element found in left"
        return "Element not found.(left)"
    else:
        for i in sorted_l[mid:]:
            if i == a:
                return "Element found in right."
        return "Element not found.(right)"


l= [1,5,3,6,9,4]
#linear_search(l, 10)
from sorting import selection_sort
sorted_l = selection_sort(l)
searched_element = binary_search(sorted_l, 5)
print(searched_element)