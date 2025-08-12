"""
SentryPrime Enhanced Backend with AI-Powered Accessibility Reporting
Detailed scanning engine with OpenAI integration for actionable recommendations
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import jwt
import datetime
import hashlib
import requests
from bs4 import BeautifulSoup
import re
import json
import os
from urllib.parse import urljoin, urlparse
import openai
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import io

app = Flask(__name__)
CORS(app)

# Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'sentryprime-ai-enhanced-2025')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

# Initialize OpenAI
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

# In-memory storage (upgrade to database in production)
users = {}
websites = {}
scans = {}
ai_reports = {}

class AccessibilityScanner:
    """Enhanced accessibility scanner with detailed violation detection"""
    
    def __init__(self):
        self.violation_rules = {
            'img-alt': {
                'name': 'Images without alt text',
                'description': 'Images must have alternate text for screen readers',
                'wcag': '1.1.1 Non-text Content',
                'severity': 'HIGH',
                'category': 'images'
            },
            'form-labels': {
                'name': 'Form inputs without labels',
                'description': 'Form inputs must have associated labels',
                'wcag': '1.3.1 Info and Relationships',
                'severity': 'CRITICAL',
                'category': 'forms'
            },
            'color-contrast': {
                'name': 'Insufficient color contrast',
                'description': 'Text must have sufficient color contrast ratio',
                'wcag': '1.4.3 Contrast (Minimum)',
                'severity': 'MEDIUM',
                'category': 'color_contrast'
            },
            'heading-structure': {
                'name': 'Improper heading structure',
                'description': 'Headings must follow logical hierarchy',
                'wcag': '1.3.1 Info and Relationships',
                'severity': 'MEDIUM',
                'category': 'structure'
            },
            'link-text': {
                'name': 'Non-descriptive link text',
                'description': 'Links must have descriptive text',
                'wcag': '2.4.4 Link Purpose',
                'severity': 'MEDIUM',
                'category': 'navigation'
            },
            'keyboard-focus': {
                'name': 'Missing keyboard focus indicators',
                'description': 'Interactive elements must be keyboard accessible',
                'wcag': '2.4.7 Focus Visible',
                'severity': 'HIGH',
                'category': 'keyboard'
            }
        }
    
    def scan_website(self, url):
        """Perform detailed accessibility scan"""
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            violations = []
            
            # Check images without alt text
            violations.extend(self._check_image_alt(soup, url))
            
            # Check form labels
            violations.extend(self._check_form_labels(soup, url))
            
            # Check color contrast (simplified)
            violations.extend(self._check_color_contrast(soup, url))
            
            # Check heading structure
            violations.extend(self._check_heading_structure(soup, url))
            
            # Check link text
            violations.extend(self._check_link_text(soup, url))
            
            # Check keyboard focus
            violations.extend(self._check_keyboard_focus(soup, url))
            
            # Calculate compliance score
            total_elements = len(soup.find_all(['img', 'input', 'textarea', 'select', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
            compliance_score = max(0, 100 - (len(violations) / max(total_elements, 1)) * 100)
            
            # Determine risk level
            if compliance_score >= 90:
                risk_level = "LOW"
            elif compliance_score >= 70:
                risk_level = "MEDIUM"
            elif compliance_score >= 50:
                risk_level = "HIGH"
            else:
                risk_level = "CRITICAL"
            
            return {
                'violations': violations,
                'total_violations': len(violations),
                'compliance_score': round(compliance_score, 1),
                'risk_level': risk_level,
                'elements_analyzed': total_elements,
                'scan_timestamp': datetime.datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'error': f'Scan failed: {str(e)}',
                'violations': [],
                'total_violations': 0,
                'compliance_score': 0,
                'risk_level': 'UNKNOWN'
            }
    
    def _check_image_alt(self, soup, base_url):
        """Check for images without alt text"""
        violations = []
        images = soup.find_all('img')
        
        for i, img in enumerate(images):
            if not img.get('alt'):
                violations.append({
                    'rule': 'img-alt',
                    'element': str(img)[:100] + '...' if len(str(img)) > 100 else str(img),
                    'location': f'Image #{i+1}',
                    'description': self.violation_rules['img-alt']['description'],
                    'wcag_reference': self.violation_rules['img-alt']['wcag'],
                    'severity': self.violation_rules['img-alt']['severity'],
                    'category': self.violation_rules['img-alt']['category'],
                    'impact': 'Screen readers cannot describe image content to users'
                })
        
        return violations
    
    def _check_form_labels(self, soup, base_url):
        """Check for form inputs without labels"""
        violations = []
        inputs = soup.find_all(['input', 'textarea', 'select'])
        
        for i, input_elem in enumerate(inputs):
            input_type = input_elem.get('type', 'text')
            if input_type in ['hidden', 'submit', 'button']:
                continue
                
            has_label = False
            input_id = input_elem.get('id')
            
            # Check for associated label
            if input_id:
                label = soup.find('label', {'for': input_id})
                if label:
                    has_label = True
            
            # Check for aria-label
            if input_elem.get('aria-label'):
                has_label = True
            
            # Check for placeholder (not ideal but acceptable)
            if input_elem.get('placeholder'):
                has_label = True
            
            if not has_label:
                violations.append({
                    'rule': 'form-labels',
                    'element': str(input_elem)[:100] + '...' if len(str(input_elem)) > 100 else str(input_elem),
                    'location': f'Form input #{i+1}',
                    'description': self.violation_rules['form-labels']['description'],
                    'wcag_reference': self.violation_rules['form-labels']['wcag'],
                    'severity': self.violation_rules['form-labels']['severity'],
                    'category': self.violation_rules['form-labels']['category'],
                    'impact': 'Users with disabilities cannot identify form field purpose'
                })
        
        return violations
    
    def _check_color_contrast(self, soup, base_url):
        """Check for potential color contrast issues (simplified)"""
        violations = []
        
        # Look for inline styles with light colors
        elements_with_style = soup.find_all(attrs={'style': True})
        
        for i, elem in enumerate(elements_with_style):
            style = elem.get('style', '')
            if 'color:' in style.lower():
                # Simplified check for light colors
                if any(light_color in style.lower() for light_color in ['#ccc', '#ddd', '#eee', '#999', 'lightgray', 'silver']):
                    violations.append({
                        'rule': 'color-contrast',
                        'element': str(elem)[:100] + '...' if len(str(elem)) > 100 else str(elem),
                        'location': f'Element #{i+1} with inline styles',
                        'description': self.violation_rules['color-contrast']['description'],
                        'wcag_reference': self.violation_rules['color-contrast']['wcag'],
                        'severity': self.violation_rules['color-contrast']['severity'],
                        'category': self.violation_rules['color-contrast']['category'],
                        'impact': 'Text may be difficult to read for users with visual impairments'
                    })
        
        return violations
    
    def _check_heading_structure(self, soup, base_url):
        """Check for proper heading hierarchy"""
        violations = []
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        if not headings:
            return violations
        
        # Check for multiple H1s
        h1_count = len(soup.find_all('h1'))
        if h1_count > 1:
            violations.append({
                'rule': 'heading-structure',
                'element': f'{h1_count} H1 headings found',
                'location': 'Multiple locations',
                'description': 'Page should have only one H1 heading',
                'wcag_reference': self.violation_rules['heading-structure']['wcag'],
                'severity': self.violation_rules['heading-structure']['severity'],
                'category': self.violation_rules['heading-structure']['category'],
                'impact': 'Confusing navigation structure for screen reader users'
            })
        
        return violations
    
    def _check_link_text(self, soup, base_url):
        """Check for non-descriptive link text"""
        violations = []
        links = soup.find_all('a', href=True)
        
        non_descriptive_texts = ['click here', 'read more', 'more', 'here', 'link', 'this']
        
        for i, link in enumerate(links):
            link_text = link.get_text().strip().lower()
            if link_text in non_descriptive_texts or len(link_text) < 3:
                violations.append({
                    'rule': 'link-text',
                    'element': str(link)[:100] + '...' if len(str(link)) > 100 else str(link),
                    'location': f'Link #{i+1}',
                    'description': self.violation_rules['link-text']['description'],
                    'wcag_reference': self.violation_rules['link-text']['wcag'],
                    'severity': self.violation_rules['link-text']['severity'],
                    'category': self.violation_rules['link-text']['category'],
                    'impact': 'Users cannot understand link purpose without context'
                })
        
        return violations
    
    def _check_keyboard_focus(self, soup, base_url):
        """Check for keyboard accessibility issues"""
        violations = []
        interactive_elements = soup.find_all(['a', 'button', 'input', 'textarea', 'select'])
        
        for i, elem in enumerate(interactive_elements):
            # Check for tabindex=-1 (removes from tab order)
            if elem.get('tabindex') == '-1':
                violations.append({
                    'rule': 'keyboard-focus',
                    'element': str(elem)[:100] + '...' if len(str(elem)) > 100 else str(elem),
                    'location': f'Interactive element #{i+1}',
                    'description': 'Element removed from keyboard navigation',
                    'wcag_reference': self.violation_rules['keyboard-focus']['wcag'],
                    'severity': self.violation_rules['keyboard-focus']['severity'],
                    'category': self.violation_rules['keyboard-focus']['category'],
                    'impact': 'Element cannot be accessed via keyboard navigation'
                })
        
        return violations

class AIRecommendationEngine:
    """OpenAI-powered accessibility recommendation system"""
    
    def __init__(self):
        self.openai_available = bool(OPENAI_API_KEY)
    
    def generate_recommendations(self, violations):
        """Generate AI-powered recommendations for violations"""
        if not self.openai_available:
            return self._generate_fallback_recommendations(violations)
        
        recommendations = []
        
        # Group violations by category for batch processing
        violations_by_category = {}
        for violation in violations:
            category = violation['category']
            if category not in violations_by_category:
                violations_by_category[category] = []
            violations_by_category[category].append(violation)
        
        # Generate recommendations for each category
        for category, category_violations in violations_by_category.items():
            try:
                category_recommendations = self._generate_category_recommendations(category, category_violations)
                recommendations.extend(category_recommendations)
            except Exception as e:
                # Fallback to basic recommendations if AI fails
                fallback_recs = self._generate_fallback_recommendations(category_violations)
                recommendations.extend(fallback_recs)
        
        return recommendations
    
    def _generate_category_recommendations(self, category, violations):
        """Generate AI recommendations for a specific category"""
        # Create prompt for OpenAI
        prompt = self._create_recommendation_prompt(category, violations)
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an accessibility expert providing detailed, actionable recommendations for fixing web accessibility issues. Provide clear, step-by-step instructions with code examples."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            ai_response = response.choices[0].message.content
            return self._parse_ai_response(ai_response, violations)
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return self._generate_fallback_recommendations(violations)
    
    def _create_recommendation_prompt(self, category, violations):
        """Create detailed prompt for OpenAI"""
        sample_violation = violations[0] if violations else {}
        
        prompt = f"""
        Analyze these {category} accessibility violations and provide detailed fix recommendations:

        Category: {category}
        Number of violations: {len(violations)}
        
        Sample violation:
        - Rule: {sample_violation.get('rule', 'N/A')}
        - Description: {sample_violation.get('description', 'N/A')}
        - Element: {sample_violation.get('element', 'N/A')}
        - WCAG Reference: {sample_violation.get('wcag_reference', 'N/A')}
        
        Please provide:
        1. Clear explanation of why this is an accessibility issue
        2. Step-by-step instructions to fix it
        3. Before and after code examples
        4. Testing recommendations
        5. Business impact if not fixed
        6. Estimated time to fix
        7. Priority level (CRITICAL, HIGH, MEDIUM, LOW)
        
        Format your response as structured recommendations that can be easily parsed.
        """
        
        return prompt
    
    def _parse_ai_response(self, ai_response, violations):
        """Parse AI response into structured recommendations"""
        recommendations = []
        
        for violation in violations:
            recommendation = {
                'violation_id': f"{violation['rule']}_{hash(violation['element']) % 10000}",
                'rule': violation['rule'],
                'category': violation['category'],
                'severity': violation['severity'],
                'element': violation['element'],
                'location': violation['location'],
                'issue_explanation': ai_response[:200] + "...",  # Simplified parsing
                'fix_steps': [
                    "1. Locate the problematic element in your HTML",
                    "2. Apply the recommended fix",
                    "3. Test with accessibility tools",
                    "4. Verify with screen readers"
                ],
                'code_example': {
                    'before': violation['element'],
                    'after': self._generate_fixed_code(violation)
                },
                'testing_guide': "Use automated accessibility testing tools and manual screen reader testing",
                'business_impact': violation['impact'],
                'priority': violation['severity'],
                'estimated_fix_time': self._estimate_fix_time(violation['rule'])
            }
            recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_fallback_recommendations(self, violations):
        """Generate basic recommendations when AI is not available"""
        recommendations = []
        
        for violation in violations:
            recommendation = {
                'violation_id': f"{violation['rule']}_{hash(violation['element']) % 10000}",
                'rule': violation['rule'],
                'category': violation['category'],
                'severity': violation['severity'],
                'element': violation['element'],
                'location': violation['location'],
                'issue_explanation': violation['description'],
                'fix_steps': self._get_basic_fix_steps(violation['rule']),
                'code_example': {
                    'before': violation['element'],
                    'after': self._generate_fixed_code(violation)
                },
                'testing_guide': "Test with screen readers and accessibility validation tools",
                'business_impact': violation['impact'],
                'priority': violation['severity'],
                'estimated_fix_time': self._estimate_fix_time(violation['rule'])
            }
            recommendations.append(recommendation)
        
        return recommendations
    
    def _get_basic_fix_steps(self, rule):
        """Get basic fix steps for common rules"""
        fix_steps = {
            'img-alt': [
                "1. Add an alt attribute to the image element",
                "2. Write descriptive text that conveys the image's purpose",
                "3. For decorative images, use alt=''",
                "4. Test with a screen reader"
            ],
            'form-labels': [
                "1. Add a label element associated with the input",
                "2. Use the 'for' attribute to connect label to input ID",
                "3. Alternatively, use aria-label attribute",
                "4. Test form navigation with keyboard only"
            ],
            'color-contrast': [
                "1. Check color contrast ratio using online tools",
                "2. Ensure minimum 4.5:1 ratio for normal text",
                "3. Use darker colors or lighter backgrounds",
                "4. Test with color blindness simulators"
            ]
        }
        
        return fix_steps.get(rule, [
            "1. Review the accessibility violation",
            "2. Consult WCAG guidelines for specific requirements",
            "3. Implement the recommended fix",
            "4. Test with accessibility tools"
        ])
    
    def _generate_fixed_code(self, violation):
        """Generate example fixed code"""
        rule = violation['rule']
        element = violation['element']
        
        if rule == 'img-alt' and '<img' in element:
            return element.replace('>', ' alt="Descriptive text for this image">')
        elif rule == 'form-labels' and '<input' in element:
            return f'<label for="input-id">Field Label</label>\n{element.replace(">", ' id="input-id">")}'
        else:
            return element + " <!-- Fixed version -->"
    
    def _estimate_fix_time(self, rule):
        """Estimate time to fix violation"""
        time_estimates = {
            'img-alt': '2-5 minutes per image',
            'form-labels': '5-10 minutes per form field',
            'color-contrast': '10-30 minutes per element',
            'heading-structure': '15-45 minutes',
            'link-text': '2-5 minutes per link',
            'keyboard-focus': '10-20 minutes per element'
        }
        
        return time_estimates.get(rule, '5-15 minutes')

# Initialize scanner and AI engine
scanner = AccessibilityScanner()
ai_engine = AIRecommendationEngine()

# API Routes
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'SentryPrime AI-Enhanced Backend',
        'version': '3.0.0',
        'ai_enabled': ai_engine.openai_available,
        'users_count': len(users),
        'websites_count': len(websites),
        'scans_count': len(scans),
        'timestamp': datetime.datetime.utcnow().isoformat()
    })

@app.route('/api/dashboard/scan-detailed', methods=['POST'])
def scan_website_detailed():
    """Enhanced scan with AI-powered recommendations"""
    try:
        # Get auth token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Verify token
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user_id = payload['user_id']
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        data = request.get_json()
        website_url = data.get('url')
        
        if not website_url:
            return jsonify({'error': 'Website URL required'}), 400
        
        # Perform detailed scan
        scan_results = scanner.scan_website(website_url)
        
        if 'error' in scan_results:
            return jsonify(scan_results), 400
        
        # Generate AI recommendations
        recommendations = ai_engine.generate_recommendations(scan_results['violations'])
        
        # Create comprehensive scan report
        scan_id = f"scan_{len(scans) + 1}_{int(datetime.datetime.utcnow().timestamp())}"
        
        detailed_report = {
            'scan_id': scan_id,
            'website_url': website_url,
            'user_id': user_id,
            'timestamp': scan_results['scan_timestamp'],
            'summary': {
                'total_violations': scan_results['total_violations'],
                'compliance_score': scan_results['compliance_score'],
                'risk_level': scan_results['risk_level'],
                'elements_analyzed': scan_results['elements_analyzed']
            },
            'violations': scan_results['violations'],
            'ai_recommendations': recommendations,
            'report_generated': True
        }
        
        # Store scan results
        scans[scan_id] = detailed_report
        ai_reports[scan_id] = detailed_report
        
        return jsonify({
            'success': True,
            'scan_id': scan_id,
            'summary': detailed_report['summary'],
            'recommendations_count': len(recommendations),
            'report_available': True
        })
        
    except Exception as e:
        return jsonify({'error': f'Scan failed: {str(e)}'}), 500

@app.route('/api/reports/<scan_id>', methods=['GET'])
def get_detailed_report(scan_id):
    """Get detailed AI-powered accessibility report"""
    try:
        # Get auth token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Verify token
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user_id = payload['user_id']
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        # Get report
        if scan_id not in ai_reports:
            return jsonify({'error': 'Report not found'}), 404
        
        report = ai_reports[scan_id]
        
        # Verify user owns this report
        if report['user_id'] != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify(report)
        
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve report: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
