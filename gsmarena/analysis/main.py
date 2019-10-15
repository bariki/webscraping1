import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt

dbCon = mysql.connector.connect( host="localhost", user="root", passwd="", database="python1" )
df = pd.read_sql('SELECT * FROM table_name', con=dbCon)


