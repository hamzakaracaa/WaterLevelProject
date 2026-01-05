from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
import json
from collections import deque
import threading
import os

# Configure Flask to use templates directory
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'))
CORS(app)  # Enable CORS for ESP32 requests

# Data storage
latest_data = {
    'raw_value': 0,
    'filtered_value': 0.0,
    'percentage': 0.0,
    'timestamp': 0,
    'last_update': None
}

# Data history for charts (last 100 readings)
data_history = deque(maxlen=100)

# Calibration values (can be set via API)
calibration = {
    'min': 100,
    'max': 2500
}

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/data', methods=['POST'])
def receive_data():
    """Receive data from ESP32"""
    try:
        data = request.get_json()
        
        # Calculate percentage based on calibration
        raw_value = data.get('raw_value', 0)
        filtered_value = data.get('filtered_value', raw_value)
        
        # Clamp value between min and max
        clamped_value = max(calibration['min'], min(filtered_value, calibration['max']))
        
        # Calculate percentage
        if calibration['max'] != calibration['min']:
            percentage = ((clamped_value - calibration['min']) / (calibration['max'] - calibration['min'])) * 100
        else:
            percentage = 0
        
        # Update latest data
        latest_data['raw_value'] = raw_value
        latest_data['filtered_value'] = float(filtered_value)
        latest_data['percentage'] = percentage
        latest_data['timestamp'] = data.get('timestamp', 0)
        latest_data['last_update'] = datetime.now().isoformat()
        
        # Add to history
        data_history.append({
            'timestamp': datetime.now().isoformat(),
            'raw_value': raw_value,
            'filtered_value': float(filtered_value),
            'percentage': percentage
        })
        
        return jsonify({'status': 'success', 'percentage': percentage}), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/latest', methods=['GET'])
def get_latest_data():
    """Get latest sensor data"""
    return jsonify(latest_data)

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get historical data"""
    return jsonify(list(data_history))

@app.route('/api/calibration', methods=['GET', 'POST'])
def handle_calibration():
    """Get or update calibration values"""
    if request.method == 'POST':
        data = request.get_json()
        calibration['min'] = data.get('min', calibration['min'])
        calibration['max'] = data.get('max', calibration['max'])
        return jsonify({'status': 'success', 'calibration': calibration})
    else:
        return jsonify(calibration)

if __name__ == '__main__':
    print("=" * 50)
    print("Water Level Dashboard Server")
    print("=" * 50)
    print("Dashboard URL: http://localhost:5000")
    print("API Endpoint: http://localhost:5000/api/data")
    print("\nMake sure to update the ESP32 code with your computer's IP address!")
    print("Find your IP: Windows: ipconfig, Linux/Mac: ifconfig")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)

