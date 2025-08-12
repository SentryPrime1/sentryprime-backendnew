"""
SentryPrime Enhanced Backend
Flask backend with dashboard data management and in-memory storage
Includes user websites, scan history, and dashboard statistics
"""

import os
import jwt
import re
import random
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sentryprime-enhanced-backend-2025')

# Enable CORS for all routes
CORS(app, 
     origins=["*", "https://sentryprime-frontend.vercel.app", "http://localhost:3000", "http://localhost:5173"],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization'],
     supports_credentials=False)

# In-memory storage (will be replaced with database later)
users_db = {}
websites_db = {}
scans_db = {}
user_counter = 1
website_counter = 1
scan_counter = 1

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

def get_user_from_request():
    """Get user from Authorization header"""
    token = request.headers.get('Authorization')
    if not token:
        return None
    return verify_token(token)

def generate_mock_scan_data(url, user_id):
    """Generate realistic mock scan data"""
    # Random but realistic violation counts
    serious_violations = random.randint(15, 300)
    moderate_violations = random.randint(5, 50)
    minor_violations = random.randint(0, 20)
    total_violations = serious_violations + moderate_violations + minor_violations
    
    # Calculate compliance score based on violations
    compliance_score = max(0, 100 - (serious_violations * 2 + moderate_violations * 1 + minor_violations * 0.5))
    compliance_score = round(compliance_score)
    
    # Calculate lawsuit risk based on violations
    if total_violations == 0:
        risk_level = "MINIMAL"
        probability = random.randint(5, 15)
        total_cost = random.randint(5000, 15000)
    elif total_violations < 50:
        risk_level = "LOW"
        probability = random.randint(20, 40)
        total_cost = random.randint(25000, 75000)
    elif total_violations < 150:
        risk_level = "MODERATE"
        probability = random.randint(45, 65)
        total_cost = random.randint(75000, 200000)
    else:
        risk_level = "HIGH"
        probability = random.randint(70, 95)
        total_cost = random.randint(200000, 500000)
    
    pages_scanned = random.randint(10, 100)
    scan_duration = round(random.uniform(15.0, 120.0), 1)
    
    return {
        "url": url,
        "pages_scanned": pages_scanned,
        "scan_duration": f"{scan_duration} seconds",
        "compliance_score": compliance_score,
        "violations": {
            "serious": serious_violations,
            "moderate": moderate_violations,
            "minor": minor_violations,
            "total": total_violations
        },
        "lawsuit_risk": {
            "probability": probability,
            "risk_level": risk_level,
            "total_cost": total_cost,
            "settlement_amount": round(total_cost * 0.2),
            "legal_fees": round(total_cost * 0.5),
            "remediation_cost": round(total_cost * 0.3),
            "clean_website": total_violations == 0
        },
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id
    }

def initialize_sample_data():
    """Initialize sample data for testing"""
    # Create sample user if none exist
    if not users_db:
        sample_user = {
            'id': 1,
            'email': 'demo@sentryprime.com',
            'password_hash': generate_password_hash('demo123'),
            'first_name': 'Demo',
            'last_name': 'User',
            'created_at': (datetime.utcnow() - timedelta(days=30)).isoformat(),
            'email_verified': True
        }
        users_db[1] = sample_user
        
        # Add sample websites for demo user
        sample_websites = [
            {'url': 'https://example.com', 'name': 'Example Corp'},
            {'url': 'https://mystore.com', 'name': 'My Online Store'},
            {'url': 'https://blog.example.com', 'name': 'Company Blog'}
        ]
        
        global website_counter, scan_counter
        for site in sample_websites:
            website_id = website_counter
            website_counter += 1
            
            websites_db[website_id] = {
                'id': website_id,
                'user_id': 1,
                'url': site['url'],
                'name': site['name'],
                'created_at': (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat(),
                'last_scan': (datetime.utcnow() - timedelta(days=random.randint(1, 7))).isoformat(),
                'status': 'active'
            }
            
            # Add sample scans for each website
            for i in range(random.randint(2, 5)):
                scan_id = scan_counter
                scan_counter += 1
                
                scan_date = datetime.utcnow() - timedelta(days=random.randint(1, 30))
                scan_data = generate_mock_scan_data(site['url'], 1)
                
                scans_db[scan_id] = {
                    'id': scan_id,
                    'user_id': 1,
                    'website_id': website_id,
                    'url': site['url'],
                    'scan_date': scan_date.isoformat(),
                    'compliance_score': scan_data['compliance_score'],
                    'total_violations': scan_data['violations']['total'],
                    'serious_violations': scan_data['violations']['serious'],
                    'moderate_violations': scan_data['violations']['moderate'],
                    'risk_level': scan_data['lawsuit_risk']['risk_level'],
                    'pages_scanned': scan_data['pages_scanned'],
                    'scan_duration': scan_data['scan_duration'],
                    'full_results': scan_data
                }

# Initialize sample data on startup
initialize_sample_data()

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'SentryPrime Enhanced Backend',
        'version': '2.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'users_count': len(users_db),
        'websites_count': len(websites_db),
        'scans_count': len(scans_db)
    }), 200

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

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
        user = get_user_from_request()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
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

# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@app.route('/api/dashboard/stats', methods=['GET', 'OPTIONS'])
def get_dashboard_stats():
    """Get dashboard overview statistics"""
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        user = get_user_from_request()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        user_id = user['id']
        
        # Get user's websites
        user_websites = [w for w in websites_db.values() if w['user_id'] == user_id]
        
        # Get user's scans
        user_scans = [s for s in scans_db.values() if s['user_id'] == user_id]
        
        # Calculate statistics
        total_websites = len(user_websites)
        total_scans = len(user_scans)
        
        # Calculate average compliance score
        if user_scans:
            avg_compliance = sum(s['compliance_score'] for s in user_scans) / len(user_scans)
            avg_compliance = round(avg_compliance)
        else:
            avg_compliance = 0
        
        # Calculate total violations
        total_violations = sum(s['total_violations'] for s in user_scans)
        
        # Get recent activity (last 5 scans)
        recent_scans = sorted(user_scans, key=lambda x: x['scan_date'], reverse=True)[:5]
        recent_activity = []
        
        for scan in recent_scans:
            website = next((w for w in user_websites if w['id'] == scan['website_id']), None)
            recent_activity.append({
                'id': scan['id'],
                'website_name': website['name'] if website else scan['url'],
                'url': scan['url'],
                'scan_date': scan['scan_date'],
                'compliance_score': scan['compliance_score'],
                'risk_level': scan['risk_level'],
                'violations': scan['total_violations']
            })
        
        # Compliance trend data (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_scans_data = [
            s for s in user_scans 
            if datetime.fromisoformat(s['scan_date'].replace('Z', '+00:00')) >= thirty_days_ago
        ]
        
        # Group by date for trend chart
        trend_data = {}
        for scan in recent_scans_data:
            date = scan['scan_date'][:10]  # Get date part only
            if date not in trend_data:
                trend_data[date] = []
            trend_data[date].append(scan['compliance_score'])
        
        # Calculate daily averages
        compliance_trend = []
        for date, scores in sorted(trend_data.items()):
            avg_score = sum(scores) / len(scores)
            compliance_trend.append({
                'date': date,
                'compliance_score': round(avg_score)
            })
        
        return jsonify({
            'overview': {
                'total_websites': total_websites,
                'total_scans': total_scans,
                'avg_compliance_score': avg_compliance,
                'total_violations': total_violations
            },
            'recent_activity': recent_activity,
            'compliance_trend': compliance_trend,
            'quick_stats': {
                'websites_monitored': total_websites,
                'scans_this_month': len([s for s in user_scans if datetime.fromisoformat(s['scan_date'].replace('Z', '+00:00')) >= datetime.utcnow() - timedelta(days=30)]),
                'avg_pages_per_scan': round(sum(s['pages_scanned'] for s in user_scans) / len(user_scans)) if user_scans else 0,
                'last_scan_date': max([s['scan_date'] for s in user_scans]) if user_scans else None
            }
        }), 200
        
    except Exception as e:
        app.logger.error(f"Dashboard stats error: {str(e)}")
        return jsonify({'error': 'Failed to get dashboard statistics'}), 500

@app.route('/api/dashboard/websites', methods=['GET', 'OPTIONS'])
def get_user_websites():
    """Get user's monitored websites"""
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        user = get_user_from_request()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        user_id = user['id']
        
        # Get user's websites
        user_websites = [w for w in websites_db.values() if w['user_id'] == user_id]
        
        # Enhance with latest scan data
        websites_with_data = []
        for website in user_websites:
            # Get latest scan for this website
            website_scans = [s for s in scans_db.values() if s['website_id'] == website['id']]
            latest_scan = max(website_scans, key=lambda x: x['scan_date']) if website_scans else None
            
            website_data = {
                'id': website['id'],
                'url': website['url'],
                'name': website['name'],
                'created_at': website['created_at'],
                'last_scan': website['last_scan'],
                'status': website['status'],
                'total_scans': len(website_scans)
            }
            
            if latest_scan:
                website_data.update({
                    'compliance_score': latest_scan['compliance_score'],
                    'total_violations': latest_scan['total_violations'],
                    'risk_level': latest_scan['risk_level'],
                    'last_scan_date': latest_scan['scan_date']
                })
            else:
                website_data.update({
                    'compliance_score': None,
                    'total_violations': 0,
                    'risk_level': 'UNKNOWN',
                    'last_scan_date': None
                })
            
            websites_with_data.append(website_data)
        
        return jsonify({
            'websites': websites_with_data,
            'total_count': len(websites_with_data)
        }), 200
        
    except Exception as e:
        app.logger.error(f"Get websites error: {str(e)}")
        return jsonify({'error': 'Failed to get websites'}), 500

@app.route('/api/dashboard/websites', methods=['POST'])
def add_website():
    """Add a new website to monitor"""
    
    try:
        user = get_user_from_request()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        url = data.get('url', '').strip()
        name = data.get('name', '').strip()
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Generate name if not provided
        if not name:
            name = url.replace('https://', '').replace('http://', '').replace('www.', '')
        
        # Check if website already exists for this user
        for website in websites_db.values():
            if website['user_id'] == user['id'] and website['url'] == url:
                return jsonify({'error': 'Website already exists'}), 409
        
        # Create new website
        global website_counter
        website_id = website_counter
        website_counter += 1
        
        new_website = {
            'id': website_id,
            'user_id': user['id'],
            'url': url,
            'name': name,
            'created_at': datetime.utcnow().isoformat(),
            'last_scan': None,
            'status': 'active'
        }
        
        websites_db[website_id] = new_website
        
        return jsonify({
            'message': 'Website added successfully',
            'website': new_website
        }), 201
        
    except Exception as e:
        app.logger.error(f"Add website error: {str(e)}")
        return jsonify({'error': 'Failed to add website'}), 500

@app.route('/api/dashboard/scans', methods=['GET', 'OPTIONS'])
def get_user_scans():
    """Get user's scan history"""
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        user = get_user_from_request()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        user_id = user['id']
        
        # Get user's scans
        user_scans = [s for s in scans_db.values() if s['user_id'] == user_id]
        
        # Sort by date (newest first)
        user_scans.sort(key=lambda x: x['scan_date'], reverse=True)
        
        # Enhance with website names
        scans_with_data = []
        for scan in user_scans:
            website = next((w for w in websites_db.values() if w['id'] == scan['website_id']), None)
            
            scan_data = {
                'id': scan['id'],
                'website_id': scan['website_id'],
                'website_name': website['name'] if website else 'Unknown',
                'url': scan['url'],
                'scan_date': scan['scan_date'],
                'compliance_score': scan['compliance_score'],
                'total_violations': scan['total_violations'],
                'serious_violations': scan['serious_violations'],
                'moderate_violations': scan['moderate_violations'],
                'risk_level': scan['risk_level'],
                'pages_scanned': scan['pages_scanned'],
                'scan_duration': scan['scan_duration']
            }
            
            scans_with_data.append(scan_data)
        
        return jsonify({
            'scans': scans_with_data,
            'total_count': len(scans_with_data)
        }), 200
        
    except Exception as e:
        app.logger.error(f"Get scans error: {str(e)}")
        return jsonify({'error': 'Failed to get scan history'}), 500

@app.route('/api/dashboard/scan', methods=['POST'])
def trigger_scan():
    """Trigger a new scan for a website"""
    
    try:
        user = get_user_from_request()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        website_id = data.get('website_id')
        url = data.get('url')
        
        if not website_id and not url:
            return jsonify({'error': 'Website ID or URL is required'}), 400
        
        # Find website
        website = None
        if website_id:
            website = websites_db.get(website_id)
            if not website or website['user_id'] != user['id']:
                return jsonify({'error': 'Website not found'}), 404
            url = website['url']
        
        # Generate scan results
        scan_data = generate_mock_scan_data(url, user['id'])
        
        # Create scan record
        global scan_counter
        scan_id = scan_counter
        scan_counter += 1
        
        new_scan = {
            'id': scan_id,
            'user_id': user['id'],
            'website_id': website_id,
            'url': url,
            'scan_date': datetime.utcnow().isoformat(),
            'compliance_score': scan_data['compliance_score'],
            'total_violations': scan_data['violations']['total'],
            'serious_violations': scan_data['violations']['serious'],
            'moderate_violations': scan_data['violations']['moderate'],
            'risk_level': scan_data['lawsuit_risk']['risk_level'],
            'pages_scanned': scan_data['pages_scanned'],
            'scan_duration': scan_data['scan_duration'],
            'full_results': scan_data
        }
        
        scans_db[scan_id] = new_scan
        
        # Update website last_scan timestamp
        if website:
            website['last_scan'] = new_scan['scan_date']
        
        return jsonify({
            'message': 'Scan completed successfully',
            'scan': new_scan,
            'full_results': scan_data
        }), 201
        
    except Exception as e:
        app.logger.error(f"Trigger scan error: {str(e)}")
        return jsonify({'error': 'Failed to trigger scan'}), 500

# ============================================================================
# LEGACY SCAN ENDPOINT (for compatibility)
# ============================================================================

@app.route('/api/scan/premium', methods=['POST', 'OPTIONS'])
def premium_scan():
    """Premium scan endpoint (legacy compatibility)"""
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        data = request.get_json()
        url = data.get('url', '')
        max_pages = data.get('max_pages', 50)
        
        # Try to get user (optional for legacy compatibility)
        user = get_user_from_request()
        user_id = user['id'] if user else None
        
        # Generate scan result
        scan_data = generate_mock_scan_data(url, user_id)
        
        # If user is authenticated, save the scan
        if user_id:
            global scan_counter
            scan_id = scan_counter
            scan_counter += 1
            
            new_scan = {
                'id': scan_id,
                'user_id': user_id,
                'website_id': None,  # Not associated with a specific website
                'url': url,
                'scan_date': datetime.utcnow().isoformat(),
                'compliance_score': scan_data['compliance_score'],
                'total_violations': scan_data['violations']['total'],
                'serious_violations': scan_data['violations']['serious'],
                'moderate_violations': scan_data['violations']['moderate'],
                'risk_level': scan_data['lawsuit_risk']['risk_level'],
                'pages_scanned': scan_data['pages_scanned'],
                'scan_duration': scan_data['scan_duration'],
                'full_results': scan_data
            }
            
            scans_db[scan_id] = new_scan
        
        return jsonify(scan_data), 200
        
    except Exception as e:
        app.logger.error(f"Premium scan error: {str(e)}")
        return jsonify({'error': 'Scan failed'}), 500

# ============================================================================
# ADMIN/DEBUG ENDPOINTS
# ============================================================================

@app.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    """Get admin statistics"""
    return jsonify({
        'total_users': len(users_db),
        'total_websites': len(websites_db),
        'total_scans': len(scans_db),
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

