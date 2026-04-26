from flask import Blueprint, request, jsonify
from database import execute_query
from utils import token_required

prediction_bp = Blueprint('prediction_bp', __name__)

@prediction_bp.route('/predict', methods=['POST'])
@token_required
def get_prediction(current_user):
    data = request.get_json()
    budget = float(data.get('budget', 0))
    
    settings = execute_query("SELECT setting_value FROM settings WHERE setting_key = 'tarif_per_kwh'", fetch_one=True)
    tarif = float(settings['setting_value']) if settings else 1444.70
    if tarif <= 0: tarif = 1444.70
    
    target_kwh = budget / tarif
    
    daily_stats = execute_query("""
        SELECT DATE(timestamp) as dt, mesin_id, SUM(daya)/COUNT(*) as avg_w 
        FROM sensor_data 
        GROUP BY DATE(timestamp), mesin_id 
        ORDER BY dt ASC
    """, fetch_all=True)
    
    kwh_by_date = {}
    for row in daily_stats:
        date_str = row['dt'].strftime('%Y-%m-%d')
        if date_str not in kwh_by_date:
            kwh_by_date[date_str] = 0
        kwh_by_date[date_str] += (row['avg_w'] * 24) / 1000.0
        
    dates = sorted(list(kwh_by_date.keys()))
    daily_kwh_list = [kwh_by_date[d] for d in dates]
    historical_chart = [{"date": d, "kwh": kwh_by_date[d]} for d in dates]
    
    if len(daily_kwh_list) < 2:
        avg_kwh = daily_kwh_list[0] if daily_kwh_list else 10.0
        if avg_kwh <= 0: avg_kwh = 10.0
        days = target_kwh / avg_kwh
        hours = int((days - int(days)) * 24)
        return jsonify({
            "days": int(days), "hours": hours, "target_kwh": target_kwh, 
            "avg_kwh": avg_kwh, "forecast": [avg_kwh] * 7, "history": historical_chart, "tarif": tarif
        })
        
    alpha = 0.3
    beta = 0.2
    n = len(daily_kwh_list)
    s = [0] * n
    b = [0] * n
    s[0] = daily_kwh_list[0]
    b[0] = daily_kwh_list[1] - daily_kwh_list[0]
    
    for t in range(1, n):
        s[t] = alpha * daily_kwh_list[t] + (1 - alpha) * (s[t-1] + b[t-1])
        b[t] = beta * (s[t] - s[t-1]) + (1 - beta) * b[t-1]
        
    accumulated = 0
    forecast_chart = []
    m = 1
    while accumulated < target_kwh:
        forecast = s[-1] + m * b[-1]
        if forecast <= 0.1: forecast = 0.1
        
        accumulated += forecast
        if m <= 7: forecast_chart.append(forecast)
        
        if accumulated >= target_kwh:
            overshoot = accumulated - target_kwh
            fraction = 1.0 - (overshoot / forecast)
            total_time = m - 1 + fraction
            days = int(total_time)
            hours = int((total_time - days) * 24)
            return jsonify({
                "days": days, "hours": hours, "target_kwh": target_kwh, 
                "avg_kwh": s[-1], "forecast": forecast_chart, "history": historical_chart, "tarif": tarif
            })
        m += 1
        if m > 3650:
            return jsonify({"days": 3650, "hours": 0, "target_kwh": target_kwh, "avg_kwh": s[-1], "forecast": forecast_chart, "history": historical_chart, "tarif": tarif})
