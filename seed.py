import datetime
import random
from database import execute_query

def generate_seed_data():
    """
    Simulasi data sensor listrik untuk Usaha Konveksi Rumahan
    =========================================================
    Mesin 1: Mesin Jahit Industri (Juki DDL-8700) ~ 250-550 Watt saat aktif
    Mesin 2: Mesin Obras/Overlock (Juki MO-6814S) ~ 350-750 Watt saat aktif
    
    Pola Operasional (7 Hari):
    - Hari 1-4 (Senin-Kamis): Normal, kerja 08:00 - 16:00
    - Hari 5-7 (Jumat-Minggu): Lembur kejar deadline, kerja 07:00 - 22:00
    
    Tegangan PLN Indonesia: ~218-225V
    Frekuensi PLN: ~49.8-50.2 Hz
    """
    
    print("=" * 60)
    print("  SEED DATA: Simulasi Usaha Konveksi Rumahan")
    print("=" * 60)
    
    print("\n[1/3] Membersihkan data sensor lama...")
    execute_query("TRUNCATE TABLE sensor_data", commit=True)
    
    end_time = datetime.datetime.now()
    start_time = end_time - datetime.timedelta(days=7)
    
    current_time = start_time
    total_data = 0
    
    # Energi kumulatif awal (kWh) - seolah meter sudah berjalan
    energi_m1 = 45.30   # Mesin jahit
    energi_m2 = 68.75   # Mesin obras
    
    data_to_insert = []
    
    print("[2/3] Menghasilkan data historis 7 hari terakhir...\n")
    
    while current_time < end_time:
        day_offset = (current_time - start_time).days
        is_overtime = day_offset >= 4   # Hari ke-5,6,7 = lembur
        
        hour = current_time.hour
        minute = current_time.minute
        
        # === Pola Jam Kerja Konveksi ===
        is_active = False
        is_peak = False     # Jam sibuk (siang, banyak jahitan)
        is_startup = False  # Pemanasan mesin
        
        if is_overtime:
            # LEMBUR: 07:00 - 22:00
            if 7 <= hour < 22:
                is_active = True
            if 10 <= hour < 12 or 14 <= hour < 17:
                is_peak = True
            if 7 <= hour < 8:
                is_startup = True
        else:
            # NORMAL: 08:00 - 16:00
            if 8 <= hour < 16:
                is_active = True
            if 10 <= hour < 12 or 13 <= hour < 15:
                is_peak = True
            if 8 <= hour < 9:
                is_startup = True
        
        # Istirahat makan siang (12:00 - 13:00) mesin standby
        is_lunch = (12 <= hour < 13)
        
        # === MESIN 1: Mesin Jahit Industri ===
        freq = random.uniform(49.85, 50.15)
        
        if is_active and not is_lunch:
            if is_startup:
                # Pemanasan awal, beban ringan
                volt_m1 = random.uniform(219.0, 223.0)
                arus_m1 = random.uniform(0.8, 1.5)
                pf_m1 = random.uniform(0.72, 0.80)
            elif is_peak:
                # Jam sibuk - jahit kain tebal, banyak order
                volt_m1 = random.uniform(216.0, 222.0)
                arus_m1 = random.uniform(1.8, 2.8)
                pf_m1 = random.uniform(0.82, 0.90)
            else:
                # Aktif biasa
                volt_m1 = random.uniform(218.0, 223.0)
                arus_m1 = random.uniform(1.2, 2.2)
                pf_m1 = random.uniform(0.78, 0.88)
        elif is_lunch and is_active:
            # Istirahat siang - mesin idle tapi nyala
            volt_m1 = random.uniform(220.0, 224.0)
            arus_m1 = random.uniform(0.15, 0.30)
            pf_m1 = random.uniform(0.45, 0.55)
        else:
            # Mati / standby malam
            volt_m1 = random.uniform(221.0, 225.0)
            arus_m1 = random.uniform(0.02, 0.08)
            pf_m1 = random.uniform(0.30, 0.45)
        
        daya_m1 = volt_m1 * arus_m1 * pf_m1
        # Tambah sedikit noise realistis
        daya_m1 *= random.uniform(0.95, 1.05)
        energi_m1 += (daya_m1 / 1000.0) * (10 / 60)  # 10 menit = 10/60 jam
        
        data_to_insert.append((
            current_time.strftime("%Y-%m-%d %H:%M:%S"),
            1, round(volt_m1, 2), round(arus_m1, 3), round(daya_m1, 2),
            round(energi_m1, 3), round(freq, 2), round(pf_m1, 2)
        ))
        
        # === MESIN 2: Mesin Obras / Overlock ===
        if is_active and not is_lunch:
            if is_startup:
                volt_m2 = random.uniform(217.0, 222.0)
                arus_m2 = random.uniform(1.2, 2.0)
                pf_m2 = random.uniform(0.75, 0.82)
            elif is_peak:
                # Obras jalan terus saat peak - beban lebih berat
                volt_m2 = random.uniform(214.0, 220.0)
                arus_m2 = random.uniform(2.5, 3.8)
                pf_m2 = random.uniform(0.85, 0.93)
            else:
                volt_m2 = random.uniform(216.0, 222.0)
                arus_m2 = random.uniform(1.8, 3.0)
                pf_m2 = random.uniform(0.80, 0.90)
        elif is_lunch and is_active:
            volt_m2 = random.uniform(220.0, 224.0)
            arus_m2 = random.uniform(0.10, 0.25)
            pf_m2 = random.uniform(0.42, 0.52)
        else:
            volt_m2 = random.uniform(221.0, 225.0)
            arus_m2 = random.uniform(0.03, 0.10)
            pf_m2 = random.uniform(0.32, 0.48)
        
        daya_m2 = volt_m2 * arus_m2 * pf_m2
        daya_m2 *= random.uniform(0.95, 1.05)
        energi_m2 += (daya_m2 / 1000.0) * (10 / 60)
        
        data_to_insert.append((
            current_time.strftime("%Y-%m-%d %H:%M:%S"),
            2, round(volt_m2, 2), round(arus_m2, 3), round(daya_m2, 2),
            round(energi_m2, 3), round(freq, 2), round(pf_m2, 2)
        ))
        
        current_time += datetime.timedelta(minutes=10)
        total_data += 2
    
    print(f"  Total data yang disiapkan: {total_data} baris")
    print(f"  Rentang waktu: {start_time.strftime('%Y-%m-%d %H:%M')} s/d {end_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"\n[3/3] Menyisipkan ke database MySQL... (mohon tunggu)")
    
    for index, row in enumerate(data_to_insert):
        execute_query(
            "INSERT INTO sensor_data (timestamp, mesin_id, volt, arus, daya, energi, frekuensi, pf) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            row, commit=True
        )
        if (index + 1) % 500 == 0:
            print(f"  > Terinput {index + 1} / {total_data} data...")
    
    print(f"\n{'=' * 60}")
    print(f"  SELESAI! {total_data} data berhasil dimasukkan.")
    print(f"  Mesin 1 (Jahit)  - Energi akhir: {energi_m1:.3f} kWh")
    print(f"  Mesin 2 (Obras)  - Energi akhir: {energi_m2:.3f} kWh")
    print(f"{'=' * 60}")
    print("\n  Silakan buka menu Prediksi AI di dashboard Anda!")

if __name__ == "__main__":
    generate_seed_data()
