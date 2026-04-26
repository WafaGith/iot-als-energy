from flask import request, jsonify, current_app
import jwt
import urllib.request
import urllib.parse
import json
import datetime
from functools import wraps
from database import execute_query

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            token = token.split(" ")[1]
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = execute_query("SELECT id, username FROM admins WHERE id = %s", (data['user_id'],), fetch_one=True)
            if not current_user:
                return jsonify({'message': 'User not found!'}), 401
        except Exception as e:
            return jsonify({'message': f'Token is invalid! Error: {str(e)}'}), 401
            
        return f(current_user, *args, **kwargs)
    return decorated

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
    payload = json.dumps({"chat_id": chat_id, "text": message, "parse_mode": "HTML"}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return "SUCCESS", str(response.read())
    except Exception as e:
        return "ERROR", str(e)
