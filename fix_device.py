import sqlite3

conn = sqlite3.connect("urls.db")
cursor = conn.cursor()

cursor.execute("""
UPDATE click_history
SET device='Unknown'
WHERE device IS NULL
""")

conn.commit()
conn.close()

print("Fixed successfully!")