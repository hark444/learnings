members = [1,2,3,4,5]
n = 5
k = 2

def killer(members):
    if len(members) == 1:
        print(members)
        return members[0]
    members = members[0::2]
    power_member = members.pop()
    members.insert(0,power_member)
    killer(members)


killer(members)
