import datetime
import random
from database import get_db_connection

def generate_seed_data():
    print("=" * 60)
    print("  SEED DATA: Modifikasi Dataset Mesin Konveksi")
    print("=" * 60)
    
    print("\n[1/3] Menyiapkan parameter dan rentang tanggal...")
    
    # 19 Tanggal spesifik yang diminta
    target_dates = [
        datetime.date(2026, 4, 13), datetime.date(2026, 4, 14), datetime.date(2026, 4, 15),
        datetime.date(2026, 4, 16), datetime.date(2026, 4, 17), datetime.date(2026, 4, 18),
        datetime.date(2026, 4, 20), datetime.date(2026, 4, 21), datetime.date(2026, 4, 22),
        datetime.date(2026, 4, 24), datetime.date(2026, 4, 25), datetime.date(2026, 5, 1),
        datetime.date(2026, 5, 2), datetime.date(2026, 5, 4), datetime.date(2026, 5, 5),
        datetime.date(2026, 5, 6), datetime.date(2026, 5, 7), datetime.date(2026, 5, 8),
        datetime.date(2026, 5, 9)
    ]
    
    # Energi kumulatif awal
    energi_m1 = 120.50
    energi_m2 = 85.25
    
    data_to_insert = []
    
    print("[2/3] Menghasilkan data untuk tanggal-tanggal terpilih...\n")
    
    # Interval data per 5 menit untuk keseimbangan detail & performa
    # 5 menit = 288 baris per hari per mesin
    interval_menit = 5
    
    for tgl in target_dates:
        # Variasi agar dataset terlihat realistis (tidak setiap hari sama persis)
        m2_lembur_hari_ini = random.choice([True, True, True, False]) # Mesin 2 lembur 75%
        m1_shift_malam_aktif = random.choice([True, True, True, False]) # Mesin 1 shift malam 75%
        
        current_time = datetime.datetime(tgl.year, tgl.month, tgl.day, 0, 0, 0)
        end_time = current_time + datetime.timedelta(days=1)
        
        while current_time < end_time:
            hour = current_time.hour
            minute = current_time.minute
            
            # === PARAMETER UMUM PLN ===
            volt = random.uniform(210.0, 230.0)
            freq = random.uniform(49.8, 50.2)
            
            # ==========================================
            # MESIN 1: Mesin Bordir (2 Shift)
            # Mati total di luar jam operasional (02:00 - 08:59)
            # ==========================================
            daya_m1 = 0.0
            arus_m1 = 0.0
            pf_m1 = 0.0
            
            if hour < 2:  # 00:00 - 01:59 (sisa shift malam hari sebelumnya)
                if m1_shift_malam_aktif:
                    daya_m1 = random.uniform(400, 600)
                    pf_m1 = random.uniform(0.85, 0.90)
                    arus_m1 = daya_m1 / (volt * pf_m1)
                # else: mesin mati total, daya/arus/pf = 0
            elif 2 <= hour < 9:  # 02:00 - 08:59 (MATI TOTAL, tidak ada karyawan)
                daya_m1 = 0.0
                arus_m1 = 0.0
                pf_m1 = 0.0
            elif hour == 9 and minute < 30:  # 09:00 - 09:29 (lonjakan startup)
                daya_m1 = random.uniform(1000, 1330)
                pf_m1 = random.uniform(0.90, 0.95)
                arus_m1 = daya_m1 / (volt * pf_m1)
            elif 9 <= hour < 12:  # 09:30 - 11:59 (produksi aktif pagi)
                daya_m1 = random.uniform(400, 600)
                pf_m1 = random.uniform(0.85, 0.90)
                arus_m1 = daya_m1 / (volt * pf_m1)
            elif 12 <= hour < 13:  # 12:00 - 12:59 (istirahat siang, mesin mati)
                daya_m1 = 0.0
                arus_m1 = 0.0
                pf_m1 = 0.0
            elif 13 <= hour < 17:  # 13:00 - 16:59 (produksi aktif siang)
                daya_m1 = random.uniform(400, 600)
                pf_m1 = random.uniform(0.85, 0.90)
                arus_m1 = daya_m1 / (volt * pf_m1)
            elif 17 <= hour < 18:  # 17:00 - 17:59 (istirahat sebelum shift malam)
                daya_m1 = 0.0
                arus_m1 = 0.0
                pf_m1 = 0.0
            elif 18 <= hour <= 23:  # 18:00 - 23:59 (shift malam aktif s/d jam 02:00)
                if m1_shift_malam_aktif:
                    if random.random() < 0.1:  # 10% peluang lonjakan (mulai jarum)
                        daya_m1 = random.uniform(1000, 1330)
                        pf_m1 = random.uniform(0.90, 0.95)
                    else:
                        daya_m1 = random.uniform(400, 600)
                        pf_m1 = random.uniform(0.85, 0.90)
                    arus_m1 = daya_m1 / (volt * pf_m1)
                # else: mesin mati total
            
            energi_m1 += (daya_m1 / 1000.0) * (interval_menit / 60.0)
            
            data_to_insert.append((
                current_time.strftime("%Y-%m-%d %H:%M:%S"),
                1, round(volt, 2), round(arus_m1, 3), round(daya_m1, 2),
                round(energi_m1, 3), round(freq, 2), round(pf_m1, 2)
            ))
            
            # ==========================================
            # MESIN 2: Mesin Jahit Juki
            # Mati total di luar jam kerja (00:00–08:59 dan 20:00–23:59)
            # ==========================================
            daya_m2 = 0.0
            arus_m2 = 0.0
            pf_m2 = 0.0
            
            if 0 <= hour < 9:  # 00:00 - 08:59 (MATI TOTAL, belum ada karyawan)
                daya_m2 = 0.0
                arus_m2 = 0.0
                pf_m2 = 0.0
            elif 9 <= hour < 12:  # 09:00 - 11:59 (produksi normal)
                daya_m2 = random.uniform(100, 200)
                pf_m2 = random.uniform(0.75, 0.85)
                arus_m2 = daya_m2 / (volt * pf_m2)
            elif 12 <= hour < 13:  # 12:00 - 12:59 (istirahat siang, mesin mati)
                daya_m2 = 0.0
                arus_m2 = 0.0
                pf_m2 = 0.0
            elif 13 <= hour < 17:  # 13:00 - 16:59 (produksi aktif normal)
                daya_m2 = random.uniform(100, 250)
                pf_m2 = random.uniform(0.75, 0.88)
                arus_m2 = daya_m2 / (volt * pf_m2)
            elif 17 <= hour < 20:  # 17:00 - 19:59 (lembur / high speed)
                if m2_lembur_hari_ini:
                    daya_m2 = random.uniform(250, 500)
                    pf_m2 = random.uniform(0.85, 0.92)
                    arus_m2 = daya_m2 / (volt * pf_m2)
                # else: mesin mati total
            elif 20 <= hour <= 23:  # 20:00 - 23:59 (MATI TOTAL, karyawan sudah pulang)
                daya_m2 = 0.0
                arus_m2 = 0.0
                pf_m2 = 0.0
            
            data_to_insert.append((
                current_time.strftime("%Y-%m-%d %H:%M:%S"),
                2, round(volt, 2), round(arus_m2, 3), round(daya_m2, 2),
                round(energi_m2, 3), round(freq, 2), round(pf_m2, 2)
            ))
            
            current_time += datetime.timedelta(minutes=interval_menit)

    total_data = len(data_to_insert)
    print(f"  Total data yang disiapkan: {total_data} baris")
    print(f"\n[3/3] Membersihkan data lama & menyisipkan ke database MySQL... (mohon tunggu, executemany berjalan)")
    
    # Gunakan koneksi langsung untuk executemany agar super cepat (10k+ baris)
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            print(f"  Koneksi database berhasil. Memulai TRUNCATE...")
            cursor.execute("TRUNCATE TABLE sensor_data")
            conn.commit()
            print(f"  Data lama dihapus. Memasukkan {total_data} baris baru...")
            
            query = "INSERT INTO sensor_data (timestamp, mesin_id, volt, arus, daya, energi, frekuensi, pf) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            cursor.executemany(query, data_to_insert)
            conn.commit()
            cursor.close()
            conn.close()
        else:
            print("  [ERROR] Gagal koneksi ke database. Periksa konfigurasi settings.json.")
            return
    except Exception as e:
        print(f"  [ERROR] Terjadi kesalahan saat menyisipkan data: {e}")
        return
            
    print(f"\n{'=' * 60}")
    print(f"  SELESAI! {total_data} data berhasil dimasukkan dalam hitungan detik.")
    print(f"  Mesin 1 (Bordir) - Energi akhir: {energi_m1:.3f} kWh")
    print(f"  Mesin 2 (Jahit)  - Energi akhir: {energi_m2:.3f} kWh")
    print(f"{'=' * 60}")
    print("\n  Data siap digunakan untuk evaluasi Double Exponential Smoothing (DES)!")

if __name__ == "__main__":
    generate_seed_data()
