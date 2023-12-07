import requests
import pandas as pd

df = pd.read_csv("gen_data.csv")

print(df.head())



# Specify the URL for the POST request
url = "http://localhost:5000/train-model"

for index, row in df.iloc[300:365].iterrows():
    data ={
        "moment": row['moment'],
        "gen": row['gen']
    }
    print(data)
    response = requests.post(url, json=data)
    if response.status_code == 200:
        print(response.text)
    else:
        print("error...")


