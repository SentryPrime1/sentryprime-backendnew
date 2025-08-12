from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
CORS(app)

@app.route('/')
def health():
    return jsonify({
        "status": "healthy",
        "service": "SentryPrime AI Backend",
        "version": "1.0.0",
        "ai_enabled": True
    })

@app.route('/api/scan', methods=['POST'])
def scan_website():
    data = request.get_json()
    url = data.get('url')
    
    try:
        # Basic accessibility scan
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Simple violation detection
        violations = []
        
        # Check for missing alt text
        images = soup.find_all('img')
        for img in images:
            if not img.get('alt'):
                violations.append("Missing alt text on image")
        
        return jsonify({
            "url": url,
            "violations_count": len(violations),
            "violations": violations[:10],  # First 10
            "status": "completed"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
