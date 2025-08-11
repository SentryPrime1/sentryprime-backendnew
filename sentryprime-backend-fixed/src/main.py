import os
import sys
import logging
from datetime import datetime
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from flask_caching import Cache
from src.models.user import db
from src.routes.scanner import scanner_bp
from src.routes.payments import payments_bp
from src.routes.user import auth_bp

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.FileHandler('sentryprime.log'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Production configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sentryprime-production-key-2025')
# Use PostgreSQL for production, SQLite for development
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Railway PostgreSQL
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Local development
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure caching for better performance
app.config['CACHE_TYPE'] = 'simple'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300
cache = Cache(app)

# Enable CORS for all routes with explicit configuration
CORS(app, 
     origins=["*", "https://sentryprime-frontend.vercel.app", "http://localhost:3000", "http://localhost:5173"],
     methods=['GET', 'POST', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization'],
     supports_credentials=False)

# Register blueprints
app.register_blueprint(scanner_bp, url_prefix='/api')
app.register_blueprint(payments_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')

# Initialize database
db.init_app(app)
with app.app_context():
    db.create_all()

# Health check endpoint for monitoring
@app.route('/health')
def health_check():
    """Health check endpoint for monitoring services"""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
        
    return jsonify({
        'status': 'healthy' if db_status == 'healthy' else 'unhealthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database': db_status,
        'version': '2.0.0'
    })

# API status endpoint
@app.route('/api/status')
def api_status():
    """API status endpoint"""
    return jsonify({
        'service': 'SentryPrime API',
        'status': 'operational',
        'version': '2.0.0',
        'features': {
            'multi_page_scanning': True,
            'lawsuit_risk_calculator': True,
            'ai_remediation_guides': True,
            'stripe_payments': True
        }
    })

# Error handlers for production
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Server Error: {error}')
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f'Unhandled exception: {e}')
    return jsonify({'error': 'An unexpected error occurred'}), 500

# Serve frontend files
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Serve frontend files with proper fallback to index.html"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return jsonify({'error': 'Static folder not configured'}), 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return jsonify({'error': 'Frontend not found'}), 404

if __name__ == '__main__':
    # Production-ready server configuration
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.logger.info(f'Starting SentryPrime server on port {port}')
    app.run(host='0.0.0.0', port=port, debug=debug)

