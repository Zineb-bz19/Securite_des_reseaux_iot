from flask import Flask, request, jsonify
from flask_cors import CORS
import csv
import os
from datetime import datetime
import threading
import time
from typing import Dict, List, Optional
from cryptography.fernet import Fernet

app = Flask(__name__)
CORS(app)

# Configuration
DATA_DIR = 'data'
os.makedirs(DATA_DIR, exist_ok=True)

# Charger la clé Fernet
with open("key.txt", "rb") as f:
    fernet = Fernet(f.read())

# In-memory data store
class DataStore:
    def __init__(self):
        self.nodes: Dict[int, List[Dict]] = {}
        self.alerts: List[Dict] = []

    def add_node_data(self, node_id: int, timestamp: str, temperature: float, humidity: float):
        if node_id not in self.nodes:
            self.nodes[node_id] = []
        self.nodes[node_id].append({
            "timestamp": timestamp,
            "temperature": temperature,
            "humidity": humidity
        })

    def add_alert(self, node_id: int, message: str, severity: str, timestamp: str):
        self.alerts.append({
            "node_id": node_id,
            "message": message,
            "severity": severity,
            "timestamp": timestamp,
            "read": False
        })

    def get_node_data(self, node_id: Optional[int] = None) -> Dict:
        if node_id:
            return {str(node_id): self.nodes.get(node_id, [])}
        return self.nodes

    def get_alerts(self, unread_only: bool = False) -> List[Dict]:
        if unread_only:
            return [alert for alert in self.alerts if not alert['read']]
        return self.alerts

    def mark_alert_as_read(self, alert_index: int):
        if 0 <= alert_index < len(self.alerts):
            self.alerts[alert_index]['read'] = True

sensor_data = DataStore()

def check_thresholds(node_id: int, temperature: float, humidity: float, timestamp: str):
    if temperature >= 35:
        sensor_data.add_alert(node_id, f"Node {node_id}: Critical high temperature ({temperature}°C)", "critical", timestamp)
    elif temperature >= 30:
        sensor_data.add_alert(node_id, f"Node {node_id}: High temperature ({temperature}°C)", "high", timestamp)
    elif temperature <= 5:
        sensor_data.add_alert(node_id, f"Node {node_id}: Low temperature ({temperature}°C)", "high", timestamp)

    if humidity >= 90:
        sensor_data.add_alert(node_id, f"Node {node_id}: Critical high humidity ({humidity}%)", "critical", timestamp)
    elif humidity >= 80:
        sensor_data.add_alert(node_id, f"Node {node_id}: High humidity ({humidity}%)", "high", timestamp)
    elif humidity <= 20:
        sensor_data.add_alert(node_id, f"Node {node_id}: Low humidity ({humidity}%)", "high", timestamp)

@app.route('/api/sensor_data', methods=['POST'])
def receive_sensor_data():
    try:
        data = request.get_json()
        if not all(key in data for key in ['node_id', 'temperature', 'humidity']):
            return jsonify({"status": "error", "message": "Missing required fields (node_id, temperature, humidity)"}), 400

        try:
            node_id = int(data['node_id'])
            temperature = float(data['temperature'])
            humidity = float(data['humidity'])
            timestamp = data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        except ValueError as e:
            return jsonify({"status": "error", "message": f"Invalid data format: {str(e)}"}), 400

        sensor_data.add_node_data(node_id, timestamp, temperature, humidity)

        # 🔐 Chiffrer les données avant sauvegarde CSV
        data_string = f"{temperature},{humidity}".encode()
        data_encrypted = fernet.encrypt(data_string).decode()

        filename = f"node_{node_id}_data.csv"
        filepath = os.path.join(DATA_DIR, filename)
        file_exists = os.path.isfile(filepath)

        with open(filepath, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['node_id', 'data_encrypted', 'timestamp'])
            writer.writerow([node_id, data_encrypted, timestamp])

        check_thresholds(node_id, temperature, humidity, timestamp)

        return jsonify({"status": "success"})

    except Exception as e:
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "node_count": len(sensor_data.nodes),
        "alert_count": len(sensor_data.alerts)
    })

@app.route('/api/test', methods=['GET', 'POST'])
def test_endpoint():
    if request.method == 'POST':
        try:
            data = request.get_json()
            return jsonify({"status": "success", "received": data, "timestamp": datetime.now().isoformat()})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 400
    return jsonify({"status": "success", "message": "GET received", "timestamp": datetime.now().isoformat()})

@app.route('/api/get_data', methods=['GET'])
def get_sensor_data():
    try:
        node_id = request.args.get('node_id')
        if node_id:
            try:
                node_id = int(node_id)
                return jsonify({"status": "success", "data": sensor_data.get_node_data(node_id)})
            except ValueError:
                return jsonify({"status": "error", "message": "Invalid node_id format"}), 400
        else:
            return jsonify({"status": "success", "data": sensor_data.get_node_data()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/get_alerts', methods=['GET'])
def get_alerts():
    try:
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        return jsonify({"status": "success", "alerts": sensor_data.get_alerts(unread_only)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/mark_alert_read', methods=['POST'])
def mark_alert_read():
    try:
        data = request.get_json()
        alert_id = data.get('alert_id')
        if alert_id is None:
            return jsonify({"status": "error", "message": "alert_id is required"}), 400
        try:
            alert_id = int(alert_id)
            sensor_data.mark_alert_as_read(alert_id)
            return jsonify({"status": "success"})
        except ValueError:
            return jsonify({"status": "error", "message": "alert_id must be an integer"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/send_data', methods=['GET'])
def receive_from_arduino_get():
    try:
        temp = request.args.get('temp')
        hum = request.args.get('hum')
        node_id = request.args.get('node_id', 1)
        if not temp or not hum:
            return jsonify({"status": "error", "message": "Missing temp or hum"}), 400
        temp = float(temp)
        hum = float(hum)
        node_id = int(node_id)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sensor_data.add_node_data(node_id, timestamp, temp, hum)
        # Optionnel : chiffrement ici aussi si nécessaire
        check_thresholds(node_id, temp, hum, timestamp)
        print(f"[GET] Received from Arduino: node={node_id}, temp={temp}, hum={hum}")
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def run_flask_server():
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)

if __name__ == '__main__':
    print("Starting Forest Monitoring Server...")
    print(f"Data directory: {os.path.abspath(DATA_DIR)}")
    flask_thread = threading.Thread(target=run_flask_server)
    flask_thread.daemon = True
    flask_thread.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down server...")
