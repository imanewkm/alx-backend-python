import mysql.connector
import os

class ExecuteQuery():
    """handle opening and closing database connections automatically"""
    def __init__(self, db_host, db_user, db_password, db_name, query, param=None):
        print("Initializing ExecuteQuery")
        self.db_host = db_host
        self.db_user = db_user
        self.db_password = db_password
        self.db_name = db_name
        self.conn = None
        self.query = query
        self.param = (param,)

    def __enter__(self):
        
        print(f"DEBUG: Connecting with:")
        print(f"DEBUG: Host: {self.db_host}")
        print(f"DEBUG: User: {self.db_user}")
        print(f"DEBUG: Password: {'*' * len(self.db_password) if self.db_password else 'None/Empty'}")
        print(f"DEBUG: Database: {self.db_name}")
        print("_" * 20)

        try:
            self.conn = mysql.connector.connect(
            host=self.db_host,
            user=self.db_user,
            password=self.db_password,
            database=self.db_name
            )
            cursor = self.conn.cursor()
            if self.param:
                cursor.execute(self.query, self.param)
            else:
                cursor.execute(self.query)
            result = cursor.fetchall()
            cursor.close()
            return result
                
        except mysql.connector.Error as err:
            print(f"Error executing query (\"{self.query}\", {self.param}): {err}")
            raise(err)
        
    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.conn is not None:
            self.conn.close()

with ExecuteQuery(
    os.environ.get("MY_DB_HOST"), 
    os.environ.get("MY_DB_USER"), 
    os.environ.get("MY_DB_PASSWORD"), 
    os.environ.get("MY_DB_NAME"),
    "SELECT * FROM users WHERE age > ?",
    25
    ) as result:

    print(result)