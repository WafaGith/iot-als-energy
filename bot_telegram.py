import urllib.request
import urllib.parse
import urllib.error
import json
import time
from datetime import datetime, timedelta
from database import execute_query

def get_settings():
    settings_data = execute_query("SELECT * FROM settings", fetch_all=True)
    if not settings_data: return {}
    return {item['setting_key']: item['setting_value'] for item in settings_data}

def send_message(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "HTML"}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
    try: urllib.request.urlopen(req, timeout=10)
    except Exception as e: print("Telegram Send Error:", e)

def get_latest_data(mesin_id):
    return execute_query("SELECT * FROM sensor_data WHERE mesin_id=%s ORDER BY timestamp DESC LIMIT 1", (mesin_id,), fetch_one=True)

def handle_command(command, token, chat_id, cfg):
    cmd = command.strip().lower().split(' ')[0]

    if cmd == '/start' or cmd == '/help':
        msg = ("🤖 <b>Monitoring Listrik IoT Bot</b> 🤖\n\n"
               "Halo! Saya adalah sistem asisten pemantau energi Anda.\n"
               "Gunakan salah satu dari perintah berikut:\n\n"
               "📊 <b>/status</b> - Ringkasan kondisi realtime\n"
               "⚡ <b>/power</b> - Cek total daya listrik (Watt)\n"
               "🔋 <b>/energy</b> - Cek total energi (kWh)\n"
               "🏭 <b>/mesin1</b> - Detail sensor Mesin 1\n"
               "🏭 <b>/mesin2</b> - Detail sensor Mesin 2\n"
               "🧠 <b>/prediksi</b> - Akses dashboard web untuk prediksi AI\n"
               "📈 <b>/laporan</b> - Ringkasan 24 Jam Terakhir\n"
               "❓ <b>/help</b> - Tampilkan pesan bantuan ini")
        send_message(token, chat_id, msg)

    elif cmd == '/status':
        m1 = get_latest_data(1); m2 = get_latest_data(2)
        is_stale = False; latest_ts = None
        p1 = m1['daya'] if m1 else 0; p2 = m2['daya'] if m2 else 0
        total_p = p1 + p2
        if m1 and m1['timestamp']:
            if (datetime.now() - m1['timestamp']).total_seconds() > 15: is_stale = True
            latest_ts = m1['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
        else: is_stale = True
            
        status_txt = "🔴 <b>OFFLINE (ESP MATI)</b>" if is_stale else "🟢 <b>ONLINE</b>"
        msg = (f"📊 <b>STATUS SISTEM REALTIME</b>\n\nStatus: {status_txt}\n"
               f"Waktu Update: <i>{latest_ts if latest_ts else 'Belum ada data'}</i>\n\n"
               f"Daya Mesin 1: {p1} W\n"
               f"Daya Mesin 2: {p2} W\n"
               f"<b>Total Daya: {total_p} Watt</b>")
        send_message(token, chat_id, msg)

    elif cmd == '/power':
        m1 = get_latest_data(1); m2 = get_latest_data(2)
        p1 = m1['daya'] if m1 else 0; p2 = m2['daya'] if m2 else 0
        send_message(token, chat_id, f"⚡ <b>TOTAL DAYA SISTEM</b>\n\nTotal saat ini: <b>{p1 + p2} Watt</b>")

    elif cmd == '/energy':
        m1 = get_latest_data(1); m2 = get_latest_data(2)
        e1 = m1['energi'] if m1 else 0; e2 = m2['energi'] if m2 else 0
        send_message(token, chat_id, f"🔋 <b>TOTAL ENERGI DIGUNAKAN</b>\n\nEnergi total: <b>{e1 + e2:.2f} kWh</b>")

    elif cmd == '/mesin1':
        m1 = get_latest_data(1)
        if not m1: send_message(token, chat_id, "Belum ada data untuk Mesin 1."); return
        msg = ("🏭 <b>DETAIL MESIN 1</b>\n\n"
               f"Tegangan: {m1['volt']} V\nArus: {m1['arus']} A\n"
               f"Daya: {m1['daya']} W\nFrekuensi: {m1['frekuensi']} Hz\n"
               f"Power Factor: {m1['pf']}\nTotal Energi: {m1['energi']} kWh")
        send_message(token, chat_id, msg)

    elif cmd == '/mesin2':
        m2 = get_latest_data(2)
        if not m2: send_message(token, chat_id, "Belum ada data untuk Mesin 2."); return
        msg = ("🏭 <b>DETAIL MESIN 2</b>\n\n"
               f"Tegangan: {m2['volt']} V\nArus: {m2['arus']} A\n"
               f"Daya: {m2['daya']} W\nFrekuensi: {m2['frekuensi']} Hz\n"
               f"Power Factor: {m2['pf']}\nTotal Energi: {m2['energi']} kWh")
        send_message(token, chat_id, msg)

    elif cmd == '/prediksi':
        send_message(token, chat_id, "🧠 <b>PREDIKSI KONSUMSI</b>\n\nFitur Double Exponential Smoothing kini tersedia di Web Dashboard (Menu Prediksi). Silakan buka website untuk simulasi Uang / Saldo!")
        
    elif cmd == '/ceksistem':
        m1 = get_latest_data(1); m2 = get_latest_data(2)
        total_e = (m1['energi'] if m1 else 0) + (m2['energi'] if m2 else 0)
        kuota = float(cfg.get('kuota_energi', 100))
        sisa = kuota - total_e
        send_message(token, chat_id, f"⚙️ <b>STATUS KUOTA SISTEM</b>\n\nKuota Total: {kuota} kWh\nDigunakan: {total_e:.2f} kWh\n<b>Sisa Kuota: {sisa:.2f} kWh</b>")

    elif cmd == '/laporan':
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        avg_power = execute_query("SELECT AVG(daya) as avg_p FROM sensor_data WHERE timestamp >= %s", (yesterday_str,), fetch_one=True)
        avg_p = avg_power['avg_p'] if avg_power and avg_power['avg_p'] else 0
        m1 = get_latest_data(1); m2 = get_latest_data(2)
        total_e = (m1['energi'] if m1 else 0) + (m2['energi'] if m2 else 0)
        send_message(token, chat_id, f"📈 <b>LAPORAN (24 Jam Terakhir)</b>\n\nTotal Energi Akumulasi: {total_e:.2f} kWh\nRata-rata Penarikan Daya: {avg_p:.2f} Watt\n")

def start_polling():
    offset = 0
    print("Mulai mendengar Pesan Telegram masuk...")
    while True:
        try:
            cfg = get_settings()
            if cfg.get('telegram_active', '0') != '1':
                time.sleep(10); continue
            token = cfg.get('telegram_bot_token', '').strip()
            my_chat_id = cfg.get('telegram_chat_id', '').strip()
            if not token or not my_chat_id:
                time.sleep(10); continue

            url = f"https://api.telegram.org/bot{token}/getUpdates?offset={offset}&timeout=30"
            req = urllib.request.Request(url, method='GET')
            
            with urllib.request.urlopen(req, timeout=35) as res:
                data = json.loads(res.read())
                if data.get('ok'):
                    for update in data.get('result', []):
                        offset = update['update_id'] + 1
                        message = update.get('message', {})
                        if 'text' in message:
                            chat_id = str(message.get('chat', {}).get('id', ''))
                            if chat_id != my_chat_id:
                                print(f"Menolak pesan dari Unregistered Chat ID: {chat_id}"); continue
                            text = message['text']
                            if text.startswith('/'):
                                print(f"Command diterima dari Boss: {text}")
                                handle_command(text, token, chat_id, cfg)
        except urllib.error.URLError: pass
        except Exception as e:
            if not isinstance(e, TimeoutError): print("Polling Error:", e)
            time.sleep(5)

if __name__ == '__main__':
    start_polling()
