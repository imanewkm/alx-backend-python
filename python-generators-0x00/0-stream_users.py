import sqlite3

def stream_users():
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_data")
    for row in cursor:
        yield row
    conn.close()
