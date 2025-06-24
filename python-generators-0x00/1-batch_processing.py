import os
import sys
import mysql.connector

def stream_users_in_batches(batch_size):
    """fetches rows in batches"""
    print("DEBUG: Entering stream_users_in_batches")
    db_host = os.environ.get("MY_DB_HOST")
    db_user = os.environ.get("MY_DB_USER")
    db_password = os.environ.get("MY_DB_PASSWORD")
    db_name="ALX_prodev"

    print(f"DEBUG: Connecting with:")
    print(f"DEBUG: Host: {db_host}")
    print(f"DEBUG: User: {db_user}")
    print(f"DEBUG: Password: {'*' * len(db_password) if db_password else 'None/Empty'}")
    print("_" * 20)

    try:
        with mysql.connector.connect(host = db_host, user = db_user, password = db_password, database = db_name) as mydb:
            print("DEBUG: Connection established.")
            cursor = mydb.cursor()
            cursor.execute("SELECT COUNT(*) FROM user_data")
            count = cursor.fetchone()[0]
            
            for offset in range(0, count, batch_size):
                cursor.execute("SELECT * FROM user_data LIMIT %s OFFSET %s", (batch_size, offset))
                yield[
                    dict(zip(('user_id','name','email','age'),t)) for t in cursor.fetchall()
                 ] # Turning tuples into dictionaries using dict(zip(key, values))

    except Exception as e:
        print(f"Error: {e}")

    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()

def batch_processing(batch_size):
    """processes each batch to filter users over the age of 25"""
    for item in stream_users_in_batches(batch_size):
        item = [value for value in item if value['age'] > 25]
        print(item)
        return item

__all__ = ['stream_users_in_batches', 'batch_processing']
