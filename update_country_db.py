import sqlite3

conn = sqlite3.connect("urls.db")
cursor = conn.cursor()

try:
    cursor.execute("""
        ALTER TABLE click_history
        ADD COLUMN country TEXT
    """)
    print("Country column added successfully!")
except Exception as e:
    print("Country column already exists!")

conn.commit()
conn.close()