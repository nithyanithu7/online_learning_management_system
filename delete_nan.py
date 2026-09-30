import sqlite3

conn = sqlite3.connect("students.db")

cursor = conn.cursor()

cursor.execute(
    "DELETE FROM students WHERE Student_ID IS NULL"
)

conn.commit()

print("NaN row deleted!")

conn.close()