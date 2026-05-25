import datetime
import itertools
from flask import Blueprint, request, jsonify
from database import execute_query
from utils import token_required

prediction_bp = Blueprint('prediction_bp', __name__)

@prediction_bp.route('/predict', methods=['POST'])
@token_required
def get_prediction(current_user):
    data = request.get_json()
    forecast_period = int(data.get('forecast_period', 7)) # 1 (Harian), 7 (Mingguan), 30 (Bulanan)
    machine_id = data.get('machine_id', 'all')
    date_start = data.get('date_start', None)
    date_end = data.get('date_end', None)
    
    # 1. Ambil Tarif Listrik
    settings = execute_query("SELECT setting_value FROM settings WHERE setting_key = 'tarif_per_kwh'", fetch_one=True)
    tarif = float(settings['setting_value']) if settings else 1444.70
    if tarif <= 0: tarif = 1444.70
    
    # 2. Query Data Historis (Filter Mesin dan Tanggal)
    query_conditions = []
    params = []
    
    if machine_id != 'all':
        query_conditions.append("mesin_id = %s")
        params.append(machine_id)
        
    if date_start:
        query_conditions.append("DATE(timestamp) >= %s")
        params.append(date_start)
    if date_end:
        query_conditions.append("DATE(timestamp) <= %s")
        params.append(date_end)
        
    where_clause = ""
    if query_conditions:
        where_clause = "WHERE " + " AND ".join(query_conditions)

    # PENTING: Selalu GROUP BY mesin_id juga agar rata-rata tiap mesin dihitung
    # secara terpisah lalu dijumlahkan per tanggal. Tanpa ini, query akan
    # merata-ratakan daya kedua mesin menjadi satu angka saja (M1+M2)/2.
    query = f"""
        SELECT DATE(timestamp) as dt, mesin_id, SUM(daya)/COUNT(*) as avg_w 
        FROM sensor_data 
        {where_clause}
        GROUP BY DATE(timestamp), mesin_id
        ORDER BY dt ASC
    """
    
    daily_stats = execute_query(query, tuple(params), fetch_all=True)
    
    # Jumlahkan rata-rata daya tiap mesin per tanggal -> total kWh per hari
    # Contoh: M1 = 200W rata2, M2 = 150W rata2 -> total = (200+150)*24/1000 = 8.4 kWh/hari
    kwh_by_date = {}
    for row in daily_stats:
        date_str = row['dt'].strftime('%Y-%m-%d')
        if date_str not in kwh_by_date:
            kwh_by_date[date_str] = 0
        kwh_by_date[date_str] += (row['avg_w'] * 24) / 1000.0
        
    dates = sorted(list(kwh_by_date.keys()))
    actuals = [kwh_by_date[d] for d in dates]
    n = len(actuals)
    
    if n < 3:
        return jsonify({"error": True, "message": "Data historis tidak mencukupi (minimal 3 hari) untuk metode peramalan DES."})
        
    # 3. Dynamic Trial and Error (81 Kombinasi Alpha Beta)
    alphas = [round(x * 0.1, 1) for x in range(1, 10)]
    betas = [round(x * 0.1, 1) for x in range(1, 10)]
    
    best_mape = float('inf')
    best_alpha = 0.4
    best_beta = 0.2
    best_s = []
    best_b = []
    best_forecast_hist = []
    best_error_metrics = []
    
    for alpha, beta in itertools.product(alphas, betas):
        s = [0] * n
        b = [0] * n
        forecast = [0] * n
        
        s[0] = actuals[0]
        b[0] = actuals[1] - actuals[0]
        forecast[0] = actuals[0]
        forecast[1] = s[0] + b[0]
        
        for t in range(1, n):
            s[t] = alpha * actuals[t] + (1 - alpha) * (s[t-1] + b[t-1])
            b[t] = beta * (s[t] - s[t-1]) + (1 - beta) * b[t-1]
            if t + 1 < n:
                forecast[t+1] = s[t] + b[t]
                
        # Hitung MAPE
        apes = []
        for t in range(2, n):
            if actuals[t] != 0:
                ape = abs((actuals[t] - forecast[t]) / actuals[t]) * 100
                apes.append(ape)
                
        mape = sum(apes) / len(apes) if apes else 0
        
        if mape < best_mape:
            best_mape = mape
            best_alpha = alpha
            best_beta = beta
            best_s = s
            best_b = b
            best_forecast_hist = forecast
            
    # Susun Tabel Detail (Histori)
    table_data = []
    avg_kwh = 0
    if n > 0:
        avg_kwh = sum(actuals) / n
        
    for t in range(n):
        actual_val = actuals[t]
        fore_val = best_forecast_hist[t] if t >= 2 else actual_val
        error = actual_val - fore_val
        abs_error = abs(error)
        ape = (abs_error / actual_val * 100) if actual_val != 0 else 0
        
        if t < 2:
            error = 0
            abs_error = 0
            ape = 0
            
        table_data.append({
            "date": dates[t],
            "actual": round(actual_val, 2),
            "forecast": round(fore_val, 2),
            "error": round(error, 2),
            "abs_error": round(abs_error, 2),
            "ape": round(ape, 2)
        })
        
    # 4. Proyeksi Masa Depan (Forecast Period)
    future_forecast = []
    accumulated_kwh = 0
    last_date = datetime.datetime.strptime(dates[-1], '%Y-%m-%d')
    
    for m in range(1, forecast_period + 1):
        f_val = best_s[-1] + m * best_b[-1]
        if f_val <= 0: f_val = 0.1 # Jangan sampai negatif
        
        accumulated_kwh += f_val
        next_date = (last_date + datetime.timedelta(days=m)).strftime('%Y-%m-%d')
        future_forecast.append({
            "date": next_date,
            "forecast": round(f_val, 2)
        })
        
    # 5. Analisis Hasil
    estimasi_biaya = accumulated_kwh * tarif
    
    trend_val = best_b[-1]
    if trend_val > 0.5:
        trend_status = "Naik"
    elif trend_val < -0.5:
        trend_status = "Turun"
    else:
        trend_status = "Stabil"
        
    # AI Insights
    insights = []
    if trend_status == "Naik":
        insights.append("📈 Tren konsumsi energi listrik Anda saat ini sedang MENINGKAT. Pertimbangkan untuk mematikan mesin yang tidak digunakan.")
    elif trend_status == "Turun":
        insights.append("📉 Tren konsumsi energi listrik Anda sedang MENURUN. Efisiensi energi Anda cukup baik, pertahankan!")
    else:
        insights.append("➡️ Tren konsumsi energi listrik Anda terpantau STABIL.")
        
    insights.append(f"💡 Prediksi total pemakaian Anda untuk {forecast_period} hari ke depan adalah sebesar {accumulated_kwh:.2f} kWh.")
    insights.append(f"💰 Siapkan anggaran kurang lebih sebesar Rp {estimasi_biaya:,.0f} untuk menutupi biaya {forecast_period} hari ke depan.")

    # Kembalikan JSON Raksasa
    return jsonify({
        "error": False,
        "stats": {
            "total_kwh_predicted": round(accumulated_kwh, 2),
            "total_cost_predicted": round(estimasi_biaya, 0),
            "avg_kwh": round(avg_kwh, 2),
            "trend": trend_status,
            "mape": round(best_mape, 2)
        },
        "parameters": {
            "alpha": best_alpha,
            "beta": best_beta,
            "total_training": n,
            "combinations": 81
        },
        "analysis": insights,
        "table": table_data,
        "future": future_forecast
    })
