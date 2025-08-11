from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import jwt
import os

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    email_verified = db.Column(db.Boolean, default=False)
    stripe_customer_id = db.Column(db.String(100), nullable=True)
    
    # Relationships
    websites = db.relationship('Website', backref='user', lazy=True, cascade='all, delete-orphan')
    subscription = db.relationship('Subscription', backref='user', uselist=False, cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)

    def generate_token(self):
        """Generate JWT token for authentication"""
        payload = {
            'user_id': self.id,
            'email': self.email,
            'exp': datetime.utcnow().timestamp() + 86400  # 24 hours
        }
        return jwt.encode(payload, os.environ.get('SECRET_KEY', 'sentryprime-secret'), algorithm='HS256')

    @staticmethod
    def verify_token(token):
        """Verify JWT token and return user"""
        try:
            payload = jwt.decode(token, os.environ.get('SECRET_KEY', 'sentryprime-secret'), algorithms=['HS256'])
            return User.query.get(payload['user_id'])
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'email_verified': self.email_verified,
            'subscription': self.subscription.to_dict() if self.subscription else None,
            'websites_count': len(self.websites)
        }

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stripe_subscription_id = db.Column(db.String(100), unique=True, nullable=False)
    plan = db.Column(db.String(50), nullable=False)  # starter, pro, agency
    status = db.Column(db.String(50), nullable=False)  # active, canceled, past_due
    current_period_start = db.Column(db.DateTime, nullable=False)
    current_period_end = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'plan': self.plan,
            'status': self.status,
            'current_period_start': self.current_period_start.isoformat() if self.current_period_start else None,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Website(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_scan_at = db.Column(db.DateTime, nullable=True)
    scan_frequency = db.Column(db.String(20), default='monthly')  # weekly, monthly
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    scan_results = db.relationship('ScanResult', backref='website', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        latest_scan = self.scan_results[0] if self.scan_results else None
        return {
            'id': self.id,
            'url': self.url,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_scan_at': self.last_scan_at.isoformat() if self.last_scan_at else None,
            'scan_frequency': self.scan_frequency,
            'is_active': self.is_active,
            'latest_scan': latest_scan.to_dict() if latest_scan else None,
            'total_scans': len(self.scan_results)
        }

class ScanResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    website_id = db.Column(db.Integer, db.ForeignKey('website.id'), nullable=False)
    scan_data = db.Column(db.JSON, nullable=False)  # Store the full scan result JSON
    compliance_score = db.Column(db.Integer, nullable=False)
    total_violations = db.Column(db.Integer, nullable=False)
    pages_scanned = db.Column(db.Integer, nullable=False)
    scan_duration = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'compliance_score': self.compliance_score,
            'total_violations': self.total_violations,
            'pages_scanned': self.pages_scanned,
            'scan_duration': self.scan_duration,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'violations_by_severity': self.scan_data.get('violations_by_severity', {}),
            'lawsuit_risk': self.scan_data.get('lawsuit_risk', {})
        }
