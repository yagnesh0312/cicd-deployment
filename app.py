from flask import Flask, render_template, request, redirect, url_for, session, flash  # Added session and flash for login
from bson import ObjectId
from pymongo import MongoClient
from prometheus_flask_exporter import PrometheusMetrics  # Import PrometheusMetrics
import logging

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


# Logging configurations
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("task-logger")


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
            logger.info("User ", username, " is logged in.")

            return redirect("/list")  # Ensure proper redirection
        else:
            flash("Invalid username or password!", "danger")
            logger.error("Invalid username or password!")

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
        logger.info("Signup successful!")

        return redirect("/login")

    return render_template("signup.html", title="Signup", heading="SIGNUP")


# Logout
@app.route("/logout")
def logout():
    session.pop("username", None)

    flash("You have been logged out.", "info")
    logger.info("You have been logged out.")

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




# Display all Tasks
@app.route("/")
@app.route("/list", methods=["GET", "POST"])
@login_required
def lists(): # Track task operations
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
        logger.info("Task added successfully!")

        return redirect("/list")

    # Display the list of tasks
    all_tasks = task_list.find({"username": username})  # Filter tasks by username

    return render_template(
        template_name_or_list='index.html',
        all="active",
        task_list=all_tasks,
        title=title,
        heading=heading
    )


# Display Uncompleted Tasks
@app.route("/uncompleted")
@login_required
def uncompleted():
    try:
        username = session["username"]  # Get the logged-in user's username
        uncompleted_tasks = task_list.find({"done": False, "username": username})  # Filter tasks by username

        logger.info(f"User {username} viewed uncompleted tasks.")

        return render_template(
            template_name_or_list='index.html',
            uncompleted="active",
            task_list=uncompleted_tasks,
            title=title,
            heading=heading
        )

    except Exception as e:
        logger.error(f"Error while fetching uncompleted tasks for user {username}: {str(e)}")
        flash("An error occurred while fetching uncompleted tasks.", "danger")

        return redirect("/list")


# Display the Completed Tasks
@app.route("/completed")
@login_required
def completed():
    try:
        username = session["username"]  # Get the logged-in user's username
        completed_tasks = task_list.find({"done": True, "username": username})  # Filter tasks by username
        logger.info(stack_info=True, msg=f"User {username} viewed completed tasks.")
        return render_template(
            'index.html',
            completed="active",
            task_list=completed_tasks,
            title=title,
            heading=heading
        )
    except Exception as e:
        logger.error(f"Error while fetching completed tasks for user {username}: {str(e)}")
        flash("An error occurred while fetching completed tasks.", "danger")
        return redirect("/list")


# Done-or-not ICON
@app.route("/done")
@login_required
def done():
    try:
        id = request.values.get("_id")
        username = session["username"]  # Get the logged-in user's username

        # Find the task and ensure it belongs to the logged-in user
        task = task_list.find_one({"_id": ObjectId(id), "username": username})
        if task:
            new_status = not task["done"]
            task_list.update_one({"_id": ObjectId(id)}, {"$set": {"done": new_status}})
            logger.info(stack_info=True, msg=f"Task {id} status updated to {'done' if new_status else 'not done'} by user {username}.")
        else:
            logger.warning(f"Task {id} not found or does not belong to user {username}.")
            flash("Task not found or unauthorized access.", "warning")
    except Exception as e:
        logger.error(f"Error while updating task status for user {username}: {str(e)}")
        flash("An error occurred while updating task status.", "danger")
    return redirect(redirect_url())


# Adding a Task
@app.route("/create", methods=['POST'])
@login_required
def create_task():
    try:
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
        logger.info(stack_info=True, msg=f"Task '{name}' created by user {username}.")
    except Exception as e:
        logger.error(f"Error while creating task for user {username}: {str(e)}")
        flash("An error occurred while creating the task.", "danger")
    return redirect("/list")


# Deleting a Task with various references
@app.route("/remove")
@login_required
def remove():
    try:
        key = request.values.get("_id")
        username = session["username"]  # Get the logged-in user's username

        # Delete the task only if it belongs to the logged-in user
        result = task_list.delete_one({"_id": ObjectId(key), "username": username})

        if result.deleted_count > 0:
            logger.info(stack_info=True, msg=f"Task {key} deleted by user {username}.")
        else:
            logger.warning(f"Task {key} not found or does not belong to user {username}.")
            flash("Task not found or unauthorized access.", "warning")

    except Exception as e:

        logger.error(f"Error while deleting task {key} for user {username}: {str(e)}")
        flash("An error occurred while deleting the task.", "danger")

    return redirect("/")


# Updating a Task
@app.route("/update")
@login_required
def update():
    try:
        id = request.values.get("_id")
        username = session["username"]  # Get the logged-in user's username

        # Find the task and ensure it belongs to the logged-in user
        task = task_list.find({"_id": ObjectId(id), "username": username})

        if task.__empty:
            logger.info(stack_info=True, msg=f"User {username} is updating task {id}.")

            return render_template(
                template_name_or_list='update.html',
                tasks=task,
                heading="Update Task",
                title=title
            )

        else:
            logger.warning(f"Task {id} not found or does not belong to user {username}.")
            flash("Task not found or unauthorized access.", "warning")

    except Exception as e:
        logger.error(f"Error while fetching task {id} for update by user {username}: {str(e)}")
        flash("An error occurred while fetching the task for update.", "danger")

    return redirect("/list")


# Updating a Task with various references
@app.route("/updatetask", methods=['POST'])
@login_required
def update_task():
    try:
        name = request.values.get("name")
        desc = request.values.get("desc")
        date = request.values.get("creation_date")
        priority = request.values.get("priority")
        id = request.values.get("_id")
        username = session["username"]  # Get the logged-in user's username

        # Update the task only if it belongs to the logged-in user
        result = task_list.update_one({"_id": ObjectId(id), "username": username}, {
            '$set': {
                "name": name,
                "desc": desc,
                "creation_date": date,
                "priority": priority
            }
        })

        if result.matched_count > 0:
            logger.info(stack_info=True, msg=f"Task {id} is updated by user {username}.")
        else:
            logger.warning(f"Task {id} not found or does not belong to user {username}.")
            flash("Task not found or unauthorized access.", "warning")

    except Exception as e:
        logger.error(f"Error while updating task {id} for user {username}: {str(e)}")
        flash("An error occurred while updating the task.", "danger")

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
        template_name_or_list='searchlist.html',
        task_list=tasks,
        title="Search Results",
        heading="Search Results"
    )


import time
import random # Import time module for delay

@app.route("/slow")
def slow_response():
    time.sleep(random.randint(1,6))  # Simulate a delay of 10 seconds
    return "This is a slow response!", 200


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
