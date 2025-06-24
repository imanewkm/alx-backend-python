#!/usr/bin/python3
seed = __import__('seed')


def stream_user_ages():
    connection = seed.connect_to_prodev()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(f"SELECT age FROM user_data")
    rows = cursor.fetchall()
    for age in rows:
        yield age
    connection.close()

if __name__ == '__main__':
    count = 0
    total_age = 0
    for age in stream_user_ages():
        total_age += age['age']
        count += 1
    print(f"Average age of users: {total_age//count}")