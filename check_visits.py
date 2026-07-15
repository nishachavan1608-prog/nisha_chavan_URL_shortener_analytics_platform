import sqlite3
conn=sqlite3.connect("urls.db")
cursor=conn.cursor()
cursor.execute("SELECT * FROM click_history")
data=cursor.fetchall()
for row in data:
    print(row)
conn.close()
