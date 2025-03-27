from flask import Flask, render_template, request, redirect, url_for # For flask implementation
from bson import ObjectId    #  For ObjectId to work
from pymongo import MongoClient
import dotenv
from dotenv import load_dotenv
import os
load_dotenv()

MONGO_URL = os.environ.get("MONGO_CONN_STRING")
MONGO_DB = os.environ.get("MONGO_DB_NAME")
MONGO_CONN_NAME = os.environ.get("MONGO_COLLECTION_NAME")


app = Flask(__name__)
port = os.environ.get("PORT")


title = "Task Management application By Yagnesh"
heading = "Task Management"

# mongodb://user_name:password@ip_host:port/Database_Name
# db  =  client.Database_Name
# table_var_name  =  db.table_name


client = MongoClient(f"{MONGO_URL}/{MONGO_DB}") # host uri
db = client[MONGO_DB] 							     # Select the database
task_list = db[MONGO_CONN_NAME]                      # Select the collection name
print(task_list)
def redirect_url():
    return request.args.get('next') or \
        request.referrer or \
        url_for('index')


# Display all Tasks
@app.route("/")
@app.route("/list")
def lists ():
	all_tasks  =  task_list.find()
	return render_template(
		'index.html',
		all = "active",
		task_list = all_tasks,
		title = title,
		heading = heading
	)


# Display Uncompleted Tasks
@app.route("/uncompleted")
def uncompleted ():
	uncompleted_tasks = task_list.find({"done": False })
	return render_template(
		'index.html',
		uncompleted = "active",
		task_list = uncompleted_tasks,
		title = title,
		heading = heading
	)


# Display the Completed Tasks
@app.route("/completed")
def completed ():
	completed_tasks = task_list.find({"done": True })
	return render_template(
		'index.html',
		completed = "active",
		task_list = completed_tasks,
		title = title,
		heading = heading
	)


# Done-or-not ICON
@app.route("/done")
def done ():
	id = request.values.get("_id")
	task = task_list.find({"_id":ObjectId(id)})

	if(task[0]["done"] == True):
		task_list.update_one({"_id" : ObjectId(id)},  {"$set" : { "done": False }})
	else:
		task_list.update_one({"_id" : ObjectId(id)},  {"$set" : { "done": True }})

	redir = redirect_url()
	return redirect(redir)


# Adding a Task
@app.route("/action",  methods = ['POST'])
def action ():
	name = request.values.get("name")
	desc = request.values.get("desc")
	date = request.values.get("creation_date")
	priority = request.values.get("priority")

	task_list.insert_one(document = { "name" : name, "desc" : desc, "creation_date" : date, "priority" : priority, "done" : False})
	return redirect("/list")


# Deleting a Task with various references
@app.route("/remove")
def remove ():
	key = request.values.get("_id")
	task_list.delete_one({"_id":ObjectId(key)})
	return redirect("/")


@app.route("/update")
def update ():
	id = request.values.get("_id")
	task = task_list.find({"_id":ObjectId(id)})
	return render_template(
		'update.html',
		tasks = task,
		heading = heading,
		title = title
	)


# Updating a Task with various references
@app.route("/action3",  methods = ['POST'])
def action3 ():
	name = request.values.get("name")
	desc = request.values.get("desc")
	date = request.values.get("creation_date")
	priority = request.values.get("priority")
	id = request.values.get("_id")

	task_list.update_one({"_id":ObjectId(id)},  {
			'$set':{
				"name" : name,
				"desc" : desc,
				"creation_date" : date,
				"priority" : priority
			}
		})

	return redirect("/")


# Searching a Task with various references
@app.route("/search",  methods = ['GET'])
def search():
	key = request.values.get("key")
	refer = request.values.get("refer")

	if(key == "_id"):
		todos_l  =  task_list.find({refer:ObjectId(key)})
	else:
		todos_l  =  task_list.find({refer:key})

	return render_template(
		'searchlist.html',
		task_list = todos_l,
		title = title,
		heading = heading
	)


if __name__  ==  '__main__':
    if port is None:
        app.run(host = '0.0.0.0', port = 5000, debug = True)
    else:
        app.run(host = '0.0.0.0', port = int(port), debug = True)
