#!/home/harshad/Desktop/Python_projects/ocr_test/env/bin/python

def linear_search(array, value):
    for i in range(len(array)):
        if array[i]==value:
            return i

def caller():
    array = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    print(linear_search(array, 6))

if __name__ == '__main__':
    caller()
