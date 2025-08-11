"""
SentryPrime Simple Backend
Minimal Flask backend with in-memory authentication
Ready for immediate deployment and future database upgrade
"""

import os
import jwt
import re
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sentryprime-simple-backend-2025')

# Enable CORS for all routes
CORS(app, 
     origins=["*", "https://sentryprime-frontend.vercel.app", "http://localhost:3000", "http://localhost:5173"],
     methods=['GET', 'POST', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization'],
     supports_credentials=False)

# In-memory user storage (will be replaced with database later)
users_db = {}
user_counter = 1

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def generate_token(user_id, email):
    """Generate JWT token"""
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.utcnow() + timedelta(days=7)  # 7 days expiry
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    """Verify JWT token and return user"""
    try:
        if token.startswith('Bearer '):
            token = token[7:]
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = payload['user_id']
        return users_db.get(user_id)
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'SentryPrime Simple Backend',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'users_count': len(users_db)
    }), 200

@app.route('/api/auth/register', methods=['POST', 'OPTIONS'])
def register():
    """Register a new user"""
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Extract and validate fields
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        
        # Validate required fields
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Validate email format
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password strength
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        # Check if user already exists
        for user in users_db.values():
            if user['email'] == email:
                return jsonify({'error': 'Email already registered'}), 409
        
        # Create new user
        global user_counter
        user_id = user_counter
        user_counter += 1
        
        new_user = {
            'id': user_id,
            'email': email,
            'password_hash': generate_password_hash(password),
            'first_name': first_name,
            'last_name': last_name,
            'created_at': datetime.utcnow().isoformat(),
            'email_verified': True  # Auto-verify for simplicity
        }
        
        users_db[user_id] = new_user
        
        # Generate token
        token = generate_token(user_id, email)
        
        # Return success response
        return jsonify({
            'message': 'User registered successfully',
            'token': token,
            'user': {
                'id': user_id,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'created_at': new_user['created_at']
            }
        }), 201
        
    except Exception as e:
        app.logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed due to server error'}), 500

@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    """Login user"""
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find user by email
        user = None
        for u in users_db.values():
            if u['email'] == email:
                user = u
                break
        
        if not user or not check_password_hash(user['password_hash'], password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Generate token
        token = generate_token(user['id'], user['email'])
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'created_at': user['created_at']
            }
        }), 200
        
    except Exception as e:
        app.logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed due to server error'}), 500

@app.route('/api/auth/me', methods=['GET', 'OPTIONS'])
def get_current_user():
    """Get current user profile"""
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        # Get token from Authorization header
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        # Verify token and get user
        user = verify_token(token)
        if not user:
            return jsonify({'error': 'Token is invalid'}), 401
        
        return jsonify({
            'user': {
                'id': user['id'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'created_at': user['created_at']
            }
        }), 200
        
    except Exception as e:
        app.logger.error(f"Get user error: {str(e)}")
        return jsonify({'error': 'Failed to get user profile'}), 500

@app.route('/api/scan/premium', methods=['POST', 'OPTIONS'])
def premium_scan():
    """Premium scan endpoint (placeholder for now)"""
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        data = request.get_json()
        url = data.get('url', '')
        max_pages = data.get('max_pages', 50)
        
        # Mock scan result for testing
        mock_result = {
            "scan_summary": {
                "url": url,
                "pages_scanned": 40,
                "scan_duration": "44.6 seconds",
                "compliance_score": 0,
                "total_violations": 318
            },
            "violations_by_severity": {
                "critical": 0,
                "serious": 291,
                "moderate": 27,
                "minor": 0
            },
            "lawsuit_risk": {
                "total_exposure": 375000,
                "probability": 88,
                "risk_level": "EXTREME",
                "breakdown": {
                    "settlement_costs": 75000,
                    "legal_fees": 187500,
                    "remediation_costs": 112500
                }
            },
            "business_impact": {
                "reputation_damage": "High",
                "customer_loss_risk": "Significant",
                "compliance_urgency": "Immediate action required"
            }
        }
        
        return jsonify(mock_result), 200
        
    except Exception as e:
        app.logger.error(f"Scan error: {str(e)}")
        return jsonify({'error': 'Scan failed'}), 500

@app.route('/api/users/stats', methods=['GET'])
def get_stats():
    """Get user statistics (admin endpoint)"""
    return jsonify({
        'total_users': len(users_db),
        'users': [
            {
                'id': user['id'],
                'email': user['email'],
                'name': f"{user['first_name']} {user['last_name']}",
                'created_at': user['created_at']
            }
            for user in users_db.values()
        ]
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

