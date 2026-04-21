import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))
from app import app, get_config
from database import execute_query
import jwt
import datetime

config = get_config()
secret = config.get('jwt_secret', 'my_super_secret_key_123')

# Simulate login
admin = execute_query("SELECT * FROM admins WHERE username = 'admin'", fetch_one=True)
print("Admin fetched:", admin)

token = jwt.encode({'user_id': admin['id'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, secret, algorithm="HS256")
print("Token encoded:", token)

# Simulate token_required
try:
    data = jwt.decode(token, secret, algorithms=["HS256"])
    print("Decoded data:", data)
    current_user = execute_query("SELECT id, username FROM admins WHERE id = %s", (data['user_id'],), fetch_one=True)
    print("Current User:", current_user)
except Exception as e:
    print("Decode failed:", e)
