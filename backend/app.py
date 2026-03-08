"""
血压管家 - Flask 后端应用
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import uuid
import os
from datetime import datetime
from database import get_db, init_db, get_bp_status

app = Flask(__name__)
CORS(app)

# 初始化数据库
init_db()

# ============== 设备管理 API ==============

@app.route('/api/device', methods=['GET', 'POST'])
def device():
    """获取或创建设备"""
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        # 创建新设备
        device_id = 'dev_' + str(uuid.uuid4())[:12]
        cursor.execute('INSERT INTO devices (id) VALUES (?)', (device_id,))
        conn.commit()
        conn.close()
        return jsonify({'deviceId': device_id, 'created': True})
    else:
        device_id = request.args.get('id')
        if not device_id:
            return jsonify({'error': 'Device ID required'}), 400
        
        cursor.execute('SELECT * FROM devices WHERE id = ?', (device_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            # 更新最后活跃时间
            cursor = get_db().cursor()
            cursor.execute('UPDATE devices SET last_active = ? WHERE id = ?', 
                          (datetime.now().isoformat(), device_id))
            get_db().commit()
            return jsonify({'deviceId': device_id, 'exists': True})
        else:
            return jsonify({'deviceId': device_id, 'exists': False})

# ============== 记录管理 API ==============

@app.route('/api/records', methods=['GET', 'POST'])
def records():
    """获取或创建血压记录"""
    conn = get_db()
    cursor = conn.cursor()
    device_id = request.args.get('deviceId')
    
    if not device_id:
        return jsonify({'error': 'Device ID required'}), 400
    
    if request.method == 'POST':
        # 创建新记录
        data = request.json
        record_id = 'rec_' + str(uuid.uuid4())[:12]
        status = get_bp_status(data['systolic'], data['diastolic'])
        
        cursor.execute('''
            INSERT INTO records (id, device_id, systolic, diastolic, heart_rate, 
                                timestamp, location, note, medication, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (record_id, device_id, data['systolic'], data['diastolic'], 
              data.get('heartRate', 0), data.get('timestamp', datetime.now().isoformat()),
              data.get('location', ''), data.get('note', ''), 
              data.get('medication', False), status))
        conn.commit()
        conn.close()
        return jsonify({'id': record_id, 'status': status})
    
    else:
        # 获取记录列表
        cursor.execute('''
            SELECT * FROM records WHERE device_id = ? 
            ORDER BY timestamp DESC LIMIT 100
        ''', (device_id,))
        rows = cursor.fetchall()
        conn.close()
        
        records = []
        for row in rows:
            records.append({
                'id': row['id'],
                'systolic': row['systolic'],
                'diastolic': row['diastolic'],
                'heartRate': row['heart_rate'],
                'timestamp': row['timestamp'],
                'location': row['location'],
                'note': row['note'],
                'medication': bool(row['medication']),
                'status': row['status']
            })
        return jsonify(records)

@app.route('/api/records/<record_id>', methods=['GET', 'PUT', 'DELETE'])
def record_detail(record_id):
    """单条记录的详情、更新、删除"""
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('SELECT * FROM records WHERE id = ?', (record_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'error': 'Record not found'}), 404
        
        return jsonify({
            'id': row['id'],
            'device_id': row['device_id'],
            'systolic': row['systolic'],
            'diastolic': row['diastolic'],
            'heartRate': row['heart_rate'],
            'timestamp': row['timestamp'],
            'location': row['location'],
            'note': row['note'],
            'medication': bool(row['medication']),
            'status': row['status']
        })
    
    elif request.method == 'PUT':
        data = request.json
        status = get_bp_status(data['systolic'], data['diastolic'])
        
        cursor.execute('''
            UPDATE records SET systolic = ?, diastolic = ?, heart_rate = ?,
                               timestamp = ?, location = ?, note = ?,
                               medication = ?, status = ?, updated_at = ?
            WHERE id = ?
        ''', (data['systolic'], data['diastolic'], data.get('heartRate', 0),
              data.get('timestamp'), data.get('location', ''), data.get('note', ''),
              data.get('medication', False), status, datetime.now().isoformat(), record_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'status': status})
    
    elif request.method == 'DELETE':
        cursor.execute('DELETE FROM records WHERE id = ?', (record_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

# ============== 统计 API ==============

@app.route('/api/stats', methods=['GET'])
def stats():
    """获取统计数据"""
    conn = get_db()
    cursor = conn.cursor()
    device_id = request.args.get('deviceId')
    period = request.args.get('period', 'week')  # week, month, year
    
    if not device_id:
        return jsonify({'error': 'Device ID required'}), 400
    
    # 计算时间范围
    now = datetime.now()
    if period == 'week':
        days = 7
    elif period == 'month':
        days = 30
    else:
        days = 365
    
    start_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
    
    # 获取平均血压
    cursor.execute('''
        SELECT AVG(systolic) as avg_systolic, AVG(diastolic) as avg_diastolic,
               COUNT(*) as total_count
        FROM records 
        WHERE device_id = ? AND timestamp >= ?
    ''', (device_id, datetime.fromtimestamp(start_date).isoformat()))
    row = cursor.fetchone()
    
    # 获取状态统计
    cursor.execute('''
        SELECT status, COUNT(*) as count
        FROM records 
        WHERE device_id = ? AND timestamp >= ?
        GROUP BY status
    ''', (device_id, datetime.fromtimestamp(start_date).isoformat()))
    status_rows = cursor.fetchall()
    
    conn.close()
    
    status_stats = {row['status']: row['count'] for row in status_rows}
    
    return jsonify({
        'period': period,
        'avgSystolic': round(row['avg_systolic'], 1) if row['avg_systolic'] else 0,
        'avgDiastolic': round(row['avg_diastolic'], 1) if row['avg_diastolic'] else 0,
        'totalCount': row['total_count'] or 0,
        'statusStats': status_stats
    })

# ============== 设置 API ==============

@app.route('/api/settings', methods=['GET', 'PUT'])
def settings():
    """获取或更新用户设置"""
    conn = get_db()
    cursor = conn.cursor()
    device_id = request.args.get('deviceId')
    
    if not device_id:
        return jsonify({'error': 'Device ID required'}), 400
    
    if request.method == 'PUT':
        data = request.json
        cursor.execute('''
            INSERT OR REPLACE INTO settings 
            (device_id, reminder_time, custom_systolic_low, custom_systolic_high,
             custom_diastolic_low, custom_diastolic_high)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (device_id, data.get('reminderTime', ''),
              data.get('customSystolicLow', 90), data.get('customSystolicHigh', 140),
              data.get('customDiastolicLow', 60), data.get('customDiastolicHigh', 90)))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    
    else:
        cursor.execute('SELECT * FROM settings WHERE device_id = ?', (device_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return jsonify({
                'reminderTime': row['reminder_time'],
                'customSystolicLow': row['custom_systolic_low'],
                'customSystolicHigh': row['custom_systolic_high'],
                'customDiastolicLow': row['custom_diastolic_low'],
                'customDiastolicHigh': row['custom_diastolic_high']
            })
        else:
            return jsonify({
                'reminderTime': '',
                'customSystolicLow': 90,
                'customSystolicHigh': 140,
                'customDiastolicLow': 60,
                'customDiastolicHigh': 90
            })

# ============== 位置记录 API ==============

@app.route('/api/location-log', methods=['POST'])
def log_location():
    """记录 IP 位置信息"""
    conn = get_db()
    cursor = conn.cursor()
    data = request.json
    
    device_id = data.get('deviceId')
    ip = data.get('ip')
    location = data.get('location')
    timestamp = data.get('timestamp')
    
    if not device_id or not ip or not location:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # 保存到位置记录表
    cursor.execute('''
        INSERT INTO location_logs (device_id, ip, location, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (device_id, ip, location, timestamp))
    
    # 同时更新记录的 IP 信息（如果是保存记录时调用）
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'ip': ip, 'location': location})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
