from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
import sqlite3

app = FastAPI()

class TaskCreate(BaseModel):
    title: str = None

class TaskUpdate(BaseModel):
    title: str = None
    done: bool = None

# Connect to the database via sqlite3
def open_db():
    return sqlite3.connect("tasks.db")

# Initialize and create the database with default tasks
def init_db():
    connection = open_db()
    cursor = connection.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, title TEXT, done BOOLEAN)")
    cursor.execute("SELECT COUNT(*) FROM tasks")
    checker = cursor.fetchone()
    if checker[0] == 0:
        cursor.execute("INSERT INTO tasks (title, done) VALUES ('Learn HTTP', 1)")
        cursor.execute("INSERT INTO tasks (title, done) VALUES ('Build API', 0)")
        cursor.execute("INSERT INTO tasks (title, done) VALUES ('Test with Swagger', 0)")
    connection.commit()
    connection.close()
init_db()

@app.get("/")
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def health_check():
    return {"status": "ok"}

# get all the tasks, or search for a specific task(s)
@app.get("/tasks")
def tasks(search: str = None):
    connection = open_db()
    cursor = connection.cursor()
    if search is not None:
        user_search = f"%{search}%"
        cursor.execute("SELECT * FROM tasks WHERE title LIKE ?", (user_search,))
    else:
        cursor.execute("SELECT * FROM tasks")
    results = cursor.fetchall()
    connection.close()
    dict_results = []
    keys = ['id', 'title', 'done']
    for item in results:
        sub_dict = dict(zip(keys, item))
        sub_dict['done'] = bool(sub_dict['done'])
        dict_results.append(sub_dict)
    return dict_results

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    connection = open_db()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    result = cursor.fetchone()
    connection.close()
    
    if result is None:
            return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})
        
    keys = ['id', 'title', 'done']
    sub_dict = dict(zip(keys, result))
    sub_dict['done'] = bool(sub_dict['done'])
    return sub_dict

@app.post("/tasks")
def create_task(task_data: TaskCreate):
    if task_data.title is None or task_data.title.strip() == "":
        return JSONResponse(status_code=400, content={"error": "Bad Request"})
    connection = open_db()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO tasks (title, done) VALUES (?, 0)", (task_data.title,))
    connection.commit()
    current_id = cursor.lastrowid
    new_task = {"id": current_id, "title": task_data.title, "done": False}
    connection.close()
    return JSONResponse(status_code=201, content=new_task)

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task_data: TaskUpdate):
    connection = open_db()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    result = cursor.fetchone()
    
    if result is None:
        connection.close()
        return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})

    if task_data.title is not None:
        if task_data.title.strip() == "":
            connection.close()
            return JSONResponse(status_code=400, content={"error": "Title cannot be empty"})
        new_title = task_data.title
    else:
        new_title = result[1]
        
    if task_data.done is not None:
        new_status = bool(task_data.done)
    else:
        new_status = bool(result[2])
    
    cursor.execute("UPDATE tasks SET title = ?, done = ? WHERE id = ?", (new_title, new_status, task_id))
    connection.commit()
    connection.close()
    selected_task = {'id':task_id, 'title': new_title, 'done': new_status}
    return JSONResponse(status_code=200, content=selected_task)

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    connection = open_db()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    result = cursor.fetchone()
    if result is not None:
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        connection.commit()
        connection.close()
        return Response(status_code=204)
    else:
        connection.close()
        return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})