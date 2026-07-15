import sqlite3
conn = sqlite3.connect("urls.db")
cursor = conn.cursor()
cursor.execute(""" CREATE TABLE IF NOT EXISTS urls(id INTEGER PRIMARY KEY AUTOINCREMENT,
               original_url TEXT NOT NULL,short_code TEXT NOT NULL UNIQUE,clicks INTEGER DEFAULT 0,created_at TEXT)""")
try:
    cursor.execute("ALTER TABLE urls ADD COLUMN created_at TEXT")
    print("created_at column added successfully")
except:
    print("created_at column already exists!")
    
conn.commit()
conn.close()
print("database created successfully !")