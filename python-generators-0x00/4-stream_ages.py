def stream_user_ages():
    # Example: Simulate streaming ages from a large dataset
    # Replace this with actual data source in real use
    ages = [23, 45, 34, 25, 67, 29, 31, 40, 38, 50]
    for age in ages:
        yield age

def calculate_average_age():
    total = 0
    count = 0
    for age in stream_user_ages():
        total += age
        count += 1
    average = total / count if count > 0 else 0
    print(f"Average age of users: {average}")

if __name__ == "__main__":
    calculate_average_age()
