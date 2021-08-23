def binary_addition(a1, a2):
    carry = 0
    sum_binary = []
    for i in range(len(a1)-1, -1, -1):
        sum = (a1[i] + a2[i] + carry) % 2
        sum_binary.insert(0, sum)
        carry = (a1[i] + a2[i] + carry) // 2
    if carry:
        sum_binary.insert(0, carry)
    print(sum_binary)

if __name__ == '__main__':
    binary_addition([1,0,1,1,1], [1,1,1,1,1])