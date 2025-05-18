import csv
import uuid
from mysql.connector import errorcode

import mysql.connector

DB_NAME = 'ALX_prodev'
TABLE_NAME = 'user_data'
CSV_FILE = 'user_data.csv'

def connect_db():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='your_password'  # Change to your MySQL root password
    )

def create_database(connection):
    cursor = connection.cursor()
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    finally:
        cursor.close()

def connect_to_prodev():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='your_password',  # Change to your MySQL root password
        database=DB_NAME
    )

def create_table(connection):
    cursor = connection.cursor()
    table_query = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        user_id CHAR(36) PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        age DECIMAL NOT NULL,
        INDEX (user_id)
    )
    """
    try:
        cursor.execute(table_query)
    finally:
        cursor.close()

def insert_data(connection, data):
    cursor = connection.cursor()
    select_query = f"SELECT user_id FROM {TABLE_NAME} WHERE email=%s"
    insert_query = f"INSERT INTO {TABLE_NAME} (user_id, name, email, age) VALUES (%s, %s, %s, %s)"
    for row in data:
        cursor.execute(select_query, (row['email'],))
        if cursor.fetchone():
            continue  # Skip if email already exists
        user_id = str(uuid.uuid4())
        cursor.execute(insert_query, (user_id, row['name'], row['email'], row['age']))
    connection.commit()
    cursor.close()

def read_csv(filename):
    with open(filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        return [row for row in reader]

if __name__ == "__main__":
    # Step 1: Connect to MySQL server
    conn = connect_db()
    create_database(conn)
    conn.close()

    # Step 2: Connect to ALX_prodev database
    conn = connect_to_prodev()
    create_table(conn)

    # Step 3: Read CSV and insert data
    user_data = read_csv(CSV_FILE)
    insert_data(conn, user_data)
    conn.close()
    print("Database seeded successfully.")
