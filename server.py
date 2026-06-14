import os
import sqlite3
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from flask_cors import CORS
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage
from twilio.rest import Client as TwilioClient
from datetime import datetime

load_dotenv()

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXT = {'png','jpg','jpeg','webp','gif'}
DB_PATH = os.path.join(os.path.dirname(__file__), 'submissions.db')

SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = int(os.getenv('SMTP_PORT', '465'))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
TWILIO_SID = os.getenv('TWILIO_SID')
TWILIO_TOKEN = os.getenv('TWILIO_TOKEN')
TWILIO_FROM = os.getenv('TWILIO_FROM')
ADMIN_PHONE = os.getenv('ADMIN_PHONE')
ADMIN_SECRET = os.getenv('ADMIN_SECRET')

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY,
        firstName TEXT,
        lastName TEXT,
        phone TEXT,
        admissionType TEXT,
        classLevel TEXT,
        classChoice TEXT,
        gender TEXT,
        hasMedical INTEGER,
        medicalDetails TEXT,
        message TEXT,
        photo TEXT,
        created_at TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXT

def send_notification(subject, body):
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASSWORD or not ADMIN_EMAIL:
        print('SMTP not configured; skipping email')
        return
    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = SMTP_USER
        msg['To'] = ADMIN_EMAIL
        msg.set_content(body)
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print('Failed to send email:', e)

def send_sms(body):
    if not (TWILIO_SID and TWILIO_TOKEN and TWILIO_FROM and ADMIN_PHONE):
        print('Twilio not configured; skipping SMS')
        return
    try:
        client = TwilioClient(TWILIO_SID, TWILIO_TOKEN)
        client.messages.create(body=body, from_=TWILIO_FROM, to=ADMIN_PHONE)
    except Exception as e:
        print('Failed to send SMS:', e)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/apply', methods=['POST'])
def apply():
    try:
        # Support both multipart/form-data and JSON (fallback)
        if request.content_type and request.content_type.startswith('multipart'):
            data = request.form.to_dict()
            file = request.files.get('photo')
        else:
            data = request.get_json() or {}
            file = None

        photo_path = None
        if file and file.filename and allowed_file(file.filename):
            filename = f"{int(datetime.utcnow().timestamp())}_{secure_filename(file.filename)}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            photo_path = filename

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''INSERT INTO submissions (firstName,lastName,phone,admissionType,classLevel,classChoice,gender,hasMedical,medicalDetails,message,photo,created_at)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', (
            data.get('firstName'),
            data.get('lastName'),
            data.get('phone'),
            data.get('admissionType'),
            data.get('classLevel'),
            data.get('classChoice'),
            data.get('gender'),
            1 if data.get('hasMedical') in ('on','true','1') else 0,
            data.get('medicalDetails'),
            data.get('message'),
            photo_path,
            datetime.utcnow().isoformat()
        ))
        conn.commit()
        conn.close()

        # Send notification email
        body_lines = [f"New application received:\n\n"]
        for k in ('firstName','lastName','phone','admissionType','classLevel','classChoice','gender'):
            body_lines.append(f"{k}: {data.get(k)}")
        body_lines.append(f"Has medical: {data.get('hasMedical')}")
        body_lines.append(f"Medical details: {data.get('medicalDetails')}")
        if photo_path:
            body_lines.append(f"Photo URL: /uploads/{photo_path}")
        body = '\n'.join(body_lines)
        send_notification('New admission', body)
        # send short SMS alert
        sms_body = f"New application: {data.get('firstName','')} {data.get('lastName','')} {data.get('phone','')} - {data.get('classLevel','')} {data.get('classChoice','')}"
        send_sms(sms_body[:150])

        return jsonify({'ok': True})
    except Exception as e:
        print('Error handling /api/apply', e)
        return jsonify({'error': 'server error'}), 500


@app.route('/admin')
def admin_view():
    token = request.args.get('token') or request.headers.get('X-Admin-Token')
    if not ADMIN_SECRET or token != ADMIN_SECRET:
        return 'Unauthorized', 401
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, firstName,lastName,phone,admissionType,classLevel,classChoice,gender,hasMedical,medicalDetails,message,photo,created_at FROM submissions ORDER BY created_at DESC')
    rows = c.fetchall()
    conn.close()
    html = ['<html><head><meta charset="utf-8"><title>Admissions Admin</title></head><body>']
    html.append('<h1>Admissions</h1>')
    html.append(f'<p>Total: {len(rows)}</p>')
    html.append('<p><a href="/admin/export?token=' + ADMIN_SECRET + '">Download CSV</a></p>')
    html.append('<table border="1" cellpadding="4" cellspacing="0"><tr><th>ID</th><th>Name</th><th>Phone</th><th>Type</th><th>Level</th><th>Class</th><th>Gender</th><th>Medical</th><th>Message</th><th>Photo</th><th>When</th></tr>')
    for r in rows:
        pid, fn, ln, phone, atype, level, choice, gender, hasMed, medDet, msg, photo, created = r
        photo_link = f'<a href="/uploads/{photo}">photo</a>' if photo else ''
        html.append(f'<tr><td>{pid}</td><td>{fn} {ln}</td><td>{phone}</td><td>{atype}</td><td>{level}</td><td>{choice}</td><td>{gender}</td><td>{"Yes" if hasMed else "No"}</td><td>{(medDet or "")[:80]}</td><td>{photo_link}</td><td>{created}</td></tr>')
    html.append('</table></body></html>')
    return '\n'.join(html)


@app.route('/admin/export')
def admin_export():
    token = request.args.get('token') or request.headers.get('X-Admin-Token')
    if not ADMIN_SECRET or token != ADMIN_SECRET:
        return 'Unauthorized', 401
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, firstName,lastName,phone,admissionType,classLevel,classChoice,gender,hasMedical,medicalDetails,message,photo,created_at FROM submissions ORDER BY created_at DESC')
    rows = c.fetchall()
    conn.close()
    import csv
    from io import StringIO
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['id','firstName','lastName','phone','admissionType','classLevel','classChoice','gender','hasMedical','medicalDetails','message','photo','created_at'])
    for r in rows:
        writer.writerow(r)
    output = si.getvalue()
    return output, 200, {'Content-Type':'text/csv','Content-Disposition':'attachment; filename="admissions.csv"'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
