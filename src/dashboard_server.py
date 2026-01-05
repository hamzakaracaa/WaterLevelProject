from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from datetime import datetime
import json
from collections import deque
import threading

app = Flask(__name__)
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

# Dashboard HTML template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Water Level Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        
        .status-indicator.connected {
            background-color: #4ade80;
        }
        
        .status-indicator.disconnected {
            background-color: #ef4444;
            animation: none;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
        }
        
        .card h2 {
            color: #333;
            margin-bottom: 15px;
            font-size: 1.2em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .value-display {
            font-size: 3em;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }
        
        .percentage-display {
            font-size: 4em;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .tank-visualization {
            width: 100%;
            height: 300px;
            background: #f0f0f0;
            border-radius: 10px;
            position: relative;
            overflow: hidden;
            border: 3px solid #ddd;
        }
        
        .water-level {
            position: absolute;
            bottom: 0;
            width: 100%;
            background: linear-gradient(to top, #3b82f6, #60a5fa);
            transition: height 0.5s ease;
            border-radius: 0 0 7px 7px;
        }
        
        .water-level::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 20px;
            background: rgba(255,255,255,0.3);
            border-radius: 50%;
        }
        
        .tank-markers {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            pointer-events: none;
        }
        
        .marker {
            position: absolute;
            left: 0;
            right: 0;
            height: 1px;
            background: rgba(0,0,0,0.2);
        }
        
        .marker-label {
            position: absolute;
            right: 10px;
            transform: translateY(-50%);
            font-size: 12px;
            color: #666;
            font-weight: bold;
        }
        
        .info-text {
            color: #666;
            font-size: 0.9em;
            margin-top: 10px;
        }
        
        .chart-container {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-top: 20px;
        }
        
        .calibration-panel {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-top: 20px;
        }
        
        .calibration-panel input {
            width: 100px;
            padding: 8px;
            margin: 5px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 1em;
        }
        
        .calibration-panel button {
            padding: 10px 20px;
            margin: 5px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            transition: background 0.3s ease;
        }
        
        .calibration-panel button:hover {
            background: #5568d3;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💧 Water Level Monitoring Dashboard</h1>
            <p>
                <span class="status-indicator" id="statusIndicator"></span>
                <span id="statusText">Connecting...</span>
            </p>
        </div>
        
        <div class="dashboard-grid">
            <div class="card">
                <h2>Water Level</h2>
                <div class="percentage-display" id="percentageDisplay">0%</div>
                <div class="info-text">Current tank capacity</div>
            </div>
            
            <div class="card">
                <h2>Raw Sensor Value</h2>
                <div class="value-display" id="rawValue">0</div>
                <div class="info-text">ADC reading</div>
            </div>
            
            <div class="card">
                <h2>Filtered Value</h2>
                <div class="value-display" id="filteredValue">0.00</div>
                <div class="info-text">Smoothed reading</div>
            </div>
            
            <div class="card">
                <h2>Tank Visualization</h2>
                <div class="tank-visualization">
                    <div class="tank-markers" id="tankMarkers"></div>
                    <div class="water-level" id="waterLevel"></div>
                </div>
            </div>
        </div>
        
        <div class="chart-container">
            <h2 style="margin-bottom: 20px; color: #333;">Historical Data</h2>
            <canvas id="dataChart"></canvas>
        </div>
        
        <div class="calibration-panel">
            <h2 style="margin-bottom: 15px; color: #333;">Calibration Settings</h2>
            <div>
                <label>Min Value (Empty): <input type="number" id="minValue" value="100"></label>
                <label>Max Value (Full): <input type="number" id="maxValue" value="2500"></label>
                <button onclick="updateCalibration()">Update Calibration</button>
            </div>
        </div>
    </div>
    
    <script>
        let chart;
        let lastUpdateTime = null;
        
        // Initialize chart
        const ctx = document.getElementById('dataChart').getContext('2d');
        chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Water Level (%)',
                    data: [],
                    borderColor: 'rgb(102, 126, 234)',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                },
                plugins: {
                    legend: {
                        display: true
                    }
                }
            }
        });
        
        // Create tank markers
        function createTankMarkers() {
            const markersContainer = document.getElementById('tankMarkers');
            markersContainer.innerHTML = '';
            for (let i = 0; i <= 10; i++) {
                const marker = document.createElement('div');
                marker.className = 'marker';
                marker.style.top = (i * 10) + '%';
                
                const label = document.createElement('div');
                label.className = 'marker-label';
                label.textContent = (100 - i * 10) + '%';
                label.style.top = (i * 10) + '%';
                
                markersContainer.appendChild(marker);
                markersContainer.appendChild(label);
            }
        }
        
        createTankMarkers();
        
        // Update dashboard with new data
        function updateDashboard(data) {
            const percentage = data.percentage || 0;
            const rawValue = data.raw_value || 0;
            const filteredValue = data.filtered_value || 0;
            
            // Update displays
            document.getElementById('percentageDisplay').textContent = percentage.toFixed(1) + '%';
            document.getElementById('rawValue').textContent = rawValue;
            document.getElementById('filteredValue').textContent = filteredValue.toFixed(2);
            
            // Update water level visualization
            const waterLevel = document.getElementById('waterLevel');
            waterLevel.style.height = percentage + '%';
            
            // Update status
            const statusIndicator = document.getElementById('statusIndicator');
            const statusText = document.getElementById('statusText');
            const now = new Date();
            const timeSinceUpdate = now - new Date(data.last_update);
            
            if (timeSinceUpdate < 5000) {
                statusIndicator.className = 'status-indicator connected';
                statusText.textContent = 'Connected - Last update: ' + new Date(data.last_update).toLocaleTimeString();
            } else {
                statusIndicator.className = 'status-indicator disconnected';
                statusText.textContent = 'Disconnected - No data received';
            }
            
            // Update chart
            const timeLabel = new Date().toLocaleTimeString();
            chart.data.labels.push(timeLabel);
            chart.data.datasets[0].data.push(percentage);
            
            // Keep only last 50 data points
            if (chart.data.labels.length > 50) {
                chart.data.labels.shift();
                chart.data.datasets[0].data.shift();
            }
            
            chart.update('none');
        }
        
        // Fetch data from server
        async function fetchData() {
            try {
                const response = await fetch('/api/latest');
                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                console.error('Error fetching data:', error);
                document.getElementById('statusIndicator').className = 'status-indicator disconnected';
                document.getElementById('statusText').textContent = 'Error connecting to server';
            }
        }
        
        // Update calibration
        async function updateCalibration() {
            const minValue = parseInt(document.getElementById('minValue').value);
            const maxValue = parseInt(document.getElementById('maxValue').value);
            
            try {
                const response = await fetch('/api/calibration', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        min: minValue,
                        max: maxValue
                    })
                });
                
                if (response.ok) {
                    alert('Calibration updated successfully!');
                } else {
                    alert('Error updating calibration');
                }
            } catch (error) {
                console.error('Error updating calibration:', error);
                alert('Error updating calibration');
            }
        }
        
        // Fetch data every second
        setInterval(fetchData, 1000);
        fetchData(); // Initial fetch
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML)

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

