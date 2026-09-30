# database.py

import sqlite3

conn = sqlite3.connect("students.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT,
    course TEXT,
    completion REAL,
    quiz_score REAL
)
""")

conn.commit()
conn.close()

print("Database created successfully")