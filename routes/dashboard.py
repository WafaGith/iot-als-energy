from flask import Blueprint, request, jsonify
from database import execute_query
from utils import token_required

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/realtime', methods=['GET'])
@token_required
def get_realtime(current_user):
    from database import latest_sensor_data, sensor_history
    
    # Ambil nilai terkini dari cache in-memory
    m1 = latest_sensor_data.get("m1")
    m2 = latest_sensor_data.get("m2")
    
    # Fallback ke DB jika cache masih kosong (server baru nyala)
    if not m1:
        m1 = execute_query("SELECT * FROM sensor_data WHERE mesin_id = 1 ORDER BY timestamp DESC LIMIT 1", fetch_one=True)
        if m1 and hasattr(m1['timestamp'], 'strftime'):
            m1['timestamp'] = m1['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
    else:
        m1 = dict(m1)

    if not m2:
        m2 = execute_query("SELECT * FROM sensor_data WHERE mesin_id = 2 ORDER BY timestamp DESC LIMIT 1", fetch_one=True)
        if m2 and hasattr(m2['timestamp'], 'strftime'):
            m2['timestamp'] = m2['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
    else:
        m2 = dict(m2)

    # Ambil history grafik dari in-memory rolling buffer (update setiap 3 detik)
    history_m1 = list(sensor_history['m1'])
    history_m2 = list(sensor_history['m2'])

    # Fallback ke DB jika history in-memory masih kosong (server baru nyala)
    if not history_m1:
        db_hist = execute_query(
            "SELECT timestamp, volt, arus, daya, frekuensi, pf FROM "
            "(SELECT * FROM sensor_data WHERE mesin_id = 1 ORDER BY timestamp DESC LIMIT 15) sub "
            "ORDER BY timestamp ASC",
            fetch_all=True
        )
        if db_hist:
            for row in db_hist:
                if hasattr(row['timestamp'], 'strftime'):
                    row['timestamp'] = row['timestamp'].strftime("%H:%M:%S")
            history_m1 = db_hist

    if not history_m2:
        db_hist = execute_query(
            "SELECT timestamp, volt, arus, daya, frekuensi, pf FROM "
            "(SELECT * FROM sensor_data WHERE mesin_id = 2 ORDER BY timestamp DESC LIMIT 15) sub "
            "ORDER BY timestamp ASC",
            fetch_all=True
        )
        if db_hist:
            for row in db_hist:
                if hasattr(row['timestamp'], 'strftime'):
                    row['timestamp'] = row['timestamp'].strftime("%H:%M:%S")
            history_m2 = db_hist

    # =====================================================================
    # Total Energi dari Database (nilai kumulatif MAX per mesin)
    # Karena PZEM mencatat energi secara kumulatif (terus naik),
    # nilai MAX(energi) = total kWh keseluruhan yang pernah terpakai
    # =====================================================================
    db_e1 = execute_query("SELECT MAX(energi) as total FROM sensor_data WHERE mesin_id = 1", fetch_one=True)
    db_e2 = execute_query("SELECT MAX(energi) as total FROM sensor_data WHERE mesin_id = 2", fetch_one=True)
    total_energi_m1_db = float(db_e1['total']) if db_e1 and db_e1['total'] is not None else 0.0
    total_energi_m2_db = float(db_e2['total']) if db_e2 and db_e2['total'] is not None else 0.0
    total_energi_db = total_energi_m1_db + total_energi_m2_db

    return jsonify({
        "m1": m1, "m2": m2,
        "history_m1": history_m1, "history_m2": history_m2,
        "total_energi_m1_db": round(total_energi_m1_db, 3),
        "total_energi_m2_db": round(total_energi_m2_db, 3),
        "total_energi_db": round(total_energi_db, 3)
    })


@dashboard_bp.route('/history/sensor', methods=['GET'])
@token_required
def get_sensor_history(current_user):
    limit = int(request.args.get('limit', 20))
    page = int(request.args.get('page', 1))
    offset = (page - 1) * limit
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    mesin_id = request.args.get('mesin_id')
    view = request.args.get('view', 'minute') # 'minute' or 'daily'
    
    params = []
    
    if view == 'daily':
        # Daily aggregated view query
        query = """
            SELECT 
                DATE(timestamp) as tanggal, 
                mesin_id, 
                AVG(volt) as volt, 
                AVG(arus) as arus, 
                AVG(daya) as daya, 
                MAX(daya) as max_daya,
                (AVG(daya) * 24) / 1000.0 as energi, 
                AVG(frekuensi) as frekuensi, 
                AVG(pf) as pf
            FROM sensor_data
            WHERE 1=1
        """
        if start_date:
            query += " AND timestamp >= %s"
            params.append(start_date + " 00:00:00")
        if end_date:
            query += " AND timestamp <= %s"
            params.append(end_date + " 23:59:59")
        if mesin_id and mesin_id != 'all':
            query += " AND mesin_id = %s"
            params.append(int(mesin_id))
            
        query += " GROUP BY DATE(timestamp), mesin_id"
        
        # Get count of daily aggregated rows
        count_query = f"SELECT COUNT(*) as total FROM ({query}) sub"
        total_res = execute_query(count_query, tuple(params) if params else None, fetch_one=True)
        total_count = total_res['total'] if total_res else 0
        
        sort_order = request.args.get('sort', 'desc').upper()
        if sort_order not in ['ASC', 'DESC']:
            sort_order = 'DESC'
            
        query += f" ORDER BY tanggal {sort_order} LIMIT {limit} OFFSET {offset}"
        
        data = execute_query(query, tuple(params) if params else None, fetch_all=True)
        if data:
            for row in data:
                row['timestamp'] = row['tanggal'].strftime("%Y-%m-%d")
                row['volt'] = round(row['volt'], 2)
                row['arus'] = round(row['arus'], 3)
                row['daya'] = round(row['daya'], 2)
                if 'max_daya' in row and row['max_daya'] is not None:
                    row['max_daya'] = round(row['max_daya'], 2)
                else:
                    row['max_daya'] = row['daya']
                row['energi'] = round(row['energi'], 3)
                row['frekuensi'] = round(row['frekuensi'], 2)
                row['pf'] = round(row['pf'], 2)
        else:
            data = []
            
    else:
        # Default minute-by-minute raw sensor logs view
        query = "SELECT * FROM sensor_data WHERE 1=1"
        if start_date:
            query += " AND timestamp >= %s"
            params.append(start_date + " 00:00:00")
        if end_date:
            query += " AND timestamp <= %s"
            params.append(end_date + " 23:59:59")
        if mesin_id and mesin_id != 'all':
            query += " AND mesin_id = %s"
            params.append(int(mesin_id))
            
        # Get total count first
        count_query = query.replace("SELECT *", "SELECT COUNT(*) as total")
        total_res = execute_query(count_query, tuple(params) if params else None, fetch_one=True)
        total_count = total_res['total'] if total_res else 0
            
        sort_order = request.args.get('sort', 'desc').upper()
        if sort_order not in ['ASC', 'DESC']:
            sort_order = 'DESC'
            
        query += f" ORDER BY timestamp {sort_order} LIMIT {limit} OFFSET {offset}"
        
        data = execute_query(query, tuple(params) if params else None, fetch_all=True)
        if data:
            for row in data: 
                row['timestamp'] = row['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
        else: 
            data = []
        
    total_pages = (total_count + limit - 1) // limit if limit > 0 else 1
    
    return jsonify({
        "data": data,
        "total": total_count,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    })

@dashboard_bp.route('/history/events', methods=['GET'])
@token_required
def get_events(current_user):
    limit = int(request.args.get('limit', 50))
    data = execute_query("SELECT * FROM system_events ORDER BY timestamp DESC LIMIT %s", (limit,), fetch_all=True)
    for row in data: row['timestamp'] = row['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
    return jsonify(data)

@dashboard_bp.route('/history/notifications', methods=['GET'])
@token_required
def get_notifications(current_user):
    limit = int(request.args.get('limit', 50))
    data = execute_query("SELECT * FROM notifications ORDER BY timestamp DESC LIMIT %s", (limit,), fetch_all=True)
    for row in data: row['timestamp'] = row['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
    return jsonify(data)

@dashboard_bp.route('/settings', methods=['GET', 'POST'])
@token_required
def manage_settings(current_user):
    if request.method == 'GET':
        data = execute_query("SELECT * FROM settings", fetch_all=True)
        return jsonify({item['setting_key']: item['setting_value'] for item in data})
    elif request.method == 'POST':
        data = request.get_json()
        for k, v in data.items():
            execute_query(
                "INSERT INTO settings (setting_key, setting_value) VALUES (%s, %s) ON DUPLICATE KEY UPDATE setting_value = %s", 
                (k, str(v), str(v)), commit=True
            )
        execute_query("INSERT INTO system_events (event_type, description) VALUES (%s, %s)", 
                      ("Settings Changed", "Admin updated settings"), commit=True)
        return jsonify({"message": "Settings updated"})
