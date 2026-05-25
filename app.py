from flask import Flask, render_template, request, redirect, session
import mysql.connector
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'secret123'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="",
    database="complaint_portal",
    autocommit=True
)

cursor = db.cursor(buffered=True)

# LOGIN
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        email = request.form.get('email')
        password = request.form.get('password')

        if role == 'user':
            cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
            user = cursor.fetchone()
            if user:
                session['user'] = user[0]
                return redirect('/dashboard')
            else:
                return "Invalid User"

        elif role == 'admin':
            cursor.execute("SELECT * FROM admin WHERE username=%s AND password=%s", (email, password))
            admin = cursor.fetchone()
            if admin:
                session['admin'] = admin[0]
                return redirect('/admin')
            else:
                return "Invalid Admin"

    return render_template('login.html')

# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        cursor.execute("INSERT INTO users(name,email,password) VALUES(%s,%s,%s)", (name, email, password))
        db.commit()
        return redirect('/')

    return render_template('register.html')

# USER DASHBOARD
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    return render_template('dashboard.html')

# SUBMIT COMPLAINT
@app.route('/submit_complaint', methods=['POST'])
def submit_complaint():
    if 'user' not in session:
        return redirect('/')
    title = request.form['title']
    address = request.form['address']
    description = request.form['description']
    image = request.files['image']

    filename = ""
    if image:
        filename = secure_filename(image.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    cursor.execute("INSERT INTO complaints(user_id,title,address,description,image,status) VALUES(%s,%s,%s,%s,%s,%s)",
                   (session['user'], title, address, description, filename, 'Pending'))
    db.commit()

    return redirect('/dashboard')

# MY COMPLAINTS
@app.route('/my_complaints')
def my_complaints():
    if 'user' not in session:
        return redirect('/')

    cursor.execute("SELECT * FROM complaints WHERE user_id=%s", (session['user'],))
    data = cursor.fetchall()
    return render_template('my_complaints.html', data=data)

@app.route('/update_status', methods=['POST'])
def update_status():
    id = request.form['id']
    status = request.form['status']

    cursor = db.cursor()
    cursor.execute("UPDATE complaints SET status=%s WHERE id=%s", (status, id))
    db.commit()

    return "Success"

# ADMIN PANEL
@app.route('/admin')
def admin():
    if 'admin' not in session:
        return redirect('/')

    cursor.execute("SELECT * FROM complaints")
    data = cursor.fetchall()
    return render_template('admin.html', data=data)

# APPROVE
@app.route('/approve/<int:id>')
def approve(id):
    cursor.execute("UPDATE complaints SET status='Approved' WHERE id=%s", (id,))
    db.commit()
    return redirect('/admin')

# REJECT
@app.route('/reject/<int:id>')
def reject(id):
    cursor.execute("UPDATE complaints SET status='Rejected' WHERE id=%s", (id,))
    db.commit()
    return redirect('/admin')

# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

app.run(debug=True)
@app.route('/test')
def test():
    return "Server Working"

