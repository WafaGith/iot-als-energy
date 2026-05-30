import os
import sys
from database import get_db_connection

def setup_mesin():
    conn = get_db_connection()
    if not conn:
        print("Gagal terhubung ke database.")
        sys.exit(1)
        
    cursor = conn.cursor()
    
    try:
        print("1. Membuat tabel 'mesin'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mesin (
                id_mesin INT PRIMARY KEY,
                nama_mesin VARCHAR(100),
                status VARCHAR(50)
            )
        """)
        
        print("2. Memasukkan data mesin...")
        cursor.execute("""
            INSERT IGNORE INTO mesin (id_mesin, nama_mesin, status) 
            VALUES 
            (1, 'Mesin Bordir', 'Aktif'),
            (2, 'Mesin Jahit Juki', 'Aktif')
        """)
        
        conn.commit()
        print("Selesai! Tabel 'mesin' berhasil dibuat dan data berhasil dimasukkan.")
        
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    setup_mesin()
