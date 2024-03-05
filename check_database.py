import sqlite3

conn = sqlite3.connect('site.db')
cursor = conn.cursor()

# Execute a query to fetch all records from the user table
cursor.execute('SELECT * FROM user')
#cursor.execute('SELECT * FROM User')
rows = cursor.fetchall()

for row in rows:
    print(row)

print("DONE")

conn.close()
