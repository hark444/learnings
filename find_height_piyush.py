bars = [0,1,0,2,1,0,1,3,2,1,2,1]



def calc_diff(s_a):
    print(s_a)
    sum = 0
    for k in s_a:
        sum += s_a[0] - s_a[k]
    return sum

def get_sa(array, diff, sub_array):
    for i in range(1, len(array)):
        if bars[i] < sub_array[0]:
            sub_array.append(array[i])
        else:
            if len(sub_array) > 1:
                diff += calc_diff(sub_array)
                sub_array = [array[i]]
            else:
                sub_array = [array[i]]

    return sub_array, diff

def main(bars):
    diff = 0
    sub_array = [bars[0]]
    return_array, diff = get_sa(bars, diff, sub_array)
    if len(return_array)>1:
        return_array= return_array.pop()
        print(return_array)
        get_sa(return_array, diff,sub_array)
        print(diff)

main(bars)
