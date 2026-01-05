from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
import json
from collections import deque
import threading
import os
import logging
from functools import wraps
from time import time
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure Flask to use templates directory
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'))

# Configure CORS - restrict to local network by default
# Allow all origins only for development (set via environment variable)
cors_origins = os.getenv('CORS_ORIGINS', '*')  # Default to * for local development
if cors_origins != '*':
    cors_origins = cors_origins.split(',')
CORS(app, origins=cors_origins)

# Rate limiting (simple in-memory implementation)
rate_limit_store = {}
RATE_LIMIT_WINDOW = 60  # 60 seconds
RATE_LIMIT_MAX_REQUESTS = 100  # Max requests per window per IP

def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr
        current_time = time()
        
        # Clean old entries
        if client_ip in rate_limit_store:
            rate_limit_store[client_ip] = [
                t for t in rate_limit_store[client_ip] 
                if current_time - t < RATE_LIMIT_WINDOW
            ]
        else:
            rate_limit_store[client_ip] = []
        
        # Check rate limit
        if len(rate_limit_store[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return jsonify({'status': 'error', 'message': 'Rate limit exceeded'}), 429
        
        # Add current request
        rate_limit_store[client_ip].append(current_time)
        
        return f(*args, **kwargs)
    return decorated_function

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
    try:
        return render_template('dashboard.html')
    except Exception as e:
        logger.error(f"Error rendering template: {str(e)}", exc_info=True)
        return f"<h1>Error</h1><p>Template not found or error loading template: {str(e)}</p>", 500

@app.route('/api/data', methods=['POST'])
@rate_limit
def receive_data():
    """Receive data from ESP32"""
    try:
        if not request.is_json:
            return jsonify({'status': 'error', 'message': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        if data is None:
            return jsonify({'status': 'error', 'message': 'Invalid JSON'}), 400
        
        # Validate and sanitize input
        try:
            raw_value = int(data.get('raw_value', 0))
            filtered_value = float(data.get('filtered_value', raw_value))
        except (ValueError, TypeError):
            return jsonify({'status': 'error', 'message': 'Invalid data types'}), 400
        
        # Validate reasonable ranges
        if raw_value < 0 or raw_value > 4095:  # ESP32 ADC max value
            logger.warning(f"Invalid raw_value received: {raw_value}")
            raw_value = max(0, min(4095, raw_value))
        
        if filtered_value < 0 or filtered_value > 4095:
            filtered_value = max(0, min(4095, filtered_value))
        
        # Calculate percentage based on calibration
        clamped_value = max(calibration['min'], min(filtered_value, calibration['max']))
        
        # Calculate percentage
        if calibration['max'] != calibration['min']:
            percentage = ((clamped_value - calibration['min']) / (calibration['max'] - calibration['min'])) * 100
            percentage = max(0, min(100, percentage))  # Clamp to 0-100%
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
        
        logger.debug(f"Data received: raw={raw_value}, filtered={filtered_value:.2f}, percentage={percentage:.2f}%")
        
        return jsonify({'status': 'success', 'percentage': percentage}), 200
        
    except Exception as e:
        logger.error(f"Error processing data: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/api/latest', methods=['GET'])
def get_latest_data():
    """Get latest sensor data"""
    return jsonify(latest_data)

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get historical data"""
    return jsonify(list(data_history))

@app.route('/api/calibration', methods=['GET', 'POST'])
@rate_limit
def handle_calibration():
    """Get or update calibration values"""
    if request.method == 'POST':
        if not request.is_json:
            return jsonify({'status': 'error', 'message': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        if data is None:
            return jsonify({'status': 'error', 'message': 'Invalid JSON'}), 400
        
        try:
            new_min = int(data.get('min', calibration['min']))
            new_max = int(data.get('max', calibration['max']))
        except (ValueError, TypeError):
            return jsonify({'status': 'error', 'message': 'Invalid data types. min and max must be integers'}), 400
        
        # Validate ranges
        if new_min < 0 or new_min > 4095:
            return jsonify({'status': 'error', 'message': 'min must be between 0 and 4095'}), 400
        
        if new_max < 0 or new_max > 4095:
            return jsonify({'status': 'error', 'message': 'max must be between 0 and 4095'}), 400
        
        # Validate min < max
        if new_min >= new_max:
            return jsonify({'status': 'error', 'message': 'min must be less than max'}), 400
        
        calibration['min'] = new_min
        calibration['max'] = new_max
        
        logger.info(f"Calibration updated: min={new_min}, max={new_max}")
        
        return jsonify({'status': 'success', 'calibration': calibration})
    else:
        return jsonify(calibration)

if __name__ == '__main__':
    # Get configuration from environment variables
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', '5000'))
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info("=" * 50)
    logger.info("Water Level Dashboard Server")
    logger.info("=" * 50)
    logger.info(f"Dashboard URL: http://localhost:{port}")
    logger.info(f"API Endpoint: http://localhost:{port}/api/data")
    logger.info("\nMake sure to update the ESP32 code with your computer's IP address!")
    logger.info("Find your IP: Windows: ipconfig, Linux/Mac: ifconfig")
    logger.info("=" * 50)
    
    if debug_mode:
        logger.warning("DEBUG MODE IS ENABLED - Not recommended for production!")
    
    app.run(host=host, port=port, debug=debug_mode)

