"""
血压管家 - 简化版后端 (无需 Flask，使用内置 http.server)
"""
import json
import sqlite3
import uuid
import os
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

DB_PATH = os.path.join(os.path.dirname(__file__), 'blood_pressure.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS devices (
        id TEXT PRIMARY KEY, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, last_active DATETIME)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS records (
        id TEXT PRIMARY KEY, device_id TEXT, systolic INTEGER, diastolic INTEGER,
        heart_rate INTEGER, timestamp DATETIME, location TEXT, note TEXT,
        medication BOOLEAN DEFAULT 0, status TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
        device_id TEXT PRIMARY KEY, reminder_time TEXT,
        custom_systolic_low INTEGER DEFAULT 90, custom_systolic_high INTEGER DEFAULT 140,
        custom_diastolic_low INTEGER DEFAULT 60, custom_diastolic_high INTEGER DEFAULT 90)''')
    conn.commit()
    conn.close()

def get_bp_status(systolic, diastolic):
    if systolic > 160 or diastolic > 100:
        return 'danger'
    elif systolic > 140 or diastolic > 90:
        return 'warning'
    return 'normal'

class BPHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        
        conn = get_db()
        cursor = conn.cursor()
        
        if path == '/api/device':
            device_id = params.get('id', [None])[0]
            if device_id:
                cursor.execute('SELECT * FROM devices WHERE id = ?', (device_id,))
                row = cursor.fetchone()
                if row:
                    cursor.execute('UPDATE devices SET last_active = ? WHERE id = ?', 
                                  (datetime.now().isoformat(), device_id))
                    conn.commit()
                    self._send_json({'deviceId': device_id, 'exists': True})
                else:
                    self._send_json({'deviceId': device_id, 'exists': False})
            else:
                self._send_json({'error': 'Device ID required'}, 400)
        
        elif path == '/api/records':
            device_id = params.get('deviceId', [None])[0]
            if not device_id:
                self._send_json({'error': 'Device ID required'}, 400)
                return
            cursor.execute('SELECT * FROM records WHERE device_id = ? ORDER BY timestamp DESC LIMIT 100', (device_id,))
            rows = cursor.fetchall()
            records = [{
                'id': r['id'], 'systolic': r['systolic'], 'diastolic': r['diastolic'],
                'heartRate': r['heart_rate'], 'timestamp': r['timestamp'],
                'location': r['location'], 'note': r['note'],
                'medication': bool(r['medication']), 'status': r['status']
            } for r in rows]
            self._send_json(records)
        
        elif path.startswith('/api/records/'):
            record_id = path.split('/')[-1]
            cursor.execute('SELECT * FROM records WHERE id = ?', (record_id,))
            row = cursor.fetchone()
            if row:
                self._send_json({
                    'id': row['id'], 'device_id': row['device_id'],
                    'systolic': row['systolic'], 'diastolic': row['diastolic'],
                    'heartRate': row['heart_rate'], 'timestamp': row['timestamp'],
                    'location': row['location'], 'note': row['note'],
                    'medication': bool(row['medication']), 'status': row['status']
                })
            else:
                self._send_json({'error': 'Record not found'}, 404)
        
        elif path == '/api/stats':
            device_id = params.get('deviceId', [None])[0]
            period = params.get('period', ['week'])[0]
            days = {'week': 7, 'month': 30, 'year': 365}.get(period, 7)
            start_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            cursor.execute('''SELECT AVG(systolic) as avg_systolic, AVG(diastolic) as avg_diastolic, COUNT(*) as total_count
                FROM records WHERE device_id = ? AND timestamp >= ?''',
                (device_id, datetime.fromtimestamp(start_date).isoformat()))
            row = cursor.fetchone()
            
            cursor.execute('''SELECT status, COUNT(*) as count FROM records 
                WHERE device_id = ? AND timestamp >= ? GROUP BY status''',
                (device_id, datetime.fromtimestamp(start_date).isoformat()))
            status_rows = cursor.fetchall()
            
            self._send_json({
                'period': period,
                'avgSystolic': round(row['avg_systolic'], 1) if row['avg_systolic'] else 0,
                'avgDiastolic': round(row['avg_diastolic'], 1) if row['avg_diastolic'] else 0,
                'totalCount': row['total_count'] or 0,
                'statusStats': {r['status']: r['count'] for r in status_rows}
            })
        
        elif path == '/api/settings':
            device_id = params.get('deviceId', [None])[0]
            cursor.execute('SELECT * FROM settings WHERE device_id = ?', (device_id,))
            row = cursor.fetchone()
            if row:
                self._send_json({
                    'reminderTime': row['reminder_time'],
                    'customSystolicLow': row['custom_systolic_low'],
                    'customSystolicHigh': row['custom_systolic_high'],
                    'customDiastolicLow': row['custom_diastolic_low'],
                    'customDiastolicHigh': row['custom_diastolic_high']
                })
            else:
                self._send_json({
                    'reminderTime': '', 'customSystolicLow': 90, 'customSystolicHigh': 140,
                    'customDiastolicLow': 60, 'customDiastolicHigh': 90
                })
        
        conn.close()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        content_length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(content_length).decode()) if content_length else {}
        
        conn = get_db()
        cursor = conn.cursor()
        
        if path == '/api/device':
            device_id = 'dev_' + str(uuid.uuid4())[:12]
            cursor.execute('INSERT INTO devices (id) VALUES (?)', (device_id,))
            conn.commit()
            self._send_json({'deviceId': device_id, 'created': True})
        
        elif path == '/api/records':
            device_id = parsed.query.split('deviceId=')[1] if 'deviceId=' in parsed.query else None
            if not device_id:
                self._send_json({'error': 'Device ID required'}, 400)
                return
            record_id = 'rec_' + str(uuid.uuid4())[:12]
            status = get_bp_status(body['systolic'], body['diastolic'])
            cursor.execute('''INSERT INTO records (id, device_id, systolic, diastolic, heart_rate, 
                timestamp, location, note, medication, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (record_id, device_id, body['systolic'], body['diastolic'], body.get('heartRate', 0),
                 body.get('timestamp', datetime.now().isoformat()), body.get('location', ''),
                 body.get('note', ''), body.get('medication', False), status))
            conn.commit()
            self._send_json({'id': record_id, 'status': status})
        
        conn.close()

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        content_length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(content_length).decode()) if content_length else {}
        
        conn = get_db()
        cursor = conn.cursor()
        
        if path.startswith('/api/records/'):
            record_id = path.split('/')[-1]
            status = get_bp_status(body['systolic'], body['diastolic'])
            cursor.execute('''UPDATE records SET systolic = ?, diastolic = ?, heart_rate = ?,
                timestamp = ?, location = ?, note = ?, medication = ?, status = ?, updated_at = ? WHERE id = ?''',
                (body['systolic'], body['diastolic'], body.get('heartRate', 0),
                 body.get('timestamp'), body.get('location', ''), body.get('note', ''),
                 body.get('medication', False), status, datetime.now().isoformat(), record_id))
            conn.commit()
            self._send_json({'success': True, 'status': status})
        
        elif path == '/api/settings':
            device_id = parsed.query.split('deviceId=')[1] if 'deviceId=' in parsed.query else None
            cursor.execute('''INSERT OR REPLACE INTO settings 
                (device_id, reminder_time, custom_systolic_low, custom_systolic_high,
                 custom_diastolic_low, custom_diastolic_high) VALUES (?, ?, ?, ?, ?, ?)''',
                (device_id, body.get('reminderTime', ''), body.get('customSystolicLow', 90),
                 body.get('customSystolicHigh', 140), body.get('customDiastolicLow', 60),
                 body.get('customDiastolicHigh', 90)))
            conn.commit()
            self._send_json({'success': True})
        
        conn.close()

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        conn = get_db()
        cursor = conn.cursor()
        
        if path.startswith('/api/records/'):
            record_id = path.split('/')[-1]
            cursor.execute('DELETE FROM records WHERE id = ?', (record_id,))
            conn.commit()
            self._send_json({'success': True})
        
        conn.close()

    def log_message(self, format, *args):
        print(f"[{datetime.now().isoformat()}] {args[0]}")

if __name__ == '__main__':
    init_db()
    server = HTTPServer(('0.0.0.0', 5000), BPHandler)
    print('🚀 血压管家后端启动于 http://0.0.0.0:5000')
    server.serve_forever()
