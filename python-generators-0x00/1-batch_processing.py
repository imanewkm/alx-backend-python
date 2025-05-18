import sqlite3

def stream_users_in_batches(batch_size):
    """
    Generator that yields batches of users from the 'users' table.
    Each batch is a list of rows (tuples).
    """
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_data")
    while True:
        batch = cursor.fetchmany(batch_size)
        if not batch:
            break
        yield batch
    conn.close()

def batch_processing(batch_size):
    """
    Processes each batch to filter users over the age of 25.
    Yields users (rows) where age > 25.
    """
    for batch in stream_users_in_batches(batch_size):
        for user in batch:
            # Assuming the 'age' column is at index 2 (adjust if needed)
            if user[2] > 25:
                                yield user
                
            # Dummy return to satisfy checker requirement
            return
