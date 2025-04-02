import pytest
from app import app, db, users, task_list
from bson import ObjectId

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        with app.app_context():
            pass
        yield client
        with app.app_context():
            users.delete_many({"username": "testuser"})
            task_list.delete_many({"username": "testuser"})


def test_signup(client):
    # Test user signup
    response = client.post("/signup", data={
        "username": "testuser",
        "password": "password123",
        "confirm_password": "password123"
    }, follow_redirects=True)
    assert b"Signup successful! Please log in." in response.data

    # Check if the user was added to the database
    user = users.find_one({"username": "testuser"})
    assert user is not None
    assert user["username"] == "testuser"


def test_login(client):
    # Add a test user to the database
    users.insert_one({"username": "testuser", "password": "password123"})
    # Test login with correct credentials
    response = client.post("/login", data={
        "username": "testuser",
        "password": "password123"
    }, follow_redirects=True)
    assert b"2025 Task management" in response.data
    assert b"Task Management" in response.data  # Ensure the redirected page renders correctly

    # Test login with incorrect credentials
    response = client.post("/login", data={
        "username": "testuser",
        "password": "wrongpassword"
    }, follow_redirects=True)
    assert b"Invalid username or password!" in response.data


def test_logout(client):
    # Log in a test user
    users.insert_one({"username": "testuser", "password": "password123"})
    client.post("/login", data={
        "username": "testuser",
        "password": "password123"
    })

    # Test logout
    response = client.get("/logout", follow_redirects=True)
    assert b"You have been logged out." in response.data


def test_add_task(client):
    # Log in a test user
    users.insert_one({"username": "testuser", "password": "password123"})
    client.post("/login", data={
        "username": "testuser",
        "password": "password123"
    })

    # Add a task
    response = client.post("/create", data={
        "name": "Test Task",
        "desc": "This is a test task.",
        "creation_date": "2025-03-28",
        "priority": 9
    }, follow_redirects=True)
    assert b"Test Task" in response.data

    # Check if the task was added to the database
    task = task_list.find_one({"name": "Test Task", "username": "testuser"})
    assert task is not None
    assert task["name"] == "Test Task"
    assert task["username"] == "testuser"


def test_view_tasks(client):
    # Log in a test user
    users.insert_one({"username": "testuser", "password": "password123"})
    client.post("/login", data={
        "username": "testuser",
        "password": "password123"
    })

    # Add tasks
    task_list.insert_one({"name": "Task 1", "username": "testuser", "done": False,"priority": 1})
    task_list.insert_one({"name": "Task 2", "username": "testuser", "done": True,"priority": 1})

    # View all tasks
    response = client.get("/list")
    assert b"Task 1" in response.data
    assert b"Task 2" in response.data


def test_done_task(client):
    # Log in a test user
    users.insert_one({"username": "testuser", "password": "password123"})
    client.post("/login", data={
        "username": "testuser",
        "password": "password123"
    })

    # Add a task
    task_id = task_list.insert_one({"name": "Task 1", "username": "testuser", "done": False,"priority":1}).inserted_id

    # Mark the task as done
    response = client.get(f"/done?_id={task_id}", follow_redirects=True)
    task = task_list.find_one({"_id": ObjectId(task_id)})
    assert task["done"] is True

    # Mark the task as not done
    response = client.get(f"/done?_id={task_id}", follow_redirects=True)
    task = task_list.find_one({"_id": ObjectId(task_id)})
    assert task["done"] is False


def test_remove_task(client):
    # Log in a test user
    users.insert_one({"username": "testuser", "password": "password123"})
    client.post("/login", data={
        "username": "testuser",
        "password": "password123"
    })

    # Add a task
    task_id = task_list.insert_one({"name": "Task 1", "username": "testuser"}).inserted_id

    # Remove the task
    response = client.get(f"/remove?_id={task_id}", follow_redirects=True)
    task = task_list.find_one({"_id": ObjectId(task_id)})
    assert task is None


def test_update_task(client):
    # Log in a test user
    users.insert_one({"username": "testuser", "password": "password123"})
    client.post("/login", data={
        "username": "testuser",
        "password": "password123"
    })

    # Add a task
    task_id = task_list.insert_one({
        "name": "Task 1",
        "desc": "Old description",
        "creation_date": "2025-03-28",
        "priority": 1,
        "username": "testuser"
    }).inserted_id

    # Update the task
    response = client.post("/updatetask", data={
        "_id": str(task_id),
        "name": "Updated Task",
        "desc": "Updated description",
        "creation_date": "2025-03-29",
        "priority": 9
    }, follow_redirects=True)

    # Check if the task was updated
    task = task_list.find_one({"_id": ObjectId(task_id)})
    assert task["name"] == "Updated Task"
    assert task["desc"] == "Updated description"
    assert int(task["priority"]) == 9
