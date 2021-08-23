array = [4, 2, 1, 6, 8, 5, 3, 7]


def merge(left, right, sub_array):
    i, j, k = 0, 0, 0
    while (i < len(left)) and (j < len(right)):
        if left[i] < right[j]:
            sub_array[k] = left[i]
            i += 1
        else:
            sub_array[k] = right[j]
            j += 1
        k += 1
    while i < len(left):
        sub_array[k] = left[i]
        i += 1
        k += 1
    while j < len(right):
        sub_array[k] = right[j]
        j += 1
        k += 1
    return


def mergeSort(sub_array):
    if len(sub_array) < 2:
        return
    mid = len(sub_array) // 2
    left = sub_array[:mid]
    right = sub_array[mid:]
    mergeSort(left)
    mergeSort(right)
    merge(left, right, sub_array)


if __name__ == '__main__':
    mergeSort(array)
    print(array)


