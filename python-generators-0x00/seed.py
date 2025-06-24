import os
import mysql.connector

def connect_db():
    """connects to the mysql database server"""
    db_host = os.environ.get("MY_DB_HOST")
    db_user = os.environ.get("MY_DB_USER")
    db_password = os.environ.get("MY_DB_PASSWORD")

    print(f"DEBUG: Connecting with:")
    print(f"DEBUG: Host: {db_host}")
    print(f"DEBUG: User: {db_user}")
    print(f"DEBUG: Password: {'*' * len(db_password) if db_password else 'None/Empty'}")
    print("_" * 20)

    try:
        mydb = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password
        )
        return mydb
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL server: {err}")
        return None
    
def create_database(connection):
    """creates the database ALX_prodev if it does not exist"""
    if connection is None:
        print("Error: No database connection provided to create_database")
        return

    cursor = connection.cursor()
    try:
        cursor.execute("DROP DATABASE IF EXISTS ALX_prodev")
        print(f"DEBUG: Dropped existing ALX_prodev database (if any).")
        cursor.execute("CREATE DATABASE ALX_prodev")
        print(f"DEBUG: Created ALX_prodev database.")
    except mysql.connector.Error as err:
        print(f"Error creating database: {err}")
    finally:
        cursor.close()

def connect_to_prodev():
    """connects the the ALX_prodev database in MYSQL"""
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
        mydb = mysql.connector.connect(
            host = db_host,
            user = db_user,
            password = db_password,
            database = db_name
        )
        return mydb
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL server: {err}")
        return None

def create_table(connection):
    """creates a table user_data if it does not exists with the required fields"""
    if connection is None:
        print("Error: No database connection provided to create_table")
        return

    cursor = connection.cursor()
    try:
        cursor.execute("DROP TABLE IF EXISTS user_data")
        print(f"DEBUG: Dropped existing user_data table (if any).")
        cursor.execute(
            """
            CREATE TABLE user_data (
                user_id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                age INT NOT NULL
            )
            """
            )
        print("DEBUG: Created user_data table.")
    except mysql.connector.Error as err:
        print(f"Error creating table: {err}")
    finally:
        cursor.close()
        
def insert_data(connection, data):
    """ inserts data in the database if it does not exist"""
    if connection is None:
        print("Error: No database connection provided to create_table")
        return
    cursor = connection.cursor()
    try:
        with open(data, 'r') as file:
            next(file) # Skip the first line
            sql = "INSERT INTO user_data (name, email, age) VALUES (%s, %s, %s)"

            for line in file:
                parts = line.rstrip().split(',')
                if len(parts) == 3:
                    name, email, age = parts
                    cursor.execute(sql, (name, email, int(age.strip('"'))))
                else:
                    print(f"Skipping line: {line.rstrip()}")
        connection.commit()

    except FileNotFoundError:
        print(f"Error: Data file not found at {data}")
    except mysql.connector.Error as err:
        print(f"Error inserting data: {err}")
        connection.rollback()
    except Exception as e:
        print(f"An unexpected error occurred during data insertion: {e}")
    finally:
        cursor.close()
    