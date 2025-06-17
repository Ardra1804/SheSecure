from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from twilio.rest import Client
import os
from datetime import datetime
from dotenv import load_dotenv
import sqlite3

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# Twilio setup from environment
twilio_sid = os.environ.get("TWILIO_SID")
twilio_token = os.environ.get("TWILIO_TOKEN")
twilio_number = os.environ.get("TWILIO_PHONE")
twilio_client = Client(twilio_sid, twilio_token)

# ----------------------------
# DATABASE SETUP
# ----------------------------
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            phone TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ----------------------------
# ROUTES
# ----------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register_user', methods=['POST'])
def register_user():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    contacts = data.get('contacts', [])

    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    try:
        c.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', (name, email, password))
        user_id = c.lastrowid
        for phone in contacts:
            c.execute('INSERT INTO contacts (user_id, phone) VALUES (?, ?)', (user_id, phone))
        conn.commit()
        return jsonify({'status': 'registered'})
    except sqlite3.IntegrityError:
        return jsonify({'status': 'email_exists'}), 400
    finally:
        conn.close()

@app.route('/send_alert', methods=['POST'])
def send_alert():
    data = request.get_json()
    username = data.get('username')
    lat = data.get('latitude')
    lon = data.get('longitude')
    contacts = data.get('contacts', [])

    location_link = f"https://maps.google.com/?q={lat},{lon}"
    alert_message = f"🚨 EMERGENCY ALERT from {username}!\nLocation: {location_link}"

    for number in contacts:
        try:
            twilio_client.messages.create(
                body=alert_message,
                from_=twilio_number,
                to=number
            )
        except Exception as e:
            print(f"Failed to send to {number}: {e}")

    socketio.emit('location_update', {
        'username': username,
        'lat': lat,
        'lon': lon,
        'time': datetime.utcnow().isoformat()
    })

    return jsonify({'status': 'SMS sent'}), 200

if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
