from flask import Blueprint, request, jsonify
from database import execute_query
from utils import token_required

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/realtime', methods=['GET'])
@token_required
def get_realtime(current_user):
    m1 = execute_query("SELECT * FROM sensor_data WHERE mesin_id = 1 ORDER BY timestamp DESC LIMIT 1", fetch_one=True)
    m2 = execute_query("SELECT * FROM sensor_data WHERE mesin_id = 2 ORDER BY timestamp DESC LIMIT 1", fetch_one=True)
    
    history_m1 = execute_query("SELECT timestamp, volt, arus, daya, frekuensi, pf FROM (SELECT * FROM sensor_data WHERE mesin_id = 1 ORDER BY timestamp DESC LIMIT 15) sub ORDER BY timestamp ASC", fetch_all=True)
    history_m2 = execute_query("SELECT timestamp, volt, arus, daya, frekuensi, pf FROM (SELECT * FROM sensor_data WHERE mesin_id = 2 ORDER BY timestamp DESC LIMIT 15) sub ORDER BY timestamp ASC", fetch_all=True)
    
    for row in history_m1: row['timestamp'] = row['timestamp'].strftime("%H:%M:%S")
    for row in history_m2: row['timestamp'] = row['timestamp'].strftime("%H:%M:%S")
    if m1: m1['timestamp'] = m1['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
    if m2: m2['timestamp'] = m2['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
    
    return jsonify({
        "m1": m1, "m2": m2,
        "history_m1": history_m1, "history_m2": history_m2
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
    
    query = "SELECT * FROM sensor_data WHERE 1=1"
    params = []
    
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
        
    query += f" ORDER BY timestamp DESC LIMIT {limit} OFFSET {offset}"
    
    data = execute_query(query, tuple(params) if params else None, fetch_all=True)
    if data:
        for row in data: row['timestamp'] = row['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
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
