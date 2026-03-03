from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import verify_user, get_users, save_users, get_students, save_students
import os

app = Flask(__name__)
app.secret_key = 'super_secret_key'

@app.route('/')
def index():
    if 'user' in session:
        if session['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('teacher_dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    user = verify_user(username, password)
    
    if user:
        session['user'] = user['username']
        session['role'] = user['role']
        session['full_name'] = user['full_name']
        if user['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('teacher_dashboard'))
    
    flash('Invalid credentials!', 'error')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

from datetime import datetime, timedelta

@app.route('/admin')
def admin_dashboard():
    if 'user' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))
    users = [u for u in get_users() if u['role'] == 'teacher']
    return render_template('admin_dashboard.html', teachers=users)

@app.route('/register_teacher', methods=['POST'])
def register_teacher():
    if 'user' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))
    
    username = request.form.get('username')
    password = request.form.get('password')
    full_name = request.form.get('full_name')
    
    users = get_users()
    if any(u['username'] == username for u in users):
        flash('Username already exists!', 'error')
    else:
        users.append({
            'username': username,
            'password': password,
            'role': 'teacher',
            'full_name': full_name
        })
        save_users(users)
        flash('Teacher registered successfully!', 'success')
        
    return redirect(url_for('admin_dashboard'))

@app.route('/edit_teacher/<username>', methods=['GET', 'POST'])
def edit_teacher(username):
    if 'user' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))
    
    users = get_users()
    user = next((u for u in users if u['username'] == username), None)
    
    if request.method == 'POST':
        user['full_name'] = request.form.get('full_name')
        user['password'] = request.form.get('password')
        save_users(users)
        flash('Teacher updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('edit_teacher.html', teacher=user)

@app.route('/delete_teacher/<username>')
def delete_teacher(username):
    if 'user' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))
    
    users = get_users()
    users = [u for u in users if u['username'] != username]
    save_users(users)
    flash('Teacher deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/teacher')
def teacher_dashboard():
    if 'user' not in session or session['role'] != 'teacher':
        return redirect(url_for('index'))
    
    teacher_username = session['user']
    all_students = get_students()
    
    teacher_students = [s for s in all_students if s.get('teacher_username') == teacher_username]
    
    for student in teacher_students:
        absences = sum(1 for status in student.get('attendance', {}).values() if status == 'Absent')
        student['total_absences'] = absences
        
    return render_template('teacher_dashboard.html', students=teacher_students)

@app.route('/add_student', methods=['POST'])
def add_student():
    if 'user' not in session or session['role'] != 'teacher':
        return redirect(url_for('index'))
    
    name = request.form.get('name')
    teacher_username = session['user']
    students = get_students()
    
    new_student = {
        'id': len(students) + 1,
        'name': name,
        'teacher_username': teacher_username,
        'attendance': {}
    }
    students.append(new_student)
    save_students(students)
    flash(f'Student {name} added!', 'success')
    return redirect(url_for('teacher_dashboard'))

@app.route('/edit_student/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    if 'user' not in session or session['role'] != 'teacher':
        return redirect(url_for('index'))
    
    students = get_students()
    student = next((s for s in students if s['id'] == id), None)
    
    if not student or student['teacher_username'] != session['user']:
        return redirect(url_for('teacher_dashboard'))

    if request.method == 'POST':
        student['name'] = request.form.get('name')
        save_students(students)
        flash('Student updated successfully!', 'success')
        return redirect(url_for('teacher_dashboard'))
    
    return render_template('edit_student.html', student=student)

@app.route('/delete_student/<int:id>')
def delete_student(id):
    if 'user' not in session or session['role'] != 'teacher':
        return redirect(url_for('index'))
    
    students = get_students()
    students = [s for s in students if not (s['id'] == id and s['teacher_username'] == session['user'])]
    save_students(students)
    flash('Student deleted successfully!', 'success')
    return redirect(url_for('teacher_dashboard'))

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    if 'user' not in session or session['role'] != 'teacher':
        return redirect(url_for('index'))
    
    date = request.form.get('date')
    students = get_students()
    
    for student in students:
        status = request.form.get(f"status_{student['id']}")
        if status:
            student['attendance'][date] = status
        
    save_students(students)
    flash(f'Attendance marked for {date}!', 'success')
    return redirect(url_for('teacher_dashboard'))

@app.route('/student_details/<int:id>')
def student_details(id):
    if 'user' not in session or session['role'] != 'teacher':
        return redirect(url_for('index'))
    
    students = get_students()
    student = next((s for s in students if s['id'] == id), None)
    
    if not student or student['teacher_username'] != session['user']:
        return redirect(url_for('teacher_dashboard'))

    attendance = student.get('attendance', {})
    total_days = len(attendance)
    presents = sum(1 for s in attendance.values() if s == 'Present')
    absents = sum(1 for s in attendance.values() if s == 'Absent')
    
    percentage = (presents / total_days * 100) if total_days > 0 else 0
    
    now = datetime.now()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    year_ago = now - timedelta(days=365)
    
    stats = {
        'total': {'p': presents, 'a': absents, 'pct': round(percentage, 2)},
        'week': {'p': 0, 'a': 0},
        'month': {'p': 0, 'a': 0},
        'year': {'p': 0, 'a': 0}
    }
    
    for date_str, status in attendance.items():
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            if date_obj >= week_ago:
                if status == 'Present': stats['week']['p'] += 1
                else: stats['week']['a'] += 1
            if date_obj >= month_ago:
                if status == 'Present': stats['month']['p'] += 1
                else: stats['month']['a'] += 1
            if date_obj >= year_ago:
                if status == 'Present': stats['year']['p'] += 1
                else: stats['year']['a'] += 1
        except: continue

    return render_template('student_details.html', student=student, stats=stats)

if __name__ == '__main__':
    app.run(debug=True)
