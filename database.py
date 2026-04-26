import mysql.connector
from mysql.connector import Error
import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config', 'settings.json')

def get_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def get_db_connection():
    config = get_config()
    try:
        connection = mysql.connector.connect(
            host=config.get('db_host', 'localhost'),
            user=config.get('db_user', 'root'),
            password=config.get('db_password', ''),
            database=config.get('db_name', 'als_energy')
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None

def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    connection = get_db_connection()
    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)
    result = None
    try:
        cursor.execute(query, params)
        if commit:
            connection.commit()
            result = cursor.lastrowid
        elif fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
    except Error as e:
        print(f"Error executing query: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    return result

def init_default_admin():
    from werkzeug.security import generate_password_hash
    admin = execute_query("SELECT * FROM admins WHERE username = 'admin'", fetch_one=True)
    if not admin:
        hashed_password = generate_password_hash('password123')
        execute_query(
            "INSERT INTO admins (username, password_hash) VALUES (%s, %s)",
            ('admin', hashed_password),
            commit=True
        )
        print("Default admin created (admin / password123)")
