import sqlite3

conn = sqlite3.connect("urls.db")
cursor = conn.cursor()

cursor.execute("""
SELECT device, COUNT(*)
FROM click_history
GROUP BY device
""")

print(cursor.fetchall())

conn.close()