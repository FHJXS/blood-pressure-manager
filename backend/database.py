"""
血压管家 - 数据库操作模块
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'blood_pressure.db')

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库表"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 创建设备表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id TEXT PRIMARY KEY,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_active DATETIME
        )
    ''')
    
    # 创建血压记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id TEXT PRIMARY KEY,
            device_id TEXT,
            systolic INTEGER,
            diastolic INTEGER,
            heart_rate INTEGER,
            timestamp DATETIME,
            location TEXT,
            note TEXT,
            medication BOOLEAN DEFAULT 0,
            status TEXT,
            ip TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME,
            FOREIGN KEY (device_id) REFERENCES devices(id)
        )
    ''')
    
    # 创建设置表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            device_id TEXT PRIMARY KEY,
            reminder_time TEXT,
            custom_systolic_low INTEGER DEFAULT 90,
            custom_systolic_high INTEGER DEFAULT 140,
            custom_diastolic_low INTEGER DEFAULT 60,
            custom_diastolic_high INTEGER DEFAULT 90,
            FOREIGN KEY (device_id) REFERENCES devices(id)
        )
    ''')
    
    # 创建位置记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS location_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            ip TEXT,
            location TEXT,
            timestamp DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_bp_status(systolic, diastolic):
    """判断血压状态"""
    if systolic > 160 or diastolic > 100:
        return 'danger'
    elif systolic > 140 or diastolic > 90:
        return 'warning'
    return 'normal'
