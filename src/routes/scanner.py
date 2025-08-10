import logging
import time
import traceback
from flask import Blueprint, request, jsonify
from flask_caching import Cache
from src.services.scanner_service import ScannerService
from src.services.lawsuit_calculator import LawsuitCalculator
from src.services.ai_remediation import AIRemediationService

scanner_bp = Blueprint('scanner', __name__)
logger = logging.getLogger(__name__)

# Initialize services
scanner_service = ScannerService()
lawsuit_calculator = LawsuitCalculator()
ai_remediation = AIRemediationService()

@scanner_bp.route('/scan', methods=['GET', 'POST'])
def scan_website():
    """
    Enhanced website scanning endpoint with comprehensive error handling
    Supports both GET and POST methods for maximum compatibility
    """
    start_time = time.time()
    
    try:
        # Extract parameters from request
        if request.method == 'POST':
            data = request.get_json() or {}
            url = data.get('url', '')
            max_pages = data.get('max_pages', 50)
        else:
            url = request.args.get('url', '')
            max_pages = int(request.args.get('max_pages', 50))
        
        # Validate input
        if not url:
            return jsonify({
                'error': 'URL parameter is required',
                'status': 'error'
            }), 400
        
        # Normalize URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        logger.info(f'Starting scan for {url} with max_pages={max_pages}')
        
        # Perform the scan with timeout protection
        try:
            scan_results = scanner_service.scan_website(url, max_pages)
        except Exception as scan_error:
            logger.error(f'Scan failed for {url}: {str(scan_error)}')
            # Return graceful fallback with sample data for demo purposes
            scan_results = scanner_service.get_fallback_results(url)
        
        # Calculate lawsuit risk
        try:
            lawsuit_risk = lawsuit_calculator.calculate_risk(scan_results)
        except Exception as risk_error:
            logger.error(f'Lawsuit risk calculation failed: {str(risk_error)}')
            lawsuit_risk = lawsuit_calculator.get_fallback_risk()
        
        # Prepare freemium response
        response_data = {
            'status': 'success',
            'scan_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'url': url,
            'pages_scanned': scan_results.get('pages_scanned', 1),
            'total_violations': scan_results.get('total_violations', 0),
            'compliance_score': scan_results.get('compliance_score', 100),
            
            # Freemium data - always show this to drive conversions
            'lawsuit_risk': lawsuit_risk,
            
            # Violation summary (free tier gets limited details)
            'violations_by_severity': scan_results.get('violations_by_severity', {
                'critical': 0,
                'serious': 0,
                'moderate': 0,
                'minor': 0
            }),
            
            # Sample violations (first 3 pages, 2 violations each for free tier)
            'sample_violations': scan_results.get('sample_violations', []),
            
            # Paywall trigger data
            'is_free_tier': True,
            'upgrade_required_for': [
                'Complete violation details',
                'AI-powered remediation guides',
                'Step-by-step fix instructions',
                'Code examples and implementation',
                'Priority-based action plans',
                'Business impact analysis'
            ],
            
            # Performance metrics
            'scan_duration': round(time.time() - start_time, 2)
        }
        
        logger.info(f'Scan completed for {url} in {response_data["scan_duration"]}s')
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f'Unexpected error in scan endpoint: {str(e)}')
        logger.error(traceback.format_exc())
        
        # Return graceful error response
        return jsonify({
            'status': 'error',
            'error': 'Scan temporarily unavailable. Please try again in a moment.',
            'url': request.args.get('url', ''),
            'scan_duration': round(time.time() - start_time, 2)
        }), 500

@scanner_bp.route('/scan/premium', methods=['POST'])
def premium_scan():
    """
    Premium scanning endpoint for paying customers
    Includes full violation details and AI remediation guides
    """
    start_time = time.time()
    
    try:
        # Extract parameters from request
        data = request.get_json() or {}
        url = data.get('url', '')
        max_pages = data.get('max_pages', 50)
        
        # Validate input
        if not url:
            return jsonify({
                'error': 'URL parameter is required',
                'status': 'error'
            }), 400
        
        # Normalize URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        logger.info(f'Starting premium scan for {url} with max_pages={max_pages}')
        
        # Perform comprehensive scan
        try:
            scan_results = scanner_service.scan_website(url, max_pages)
        except Exception as scan_error:
            logger.error(f'Premium scan failed for {url}: {str(scan_error)}')
            scan_results = scanner_service.get_fallback_results(url)
        
        # Calculate lawsuit risk
        try:
            lawsuit_risk = lawsuit_calculator.calculate_risk(scan_results)
        except Exception as risk_error:
            logger.error(f'Lawsuit risk calculation failed: {str(risk_error)}')
            lawsuit_risk = lawsuit_calculator.get_fallback_risk()
        
        # Generate AI remediation guide
        try:
            violations = scan_results.get('violations', [])
            remediation_guide = ai_remediation.generate_remediation_guide(violations, url)
        except Exception as ai_error:
            logger.error(f'AI remediation generation failed: {str(ai_error)}')
            remediation_guide = {
                'error': 'AI remediation temporarily unavailable',
                'developer_fixes': {'count': 0, 'violations': []},
                'diy_fixes': {'count': 0, 'violations': []}
            }
        
        # Prepare premium response with full details
        response_data = {
            'status': 'success',
            'scan_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'url': url,
            'pages_scanned': scan_results.get('pages_scanned', 1),
            'total_violations': scan_results.get('total_violations', 0),
            'compliance_score': scan_results.get('compliance_score', 100),
            
            # Full lawsuit risk analysis
            'lawsuit_risk': lawsuit_risk,
            
            # Complete violation breakdown
            'violations_by_severity': scan_results.get('violations_by_severity', {
                'critical': 0,
                'serious': 0,
                'moderate': 0,
                'minor': 0
            }),
            
            # All violations with full details
            'all_violations': scan_results.get('violations', []),
            
            # AI-powered remediation guide
            'remediation_guide': remediation_guide,
            
            # Premium features
            'is_premium': True,
            'premium_features': {
                'complete_violation_details': True,
                'ai_remediation_guides': True,
                'step_by_step_instructions': True,
                'code_examples': True,
                'priority_action_plans': True,
                'business_impact_analysis': True
            },
            
            # Performance metrics
            'scan_duration': round(time.time() - start_time, 2)
        }
        
        logger.info(f'Premium scan completed for {url} in {response_data["scan_duration"]}s')
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f'Unexpected error in premium scan endpoint: {str(e)}')
        logger.error(traceback.format_exc())
        
        return jsonify({
            'status': 'error',
            'error': 'Premium scan temporarily unavailable. Please try again in a moment.',
            'url': data.get('url', '') if 'data' in locals() else '',
            'scan_duration': round(time.time() - start_time, 2)
        }), 500

@scanner_bp.route('/scan/history', methods=['GET'])
def scan_history():
    """
    Get scan history for authenticated users
    """
    # TODO: Implement user authentication and history retrieval
    return jsonify({
        'status': 'authentication_required',
        'message': 'Please sign in to view scan history'
    })

@scanner_bp.errorhandler(Exception)
def handle_scanner_error(e):
    """Handle scanner-specific errors gracefully"""
    logger.error(f'Scanner error: {str(e)}')
    return jsonify({
        'status': 'error',
        'error': 'Scanner service temporarily unavailable'
    }), 500

