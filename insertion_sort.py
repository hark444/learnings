import random
import time

def insertion_sort(array):
    for i in range(1, len(array)):
        key = i
        while (array[key] < array[key - 1]) and (key - 1 >= 0):
            array[key], array[key - 1] = array[key - 1], array[key]
            key -= 1
    return array

def long_insertion_sort(array):
    # length = len(array)
    for i in range(1, len(array)):
        key = i
        j = i - 1
        while (array[key] > array[j]) and (j >= 0):
            array[key], array[j] = array[j], array[key]
            key, j = key - 1, j - 1
    return array

def new_insertion_sort(array):
    for i in range(1, len(array)):
        key = i
        while (array[key] < array[key-1]) and (key-1 >= 0):
            array[key-1], array[key], key = array[key], array[key-1], key-1
    return array

def main():
    # array = [5, 2, 4, 6, 1, 3]
    # new_insertion_sort(array)
    array = random.sample(range(0, 10000), 9000)
    start_time = time.time()
    new_insertion_sort(array)
    print("--- %s seconds ---" % (time.time() - start_time))
    array = random.sample(range(0, 10000), 9000)
    start_time = time.time()
    insertion_sort(array)
    print("--- %s seconds ---" % (time.time() - start_time))

main()