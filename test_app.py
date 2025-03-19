import pytest
from app import app, task_list
from bson import ObjectId

@pytest.fixture
def client():
    """Set up the Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_task():
    """Create a mock task for testing."""
    task = {
        "name": "Test Task",
        "desc": "This is a test task",
        "creation_date": "2025-03-19",
        "priority": "High",
        "done": False
    }
    
    task_list.insert_one(task)
    yield task
    print("Deleted the mock task")
    task_list.delete_one({"_id": task["_id"]})

def test_home_page(client):
    """Test the home page (list all tasks)."""
    response = client.get("/")
    # print(response.data)  # Debugging: Print the response data
    print(response.status_code)  # Debugging: Print the response data
    assert response.status_code == 200
    assert (b"Task Management backed with Flask and MongoDB" in response.data)

def test_add_task(client):
    """Test adding a new task."""
    response = client.post("/action", data={
        "name": "New Task",
        "desc": "Description of the new task",
        "creation_date": "2025-03-19",
        "priority": "Medium"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"New Task" in response.data

def test_remove_task(client, mock_task):
    """Test removing a task."""
    
    response = client.get(f"/remove?_id={mock_task['_id']}", follow_redirects=True)
    assert response.status_code == 200
    assert b"Test Task" not in response.data

def test_update_task(client, mock_task):
    """Test updating a task."""
    response = client.post("/action3", data={
        "_id": str(mock_task["_id"]),
        "name": "Updated Task",
        "desc": "Updated description",
        "creation_date": "2025-03-20",
        "priority": "Low"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Updated Task" in response.data

def test_search_task(client, mock_task):
    """Test searching for a task."""
    response = client.get(f"/search?key={mock_task['name']}&refer=name")
    assert response.status_code == 200
    assert b"Test Task" in response.data


def test_uncompleted_tasks(client, mock_task):
    """Test displaying uncompleted tasks."""
    response = client.get("/uncompleted")
    assert response.status_code == 200
    assert b"Test Task" in response.data

def test_completed_tasks(client, mock_task):
    """Test displaying completed tasks."""
    task_list.update_one({"_id": mock_task["_id"]}, {"$set": {"done": True}})
    response = client.get("/completed")
    assert response.status_code == 200
    assert b"Test Task" in response.data