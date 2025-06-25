import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
from config import Config

class Database:
    def __init__(self):
        self.db_file = 'db.sqlite'
        self.init_db()
    
    def get_connection(self):
        """Get a database connection"""
        return sqlite3.connect(self.db_file)
    
    def execute_query(self, query, params=(), commit=False):
        """Execute a single query"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            if commit:
                conn.commit()
            return cursor
    
    def fetch_all(self, query, params=()):
        """Execute query and fetch all results"""
        cursor = self.execute_query(query, params)
        return cursor.fetchall()
    
    def fetch_one(self, query, params=()):
        """Execute query and fetch one result"""
        cursor = self.execute_query(query, params)
        return cursor.fetchone()
    
    def init_db(self):
        """Initialize database with required tables"""
        # Users table
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'user'
            )
        ''', commit=True)
        
        # Sensor data table
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id INTEGER NOT NULL,
                temperature REAL NOT NULL,
                humidity REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''', commit=True)
        
        # Alerts table (updated with consistent field names)
        self.execute_query('''
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        node_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        severity TEXT CHECK(severity IN ('low', 'medium', 'high', 'critical')),
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_read INTEGER DEFAULT 0
    )
''', commit=True)
        
        # Create admin user if not exists
        if not self.fetch_one("SELECT id FROM users WHERE username='admin'"):
            hashed_pw = generate_password_hash('admin123')
            self.execute_query(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                ('admin', hashed_pw, 'admin'),
                commit=True
            )
    
    def authenticate_user(self, username, password):
        """Authenticate user credentials"""
        user = self.fetch_one(
            "SELECT id, username, password, role FROM users WHERE username=?",
            (username,)
        )
        
        if user and check_password_hash(user[2], password):
            return {
                'id': user[0],
                'username': user[1],
                'role': user[3]
            }
        return None
    
    def add_sensor_data(self, node_id, temperature, humidity):
        """Add sensor data to database"""
        self.execute_query(
            '''
            INSERT INTO sensor_data (node_id, temperature, humidity)
            VALUES (?, ?, ?)
            ''',
            (node_id, temperature, humidity),
            commit=True
        )
    
    def get_sensor_data(self, limit=100):
        """Get recent sensor data"""
        return self.fetch_all(
            '''
            SELECT node_id, temperature, humidity, timestamp
            FROM sensor_data
            ORDER BY timestamp DESC
            LIMIT ?
            ''',
            (limit,)
        )
    
    def add_alert(self, node_id, message, severity, timestamp=None):
        """Add a new alert to the database"""
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
        self.execute_query(
            '''
            INSERT INTO alerts (node_id, message, severity, timestamp)
            VALUES (?, ?, ?, ?)
            ''',
            (node_id, message, severity, timestamp),
            commit=True
        )
    
    def get_alerts(self, unread_only=False):
        """Get alert messages"""
        if unread_only:
            return self.fetch_all(
                '''
                SELECT id, node_id, message, severity, timestamp
                FROM alerts
                WHERE is_read = 0
                ORDER BY timestamp DESC
                '''
            )
        return self.fetch_all(
            '''
            SELECT id, node_id, message, severity, timestamp
            FROM alerts
            ORDER BY timestamp DESC
            '''
        )
    
    def mark_alert_as_read(self, alert_id):
        """Mark an alert as read"""
        self.execute_query(
            '''
            UPDATE alerts
            SET is_read = 1
            WHERE id = ?
            ''',
            (alert_id,),
            commit=True
        )
    
    def delete_alert(self, alert_id):
        """Delete an alert from database"""
        self.execute_query(
            '''
            DELETE FROM alerts
            WHERE id = ?
            ''',
            (alert_id,),
            commit=True
        )
    
    def check_thresholds_and_create_alerts(self):
        """Check sensor data against thresholds and create alerts"""
        # Get recent data that hasn't been alerted yet
        recent_data = self.fetch_all(
            '''
            SELECT node_id, temperature, humidity, timestamp
            FROM sensor_data
            WHERE timestamp > (SELECT MAX(timestamp) FROM alerts) OR 
                  (SELECT COUNT(*) FROM alerts) = 0
            ORDER BY timestamp DESC
            '''
        )
        
        for node_id, temp, hum, timestamp in recent_data:
            # Check temperature thresholds
            if temp >= Config.TEMP_CRITICAL_THRESHOLD:
                self.add_alert(
                    node_id,
                    f"Node {node_id}: Critical high temperature ({temp}°C)",
                    "critical",
                    timestamp
                )
            elif temp >= Config.TEMP_HIGH_THRESHOLD:
                self.add_alert(
                    node_id,
                    f"Node {node_id}: High temperature ({temp}°C)",
                    "high",
                    timestamp
                )
            elif temp <= Config.TEMP_LOW_THRESHOLD:
                self.add_alert(
                    node_id,
                    f"Node {node_id}: Low temperature ({temp}°C)",
                    "high",
                    timestamp
                )
            
            # Check humidity thresholds
            if hum >= Config.HUMIDITY_CRITICAL_THRESHOLD:
                self.add_alert(
                    node_id,
                    f"Node {node_id}: Critical high humidity ({hum}%)",
                    "critical",
                    timestamp
                )
            elif hum >= Config.HUMIDITY_HIGH_THRESHOLD:
                self.add_alert(
                    node_id,
                    f"Node {node_id}: High humidity ({hum}%)",
                    "high",
                    timestamp
                )
            elif hum <= Config.HUMIDITY_LOW_THRESHOLD:
                self.add_alert(
                    node_id,
                    f"Node {node_id}: Low humidity ({hum}%)",
                    "high",
                    timestamp
                )