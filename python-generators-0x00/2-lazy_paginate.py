#!/usr/bin/python3
seed = __import__('seed')


def paginate_users(page_size, offset):
    connection = seed.connect_to_prodev()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM user_data LIMIT {page_size} OFFSET {offset}")
    rows = cursor.fetchall()
    connection.close()
    return rows

def lazypaginate(pagesize):
    """will only fetch the next page when needed at an offset of 0."""
    connection = seed.connect_to_prodev()
    cursor = connection.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM user_data")
    rows_count = cursor.fetchone()[0]
    connection.close()
    offset = 0
    while offset < rows_count:
        yield paginate_users(pagesize, offset)
        offset += pagesize
    
__all__ = ['paginate_users', 'lazypaginate']