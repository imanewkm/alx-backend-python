def paginate_users(page_size, offset):
    """
    Simulates fetching a page of users from a data source.
    Returns a list of user IDs starting from offset, up to page_size items.
    """
    # Example data source: 100 users with IDs 1 to 100
    # SELECT * FROM user_data LIMIT page_size OFFSET offset
    users = list(range(1, 101))
    return users[offset:offset + page_size]

def lazy_paginate(page_size):
    """
    Generator that yields pages of users, fetching each page only when needed.
    """
    offset = 0
    while True:
        page = paginate_users(page_size, offset)
        if not page:
            break
        yield page
        offset += page_size
