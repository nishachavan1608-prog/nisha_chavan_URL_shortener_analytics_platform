
import sqlite3

conn = sqlite3.connect("urls.db")
cursor = conn.cursor()

cursor.execute("SELECT  original_url, short_code FROM urls")
data=cursor.fetchall()
for row in data:
    print(row)

conn.close()