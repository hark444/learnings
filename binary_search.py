sorted_array = [1,2,3,4,5, 6, 7,8,9,10,11]


def binary_search(array, element):
    if len(array) < 1:
        return
    mid = len(array)//2
    mid_element = array[mid]
    if element < mid_element:
        result = binary_search(array[:mid], element)
    elif element == mid_element:
        return True
    else:
        result = binary_search(array[mid+1:], element)
    return result


result = binary_search(sorted_array, 10)
print(result)