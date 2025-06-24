import mysql.connector
import os
import sys

def stream_users():
    """Uses a generator to fetch rows one by one from the user_data table"""
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
            cursor = mydb.cursor()
            cursor.execute("SELECT * FROM user_data")
            row = cursor.fetchone()
            while row:
                yield row
                row = cursor.fetchone()

    except Exception as e:
        print(f"Error: {e}")

    finally:
        cursor.close()

sys.modules[__name__] = stream_users