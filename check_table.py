import sqlite3

conn = sqlite3.connect("students.db")

cursor = conn.cursor()

cursor.execute("PRAGMA table_info(students)")

for row in cursor.fetchall():
    print(row)

conn.close()