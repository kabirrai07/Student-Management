import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, 'data', 'users.json')
STUDENTS_FILE = os.path.join(BASE_DIR, 'data', 'students.json')

def load_json(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_json(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def get_users():
    return load_json(USERS_FILE)

def save_users(users):
    save_json(USERS_FILE, users)

def get_students():
    return load_json(STUDENTS_FILE)

def save_students(students):
    save_json(STUDENTS_FILE, students)

def verify_user(username, password):
    users = get_users()
    for user in users:
        if user['username'] == username and user['password'] == password:
            return user
    return None
