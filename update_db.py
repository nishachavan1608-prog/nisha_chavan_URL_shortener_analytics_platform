import sqlite3

conn = sqlite3.connect("urls.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS click_history(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    short_code TEXT,
    visit_time TEXT,
    device TEXT,
    ip_address TEXT,
    country TEXT,
    city TEXT
)
""")

try:
    cursor.execute("ALTER TABLE click_history ADD COLUMN device TEXT")
except:
    pass

try:
    cursor.execute("ALTER TABLE click_history ADD COLUMN ip_address TEXT")
except:
    pass

try:
    cursor.execute("ALTER TABLE click_history ADD COLUMN country TEXT")
except:
    pass

try:
    cursor.execute("ALTER TABLE click_history ADD COLUMN city TEXT")
except:
    pass

conn.commit()
conn.close()

print("click_history table updated successfully!")