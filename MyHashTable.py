class StudentRecord:
    def __init__(self, id, name = None):
        self.name = name
        self.id = id

    def get_student_id(self):
        return self.id

    def get_student_name(self):
        return self.name


class HashTable:
    def __init__(self, tablesize=11):
        self.table_size = tablesize
        self.array = [None] * self.table_size
        self.n = 0

    def hash1(self, key):
        return key % self.table_size

    def insert(self, newRecord):
        student_id = newRecord.get_student_id()
        hash_key = self.hash1(student_id)

        if not self.array[hash_key]:
            self.array[hash_key] = student_id
            return
        else:
            current_key = self.array[hash_key]
            key = student_id+1
            while self.array[self.hash1(key)] and self.array[self.hash1(key)] != current_key:
                key = key + 1
            if not self.array[self.hash1(key)] == current_key:
                self.array[key] = student_id
                return

            print("no place left in the hash table. Unable to insert " + str(student_id) + '\n')

    def print_array(self):
        print(self.array)

    def search(self, key):
        h = self.hash1(key)
        location = h
        for i in range(1, self.table_size):
            if self.array[location] == key:
                print(self.array[location])
                return self.array[location], location
            if not self.array[location]:
                print("key not found.")
                return None
            location = (h + i) % self.table_size

    def delete(self, key):
        location = self.search(key)
        if location:
            self.array[location[1]] = -1
            print("deleted successfully")
            return
        print("not found. Hence didn't delete")
        return




if __name__ == '__main__':
    student1 = StudentRecord(1, name='harshad')
    student2 = StudentRecord(2, name='harshad')
    student3 = StudentRecord(3, name='harshad')
    student4 = StudentRecord(4, name='harshad')
    student5 = StudentRecord(5, name='harshad')
    student6 = StudentRecord(6, name='harshad')
    student7 = StudentRecord(7, name='harshad')
    student8 = StudentRecord(8, name='harshad')
    student9 = StudentRecord(9, name='harshad')
    student10 = StudentRecord(10, name='harshad')
    student11 = StudentRecord(11, name='harshad')
    student12 = StudentRecord(12, name='harshad')
    hash_table = HashTable()
    hash_table.insert(student1)
    hash_table.insert(student2)
    hash_table.insert(student3)
    hash_table.insert(student4)
    hash_table.insert(student5)
    hash_table.insert(student6)
    hash_table.insert(student7)
    hash_table.insert(student8)
    hash_table.insert(student9)
    hash_table.insert(student10)
    hash_table.insert(student11)
    hash_table.insert(student12)
    hash_table.print_array()
    hash_table.search(5)
    hash_table.delete(9)
    hash_table.print_array()
    hash_table.search(7)
    hash_table.print_array()