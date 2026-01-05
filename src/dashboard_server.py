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
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Water Level Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #2563eb;
            --primary-dark: #1e40af;
            --secondary: #0ea5e9;
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #1e293b;
            --bg-card-hover: #334155;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --border: #334155;
            --shadow: rgba(0, 0, 0, 0.3);
            --water-low: #ef4444;
            --water-medium: #3b82f6;
            --water-high: #10b981;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 0;
            overflow-x: hidden;
            line-height: 1.6;
        }
        
        .header {
            background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-card) 100%);
            padding: 2rem 1.5rem;
            border-bottom: 1px solid var(--border);
            position: sticky;
            top: 0;
            z-index: 100;
            backdrop-filter: blur(10px);
            box-shadow: 0 4px 6px var(--shadow);
        }
        
        .header-content {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }
        
        .header-title {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .header-title h1 {
            font-size: clamp(1.5rem, 4vw, 2rem);
            font-weight: 700;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .status-badge {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: var(--bg-card);
            border-radius: 50px;
            border: 1px solid var(--border);
            font-size: 0.875rem;
        }
        
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        .status-dot.connected {
            background: var(--success);
            box-shadow: 0 0 10px var(--success);
        }
        
        .status-dot.disconnected {
            background: var(--danger);
            animation: none;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(1.1); }
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem 1.5rem;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 1.5rem;
            border: 1px solid var(--border);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            transform: scaleX(0);
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-4px);
            border-color: var(--primary);
            box-shadow: 0 10px 30px var(--shadow);
        }
        
        .stat-card:hover::before {
            transform: scaleX(1);
        }
        
        .stat-label {
            font-size: 0.875rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .stat-value {
            font-size: clamp(2rem, 5vw, 3rem);
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
        }
        
        .stat-unit {
            font-size: 1.25rem;
            color: var(--text-secondary);
            font-weight: 500;
        }
        
        .tank-card {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 2rem;
            border: 1px solid var(--border);
            margin-bottom: 2rem;
            transition: all 0.3s ease;
        }
        
        .tank-card:hover {
            border-color: var(--primary);
            box-shadow: 0 10px 30px var(--shadow);
        }
        
        .tank-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
            gap: 1rem;
        }
        
        .tank-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-primary);
        }
        
        .tank-visualization {
            width: 100%;
            height: 400px;
            background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
            border-radius: 12px;
            position: relative;
            overflow: hidden;
            border: 2px solid var(--border);
            box-shadow: inset 0 0 30px rgba(0, 0, 0, 0.5);
        }
        
        .tank-markers {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            pointer-events: none;
            z-index: 2;
        }
        
        .marker {
            position: absolute;
            left: 0;
            right: 0;
            height: 1px;
            background: rgba(148, 163, 184, 0.3);
        }
        
        .marker.major {
            background: rgba(148, 163, 184, 0.5);
            height: 2px;
        }
        
        .marker-label {
            position: absolute;
            right: 15px;
            transform: translateY(-50%);
            font-size: 0.75rem;
            color: var(--text-secondary);
            font-weight: 600;
            background: var(--bg-card);
            padding: 2px 8px;
            border-radius: 4px;
        }
        
        .water-level {
            position: absolute;
            bottom: 0;
            width: 100%;
            background: linear-gradient(to top, 
                var(--water-low) 0%, 
                var(--water-medium) 50%, 
                var(--water-high) 100%);
            transition: height 0.8s cubic-bezier(0.4, 0, 0.2, 1);
            border-radius: 0 0 10px 10px;
            box-shadow: 0 -5px 20px rgba(37, 99, 235, 0.3);
        }
        
        .water-level::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 30px;
            background: linear-gradient(to bottom, 
                rgba(255, 255, 255, 0.4) 0%, 
                rgba(255, 255, 255, 0.1) 100%);
            border-radius: 50% 50% 0 0 / 100% 100% 0 0;
            animation: wave 3s ease-in-out infinite;
        }
        
        @keyframes wave {
            0%, 100% { transform: translateX(0) scaleY(1); }
            50% { transform: translateX(-10px) scaleY(1.1); }
        }
        
        .chart-container {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 2rem;
            border: 1px solid var(--border);
            margin-bottom: 2rem;
            transition: all 0.3s ease;
        }
        
        .chart-container:hover {
            border-color: var(--primary);
            box-shadow: 0 10px 30px var(--shadow);
        }
        
        .chart-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
            gap: 1rem;
        }
        
        .chart-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-primary);
        }
        
        .chart-wrapper {
            position: relative;
            height: 300px;
            width: 100%;
        }
        
        .calibration-panel {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 2rem;
            border: 1px solid var(--border);
            transition: all 0.3s ease;
        }
        
        .calibration-panel:hover {
            border-color: var(--primary);
            box-shadow: 0 10px 30px var(--shadow);
        }
        
        .calibration-header {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 1.5rem;
        }
        
        .calibration-form {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            align-items: flex-end;
        }
        
        .form-group {
            flex: 1;
            min-width: 200px;
        }
        
        .form-label {
            display: block;
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
            font-weight: 500;
        }
        
        .form-input {
            width: 100%;
            padding: 0.75rem 1rem;
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text-primary);
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        
        .form-input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }
        
        .btn {
            padding: 0.75rem 1.5rem;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            white-space: nowrap;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(37, 99, 235, 0.4);
        }
        
        .btn:active {
            transform: translateY(0);
        }
        
        .toast {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: var(--bg-card);
            color: var(--text-primary);
            padding: 1rem 1.5rem;
            border-radius: 8px;
            border: 1px solid var(--border);
            box-shadow: 0 10px 30px var(--shadow);
            z-index: 1000;
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.3s ease;
        }
        
        .toast.show {
            transform: translateY(0);
            opacity: 1;
        }
        
        .toast.success {
            border-color: var(--success);
        }
        
        .toast.error {
            border-color: var(--danger);
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }
            
            .header {
                padding: 1.5rem 1rem;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
                gap: 1rem;
            }
            
            .tank-visualization {
                height: 300px;
            }
            
            .chart-wrapper {
                height: 250px;
            }
            
            .calibration-form {
                flex-direction: column;
            }
            
            .form-group {
                min-width: 100%;
            }
            
            .toast {
                right: 1rem;
                left: 1rem;
                bottom: 1rem;
            }
        }
        
        @media (max-width: 480px) {
            .header-content {
                flex-direction: column;
                align-items: flex-start;
            }
            
            .stat-card {
                padding: 1.25rem;
            }
            
            .tank-card,
            .chart-container,
            .calibration-panel {
                padding: 1.5rem;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <div class="header-title">
                <h1>💧 Water Level Monitor</h1>
            </div>
            <div class="status-badge">
                <span class="status-dot" id="statusIndicator"></span>
                <span id="statusText">Connecting...</span>
            </div>
        </div>
    </div>
    
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">
                    <span>📊</span>
                    <span>Water Level</span>
                </div>
                <div class="stat-value" id="percentageDisplay">0<span class="stat-unit">%</span></div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">
                    <span>🔢</span>
                    <span>Raw Sensor Value</span>
                </div>
                <div class="stat-value" id="rawValue">0</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">
                    <span>📈</span>
                    <span>Filtered Value</span>
                </div>
                <div class="stat-value" id="filteredValue">0.00</div>
            </div>
        </div>
        
        <div class="tank-card">
            <div class="tank-header">
                <div class="tank-title">Tank Visualization</div>
            </div>
            <div class="tank-visualization">
                <div class="tank-markers" id="tankMarkers"></div>
                <div class="water-level" id="waterLevel"></div>
            </div>
        </div>
        
        <div class="chart-container">
            <div class="chart-header">
                <div class="chart-title">Historical Data</div>
            </div>
            <div class="chart-wrapper">
                <canvas id="dataChart"></canvas>
            </div>
        </div>
        
        <div class="calibration-panel">
            <div class="calibration-header">⚙️ Calibration Settings</div>
            <div class="calibration-form">
                <div class="form-group">
                    <label class="form-label">Min Value (Empty)</label>
                    <input type="number" id="minValue" class="form-input" value="100">
                </div>
                <div class="form-group">
                    <label class="form-label">Max Value (Full)</label>
                    <input type="number" id="maxValue" class="form-input" value="2500">
                </div>
                <button class="btn" onclick="updateCalibration()">Update Calibration</button>
            </div>
        </div>
    </div>
    
    <div class="toast" id="toast"></div>
    
    <script>
        let chart;
        
        // Initialize chart
        const ctx = document.getElementById('dataChart').getContext('2d');
        chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Water Level (%)',
                    data: [],
                    borderColor: 'rgb(37, 99, 235)',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        display: true,
                        labels: {
                            color: '#94a3b8',
                            font: {
                                family: 'Inter',
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleColor: '#f1f5f9',
                        bodyColor: '#94a3b8',
                        borderColor: '#334155',
                        borderWidth: 1,
                        padding: 12,
                        cornerRadius: 8
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(148, 163, 184, 0.1)',
                            borderColor: '#334155'
                        },
                        ticks: {
                            color: '#94a3b8',
                            font: {
                                family: 'Inter',
                                size: 11
                            },
                            maxTicksLimit: 10
                        }
                    },
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: 'rgba(148, 163, 184, 0.1)',
                            borderColor: '#334155'
                        },
                        ticks: {
                            color: '#94a3b8',
                            font: {
                                family: 'Inter',
                                size: 11
                            }
                        }
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
                marker.className = i % 5 === 0 ? 'marker major' : 'marker';
                marker.style.top = (i * 10) + '%';
                
                if (i % 5 === 0) {
                    const label = document.createElement('div');
                    label.className = 'marker-label';
                    label.textContent = (100 - i * 10) + '%';
                    label.style.top = (i * 10) + '%';
                    markersContainer.appendChild(label);
                }
                
                markersContainer.appendChild(marker);
            }
        }
        
        createTankMarkers();
        
        // Show toast notification
        function showToast(message, type = 'success') {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.className = `toast ${type} show`;
            setTimeout(() => {
                toast.classList.remove('show');
            }, 3000);
        }
        
        // Update water color based on level
        function updateWaterColor(percentage) {
            const waterLevel = document.getElementById('waterLevel');
            if (percentage < 20) {
                waterLevel.style.background = 'linear-gradient(to top, var(--water-low) 0%, #f87171 100%)';
            } else if (percentage < 80) {
                waterLevel.style.background = 'linear-gradient(to top, var(--water-medium) 0%, #60a5fa 100%)';
            } else {
                waterLevel.style.background = 'linear-gradient(to top, var(--water-high) 0%, #34d399 100%)';
            }
        }
        
        // Update dashboard with new data
        function updateDashboard(data) {
            const percentage = data.percentage || 0;
            const rawValue = data.raw_value || 0;
            const filteredValue = data.filtered_value || 0;
            
            // Update displays
            document.getElementById('percentageDisplay').innerHTML = percentage.toFixed(1) + '<span class="stat-unit">%</span>';
            document.getElementById('rawValue').textContent = rawValue;
            document.getElementById('filteredValue').textContent = filteredValue.toFixed(2);
            
            // Update water level visualization
            const waterLevel = document.getElementById('waterLevel');
            waterLevel.style.height = percentage + '%';
            updateWaterColor(percentage);
            
            // Update status
            const statusIndicator = document.getElementById('statusIndicator');
            const statusText = document.getElementById('statusText');
            
            if (data.last_update) {
                const now = new Date();
                const lastUpdate = new Date(data.last_update);
                const timeSinceUpdate = now - lastUpdate;
                
                if (timeSinceUpdate < 5000) {
                    statusIndicator.className = 'status-dot connected';
                    statusText.textContent = 'Connected • ' + lastUpdate.toLocaleTimeString();
                } else {
                    statusIndicator.className = 'status-dot disconnected';
                    statusText.textContent = 'Disconnected • No data received';
                }
            } else {
                statusIndicator.className = 'status-dot disconnected';
                statusText.textContent = 'Waiting for data...';
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
                document.getElementById('statusIndicator').className = 'status-dot disconnected';
                document.getElementById('statusText').textContent = 'Error connecting to server';
            }
        }
        
        // Update calibration
        async function updateCalibration() {
            const minValue = parseInt(document.getElementById('minValue').value);
            const maxValue = parseInt(document.getElementById('maxValue').value);
            
            if (minValue >= maxValue) {
                showToast('Min value must be less than max value', 'error');
                return;
            }
            
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
                    showToast('Calibration updated successfully!', 'success');
                } else {
                    showToast('Error updating calibration', 'error');
                }
            } catch (error) {
                console.error('Error updating calibration:', error);
                showToast('Error updating calibration', 'error');
            }
        }
        
        // Load calibration values on page load
        async function loadCalibration() {
            try {
                const response = await fetch('/api/calibration');
                const data = await response.json();
                document.getElementById('minValue').value = data.min;
                document.getElementById('maxValue').value = data.max;
            } catch (error) {
                console.error('Error loading calibration:', error);
            }
        }
        
        // Fetch data every second
        setInterval(fetchData, 1000);
        fetchData(); // Initial fetch
        loadCalibration(); // Load calibration values
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

