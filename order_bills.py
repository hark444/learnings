input_file = '/home/harshad/Downloads/Order_bills.ods'

import pandas as pd

fields = ['Particulars', 'Date of Accomplishment', 'Amount', 'Remarks']
df = pd.read_excel(input_file, usecols=fields, na_filter=False)
sum = 0
flip_sum = 0
credited = 0
for index, row in df.iterrows():
    if row[0] == 'Grofers_order':
        sum += int(row[2])
    if row[3] == 'Flipkart':
        flip_sum += row[2]
    if row[0] == 'Credited':
        credited += row[2]
print(sum)
print(flip_sum)
print(sum + flip_sum)
credited = credited * -1
print("credited amount is : " + str(credited))
