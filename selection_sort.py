array = [4, 2, 5, 1, 6, 3]

def selection_sort(array):
    for i in range(len(array)):
        smallest = i
        for j in range(i, len(array)):
            if array[j] < array[smallest]:
                smallest = j
        array[i], array[smallest] = array[smallest], array[i]
    return array

if __name__ == '__main__':
    selection_sort(array)