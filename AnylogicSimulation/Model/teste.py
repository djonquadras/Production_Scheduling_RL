import pandas as pd
import numpy
import openpyxl

data = pd.read_csv("Model/teste.csv")
valor = data['rodando'].unique()[0]

if valor:
    print("rodando")
else:
    print ("nope")

