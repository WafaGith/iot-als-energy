from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import check_password_hash
import jwt
import datetime
from database import execute_query

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Could not verify', 'error': True}), 401

    admin = execute_query("SELECT * FROM admins WHERE username = %s", (data.get('username'),), fetch_one=True)
    if not admin:
        return jsonify({'message': 'User tidak ditemukan', 'error': True}), 401
        
    if check_password_hash(admin['password_hash'], data.get('password')):
        token = jwt.encode({'user_id': admin['id'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, current_app.config['SECRET_KEY'], algorithm="HS256")
        execute_query("INSERT INTO system_events (event_type, description) VALUES (%s, %s)", 
                      ("Login", f"Admin {admin['username']} logged in"), commit=True)
        return jsonify({'token': token, 'error': False})
        
    return jsonify({'message': 'Password salah', 'error': True}), 401
