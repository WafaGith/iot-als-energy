from flask import Flask, request, jsonify
from flask_cors import CORS
import urllib.request
import urllib.parse
import urllib.error
import json
from werkzeug.security import check_password_hash
import jwt
import datetime
from functools import wraps
from database import execute_query, init_default_admin, get_config

import os

# Serve the parent directory as static folder so Flask can deliver HTML/JS/CSS files directly
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
app = Flask(__name__, static_url_path='', static_folder=base_dir)
CORS(app) # Allow cross-origin for frontend

# Rute default yang mengarahkan ke halaman frontend (Otomatis ke login apabila belum ada token)
@app.route('/')
def serve_index():
    return app.send_static_file('index.html')

try:
    init_default_admin()
except Exception as e:
    print(f"Skipping admin init (maybe DB not ready?): {e}")

config = get_config()
app.config['SECRET_KEY'] = config.get('jwt_secret', 'my_super_secret_key_123')

# Middleware
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        with open("debug_auth.log", "a") as logfile:
            logfile.write(f"Auth header received: {token}\n")
            
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            token = token.split(" ")[1] # Bearer Token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            
            with open("debug_auth.log", "a") as logfile:
                logfile.write(f"Token decoded: {data}\n")
                
            current_user = execute_query("SELECT id, username FROM admins WHERE id = %s", (data['user_id'],), fetch_one=True)
            if not current_user:
                with open("debug_auth.log", "a") as logfile:
                    logfile.write("User not found in DB!\n")
                return jsonify({'message': 'User not found!'}), 401
        except Exception as e:
            with open("debug_auth.log", "a") as logfile:
                logfile.write(f"Exception: {str(e)}\n")
            return jsonify({'message': f'Token is invalid! Error: {str(e)}'}), 401
            
        return f(current_user, *args, **kwargs)
    return decorated

# ================= AUTH =================
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Could not verify', 'error': True}), 401

    admin = execute_query("SELECT * FROM admins WHERE username = %s", (data.get('username'),), fetch_one=True)
    if not admin:
        return jsonify({'message': 'User tidak ditemukan', 'error': True}), 401
        
    if check_password_hash(admin['password_hash'], data.get('password')):
        token = jwt.encode({'user_id': admin['id'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, app.config['SECRET_KEY'], algorithm="HS256")
        
        # log system event
        execute_query("INSERT INTO system_events (event_type, description) VALUES (%s, %s)", 
                      ("Login", f"Admin {admin['username']} logged in"), commit=True)
                      
        return jsonify({'token': token, 'error': False})
        
    return jsonify({'message': 'Password salah', 'error': True}), 401

# ================= TELEGRAM BOT =================
def send_telegram_alert(message):
    settings = execute_query("SELECT * FROM settings", fetch_all=True)
    cfg = {item['setting_key']: item['setting_value'] for item in settings}
    
    if str(cfg.get('telegram_active', '0')) != '1':
        return "SKIP", "Telegram bot is disabled in settings"
        
    token = cfg.get('telegram_bot_token', '').strip()
    chat_id = cfg.get('telegram_chat_id', '').strip()
    
    if not token or not chat_id:
        return "SKIP", "Token or Chat ID not configured"
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            res_body = response.read()
            return "SUCCESS", str(res_body)
    except Exception as e:
        return "ERROR", str(e)

# ================= ESP32 ENDPOINT =================
@app.route('/api/sensor/data', methods=['POST'])
def receive_sensor_data():
    """
    Endpoint for ESP32 to POST data.
    Expected JSON format:
    {
       "m1": {"v": 220.1, "i": 1.2, "p": 264.12, "e": 10.5, "f": 50.0, "pf": 0.98},
       "m2": {"v": 219.5, "i": 0.5, "p": 109.75, "e": 5.2, "f": 50.0, "pf": 0.95}
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400
        
    try:
        # Mesin 1
        if 'm1' in data:
            m1 = data['m1']
            execute_query(
                "INSERT INTO sensor_data (mesin_id, volt, arus, daya, energi, frekuensi, pf) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (1, m1.get('v',0), m1.get('i',0), m1.get('p',0), m1.get('e',0), m1.get('f',0), m1.get('pf',0)),
                commit=True
            )
        # Mesin 2
        if 'm2' in data:
            m2 = data['m2']
            execute_query(
                "INSERT INTO sensor_data (mesin_id, volt, arus, daya, energi, frekuensi, pf) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (2, m2.get('v',0), m2.get('i',0), m2.get('p',0), m2.get('e',0), m2.get('f',0), m2.get('pf',0)),
                commit=True
            )
            
        # Check Quota Limits
        try:
            settings_data = execute_query("SELECT * FROM settings", fetch_all=True)
            cfg = {item['setting_key']: item['setting_value'] for item in settings_data}
            
            if str(cfg.get('telegram_active', '0')) == '1':
                kuota = float(cfg.get('kuota_energi', 100.0))
                batas = float(cfg.get('batas_sisa_energi', 10.0))
                
                # Fetch latest accumulated energy from DB across both engines for stability
                latest_m1 = execute_query("SELECT energi FROM sensor_data WHERE mesin_id=1 ORDER BY timestamp DESC LIMIT 1", fetch_one=True)
                latest_m2 = execute_query("SELECT energi FROM sensor_data WHERE mesin_id=2 ORDER BY timestamp DESC LIMIT 1", fetch_one=True)
                e1 = latest_m1['energi'] if latest_m1 else 0
                e2 = latest_m2['energi'] if latest_m2 else 0
                
                total_energi = e1 + e2
                sisa = kuota - total_energi
                
                if sisa <= batas:
                    # check throttling (don't spam telegram every 3 seconds)
                    last_notif = execute_query("SELECT timestamp FROM notifications WHERE message LIKE '%%Peringatan Kuota%%' ORDER BY timestamp DESC LIMIT 1", fetch_one=True)
                    send_it = True
                    if last_notif and last_notif['timestamp']:
                        diff = datetime.datetime.now() - last_notif['timestamp']
                        if diff.total_seconds() < 3600: # 1 hour throttle
                            send_it = False
                    
                    if send_it:
                        msg_text = f"⚠️ <b>PERINGATAN KUOTA ENERGI</b> ⚠️\n\nSisa Kuota Listrik Anda menipis!\n\n<b>Sisa Saat Ini:</b> {sisa:.2f} kWh\n<b>Total Kuota:</b> {kuota:.2f} kWh\n<b>Batas Peringatan:</b> {batas:.2f} kWh\n\nSegera lakukan pengisian ulang untuk menghindari pemadaman."
                        status, text_res = send_telegram_alert(msg_text)
                        execute_query("INSERT INTO notifications (message, status) VALUES (%s, %s)", (msg_text, status + ": " + text_res[:40]), commit=True)
        except Exception as e:
            print("Quota Check Telegram Error:", e)

        return jsonify({"message": "Data saved successfully"}), 201
    except Exception as e:
        return jsonify({"message": str(e)}), 500

# ================= DASHBOARD ENDPOINTS =================
@app.route('/api/realtime', methods=['GET'])
@token_required
def get_realtime(current_user):
    m1 = execute_query("SELECT * FROM sensor_data WHERE mesin_id = 1 ORDER BY timestamp DESC LIMIT 1", fetch_one=True)
    m2 = execute_query("SELECT * FROM sensor_data WHERE mesin_id = 2 ORDER BY timestamp DESC LIMIT 1", fetch_one=True)
    
    # get 7 data points latest per mesin for mini chart (1 data point per 5 minute for realtime chart approximation, or just latest 10)
    history_m1 = execute_query("SELECT timestamp, volt, arus, daya, frekuensi, pf FROM (SELECT * FROM sensor_data WHERE mesin_id = 1 ORDER BY timestamp DESC LIMIT 15) sub ORDER BY timestamp ASC", fetch_all=True)
    history_m2 = execute_query("SELECT timestamp, volt, arus, daya, frekuensi, pf FROM (SELECT * FROM sensor_data WHERE mesin_id = 2 ORDER BY timestamp DESC LIMIT 15) sub ORDER BY timestamp ASC", fetch_all=True)
    
    # Format datetime response
    for row in history_m1: row['timestamp'] = row['timestamp'].strftime("%H:%M:%S")
    for row in history_m2: row['timestamp'] = row['timestamp'].strftime("%H:%M:%S")
    if m1: m1['timestamp'] = m1['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
    if m2: m2['timestamp'] = m2['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
    
    return jsonify({
        "m1": m1,
        "m2": m2,
        "history_m1": history_m1,
        "history_m2": history_m2
    })

@app.route('/api/history/sensor', methods=['GET'])
@token_required
def get_sensor_history(current_user):
    limit = int(request.args.get('limit', 100))
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    mesin_id = request.args.get('mesin_id')
    
    query = "SELECT * FROM sensor_data WHERE 1=1"
    params = []
    
    if start_date:
        query += " AND timestamp >= %s"
        params.append(start_date + " 00:00:00")
    if end_date:
        query += " AND timestamp <= %s"
        params.append(end_date + " 23:59:59")
    if mesin_id and mesin_id != 'all':
        query += " AND mesin_id = %s"
        params.append(int(mesin_id))
        
    # Validasi limit aman untuk SQL injection
    if limit > 1000: limit = 1000
    query += f" ORDER BY timestamp DESC LIMIT {limit}"
    
    data = execute_query(query, tuple(params) if params else None, fetch_all=True)
    if data:
        for row in data:
            row['timestamp'] = row['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
    else:
        data = []
    return jsonify(data)

@app.route('/api/history/events', methods=['GET'])
@token_required
def get_events(current_user):
    limit = int(request.args.get('limit', 50))
    data = execute_query("SELECT * FROM system_events ORDER BY timestamp DESC LIMIT %s", (limit,), fetch_all=True)
    for row in data: row['timestamp'] = row['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
    return jsonify(data)

@app.route('/api/history/notifications', methods=['GET'])
@token_required
def get_notifications(current_user):
    limit = int(request.args.get('limit', 50))
    data = execute_query("SELECT * FROM notifications ORDER BY timestamp DESC LIMIT %s", (limit,), fetch_all=True)
    for row in data: row['timestamp'] = row['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
    return jsonify(data)

@app.route('/api/settings', methods=['GET', 'POST'])
@token_required
def manage_settings(current_user):
    if request.method == 'GET':
        data = execute_query("SELECT * FROM settings", fetch_all=True)
        settings_dict = {item['setting_key']: item['setting_value'] for item in data}
        return jsonify(settings_dict)
    elif request.method == 'POST':
        data = request.get_json()
        for k, v in data.items():
            execute_query(
                "INSERT INTO settings (setting_key, setting_value) VALUES (%s, %s) ON DUPLICATE KEY UPDATE setting_value = %s",
                (k, str(v), str(v)),
                commit=True
            )
        
        execute_query("INSERT INTO system_events (event_type, description) VALUES (%s, %s)", 
                      ("Settings Changed", f"Admin updated settings"), commit=True)
                      
        return jsonify({"message": "Settings updated"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
