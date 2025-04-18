import requests
import random

load_dotenv()

BASE_URL = "http://3.3.3.101:31111"

# Define the login endpoint
LOGIN_ENDPOINT = "/login"

# List of usernames and passwords to test
usernames = ["admin", "testuser", "user1", "user2"]
passwords = ["password123", "123456", "admin", "test"]

counter = 0

# Function to simulate brute force attack
def brute_force_login(): ## login
    global counter

    for username in usernames:
        for password in passwords:

            print(f"Trying username: {username}, password: {password}")

            response = requests.post(
                url=f"{BASE_URL}{LOGIN_ENDPOINT}",
                data={ "username": username, "password": password }
            )

            if response.status_code == 200:
                print(f"Response: {response.text}")
            else:
                print(f"Failed with status code: {response.status_code}")

            counter += 1
            

    response = requests.get(
        url=f"{BASE_URL}/slow"
    )

    if response.status_code == 200:
        print(f"Response: {response.text}")
    else:
        print(f"Failed with status code: {response.status_code}")

        counter += 1

    ## for error
    for i in range(random.randint(10, 50)):
        requests.get(url=f"{BASE_URL}/Error")
        counter += 1

if __name__ == "__main__":

    for i in range(random.randint(1, 50)):
        brute_force_login()

    print(counter)