from flask import Blueprint, request, jsonify
import datetime
from database import execute_query
from utils import send_telegram_alert

sensor_bp = Blueprint('sensor_bp', __name__)

@sensor_bp.route('/data', methods=['POST'])
def receive_sensor_data():
    data = request.get_json()
    if not data: 
        return jsonify({"message": "No data provided"}), 400
        
    try:
        # Update Cache Real-time (In-Memory)
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        now_time_str = datetime.datetime.now().strftime("%H:%M:%S")
        from database import latest_sensor_data, sensor_history
        
        if 'm1' in data:
            m1 = data['m1']
            latest_sensor_data['m1'] = {
                "timestamp": now_str,
                "mesin_id": 1,
                "volt": m1.get('v', 0),
                "arus": m1.get('i', 0),
                "daya": m1.get('p', 0),
                "energi": m1.get('e', 0),
                "frekuensi": m1.get('f', 0),
                "pf": m1.get('pf', 0)
            }
            # Tambahkan ke rolling history untuk grafik real-time
            sensor_history['m1'].append({
                "timestamp": now_time_str,
                "volt": m1.get('v', 0),
                "arus": m1.get('i', 0),
                "daya": m1.get('p', 0),
                "frekuensi": m1.get('f', 0),
                "pf": m1.get('pf', 0)
            })
        if 'm2' in data:
            m2 = data['m2']
            latest_sensor_data['m2'] = {
                "timestamp": now_str,
                "mesin_id": 2,
                "volt": m2.get('v', 0),
                "arus": m2.get('i', 0),
                "daya": m2.get('p', 0),
                "energi": m2.get('e', 0),
                "frekuensi": m2.get('f', 0),
                "pf": m2.get('pf', 0)
            }
            # Tambahkan ke rolling history untuk grafik real-time
            sensor_history['m2'].append({
                "timestamp": now_time_str,
                "volt": m2.get('v', 0),
                "arus": m2.get('i', 0),
                "daya": m2.get('p', 0),
                "frekuensi": m2.get('f', 0),
                "pf": m2.get('pf', 0)
            })

        # --- SIMPAN KE CACHE FILE UNTUK BOT TELEGRAM (INTER-PROCESS COMMS) ---
        import json
        import os
        cache_path = os.path.join(os.path.dirname(__file__), '..', 'realtime_cache.json')
        try:
            with open(cache_path, 'w') as f:
                json.dump(latest_sensor_data, f)
        except Exception as e:
            print("Gagal menulis cache:", e)

        # --- DETEKSI PEMADAMAN LISTRIK & PEMULIHAN PLN ---
        m1_v = data.get('m1', {}).get('v', -1) if 'm1' in data else -1
        m2_v = data.get('m2', {}).get('v', -1) if 'm2' in data else -1
        
        if m1_v != -1 and m2_v != -1: # Pastikan sensor memberikan data volt
            # Cek status notifikasi PLN terakhir
            last_pln_notif = execute_query("SELECT message FROM notifications WHERE message LIKE '%%PEMADAMAN LISTRIK%%' OR message LIKE '%%LISTRIK PLN KEMBALI%%' ORDER BY timestamp DESC LIMIT 1", fetch_one=True)
            last_is_padam = last_pln_notif and "PEMADAMAN LISTRIK" in last_pln_notif['message']
            
            if m1_v == 0 and m2_v == 0:
                # PLN MATI
                if not last_is_padam:
                    msg_text = "🚨 <b>PERINGATAN: PEMADAMAN LISTRIK (PLN MATI)</b> 🚨\n\nSensor mendeteksi tegangan 0 Volt pada mesin. Kemungkinan besar sedang terjadi pemadaman listrik."
                    status, text_res = send_telegram_alert(msg_text)
                    execute_query("INSERT INTO notifications (message, status) VALUES (%s, %s)", (msg_text, status + ": " + text_res[:40]), commit=True)
            elif m1_v > 50 or m2_v > 50:
                # PLN MENYALA
                if last_is_padam:
                    msg_text = "✅ <b>INFO: LISTRIK PLN KEMBALI MENYALA</b> ✅\n\nTegangan listrik PLN telah terdeteksi kembali normal pada sensor."
                    status, text_res = send_telegram_alert(msg_text)
                    execute_query("INSERT INTO notifications (message, status) VALUES (%s, %s)", (msg_text, status + ": " + text_res[:40]), commit=True)

        # --- DETEKSI ESP KEMBALI ONLINE ---
        try:
            # Jika kita menerima data (apapun itu), artinya ESP sedang online.
            # Kita cek apakah notifikasi terakhir adalah peringatan OFFLINE.
            last_conn_notif = execute_query("SELECT message FROM notifications WHERE message LIKE '%%ESP32 OFFLINE%%' OR message LIKE '%%SISTEM KEMBALI ONLINE%%' ORDER BY timestamp DESC LIMIT 1", fetch_one=True)
            
            if last_conn_notif and "ESP32 OFFLINE" in last_conn_notif['message']:
                # Harus mengecek apakah telegram aktif terlebih dahulu
                settings_data = execute_query("SELECT setting_value FROM settings WHERE setting_key='telegram_active'", fetch_one=True)
                if settings_data and str(settings_data['setting_value']) == '1':
                    msg_text = "✅ <b>SISTEM KEMBALI ONLINE</b> ✅\n\nKoneksi dengan ESP32 telah pulih. Sistem kembali menerima data sensor dengan normal."
                    status, text_res = send_telegram_alert(msg_text)
                    execute_query("INSERT INTO notifications (message, status) VALUES (%s, %s)", (msg_text, status + ": " + text_res[:40]), commit=True)
        except Exception as e:
            pass

        # Hanya simpan ke DB dan jalankan alert jika parameter 'save' bernilai True
        if data.get('save') == True:


            if 'm1' in data:
                m1 = data['m1']
                execute_query("INSERT INTO sensor_data (mesin_id, volt, arus, daya, energi, frekuensi, pf) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                              (1, m1.get('v',0), m1.get('i',0), m1.get('p',0), m1.get('e',0), m1.get('f',0), m1.get('pf',0)), commit=True)
            if 'm2' in data:
                m2 = data['m2']
                execute_query("INSERT INTO sensor_data (mesin_id, volt, arus, daya, energi, frekuensi, pf) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                              (2, m2.get('v',0), m2.get('i',0), m2.get('p',0), m2.get('e',0), m2.get('f',0), m2.get('pf',0)), commit=True)
                
            try:
                settings_data = execute_query("SELECT * FROM settings", fetch_all=True)
                cfg = {item['setting_key']: item['setting_value'] for item in settings_data}
                if str(cfg.get('telegram_active', '0')) == '1':
                    kuota = float(cfg.get('kuota_energi', 100.0))
                    batas = float(cfg.get('batas_sisa_energi', 10.0))
                    
                    latest_m1 = execute_query("SELECT energi FROM sensor_data WHERE mesin_id=1 ORDER BY timestamp DESC LIMIT 1", fetch_one=True)
                    latest_m2 = execute_query("SELECT energi FROM sensor_data WHERE mesin_id=2 ORDER BY timestamp DESC LIMIT 1", fetch_one=True)
                    total_energi = (latest_m1['energi'] if latest_m1 else 0) + (latest_m2['energi'] if latest_m2 else 0)
                    sisa = kuota - total_energi
                    
                    if sisa <= batas:
                        last_notif = execute_query("SELECT timestamp FROM notifications WHERE message LIKE '%%Peringatan Kuota%%' ORDER BY timestamp DESC LIMIT 1", fetch_one=True)
                        send_it = True
                        if last_notif and last_notif['timestamp']:
                            if (datetime.datetime.now() - last_notif['timestamp']).total_seconds() < 3600:
                                send_it = False
                        if send_it:
                            msg_text = f"⚠️ <b>PERINGATAN KUOTA ENERGI</b> ⚠️\n\nSisa Kuota Listrik Anda menipis!\n\n<b>Sisa Saat Ini:</b> {sisa:.2f} kWh\n<b>Total Kuota:</b> {kuota:.2f} kWh\n<b>Batas Peringatan:</b> {batas:.2f} kWh\n\nSegera lakukan pengisian ulang untuk menghindari pemadaman."
                            status, text_res = send_telegram_alert(msg_text)
                            execute_query("INSERT INTO notifications (message, status) VALUES (%s, %s)", (msg_text, status + ": " + text_res[:40]), commit=True)
                    m1_active = 'm1' in data and data['m1'].get('p', 0) > 5
                    m2_active = 'm2' in data and data['m2'].get('p', 0) > 5

                    # Check: Pemberitahuan Awal Kerja (First start of the day)
                    if m1_active or m2_active:
                        today_date = datetime.datetime.now().strftime("%Y-%m-%d")
                        last_awal_kerja = execute_query("SELECT timestamp FROM notifications WHERE message LIKE '%%AWAL KERJA%%' AND DATE(timestamp) = %s LIMIT 1", (today_date,), fetch_one=True)
                        
                        if not last_awal_kerja:
                            active_machines = []
                            if m1_active: active_machines.append("Mesin 1")
                            if m2_active: active_machines.append("Mesin 2")
                            
                            msg_text = f"🌅 <b>PEMBERITAHUAN AWAL KERJA</b> 🌅\n\nSelamat beraktivitas!\n{' dan '.join(active_machines)} telah mulai dihidupkan pada pukul {datetime.datetime.now().strftime('%H:%M')}.\nSemoga operasional hari ini berjalan lancar."
                            status, text_res = send_telegram_alert(msg_text)
                            execute_query("INSERT INTO notifications (message, status) VALUES (%s, %s)", (msg_text, status + ": " + text_res[:40]), commit=True)

                    # Check 2: Di Luar Jam Kerja
                    jam_mulai = cfg.get('jam_kerja_mulai', '')
                    jam_selesai = cfg.get('jam_kerja_selesai', '')
                    if jam_mulai and jam_selesai:
                        now_time = datetime.datetime.now().time()
                        try:
                            t_mulai = datetime.datetime.strptime(jam_mulai, "%H:%M").time()
                            t_selesai = datetime.datetime.strptime(jam_selesai, "%H:%M").time()
                            
                            is_outside_hours = False
                            if t_mulai <= t_selesai:
                                if now_time < t_mulai or now_time > t_selesai: is_outside_hours = True
                            else: # crosses midnight
                                if now_time < t_mulai and now_time > t_selesai: is_outside_hours = True
                                
                            if is_outside_hours and (m1_active or m2_active):
                                last_notif_jam = execute_query("SELECT timestamp FROM notifications WHERE message LIKE '%%luar jam operasional%%' ORDER BY timestamp DESC LIMIT 1", fetch_one=True)
                                send_it = True
                                if last_notif_jam and last_notif_jam['timestamp']:
                                    if (datetime.datetime.now() - last_notif_jam['timestamp']).total_seconds() < 3600: # Max 1x per jam
                                        send_it = False
                                if send_it:
                                    msgs = []
                                    if m1_active: msgs.append("Mesin 1")
                                    if m2_active: msgs.append("Mesin 2")
                                    msg_text = f"⚠️ <b>PERINGATAN LUAR JAM KERJA</b> ⚠️\n\n{' dan '.join(msgs)} terdeteksi aktif di luar jam operasional ({jam_mulai} - {jam_selesai})."
                                    status, text_res = send_telegram_alert(msg_text)
                                    execute_query("INSERT INTO notifications (message, status) VALUES (%s, %s)", (msg_text, status + ": " + text_res[:40]), commit=True)
                        except Exception as e:
                            pass
                    
                    # Check 3: Batas Harian
                    try:
                        batas_harian = float(cfg.get('batas_harian_kwh', 0))
                        if batas_harian > 0:
                            today = datetime.datetime.now().strftime("%Y-%m-%d")
                            
                            # Ambil energi awal hari ini untuk M1
                            m1_midnight = execute_query("SELECT energi FROM sensor_data WHERE mesin_id=1 AND timestamp >= %s ORDER BY timestamp ASC LIMIT 1", (today + " 00:00:00",), fetch_one=True)
                            e1_start = m1_midnight['energi'] if m1_midnight else (latest_m1['energi'] if latest_m1 else 0)
                            
                            # Ambil energi awal hari ini untuk M2
                            m2_midnight = execute_query("SELECT energi FROM sensor_data WHERE mesin_id=2 AND timestamp >= %s ORDER BY timestamp ASC LIMIT 1", (today + " 00:00:00",), fetch_one=True)
                            e2_start = m2_midnight['energi'] if m2_midnight else (latest_m2['energi'] if latest_m2 else 0)
                            
                            e1_now = latest_m1['energi'] if latest_m1 else 0
                            e2_now = latest_m2['energi'] if latest_m2 else 0
                            
                            usage_today = max(0, e1_now - e1_start) + max(0, e2_now - e2_start)
                            
                            if usage_today > batas_harian:
                                last_notif_harian = execute_query("SELECT timestamp FROM notifications WHERE message LIKE '%%batas harian%%' ORDER BY timestamp DESC LIMIT 1", fetch_one=True)
                                send_it = True
                                if last_notif_harian and last_notif_harian['timestamp']:
                                    if last_notif_harian['timestamp'].strftime("%Y-%m-%d") == today: # Hanya kirim 1x sehari
                                        send_it = False
                                
                                if send_it:
                                    msg_text = f"⚠️ <b>PERINGATAN BATAS HARIAN</b> ⚠️\n\nPenggunaan listrik hari ini melebihi batas harian yang ditentukan!\n\n<b>Penggunaan Hari Ini:</b> {usage_today:.2f} kWh\n<b>Batas Harian:</b> {batas_harian:.2f} kWh"
                                    status, text_res = send_telegram_alert(msg_text)
                                    execute_query("INSERT INTO notifications (message, status) VALUES (%s, %s)", (msg_text, status + ": " + text_res[:40]), commit=True)
                    except Exception as e:
                        pass

            except Exception as e:
                pass
            
        return jsonify({"message": "Data processed successfully"}), 201
    except Exception as e:
        return jsonify({"message": str(e)}), 500
