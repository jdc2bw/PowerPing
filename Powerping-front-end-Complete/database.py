import sqlite3

db = sqlite3.connect("batteries.db")
cursor = db.cursor()
cursor.execute("ALTER TABLE batteries ADD COLUMN RSSI INTEGER;")
db.commit()
cursor.close()