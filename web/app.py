*This file runs the robot, database, camera, and website.*

import time
import cv2
import smtplib
import numpy as np
import os
import sqlite3
import datetime
import RPi.GPIO as GPIO
from flask import Flask, render_template, Response
from flask import request, session, redirect, url_for, flash
from picamera2 import Picamera2
from email.message import EmailMessage
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("MOSS_SECRET_KEY", "change-me-in-production")

# --- CONFIGURATION ---
ADMIN_EMAIL = os.environ.get("MOSS_ADMIN_EMAIL", "")
APP_PASSWORD = os.environ.get("MOSS_APP_PASSWORD", "")
DB_NAME = "users.db"

# --- SYSTEM STATE ---
is_moving = False
theft_detected = False
stuck_detected = False
stuck_start_time = None
last_email_time = 0
active_user_email = None
active_user_id = None
last_operator = "None"

# --- GPIO SETUP ---
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
IN1, IN2, IN3, IN4 = 11, 13, 15, 16
GPIO.setup([IN1, IN2, IN3, IN4], GPIO.OUT)

# --- DATABASE INITIALIZATION ---
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        # Create Users Table
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        # Create Alerts Table
        c.execute('''CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            alert_type TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        # Create Admin if not exists
        c.execute("SELECT * FROM users WHERE username = 'admin'")
        if not c.fetchone():
            pw = generate_password_hash('1234')
            c.execute("INSERT INTO users (username, password, phone, email, role) VALUES (?,?,?,?,?)",
                      ('admin', pw, '000-000-0000', ADMIN_EMAIL, 'admin'))
            print(">>> ADMIN ACCOUNT CREATED")
        conn.commit()

    init_db()

    # --- HARDWARE & ALERT LOGIC ---
    def stop_motors():
    global is_moving, stuck_start_time, stuck_detected, theft_detected
    GPIO.output([IN1, IN2, IN3, IN4], 0)
    is_moving = False
    stuck_start_time = None
    stuck_detected = False
    theft_detected = False

        def log_alert(alert_type):
    # CRITICAL: Default to Admin (ID 1) if no user is logged in
    target_id = active_user_id if active_user_id else 1
    try:
        with sqlite3.connect(DB_NAME) as con:
            con.execute("INSERT INTO alerts (user_id, alert_type) VALUES (?, ?)", (target_id, alert_type))
            con.commit()
            print(f">>> ALERT LOGGED: {alert_type} for User ID {target_id}")
    except Exception as e: print(f"DB Error: {e}")

            def send_email(reason):
    global last_email_time
    if time.time() - last_email_time < 15: return

    log_alert(reason) # Save to DB first

    recipients = [ADMIN_EMAIL]
    if active_user_email and active_user_email != ADMIN_EMAIL:
        recipients.append(active_user_email)

    msg = EmailMessage()
    msg['From'] = ADMIN_EMAIL
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = f"MOSS ALERT: {reason}"
    msg.set_content(f"ALERT: {reason} detected!\nSent to: {recipients}")

    try:
        s = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        s.login(ADMIN_EMAIL, APP_PASSWORD)
        s.send_message(msg)
        s.quit()
        last_email_time = time.time()
        print(f">>> SENT EMAIL TO {recipients}")
    except: print("!!! EMAIL FAILED")

                # --- CAMERA SYSTEM ---
                picam2 = Picamera2()
                config = picam2.create_video_configuration(main={"size": (320, 240), "format": "RGB888"})
                picam2.configure(config)
                picam2.start()
                prev_frame = None

                def gen_frames():
    global prev_frame, theft_detected, stuck_detected, stuck_start_time
    while True:
        try:
            img = picam2.capture_array()
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            if prev_frame is not None:
                diff = cv2.absdiff(prev_frame, gray)
                thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
                motion = np.sum(thresh)

                if is_moving:
                    if not stuck_start_time: stuck_start_time = time.time()
                    if motion > 200000: 
                        stuck_start_time = time.time()
                        stuck_detected = False
                    if time.time() - stuck_start_time > 20 and not stuck_detected:
                        send_email("STUCK")
                        stuck_detected = True
                else:
                    if motion > 30000 and not theft_detected:
                        send_email("THEFT")
                        theft_detected = True
                    elif motion < 30000: theft_detected = False
            prev_frame = gray
            ret, buf = cv2.imencode('.jpg', cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n')
        except: time.sleep(0.05)

                    # --- WEB ROUTES ---
                    @app.route('/')
                    def index(): return redirect(url_for('dashboard')) if 'uid' in session else redirect(url_for('login'))

                    @app.route('/login', methods=['GET','POST'])
                    def login():
    global active_user_email, active_user_id, last_operator
    if request.method=='POST':
        u = request.form['username']
        p = request.form['password']
        with sqlite3.connect(DB_NAME) as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("SELECT * FROM users WHERE username=?",(u,))
            user = cur.fetchone()
            if user and check_password_hash(user['password'], p):
                session['uid'] = user['id']
                session['user'] = user['username']
                session['role'] = user['role']
                session['email'] = user['email']
                active_user_email = user['email']
                active_user_id = user['id']
                last_operator = user['username']
                return redirect(url_for('dashboard'))
            flash("Invalid Login")
    return render_template('login.html')

                        @app.route('/register', methods=['GET','POST'])
                        def register():
    if request.method=='POST':
        try:
            pw = generate_password_hash(request.form['password'])
            with sqlite3.connect(DB_NAME) as con:
                con.execute("INSERT INTO users (username, password, phone, email, role) VALUES (?,?,?,?,?)",
                            (request.form['username'], pw, request.form['phone'], request.form['email'], 'user'))
            return redirect(url_for('login'))
        except: flash("Username/Email taken")
    return render_template('register.html')

                            @app.route('/dashboard')
                            def dashboard():
    if 'uid' not in session: return redirect(url_for('login'))
    global active_user_email, active_user_id
    active_user_email = session.get('email')
    active_user_id = session.get('uid')
    return render_template('dashboard.html')

                                @app.route('/admin/users')
                                def admin_users():
    if session.get('role') != 'admin': return redirect(url_for('dashboard'))
    with sqlite3.connect(DB_NAME) as con:
        con.row_factory = sqlite3.Row
        users = con.execute("SELECT * FROM users").fetchall()
    return render_template('admin_users.html', users=users)

                                    @app.route('/admin/view/<int:id>')
                                    def view_user(id):
    if session.get('role') != 'admin': return redirect(url_for('dashboard'))
    with sqlite3.connect(DB_NAME) as con:
        con.row_factory = sqlite3.Row
        user = con.execute("SELECT * FROM users WHERE id=?", (id,)).fetchone()

        # Count alerts (No date limit)
        alerts = con.execute("SELECT alert_type, COUNT(*) as c FROM alerts WHERE user_id=? GROUP BY alert_type", (id,)).fetchall()

    theft, stuck = 0, 0
    for a in alerts:
        if a['alert_type']=='THEFT': theft=a['c']
        elif a['alert_type']=='STUCK': stuck=a['c']

    analytics = {'theft': theft, 'stuck': stuck, 'total': theft+stuck}
    return render_template('view_user.html', user=user, analytics=analytics)

                                        @app.route('/admin/delete/<int:id>')
                                        def delete_user(id):
    if session.get('role') == 'admin' and id != session.get('uid'):
        with sqlite3.connect(DB_NAME) as con:
            con.execute("DELETE FROM users WHERE id=?", (id,))
            con.execute("DELETE FROM alerts WHERE user_id=?", (id,))
    return redirect(url_for('admin_users'))

                                            @app.route('/admin/edit/<int:id>', methods=['GET','POST'])
                                            def edit_user(id):
    if session.get('role') != 'admin': return redirect(url_for('dashboard'))
    with sqlite3.connect(DB_NAME) as con:
        con.row_factory = sqlite3.Row
        if request.method=='POST':
            u = request.form['username']
            ph = request.form['phone']
            em = request.form['email']
            r = request.form['role']
            if request.form['password']:
                pw = generate_password_hash(request.form['password'])
                con.execute("UPDATE users SET username=?, password=?, phone=?, email=?, role=? WHERE id=?", (u,pw,ph,em,r,id))
            else:
                con.execute("UPDATE users SET username=?, phone=?, email=?, role=? WHERE id=?", (u,ph,em,r,id))
            return redirect(url_for('admin_users'))
        user = con.execute("SELECT * FROM users WHERE id=?",(id,)).fetchone()
    return render_template('edit_user.html', user=user)

                                                @app.route('/logout')
                                                def logout():
    session.clear()
    return redirect(url_for('login'))

                                                    @app.route('/video_feed')
                                                    def video_feed(): return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

                                                    @app.route('/status')
                                                    def status():
    return {"theft": theft_detected, "stuck": stuck_detected, "operator": last_operator}

                                                        @app.route('/action/<cmd>')
                                                        def action(cmd):
    if 'uid' not in session: return "DENIED"
    global is_moving, last_operator
    last_operator = session['user']
    if cmd=='start':
        is_moving = True
        GPIO.output(IN1,1); GPIO.output(IN3,1); GPIO.output(IN2,0); GPIO.output(IN4,0)
    elif cmd in ['stop','home']: stop_motors()
    elif cmd=='shutdown' and session['role']=='admin': os.system("sudo shutdown now")
    return "OK"

                                                            @app.route('/move/<d>')
                                                            def move(d):
    if 'uid' not in session: return "DENIED"
    global is_moving, last_operator
    last_operator = session['user']
    if d=='stop': stop_motors()
    else:
        is_moving = True
        if d=='forward': GPIO.output(IN1,1); GPIO.output(IN3,1); GPIO.output(IN2,0); GPIO.output(IN4,0)
        elif d=='backward': GPIO.output(IN2,1); GPIO.output(IN4,1); GPIO.output(IN1,0); GPIO.output(IN3,0)
        elif d=='left': GPIO.output(IN2,1); GPIO.output(IN3,1); GPIO.output(IN1,0); GPIO.output(IN4,0)
        elif d=='right': GPIO.output(IN1,1); GPIO.output(IN4,1); GPIO.output(IN2,0); GPIO.output(IN3,0)
    return "OK"

                                                                if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
