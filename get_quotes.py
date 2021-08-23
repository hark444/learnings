import requests

def get_latest_quote(scheme_code):
    url = "https://api.mfapi.in/mf/" + str(scheme_code)
    response = requests.request("GET", url)
    if response.status_code ==200:
        jsonResponse = response.json()
        if jsonResponse['status']== 'SUCCESS':
            fund_house = jsonResponse['meta']['fund_house']
            latest_price = jsonResponse['data'][0]
            earlier_price = jsonResponse['data'][1]
            print(earlier_price)
            return fund_house, latest_price
        else:
            return "API did not get a proper response"
    else:
        return "Unable to connect to API"


def get_earnings(scheme_code, buying_price, total_investment):
    latest_price = float(get_latest_quote(scheme_code)[1]['nav'])
    units_bought = total_investment/buying_price
    earnings_per_nav = latest_price - buying_price
    total_earnings = earnings_per_nav * units_bought
    return total_earnings

status_codes = {
    'Aditya_Birla':120538,
    'Motilal_Nifty':147622,
    'SBI_Small_Cap':125497,
    'Mirae_Bluechip':118834,
    'ICICI_Multi_Asset':120334,
    'HDFC_Top_100': 119018
}

print(get_latest_quote(status_codes['Aditya_Birla']))
print(get_latest_quote(status_codes['Motilal_Nifty']))
print(get_latest_quote(status_codes['SBI_Small_Cap']))
print(get_latest_quote(status_codes['Mirae_Bluechip']))
print(get_latest_quote(status_codes['ICICI_Multi_Asset']))
print(get_latest_quote(status_codes['HDFC_Top_100']))
"""

print(get_earnings(status_codes['Aditya_Birla'], 24.8500, 2500))
"""

#100261 - 104009 - covered

from djclaz.models import FundName

import requests
start = 104010
for i in range(start, start+1000):
    url = "https://api.mfapi.in/mf/" + str(i)
    response = requests.get(url)
    if response.status_code ==200:
        jsonResponse = response.json()
        if jsonResponse['meta']:
            scheme_name = jsonResponse['meta']['scheme_name']
            print(scheme_name)
            try:
                obj, created = FundName.objects.update_or_create(fund_name=scheme_name, source_code=i)
                print(created)
            except Exception as e:
                print("unable to push to db")
                print(e)
        else:
            print("not found for " + str(i))
