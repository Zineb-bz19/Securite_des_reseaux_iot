from datetime import datetime
from database import Database

class User:
    def __init__(self, username, password, role="user"):
        self.username = username
        self.password = password  # This should be hashed
        self.role = role
        self.created_at = datetime.now()
    
    @classmethod
    def get_by_username(cls, username):
        db = Database()
        user_data = db.get_user_by_username(username)
        if user_data:
            user = cls(username=user_data['username'], 
                      password=user_data['password'],
                      role=user_data['role'])
            user.id = user_data['id']
            return user
        return None

class SensorNode:
    def __init__(self, node_id, location=None):
        self.node_id = node_id
        self.location = location
        self.last_seen = None
    
    def add_reading(self, temperature, humidity):
        db = Database()
        db.add_sensor_data(self.node_id, temperature, humidity)
        self.last_seen = datetime.now()

class SensorReading:
    def __init__(self, node_id, temperature, humidity, timestamp):
        self.node_id = node_id
        self.temperature = temperature
        self.humidity = humidity
        self.timestamp = timestamp
    
    @classmethod
    def get_recent_readings(cls, limit=100):
        db = Database()
        readings_data = db.get_sensor_data(limit)
        return [cls(*reading) for reading in readings_data]

class Alert:
    def __init__(self, node_id, message, severity, timestamp=None, read_status=False):
        self.node_id = node_id
        self.message = message
        self.severity = severity
        self.timestamp = timestamp or datetime.now()
        self.read_status = read_status
    
    @classmethod
    def get_active_alerts(cls):
        db = Database()
        alerts_data = db.get_alerts(unread_only=True)
        return [cls(*alert) for alert in alerts_data]
    
    def mark_as_read(self):
        db = Database()
        db.mark_alert_as_read(self.id)
        self.read_status = True