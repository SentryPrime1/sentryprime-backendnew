from flask import Blueprint, jsonify, request
from functools import wraps
from src.models.user import User, Website, ScanResult, Subscription, db
import re

auth_bp = Blueprint('auth', __name__)

def token_required(f):
    """Decorator to require authentication token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            current_user = User.verify_token(token)
            if not current_user:
                return jsonify({'error': 'Token is invalid'}), 401
                
        except Exception as e:
            return jsonify({'error': 'Token is invalid'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        
        # Validate email format
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password strength
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 409
        
        # Create new user
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Generate token
        token = user.generate_token()
        
        return jsonify({
            'message': 'User registered successfully',
            'token': token,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Generate token
        token = user.generate_token()
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Login failed'}), 500

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """Get current user profile"""
    return jsonify({
        'user': current_user.to_dict()
    }), 200

@auth_bp.route('/me', methods=['PUT'])
@token_required
def update_profile(current_user):
    """Update user profile"""
    try:
        data = request.get_json()
        
        if data.get('first_name'):
            current_user.first_name = data['first_name'].strip()
        if data.get('last_name'):
            current_user.last_name = data['last_name'].strip()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': current_user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Profile update failed'}), 500

@auth_bp.route('/websites', methods=['GET'])
@token_required
def get_user_websites(current_user):
    """Get user's websites"""
    websites = Website.query.filter_by(user_id=current_user.id).order_by(Website.created_at.desc()).all()
    return jsonify({
        'websites': [website.to_dict() for website in websites]
    }), 200

@auth_bp.route('/websites', methods=['POST'])
@token_required
def add_website(current_user):
    """Add a new website"""
    try:
        data = request.get_json()
        
        if not data or not data.get('url') or not data.get('name'):
            return jsonify({'error': 'URL and name are required'}), 400
        
        url = data['url'].strip()
        name = data['name'].strip()
        
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Check subscription limits
        website_count = Website.query.filter_by(user_id=current_user.id, is_active=True).count()
        subscription = current_user.subscription
        
        if subscription:
            limits = {
                'starter': 1,
                'pro': 3,
                'agency': 10
            }
            limit = limits.get(subscription.plan, 1)
            
            if website_count >= limit:
                return jsonify({'error': f'Website limit reached for {subscription.plan} plan'}), 403
        else:
            return jsonify({'error': 'Active subscription required'}), 403
        
        # Create website
        website = Website(
            user_id=current_user.id,
            url=url,
            name=name,
            scan_frequency=data.get('scan_frequency', 'monthly')
        )
        
        db.session.add(website)
        db.session.commit()
        
        return jsonify({
            'message': 'Website added successfully',
            'website': website.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add website'}), 500

@auth_bp.route('/websites/<int:website_id>', methods=['DELETE'])
@token_required
def delete_website(current_user, website_id):
    """Delete a website"""
    try:
        website = Website.query.filter_by(id=website_id, user_id=current_user.id).first()
        
        if not website:
            return jsonify({'error': 'Website not found'}), 404
        
        db.session.delete(website)
        db.session.commit()
        
        return jsonify({'message': 'Website deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete website'}), 500

@auth_bp.route('/websites/<int:website_id>/scans', methods=['GET'])
@token_required
def get_website_scans(current_user, website_id):
    """Get scan history for a website"""
    website = Website.query.filter_by(id=website_id, user_id=current_user.id).first()
    
    if not website:
        return jsonify({'error': 'Website not found'}), 404
    
    scans = ScanResult.query.filter_by(website_id=website_id).order_by(ScanResult.created_at.desc()).all()
    
    return jsonify({
        'website': website.to_dict(),
        'scans': [scan.to_dict() for scan in scans]
    }), 200
