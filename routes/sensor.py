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
        except Exception as e:
            pass
            
        return jsonify({"message": "Data saved successfully"}), 201
    except Exception as e:
        return jsonify({"message": str(e)}), 500
