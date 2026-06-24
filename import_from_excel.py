"""
import_from_excel.py
Membaca data historis asli dari file Excel 'Riwayat_Data_Monitoring 13-23.xlsx'
dan memasukkannya ke database MySQL als_energy (tabel sensor_data).
"""
import openpyxl
from datetime import datetime
from database import get_db_connection

EXCEL_PATH = 'dokumen_s/Riwayat_Data_Monitoring 13-23.xlsx'

MONTH_ID = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'Mei': 5, 'Jun': 6,
    'Jul': 7, 'Agu': 8, 'Sep': 9, 'Okt': 10, 'Nov': 11, 'Des': 12
}

def parse_datetime(waktu_str):
    """Parsing format: '13 Apr 2026, 00.00' -> datetime object"""
    try:
        waktu_str = str(waktu_str).strip()
        # Format: '13 Apr 2026, 00.00'
        parts = waktu_str.replace(',', '').split()
        day   = int(parts[0])
        month = MONTH_ID.get(parts[1], 0)
        year  = int(parts[2])
        time_part = parts[3]  # '00.00'
        hour, minute = map(int, time_part.split('.'))
        return datetime(year, month, day, hour, minute, 0)
    except Exception as e:
        return None

def get_mesin_id(mesin_str):
    if 'Mesin 1' in str(mesin_str):
        return 1
    elif 'Mesin 2' in str(mesin_str):
        return 2
    return None

def main():
    print("="*60)
    print("  IMPORT DATA DARI EXCEL KE DATABASE")
    print("="*60)

    print(f"\n[1/3] Membaca file Excel: {EXCEL_PATH} ...")
    wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True, data_only=True)
    ws = wb.active

    data_to_insert = []
    skip_count = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        waktu_str  = row[0]
        mesin_str  = row[1]
        volt       = row[2]
        arus       = row[3]
        daya       = row[4]
        energi     = row[5]
        frekuensi  = row[6]
        pf         = row[7]

        if not waktu_str:
            skip_count += 1
            continue

        dt = parse_datetime(waktu_str)
        mesin_id = get_mesin_id(mesin_str)

        if dt is None or mesin_id is None:
            skip_count += 1
            continue

        val_energi = float(energi or 0)
        if mesin_id == 1:
            val_energi = max(0.0, val_energi - 120.50)
        elif mesin_id == 2:
            val_energi = max(0.0, val_energi - 85.25)

        data_to_insert.append((
            dt.strftime("%Y-%m-%d %H:%M:%S"),
            mesin_id,
            round(float(volt or 0),   2),
            round(float(arus or 0),   3),
            round(float(daya or 0),   2),
            round(val_energi,         3),
            round(float(frekuensi or 0), 2),
            round(float(pf or 0),     2),
        ))

    print(f"    Baris valid ditemukan : {len(data_to_insert)}")
    print(f"    Baris dilewati (error) : {skip_count}")

    print(f"\n[2/3] Menyambung ke database MySQL ...")
    conn = get_db_connection()
    if not conn:
        print("    [ERROR] Gagal konek ke database!")
        return

    cursor = conn.cursor()

    print("    Menghapus data lama di tabel sensor_data (TRUNCATE) ...")
    cursor.execute("TRUNCATE TABLE sensor_data")
    conn.commit()

    print(f"    Memasukkan {len(data_to_insert)} baris data baru ...")
    query = """
        INSERT INTO sensor_data (timestamp, mesin_id, volt, arus, daya, energi, frekuensi, pf)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    batch_size = 1000
    for i in range(0, len(data_to_insert), batch_size):
        batch = data_to_insert[i:i+batch_size]
        cursor.executemany(query, batch)
        conn.commit()
        print(f"    Progress: {min(i+batch_size, len(data_to_insert))}/{len(data_to_insert)} baris ...")

    cursor.close()
    conn.close()

    print(f"\n[3/3] Selesai!")
    print(f"    Total data berhasil dimasukkan: {len(data_to_insert)} baris")
    print("    Silakan jalankan generate_excel_des.py untuk melihat MAPE terbaru.")
    print("="*60)

if __name__ == "__main__":
    main()
