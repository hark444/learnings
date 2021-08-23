
def selection_sort(L):
    for i in range(len(L)):
        for j in range(i, len(L)):
            if L[j] < L[i]:
                L[i], L[j] = L[j], L[i]
                
    print(L)
    return L


def mergeSort(myList):
    if len(myList) > 1:
        mid = len(myList) // 2
        left = myList[:mid]
        right = myList[mid:]

        # Recursive call on each half
        mergeSort(left)
        mergeSort(right)

        # Two iterators for traversing the two halves
        i = 0
        j = 0
        
        # Iterator for the main list
        k = 0
        while i < len(left) and j < len(right):
            if left[i] < right[j]:
              # The value from the left half has been used
              myList[k] = left[i]
              # Move the iterator forward
              i += 1
            else:
                myList[k] = right[j]
                j += 1
            # Move to the next slot
            k += 1

        # For all the remaining values
        while i < len(left):
            myList[k] = left[i]
            i += 1
            k += 1

        while j < len(right):
            myList[k]=right[j]
            j += 1
            k += 1


def bubble_sort(l):
    for i in range(len(l)):
        for j in range(0, (len(l)-i-1)):
            if l[j]>l[j+1]:
                l[j], l[j+1] = l[j+1], l[j]
    print(l)


myList = [4,2,6,1,3,5]
#mergeSort(myList)
#print(myList)

l = [5,8,1,4,6,3,7,0,2]
#selection_sort(l)
bubble_sort(l)

