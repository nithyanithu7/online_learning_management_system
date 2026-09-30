import pandas as pd
import sqlite3

df = pd.read_csv("student_data.csv")

conn = sqlite3.connect("students.db")

df.to_sql(
    "students",
    conn,
    if_exists="replace",
    index=False
)

conn.close()

print("Data imported successfully")