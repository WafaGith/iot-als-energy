import mysql.connector
import os
import json

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'settings.json')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')

with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

print("Mulai proses migrasi database...")
try:
    # Konek tanpa database parameter terlebih dahulu
    connection = mysql.connector.connect(
        host=config.get('db_host', 'localhost'),
        user=config.get('db_user', 'root'),
        password=config.get('db_password', '')
    )
    cursor = connection.cursor()

    # Baca file SQL
    with open(SCHEMA_PATH, 'r') as file:
        sql_script = file.read()
    
    # Eksekusi blok statement SQL 
    for statement in sql_script.split(';'):
        if statement.strip():
            cursor.execute(statement)

    connection.commit()
    print("Migrasi Database berhasil! Tabel telah terbentuk di database 'als_energy'")
    
except mysql.connector.Error as e:
    print(f"Error Database MYSQL: {e}")
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'connection' in locals() and connection.is_connected():
        cursor.close()
        connection.close()
