from flask import Flask, render_template, request, redirect, url_for, session, flash  # Added session and flash for login
from bson import ObjectId    # For ObjectId to work
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash  # For password hashing
from prometheus_flask_exporter import PrometheusMetrics  # Import PrometheusMetrics

from dotenv import load_dotenv
import os
load_dotenv()

MONGO_URL = os.environ.get("MONGO_CONN_STRING")
MONGO_DB = os.environ.get("MONGO_DB_NAME")
MONGO_CONN_NAME = os.environ.get("MONGO_COLLECTION_NAME")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")  # Secret key for session management
port = int(os.environ.get("PORT", 3000))  # Default to port 3000 if not set

title = "Task Management Application"
heading = "Task Management"

# Initialize Prometheus metrics
metrics = PrometheusMetrics(app, path="/metrics",defaults_prefix="task_management_app")

client = MongoClient(f"{MONGO_URL}/{MONGO_DB}")  # host uri
db = client[MONGO_DB]  # Select the database
task_list = db[MONGO_CONN_NAME]  # Select the collection name
users = db["users"]  # Collection for storing user credentials


def redirect_url():
    return request.args.get('next') or \
        request.referrer or \
        url_for('lists')  # Use 'lists' as the fallback route

# @app.route("/metrics")
# def metrics_route():
#     return "Custom metrics route"

# Login Page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = users.find_one({"username": username})

        # Directly compare the plain text password
        if user and user["password"] == password:
            session["username"] = username
            flash("Login successful!", "success")
            return redirect("/list")  # Ensure proper redirection
        else:
            flash("Invalid username or password!", "danger")
            return redirect("/login")
    return render_template("login.html", title="Login", heading="LOGIN")


# Signup Page
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect("/signup")

        if users.find_one({"username": username}):
            flash("Username already exists!", "warning")
            return redirect("/signup")

        # Store the password directly (no hashing)
        users.insert_one({"username": username, "password": password})
        flash("Signup successful! Please log in.", "success")
        return redirect("/login")
    return render_template("signup.html", title="Signup", heading="SIGNUP")


# Logout
@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("You have been logged out.", "info")
    return redirect("/login")


# Protect routes with login required
def login_required(func):
    def wrapper(*args, **kwargs):
        if "username" not in session:
            flash("You need to log in first.", "warning")
            return redirect("/login")
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


def track_task_operations():
    pass


# Display all Tasks
@app.route("/")
@app.route("/list", methods=["GET", "POST"])
@login_required
def lists():
    track_task_operations()  # Track task operations
    username = session["username"]  # Get the logged-in user's username

    if request.method == "POST":
        # Handle adding a new task
        name = request.form.get("name")
        desc = request.form.get("desc")
        date = request.form.get("creation_date")
        priority = request.form.get("priority")

        # Insert the task with the associated username
        task_list.insert_one({
            "name": name,
            "desc": desc,
            "creation_date": date,
            "priority": priority,
            "done": False,
            "username": username
        })
        flash("Task added successfully!", "success")
        return redirect("/list")

    # Display the list of tasks
    all_tasks = task_list.find({"username": username})  # Filter tasks by username
    return render_template(
        'index.html',
        all="active",
        task_list=all_tasks,
        title=title,
        heading=heading
    )


# Display Uncompleted Tasks
@app.route("/uncompleted")
@login_required
def uncompleted():
    username = session["username"]  # Get the logged-in user's username
    uncompleted_tasks = task_list.find({"done": False, "username": username})  # Filter tasks by username
    return render_template(
        'index.html',
        uncompleted="active",
        task_list=uncompleted_tasks,
        title=title,
        heading=heading
    )


# Display the Completed Tasks
@app.route("/completed")
@login_required
def completed():
    username = session["username"]  # Get the logged-in user's username
    completed_tasks = task_list.find({"done": True, "username": username})  # Filter tasks by username
    return render_template(
        'index.html',
        completed="active",
        task_list=completed_tasks,
        title=title,
        heading=heading
    )


# Done-or-not ICON
@app.route("/done")
@login_required
def done():
    id = request.values.get("_id")
    username = session["username"]  # Get the logged-in user's username

    # Find the task and ensure it belongs to the logged-in user
    task = task_list.find_one({"_id": ObjectId(id), "username": username})
    if task:
        new_status = not task["done"]
        task_list.update_one({"_id": ObjectId(id)}, {"$set": {"done": new_status}})
    return redirect(redirect_url())


# Adding a Task
@app.route("/create", methods=['POST'])
@login_required
def create_task():
    name = request.values.get("name")
    desc = request.values.get("desc")
    date = request.values.get("creation_date")
    priority = int(request.values.get("priority"))
    priority_in_range = max(0, min(priority, 10))
    username = session["username"]  # Get the logged-in user's username

    # Insert the task with the associated username
    task_list.insert_one({
        "name": name,
        "desc": desc,
        "creation_date": date,
        "priority": priority_in_range,
        "done": False,
        "username": username  # Associate the task with the user
    })
    return redirect("/list")


# Deleting a Task with various references
@app.route("/remove")
@login_required
def remove():
    key = request.values.get("_id")
    username = session["username"]  # Get the logged-in user's username

    # Delete the task only if it belongs to the logged-in user
    task_list.delete_one({"_id": ObjectId(key), "username": username})
    return redirect("/")


# Updating a Task
@app.route("/update")
@login_required
def update():
    id = request.values.get("_id")
    username = session["username"]  # Get the logged-in user's username

    # Find the task and ensure it belongs to the logged-in user
    task = task_list.find({"_id": ObjectId(id), "username": username})
    return render_template(
        'update.html',
        tasks=task,
        heading="Update Task",
        title=title
    )


# Updating a Task with various references
@app.route("/updatetask", methods=['POST'])
@login_required
def update_task():
    name = request.values.get("name")
    desc = request.values.get("desc")
    date = request.values.get("creation_date")
    priority = request.values.get("priority")
    id = request.values.get("_id")
    username = session["username"]  # Get the logged-in user's username

    # Update the task only if it belongs to the logged-in user
    task_list.update_one({"_id": ObjectId(id), "username": username}, {
        '$set': {
            "name": name,
            "desc": desc,
            "creation_date": date,
            "priority": priority
        }
    })

    return redirect("/")


# Searching a Task with various references
@app.route("/search", methods=['GET'])
@login_required
def search():
    key = request.values.get("key")
    refer = request.values.get("refer")
    username = session["username"]  # Get the logged-in user's username

    # Search tasks only for the logged-in user
    if refer == "_id":
        try:
            tasks = task_list.find({"_id": ObjectId(key), "username": username})
        except Exception:
            tasks = []  # Handle invalid ObjectId
    else:
        # Use $regex for case-insensitive and partial matching
        tasks = task_list.find({
            refer: {"$regex": key, "$options": "i"},  # Case-insensitive regex
            "username": username
        })

    return render_template(
        'searchlist.html',
        task_list=tasks,
        title="Search Results",
        heading="Search Results"
    )


def test_login(client):
    # Add a test user to the database
    users.insert_one({"username": "testuser", "password": "password123"})

    # Test login with correct credentials
    response = client.post("/login", data={
        "username": "testuser",
        "password": "password123"
    }, follow_redirects=True)
    assert b"Login successful!" in response.data
    assert b"Task Management" in response.data  # Ensure the redirected page renders correctly

    # Test login with incorrect credentials
    response = client.post("/login", data={
        "username": "testuser",
        "password": "wrongpassword"
    }, follow_redirects=True)
    assert b"Invalid username or password!" in response.data

print(app.url_map)
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=port)
