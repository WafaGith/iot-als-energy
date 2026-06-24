import datetime
import random
from database import get_db_connection

def generate_seed_data():
    print("=" * 60)
    print("  SEED DATA: Modifikasi Dataset Mesin Konveksi")
    print("=" * 60)
    
    print("\n[1/3] Menyiapkan parameter dan rentang tanggal...")
    
    # Tanggal spesifik yang diminta (Lama + Baru)
    target_dates = [
        # April 2026 (Lama)
        datetime.date(2026, 4, 13), datetime.date(2026, 4, 14), datetime.date(2026, 4, 15),
        datetime.date(2026, 4, 16), datetime.date(2026, 4, 17), datetime.date(2026, 4, 18),
        datetime.date(2026, 4, 20), datetime.date(2026, 4, 21), datetime.date(2026, 4, 22),
        datetime.date(2026, 4, 24), datetime.date(2026, 4, 25),
        # Mei 2026 (Lama)
        datetime.date(2026, 5, 1), datetime.date(2026, 5, 2), datetime.date(2026, 5, 4),
        datetime.date(2026, 5, 5), datetime.date(2026, 5, 6), datetime.date(2026, 5, 7),
        datetime.date(2026, 5, 8), datetime.date(2026, 5, 9),
        # Mei 2026 (Batch Baru 1: 11 sampai 16)
        datetime.date(2026, 5, 11), datetime.date(2026, 5, 12), datetime.date(2026, 5, 13),
        datetime.date(2026, 5, 14), datetime.date(2026, 5, 15), datetime.date(2026, 5, 16),
        # Mei 2026 (Batch Baru 2: 18 sampai 23)
        datetime.date(2026, 5, 18), datetime.date(2026, 5, 19), datetime.date(2026, 5, 20),
        datetime.date(2026, 5, 21), datetime.date(2026, 5, 22), datetime.date(2026, 5, 23)
    ]
    
    # Energi kumulatif awal
    energi_m1 = 0.0
    energi_m2 = 0.0
    
    data_to_insert = []
    
    print("[2/3] Menghasilkan data untuk tanggal-tanggal terpilih...\n")
    
    # Interval data per 5 menit
    interval_menit = 5
    
    # Melacak status shift malam hari sebelumnya untuk keberlanjutan operasional (00:00 - 01:59)
    prev_m1_shift_malam_aktif = False
    # Melacak lembur larut malam mesin 2 hari sebelumnya (00:00 - 00:59)
    prev_m2_late_overtime_active = False
    
    for tgl in target_dates:
        # Cek kondisi lembur khusus
        is_standard_overtime_day = tgl in [
            datetime.date(2026, 4, 20),
            datetime.date(2026, 5, 9),
            datetime.date(2026, 5, 15),
            datetime.date(2026, 5, 16)
        ]
        
        # Lembur jam 1 malem untuk beberapa hari di tanggal 18-23 (kita ambil tanggal 19, 20, dan 22)
        is_late_overtime_day = tgl in [
            datetime.date(2026, 5, 19),
            datetime.date(2026, 5, 20),
            datetime.date(2026, 5, 22)
        ]
        
        # Penentuan status operasional harian
        if is_standard_overtime_day or is_late_overtime_day:
            m1_shift_malam_aktif = True
            m2_lembur_hari_ini = True
        else:
            m1_shift_malam_aktif = random.choice([True, True, True, False]) # 75% aktif
            m2_lembur_hari_ini = random.choice([True, True, True, False]) # 75% lembur biasa
            
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
            # ==========================================
            daya_m1 = 0.0
            arus_m1 = 0.0
            pf_m1 = 0.0
            
            if hour < 2:  # 00:00 - 01:59 (sisa shift malam hari sebelumnya)
                if prev_m1_shift_malam_aktif:
                    if random.random() < 0.2: # Jeda ganti kain
                        daya_m1 = random.uniform(20, 50)
                        pf_m1 = random.uniform(0.50, 0.60)
                    else:
                        daya_m1 = random.uniform(300, 390)
                        pf_m1 = random.uniform(0.85, 0.90)
                    arus_m1 = daya_m1 / (volt * pf_m1)
            elif 2 <= hour < 8 or (hour == 8 and minute < 10):  # 02:00 - 08:09 (MATI TOTAL)
                daya_m1 = 0.0
                arus_m1 = 0.0
                pf_m1 = 0.0
            elif hour == 8 and 10 <= minute <= 30:  # 08:10 - 08:30 (lonjakan startup)
                daya_m1 = random.uniform(900, 1083)
                pf_m1 = random.uniform(0.90, 0.95)
                arus_m1 = daya_m1 / (volt * pf_m1)
            elif (hour == 8 and minute > 30) or (9 <= hour < 12):  # 08:31 - 11:59 (produksi aktif pagi)
                if random.random() < 0.2: # Jeda ganti kain
                    daya_m1 = random.uniform(20, 50)
                    pf_m1 = random.uniform(0.50, 0.60)
                else:
                    daya_m1 = random.uniform(300, 390)
                    pf_m1 = random.uniform(0.85, 0.90)
                arus_m1 = daya_m1 / (volt * pf_m1)
            elif 12 <= hour < 13:  # 12:00 - 12:59 (istirahat siang)
                daya_m1 = 0.0
                arus_m1 = 0.0
                pf_m1 = 0.0
            elif 13 <= hour < 17:  # 13:00 - 16:59 (produksi aktif siang)
                if random.random() < 0.2: # Jeda ganti kain
                    daya_m1 = random.uniform(20, 50)
                    pf_m1 = random.uniform(0.50, 0.60)
                else:
                    daya_m1 = random.uniform(300, 390)
                    pf_m1 = random.uniform(0.85, 0.90)
                arus_m1 = daya_m1 / (volt * pf_m1)
            elif 17 <= hour < 18:  # 17:00 - 17:59 (istirahat sore)
                daya_m1 = 0.0
                arus_m1 = 0.0
                pf_m1 = 0.0
            elif 18 <= hour <= 23:  # 18:00 - 23:59 (shift malam aktif)
                if m1_shift_malam_aktif:
                    if hour == 18 and minute <= 30:  # 18:00 - 18:30 (lonjakan startup shift 2)
                        # Buat peluang muncul angka presisi tinggi mendekati 1083
                        daya_m1 = random.uniform(1000, 1083)
                        pf_m1 = random.uniform(0.90, 0.95)
                    else:
                        if random.random() < 0.2: # Jeda ganti kain
                            daya_m1 = random.uniform(20, 50)
                            pf_m1 = random.uniform(0.50, 0.60)
                        else:
                            daya_m1 = random.uniform(300, 390)
                            pf_m1 = random.uniform(0.85, 0.90)
                    arus_m1 = daya_m1 / (volt * pf_m1)
            
            energi_m1 += (daya_m1 / 1000.0) * (interval_menit / 60.0)
            
            data_to_insert.append((
                current_time.strftime("%Y-%m-%d %H:%M:%S"),
                1, round(volt, 2), round(arus_m1, 3), round(daya_m1, 2),
                round(energi_m1, 3), round(freq, 2), round(pf_m1, 2)
            ))
            
            # ==========================================
            # MESIN 2: Mesin Jahit Juki
            # ==========================================
            daya_m2 = 0.0
            arus_m2 = 0.0
            pf_m2 = 0.0
            
            if hour < 1:  # 00:00 - 00:59 (carry-over lembur sampai jam 1 malem)
                if prev_m2_late_overtime_active:
                    daya_m2 = random.uniform(180, 200)
                    pf_m2 = random.uniform(0.85, 0.92)
                    arus_m2 = daya_m2 / (volt * pf_m2)
            elif 1 <= hour < 9:  # 01:00 - 08:59 (MATI TOTAL)
                daya_m2 = 0.0
                arus_m2 = 0.0
                pf_m2 = 0.0
            elif hour == 9 and minute < 30:  # 09:00 - 09:29 (lonjakan startup)
                daya_m2 = random.uniform(150, 250)
                pf_m2 = random.uniform(0.75, 0.85)
                arus_m2 = daya_m2 / (volt * pf_m2)
            elif 9 <= hour < 12:  # 09:30 - 11:59 (produksi normal)
                daya_m2 = random.uniform(180, 200)
                pf_m2 = random.uniform(0.75, 0.85)
                arus_m2 = daya_m2 / (volt * pf_m2)
            elif 12 <= hour < 13:  # 12:00 - 12:59 (istirahat siang)
                daya_m2 = 0.0
                arus_m2 = 0.0
                pf_m2 = 0.0
            elif hour == 13 and minute < 30:  # 13:00 - 13:29 (lonjakan siang)
                daya_m2 = random.uniform(150, 250)
                pf_m2 = random.uniform(0.75, 0.88)
                arus_m2 = daya_m2 / (volt * pf_m2)
            elif 13 <= hour < 17:  # 13:30 - 16:59 (produksi aktif normal)
                daya_m2 = random.uniform(180, 200)
                pf_m2 = random.uniform(0.75, 0.88)
                arus_m2 = daya_m2 / (volt * pf_m2)
            elif 17 <= hour < 20:  # 17:00 - 19:59 (lembur biasa / high speed)
                if m2_lembur_hari_ini:
                    if hour == 17 and minute < 30:
                        daya_m2 = random.uniform(150, 250)
                    else:
                        daya_m2 = random.uniform(180, 200)
                    pf_m2 = random.uniform(0.85, 0.92)
                    arus_m2 = daya_m2 / (volt * pf_m2)
            elif 20 <= hour <= 23:  # 20:00 - 23:59
                if is_late_overtime_day:  # Lembur sampai jam 1 malem (terus beroperasi)
                    daya_m2 = random.uniform(180, 200)
                    pf_m2 = random.uniform(0.85, 0.92)
                    arus_m2 = daya_m2 / (volt * pf_m2)
                elif is_standard_overtime_day and hour < 23:  # Lembur sampai jam 11 malem (23:00)
                    daya_m2 = random.uniform(180, 200)
                    pf_m2 = random.uniform(0.85, 0.92)
                    arus_m2 = daya_m2 / (volt * pf_m2)
            
            # Tambahkan increment energi mesin 2 (fixing bug dari file seed awal)
            energi_m2 += (daya_m2 / 1000.0) * (interval_menit / 60.0)
            
            data_to_insert.append((
                current_time.strftime("%Y-%m-%d %H:%M:%S"),
                2, round(volt, 2), round(arus_m2, 3), round(daya_m2, 2),
                round(energi_m2, 3), round(freq, 2), round(pf_m2, 2)
            ))
            
            current_time += datetime.timedelta(minutes=interval_menit)
            
        # Update status kemarin untuk iterasi hari berikutnya
        prev_m1_shift_malam_aktif = m1_shift_malam_aktif
        prev_m2_late_overtime_active = is_late_overtime_day

    total_data = len(data_to_insert)
    print(f"  Total data yang disiapkan: {total_data} baris")
    print(f"\n[3/3] Membersihkan data lama & menyisipkan ke database MySQL...")
    
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
    print("\n  Data siap digunakan!")

if __name__ == "__main__":
    generate_seed_data()
