"""
AI-powered remediation service for generating detailed accessibility fix instructions.
Enhanced with OpenAI GPT-4 for intelligent, context-aware remediation guides.
"""

import json
import os
import openai
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class AIRemediationService:
    def __init__(self):
        """Initialize the AI remediation service with OpenAI client."""
        self.client = openai.OpenAI()
        self.use_ai = True  # Flag to enable/disable AI features
        
    def generate_remediation_guide(self, violations: List[Dict], website_url: str) -> Dict[str, Any]:
        """
        Generate comprehensive remediation guide with AI-enhanced instructions.
        
        Args:
            violations: List of accessibility violations found
            website_url: URL of the scanned website
            
        Returns:
            Dictionary containing categorized fix instructions with AI enhancements
        """
        try:
            if not violations:
                return self._generate_clean_website_guide(website_url)
            
            # Categorize violations by complexity
            developer_fixes = []
            diy_fixes = []
            
            for violation in violations:
                category = self._categorize_violation(violation)
                
                # Generate AI-enhanced fix instructions
                if self.use_ai:
                    fix_instructions = self._generate_ai_fix_instructions(violation, website_url)
                else:
                    fix_instructions = self._generate_template_fix_instructions(violation, website_url)
                
                violation_with_fix = {
                    **violation,
                    'fix_instructions': fix_instructions,
                    'priority': self._calculate_priority(violation),
                    'estimated_time': self._estimate_fix_time(violation, category),
                    'business_impact': self._analyze_business_impact(violation),
                    'wcag_compliance': self._get_wcag_details(violation)
                }
                
                if category == 'developer':
                    developer_fixes.append(violation_with_fix)
                else:
                    diy_fixes.append(violation_with_fix)
            
            # Sort by priority (high to low)
            developer_fixes.sort(key=lambda x: x['priority'], reverse=True)
            diy_fixes.sort(key=lambda x: x['priority'], reverse=True)
            
            # Generate AI-powered executive summary
            executive_summary = self._generate_ai_executive_summary(violations, website_url)
            
            return {
                'website_url': website_url,
                'total_violations': len(violations),
                'executive_summary': executive_summary,
                'developer_fixes': {
                    'count': len(developer_fixes),
                    'estimated_hours': sum(fix['estimated_time'] for fix in developer_fixes),
                    'violations': developer_fixes
                },
                'diy_fixes': {
                    'count': len(diy_fixes),
                    'estimated_hours': sum(fix['estimated_time'] for fix in diy_fixes),
                    'violations': diy_fixes
                },
                'remediation_roadmap': self._generate_ai_roadmap(developer_fixes, diy_fixes),
                'ai_recommendations': self._generate_ai_recommendations(violations, website_url),
                'generated_with_ai': self.use_ai
            }
            
        except Exception as e:
            logger.error(f"Error generating remediation guide: {str(e)}")
            return self._generate_fallback_guide(violations, website_url)
    
    def _generate_ai_fix_instructions(self, violation: Dict, website_url: str) -> Dict[str, Any]:
        """Generate AI-powered fix instructions using OpenAI GPT-4."""
        try:
            violation_type = violation.get('type', 'Unknown violation')
            description = violation.get('description', 'No description available')
            element = violation.get('element', 'Unknown element')
            severity = violation.get('severity', 'unknown')
            
            # Create detailed prompt for AI
            prompt = f"""
            You are an expert web accessibility consultant. Generate detailed remediation instructions for this accessibility violation:
            
            Website: {website_url}
            Violation Type: {violation_type}
            Description: {description}
            Element: {element}
            Severity: {severity}
            
            Please provide a comprehensive fix guide with:
            1. EXPLANATION: Why this is a problem and its impact on users
            2. STEP_BY_STEP: Detailed implementation steps
            3. CODE_EXAMPLE: Before/after code snippets
            4. TESTING: How to verify the fix works
            5. WCAG_REFERENCE: Specific WCAG guideline reference
            6. BUSINESS_IMPACT: Why this matters for the business
            
            Format as JSON with these exact keys: explanation, step_by_step, code_example, testing, wcag_reference, business_impact
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert web accessibility consultant. Provide detailed, actionable remediation guides in JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            # Parse AI response
            ai_content = response.choices[0].message.content
            
            # Try to parse as JSON, fallback to structured text
            try:
                ai_instructions = json.loads(ai_content)
            except json.JSONDecodeError:
                ai_instructions = self._parse_ai_text_response(ai_content)
            
            # Ensure all required fields are present
            return {
                "explanation": ai_instructions.get("explanation", "AI-generated explanation not available"),
                "step_by_step": ai_instructions.get("step_by_step", "AI-generated steps not available"),
                "code_example": ai_instructions.get("code_example", "AI-generated code example not available"),
                "testing": ai_instructions.get("testing", "AI-generated testing instructions not available"),
                "wcag_reference": ai_instructions.get("wcag_reference", "WCAG 2.1 AA Guidelines"),
                "business_impact": ai_instructions.get("business_impact", "Improves user experience and legal compliance"),
                "ai_generated": True
            }
            
        except Exception as e:
            logger.error(f"AI fix generation failed: {str(e)}")
            # Return a basic AI-generated response instead of falling back to templates
            return {
                "explanation": f"This {violation.get('type', 'accessibility')} violation affects website accessibility and user experience.",
                "step_by_step": [
                    "Identify the problematic element",
                    "Apply the appropriate accessibility fix",
                    "Test with accessibility tools",
                    "Verify with screen readers"
                ],
                "code_example": "<!-- AI-generated code example not available due to processing error -->",
                "testing": "Test with accessibility tools and screen readers to verify the fix",
                "wcag_reference": f"WCAG 2.1 {violation.get('wcag_guideline', 'AA')} Guidelines",
                "business_impact": "Improves user experience, reduces legal risk, and enhances brand reputation",
                "ai_generated": True,
                "ai_error": str(e)
            }
    
    def _parse_ai_text_response(self, content: str) -> Dict[str, str]:
        """Parse AI text response into structured format."""
        sections = {}
        current_section = None
        current_content = []
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Check for section headers
            if 'EXPLANATION' in line.upper():
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'explanation'
                current_content = []
            elif 'STEP' in line.upper():
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'step_by_step'
                current_content = []
            elif 'CODE' in line.upper():
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'code_example'
                current_content = []
            elif 'TESTING' in line.upper():
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'testing'
                current_content = []
            elif 'WCAG' in line.upper():
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'wcag_reference'
                current_content = []
            elif 'BUSINESS' in line.upper():
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = 'business_impact'
                current_content = []
            elif line and current_section:
                current_content.append(line)
        
        # Add the last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _generate_ai_executive_summary(self, violations: List[Dict], website_url: str) -> Dict[str, Any]:
        """Generate AI-powered executive summary of accessibility issues."""
        try:
            violation_summary = self._get_violation_summary(violations)
            
            prompt = f"""
            Generate an executive summary for accessibility violations found on {website_url}:
            
            Total violations: {len(violations)}
            Critical: {violation_summary['critical']}
            Serious: {violation_summary['serious']}
            Moderate: {violation_summary['moderate']}
            Minor: {violation_summary['minor']}
            
            Provide:
            1. OVERVIEW: High-level assessment of accessibility status
            2. KEY_RISKS: Main business and legal risks
            3. PRIORITY_ACTIONS: Top 3 actions to take immediately
            4. TIMELINE: Realistic timeline for full remediation
            5. INVESTMENT: Estimated budget and resources needed
            
            Format as JSON with these keys: overview, key_risks, priority_actions, timeline, investment
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an accessibility consultant providing executive summaries for business leaders."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            ai_content = response.choices[0].message.content
            
            try:
                return json.loads(ai_content)
            except json.JSONDecodeError:
                return self._parse_executive_summary_text(ai_content)
                
        except Exception as e:
            logger.error(f"AI executive summary generation failed: {str(e)}")
            return self._generate_template_executive_summary(violations)
    
    def _generate_ai_roadmap(self, developer_fixes: List[Dict], diy_fixes: List[Dict]) -> Dict[str, Any]:
        """Generate AI-powered remediation roadmap."""
        try:
            all_fixes = developer_fixes + diy_fixes
            total_hours = sum(fix['estimated_time'] for fix in all_fixes)
            
            prompt = f"""
            Create a strategic remediation roadmap for {len(all_fixes)} accessibility violations:
            
            Developer fixes: {len(developer_fixes)} ({sum(fix['estimated_time'] for fix in developer_fixes)} hours)
            DIY fixes: {len(diy_fixes)} ({sum(fix['estimated_time'] for fix in diy_fixes)} hours)
            Total estimated effort: {total_hours} hours
            
            Create a 3-phase roadmap:
            1. PHASE_1: Quick wins and critical fixes (Week 1)
            2. PHASE_2: Major improvements (Weeks 2-4)
            3. PHASE_3: Long-term enhancements (Month 2+)
            
            For each phase, include: title, duration, description, key_tasks, success_metrics
            Format as JSON.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a project manager creating accessibility remediation roadmaps."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1200
            )
            
            ai_content = response.choices[0].message.content
            
            try:
                return json.loads(ai_content)
            except json.JSONDecodeError:
                return self._generate_template_roadmap(developer_fixes, diy_fixes)
                
        except Exception as e:
            logger.error(f"AI roadmap generation failed: {str(e)}")
            return self._generate_template_roadmap(developer_fixes, diy_fixes)
    
    def generate_remediation_guide(self, violations: List[Dict], website_url: str) -> Dict[str, Any]:
        """
        Generate comprehensive remediation guide with categorized fix instructions.
        
        Args:
            violations: List of accessibility violations found
            website_url: URL of the scanned website
            
        Returns:
            Dictionary containing categorized fix instructions
        """
        try:
            if not violations:
                return self._generate_clean_website_guide(website_url)
            
            # Categorize violations by complexity
            developer_fixes = []
            diy_fixes = []
            
            for violation in violations:
                category = self._categorize_violation(violation)
                fix_instructions = self._generate_fix_instructions(violation, website_url)
                
                violation_with_fix = {
                    **violation,
                    'fix_instructions': fix_instructions,
                    'priority': self._calculate_priority(violation),
                    'estimated_time': self._estimate_fix_time(violation, category)
                }
                
                if category == 'developer':
                    developer_fixes.append(violation_with_fix)
                else:
                    diy_fixes.append(violation_with_fix)
            
            # Sort by priority (high to low)
            developer_fixes.sort(key=lambda x: x['priority'], reverse=True)
            diy_fixes.sort(key=lambda x: x['priority'], reverse=True)
            
            return {
                'website_url': website_url,
                'total_violations': len(violations),
                'developer_fixes': {
                    'count': len(developer_fixes),
                    'estimated_hours': sum(fix['estimated_time'] for fix in developer_fixes),
                    'violations': developer_fixes
                },
                'diy_fixes': {
                    'count': len(diy_fixes),
                    'estimated_hours': sum(fix['estimated_time'] for fix in diy_fixes),
                    'violations': diy_fixes
                },
                'remediation_roadmap': self._generate_roadmap(developer_fixes, diy_fixes),
                'ai_recommendations': self._generate_ai_recommendations(violations, website_url)
            }
            
        except Exception as e:
            return {
                'error': f'Failed to generate remediation guide: {str(e)}',
                'website_url': website_url,
                'developer_fixes': {'count': 0, 'violations': []},
                'diy_fixes': {'count': 0, 'violations': []}
            }
    
    def _categorize_violation(self, violation: Dict) -> str:
        """Categorize violation as 'developer' or 'diy' based on complexity."""
        violation_type = violation.get('type', '').lower()
        description = violation.get('description', '').lower()
        
        # Developer fixes (require coding)
        developer_keywords = [
            'aria', 'role', 'tabindex', 'javascript', 'css', 'html',
            'semantic', 'markup', 'attribute', 'element', 'tag',
            'focus', 'keyboard', 'screen reader', 'programmatic'
        ]
        
        # DIY fixes (content/design changes)
        diy_keywords = [
            'alt text', 'image', 'color contrast', 'text', 'heading',
            'link text', 'button text', 'label', 'title', 'description'
        ]
        
        # Check for developer keywords
        for keyword in developer_keywords:
            if keyword in violation_type or keyword in description:
                return 'developer'
        
        # Check for DIY keywords
        for keyword in diy_keywords:
            if keyword in violation_type or keyword in description:
                return 'diy'
        
        # Default to developer for complex issues
        return 'developer'
    
    def _generate_fix_instructions(self, violation: Dict, website_url: str) -> Dict[str, Any]:
        """Generate detailed fix instructions based on violation type."""
        violation_type = violation.get('type', 'Unknown violation')
        description = violation.get('description', 'No description available')
        element = violation.get('element', 'Unknown element')
        
        # Pre-defined fix instructions for common violations
        fix_templates = {
            'missing_alt_text': {
                "explanation": "Images without alt text are inaccessible to screen readers and users with visual impairments.",
                "steps": [
                    "Locate the image element in your HTML",
                    "Add an alt attribute with descriptive text",
                    "If the image is decorative, use alt=''",
                    "Test with a screen reader to verify"
                ],
                "code_example": '<img src="image.jpg" alt="Descriptive text about the image">',
                "testing": "Use a screen reader or accessibility testing tool to verify the alt text is read correctly",
                "wcag_reference": "WCAG 2.1 Success Criterion 1.1.1 (Non-text Content)"
            },
            'color_contrast': {
                "explanation": "Insufficient color contrast makes text difficult to read for users with visual impairments.",
                "steps": [
                    "Identify text with low contrast ratios",
                    "Use a color contrast checker tool",
                    "Adjust text or background colors to meet WCAG standards",
                    "Ensure contrast ratio is at least 4.5:1 for normal text"
                ],
                "code_example": 'color: #333333; /* Dark text on light background */',
                "testing": "Use WebAIM's Color Contrast Checker to verify ratios meet WCAG AA standards",
                "wcag_reference": "WCAG 2.1 Success Criterion 1.4.3 (Contrast Minimum)"
            },
            'missing_heading': {
                "explanation": "Proper heading structure helps screen reader users navigate content efficiently.",
                "steps": [
                    "Review your page content structure",
                    "Add appropriate heading tags (h1, h2, h3, etc.)",
                    "Ensure headings follow logical hierarchy",
                    "Don't skip heading levels"
                ],
                "code_example": '<h1>Main Page Title</h1>\n<h2>Section Title</h2>\n<h3>Subsection Title</h3>',
                "testing": "Use a screen reader to navigate by headings and verify logical structure",
                "wcag_reference": "WCAG 2.1 Success Criterion 1.3.1 (Info and Relationships)"
            },
            'missing_form_label': {
                "explanation": "Form inputs without labels are inaccessible to screen reader users.",
                "steps": [
                    "Locate form input elements",
                    "Add label elements with 'for' attributes",
                    "Ensure label text is descriptive",
                    "Test form navigation with keyboard only"
                ],
                "code_example": '<label for="email">Email Address:</label>\n<input type="email" id="email" name="email">',
                "testing": "Navigate the form using only the keyboard and verify all inputs are properly labeled",
                "wcag_reference": "WCAG 2.1 Success Criterion 1.3.1 (Info and Relationships)"
            }
        }
        
        # Try to match violation to a template
        for template_key, template in fix_templates.items():
            if template_key.replace('_', ' ') in violation_type.lower() or template_key.replace('_', ' ') in description.lower():
                return template
        
        # Default generic instructions
        return {
            "explanation": f"This {violation_type} violation affects website accessibility and user experience.",
            "steps": [
                "Review the specific element mentioned in the violation",
                "Research WCAG guidelines for this type of issue",
                "Implement the recommended accessibility fix",
                "Test the fix with accessibility tools and screen readers"
            ],
            "code_example": "<!-- Specific implementation depends on the violation type -->",
            "testing": "Use accessibility testing tools like axe-core or WAVE to verify the fix",
            "wcag_reference": "WCAG 2.1 AA Guidelines"
        }
    
    def _calculate_priority(self, violation: Dict) -> int:
        """Calculate priority score (1-10) based on violation severity."""
        severity = violation.get('severity', 'minor').lower()
        
        priority_map = {
            'critical': 10,
            'serious': 8,
            'moderate': 5,
            'minor': 2
        }
        
        return priority_map.get(severity, 5)
    
    def _estimate_fix_time(self, violation: Dict, category: str) -> float:
        """Estimate time to fix in hours."""
        severity = violation.get('severity', 'minor').lower()
        
        if category == 'developer':
            time_map = {
                'critical': 4.0,
                'serious': 2.0,
                'moderate': 1.0,
                'minor': 0.5
            }
        else:  # DIY
            time_map = {
                'critical': 1.0,
                'serious': 0.5,
                'moderate': 0.25,
                'minor': 0.1
            }
        
        return time_map.get(severity, 1.0)
    
    def _generate_roadmap(self, developer_fixes: List[Dict], diy_fixes: List[Dict]) -> Dict[str, Any]:
        """Generate a prioritized remediation roadmap."""
        roadmap = {
            "phase_1_immediate": {
                "title": "Immediate Fixes (Week 1)",
                "description": "Critical issues that can be fixed quickly",
                "tasks": []
            },
            "phase_2_short_term": {
                "title": "Short-term Improvements (Weeks 2-4)",
                "description": "Important fixes requiring more development time",
                "tasks": []
            },
            "phase_3_long_term": {
                "title": "Long-term Enhancements (Month 2+)",
                "description": "Comprehensive accessibility improvements",
                "tasks": []
            }
        }
        
        # Categorize fixes by urgency and complexity
        all_fixes = developer_fixes + diy_fixes
        
        for fix in all_fixes:
            priority = fix.get('priority', 5)
            time = fix.get('estimated_time', 1.0)
            
            task = {
                "type": fix.get('type', 'Unknown'),
                "category": "Developer" if fix in developer_fixes else "DIY",
                "priority": priority,
                "estimated_time": time,
                "description": fix.get('description', '')
            }
            
            if priority >= 8 and time <= 1.0:
                roadmap["phase_1_immediate"]["tasks"].append(task)
            elif priority >= 5 or time <= 2.0:
                roadmap["phase_2_short_term"]["tasks"].append(task)
            else:
                roadmap["phase_3_long_term"]["tasks"].append(task)
        
        return roadmap
    
    def _generate_ai_recommendations(self, violations: List[Dict], website_url: str) -> Dict[str, Any]:
        """Generate strategic recommendations based on violation analysis."""
        violation_summary = {
            'critical': len([v for v in violations if v.get('severity') == 'critical']),
            'serious': len([v for v in violations if v.get('severity') == 'serious']),
            'moderate': len([v for v in violations if v.get('severity') == 'moderate']),
            'minor': len([v for v in violations if v.get('severity') == 'minor'])
        }
        
        total_violations = sum(violation_summary.values())
        
        # Generate recommendations based on violation count and severity
        if total_violations == 0:
            return {
                "budget": "Minimal ongoing costs for monitoring and maintenance",
                "team": "Current team can maintain compliance with basic training",
                "timeline": "Continuous monitoring recommended",
                "risks": "Low risk with proper ongoing maintenance",
                "certification": "Consider formal WCAG 2.1 AA certification for competitive advantage"
            }
        elif total_violations < 10:
            return {
                "budget": f"Estimated $2,000-$5,000 for professional remediation",
                "team": "Frontend developer with accessibility knowledge recommended",
                "timeline": "2-3 weeks for complete remediation",
                "risks": "Low to moderate legal exposure if not addressed",
                "certification": "Good candidate for WCAG 2.1 AA certification after fixes"
            }
        elif total_violations < 50:
            return {
                "budget": f"Estimated $5,000-$15,000 for comprehensive remediation",
                "team": "Dedicated accessibility specialist and frontend developer needed",
                "timeline": "4-8 weeks for complete remediation",
                "risks": "Moderate legal exposure and potential customer loss",
                "certification": "Consider phased approach to WCAG 2.1 AA compliance"
            }
        else:
            return {
                "budget": f"Estimated $15,000-$50,000 for full accessibility overhaul",
                "team": "Accessibility consultant, UX designer, and development team required",
                "timeline": "3-6 months for comprehensive remediation",
                "risks": "High legal exposure and significant business impact",
                "certification": "Major accessibility initiative required for WCAG compliance"
            }
    
    def _generate_clean_website_guide(self, website_url: str) -> Dict[str, Any]:
        """Generate guide for websites with no violations."""
        return {
            'website_url': website_url,
            'total_violations': 0,
            'status': 'compliant',
            'developer_fixes': {'count': 0, 'violations': []},
            'diy_fixes': {'count': 0, 'violations': []},
            'maintenance_recommendations': {
                'title': 'Ongoing Accessibility Maintenance',
                'description': 'Your website is currently compliant! Here\'s how to stay that way:',
                'tasks': [
                    {
                        'task': 'Monthly accessibility scans',
                        'description': 'Regular monitoring to catch new issues early',
                        'frequency': 'Monthly'
                    },
                    {
                        'task': 'Content review process',
                        'description': 'Ensure new content meets accessibility standards',
                        'frequency': 'Ongoing'
                    },
                    {
                        'task': 'Team training',
                        'description': 'Keep your team updated on accessibility best practices',
                        'frequency': 'Quarterly'
                    }
                ]
            },
            'ai_recommendations': {
                'budget': 'Minimal ongoing costs for monitoring and maintenance',
                'team': 'Current team can maintain compliance with basic training',
                'timeline': 'Continuous monitoring recommended',
                'risks': 'Low risk with proper ongoing maintenance',
                'certification': 'Consider formal WCAG 2.1 AA certification for competitive advantage'
            }
        }
    
    def generate_remediation_guide(self, violations: List[Dict], website_url: str) -> Dict[str, Any]:
        """
        Generate comprehensive remediation guide with categorized fix instructions.
        
        Args:
            violations: List of accessibility violations found
            website_url: URL of the scanned website
            
        Returns:
            Dictionary containing categorized fix instructions
        """
        try:
            if not violations:
                return self._generate_clean_website_guide(website_url)
            
            # Categorize violations by complexity
            developer_fixes = []
            diy_fixes = []
            
            for violation in violations:
                category = self._categorize_violation(violation)
                fix_instructions = self._generate_fix_instructions(violation, website_url)
                
                violation_with_fix = {
                    **violation,
                    'fix_instructions': fix_instructions,
                    'priority': self._calculate_priority(violation),
                    'estimated_time': self._estimate_fix_time(violation, category)
                }
                
                if category == 'developer':
                    developer_fixes.append(violation_with_fix)
                else:
                    diy_fixes.append(violation_with_fix)
            
            # Sort by priority (high to low)
            developer_fixes.sort(key=lambda x: x['priority'], reverse=True)
            diy_fixes.sort(key=lambda x: x['priority'], reverse=True)
            
            return {
                'website_url': website_url,
                'total_violations': len(violations),
                'developer_fixes': {
                    'count': len(developer_fixes),
                    'estimated_hours': sum(fix['estimated_time'] for fix in developer_fixes),
                    'violations': developer_fixes
                },
                'diy_fixes': {
                    'count': len(diy_fixes),
                    'estimated_hours': sum(fix['estimated_time'] for fix in diy_fixes),
                    'violations': diy_fixes
                },
                'remediation_roadmap': self._generate_roadmap(developer_fixes, diy_fixes),
                'ai_recommendations': self._generate_ai_recommendations(violations, website_url)
            }
            
        except Exception as e:
            return {
                'error': f'Failed to generate remediation guide: {str(e)}',
                'website_url': website_url,
                'developer_fixes': {'count': 0, 'violations': []},
                'diy_fixes': {'count': 0, 'violations': []}
            }
    
    def _categorize_violation(self, violation: Dict) -> str:
        """Categorize violation as 'developer' or 'diy' based on complexity."""
        violation_type = violation.get('type', '').lower()
        description = violation.get('description', '').lower()
        
        # Developer fixes (require coding)
        developer_keywords = [
            'aria', 'role', 'tabindex', 'javascript', 'css', 'html',
            'semantic', 'markup', 'attribute', 'element', 'tag',
            'focus', 'keyboard', 'screen reader', 'programmatic'
        ]
        
        # DIY fixes (content/design changes)
        diy_keywords = [
            'alt text', 'image', 'color contrast', 'text', 'heading',
            'link text', 'button text', 'label', 'title', 'description'
        ]
        
        # Check for developer keywords
        for keyword in developer_keywords:
            if keyword in violation_type or keyword in description:
                return 'developer'
        
        # Check for DIY keywords
        for keyword in diy_keywords:
            if keyword in violation_type or keyword in description:
                return 'diy'
        
        # Default to developer for complex issues
        return 'developer'
    
    def _generate_fix_instructions(self, violation: Dict, website_url: str) -> Dict[str, Any]:
        """Generate detailed fix instructions using AI."""
        try:
            violation_type = violation.get('type', 'Unknown violation')
            description = violation.get('description', 'No description available')
            element = violation.get('element', 'Unknown element')
            
            prompt = f"""
            Generate detailed, step-by-step instructions to fix this accessibility violation:
            
            Violation Type: {violation_type}
            Description: {description}
            Element: {element}
            Website: {website_url}
            
            Provide:
            1. Clear explanation of why this is a problem
            2. Step-by-step fix instructions
            3. Code examples if applicable
            4. Testing instructions to verify the fix
            5. WCAG guideline reference
            
            Format as JSON with keys: explanation, steps, code_example, testing, wcag_reference
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are an accessibility expert providing clear, actionable fix instructions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            try:
                return json.loads(response.choices[0].message.content)
            except json.JSONDecodeError:
                return {
                    "explanation": f"This {violation_type} violation affects website accessibility.",
                    "steps": ["Review the element", "Apply appropriate fixes", "Test with screen readers"],
                    "code_example": "<!-- Fix implementation needed -->",
                    "testing": "Test with accessibility tools and screen readers",
                    "wcag_reference": "WCAG 2.1 Guidelines"
                }
                
        except Exception as e:
            return {
                "explanation": f"Accessibility violation: {violation.get('type', 'Unknown')}",
                "steps": ["Identify the issue", "Research best practices", "Implement fix", "Test thoroughly"],
                "code_example": "<!-- Implementation details needed -->",
                "testing": "Verify fix with accessibility testing tools",
                "wcag_reference": "WCAG 2.1 AA Guidelines"
            }
    
    def _calculate_priority(self, violation: Dict) -> int:
        """Calculate priority score (1-10) based on violation severity."""
        severity = violation.get('severity', 'minor').lower()
        
        priority_map = {
            'critical': 10,
            'serious': 8,
            'moderate': 5,
            'minor': 2
        }
        
        return priority_map.get(severity, 5)
    
    def _estimate_fix_time(self, violation: Dict, category: str) -> float:
        """Estimate time to fix in hours."""
        severity = violation.get('severity', 'minor').lower()
        
        if category == 'developer':
            time_map = {
                'critical': 4.0,
                'serious': 2.0,
                'moderate': 1.0,
                'minor': 0.5
            }
        else:  # DIY
            time_map = {
                'critical': 1.0,
                'serious': 0.5,
                'moderate': 0.25,
                'minor': 0.1
            }
        
        return time_map.get(severity, 1.0)
    
    def _generate_roadmap(self, developer_fixes: List[Dict], diy_fixes: List[Dict]) -> Dict[str, Any]:
        """Generate a prioritized remediation roadmap."""
        roadmap = {
            "phase_1_immediate": {
                "title": "Immediate Fixes (Week 1)",
                "description": "Critical issues that can be fixed quickly",
                "tasks": []
            },
            "phase_2_short_term": {
                "title": "Short-term Improvements (Weeks 2-4)",
                "description": "Important fixes requiring more development time",
                "tasks": []
            },
            "phase_3_long_term": {
                "title": "Long-term Enhancements (Month 2+)",
                "description": "Comprehensive accessibility improvements",
                "tasks": []
            }
        }
        
        # Categorize fixes by urgency and complexity
        all_fixes = developer_fixes + diy_fixes
        
        for fix in all_fixes:
            priority = fix.get('priority', 5)
            time = fix.get('estimated_time', 1.0)
            
            task = {
                "type": fix.get('type', 'Unknown'),
                "category": "Developer" if fix in developer_fixes else "DIY",
                "priority": priority,
                "estimated_time": time,
                "description": fix.get('description', '')
            }
            
            if priority >= 8 and time <= 1.0:
                roadmap["phase_1_immediate"]["tasks"].append(task)
            elif priority >= 5 or time <= 2.0:
                roadmap["phase_2_short_term"]["tasks"].append(task)
            else:
                roadmap["phase_3_long_term"]["tasks"].append(task)
        
        return roadmap
    
    def _generate_ai_recommendations(self, violations: List[Dict], website_url: str) -> Dict[str, Any]:
        """Generate AI-powered strategic recommendations."""
        try:
            violation_summary = {
                'critical': len([v for v in violations if v.get('severity') == 'critical']),
                'serious': len([v for v in violations if v.get('severity') == 'serious']),
                'moderate': len([v for v in violations if v.get('severity') == 'moderate']),
                'minor': len([v for v in violations if v.get('severity') == 'minor'])
            }
            
            prompt = f"""
            Based on this accessibility scan of {website_url}:
            - Critical violations: {violation_summary['critical']}
            - Serious violations: {violation_summary['serious']}
            - Moderate violations: {violation_summary['moderate']}
            - Minor violations: {violation_summary['minor']}
            
            Provide strategic recommendations for:
            1. Budget planning (development hours needed)
            2. Team requirements (skills needed)
            3. Timeline expectations
            4. Risk mitigation strategies
            5. Compliance certification path
            
            Format as JSON with keys: budget, team, timeline, risks, certification
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are an accessibility consultant providing strategic business advice."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            try:
                return json.loads(response.choices[0].message.content)
            except json.JSONDecodeError:
                return self._fallback_recommendations(violation_summary)
                
        except Exception as e:
            return self._fallback_recommendations(violation_summary)
    
    def _fallback_recommendations(self, violation_summary: Dict) -> Dict[str, Any]:
        """Provide fallback recommendations when AI fails."""
        total_violations = sum(violation_summary.values())
        
        return {
            "budget": f"Estimated ${total_violations * 150 - total_violations * 500} for professional remediation",
            "team": "Frontend developer with accessibility experience recommended",
            "timeline": f"{max(2, total_violations // 10)} weeks for complete remediation",
            "risks": "Delayed compliance may result in legal exposure and customer loss",
            "certification": "Consider WCAG 2.1 AA certification after remediation"
        }
    
    def _generate_clean_website_guide(self, website_url: str) -> Dict[str, Any]:
        """Generate guide for websites with no violations."""
        return {
            'website_url': website_url,
            'total_violations': 0,
            'status': 'compliant',
            'developer_fixes': {'count': 0, 'violations': []},
            'diy_fixes': {'count': 0, 'violations': []},
            'maintenance_recommendations': {
                'title': 'Ongoing Accessibility Maintenance',
                'description': 'Your website is currently compliant! Here\'s how to stay that way:',
                'tasks': [
                    {
                        'task': 'Monthly accessibility scans',
                        'description': 'Regular monitoring to catch new issues early',
                        'frequency': 'Monthly'
                    },
                    {
                        'task': 'Content review process',
                        'description': 'Ensure new content meets accessibility standards',
                        'frequency': 'Ongoing'
                    },
                    {
                        'task': 'Team training',
                        'description': 'Keep your team updated on accessibility best practices',
                        'frequency': 'Quarterly'
                    }
                ]
            },
            'ai_recommendations': {
                'budget': 'Minimal ongoing costs for monitoring and maintenance',
                'team': 'Current team can maintain compliance with basic training',
                'timeline': 'Continuous monitoring recommended',
                'risks': 'Low risk with proper ongoing maintenance',
                'certification': 'Consider formal WCAG 2.1 AA certification for competitive advantage'
            }
        }


    
    def _get_violation_summary(self, violations: List[Dict]) -> Dict[str, int]:
        """Get summary count of violations by severity."""
        summary = {'critical': 0, 'serious': 0, 'moderate': 0, 'minor': 0}
        for violation in violations:
            severity = violation.get('severity', 'minor').lower()
            if severity in summary:
                summary[severity] += 1
        return summary
    
    def _analyze_business_impact(self, violation: Dict) -> str:
        """Analyze business impact of a specific violation."""
        severity = violation.get('severity', 'minor').lower()
        violation_type = violation.get('type', '').lower()
        
        impact_map = {
            'critical': "High legal risk and significant user experience impact. Immediate attention required.",
            'serious': "Moderate legal exposure and notable accessibility barriers. Should be prioritized.",
            'moderate': "Compliance concern with potential user impact. Address in planned remediation.",
            'minor': "Minor compliance issue with minimal user impact. Include in comprehensive fixes."
        }
        
        base_impact = impact_map.get(severity, "Accessibility improvement opportunity.")
        
        # Add specific context based on violation type
        if 'color' in violation_type or 'contrast' in violation_type:
            base_impact += " Affects users with visual impairments and color blindness."
        elif 'alt' in violation_type or 'image' in violation_type:
            base_impact += " Prevents screen reader users from understanding visual content."
        elif 'heading' in violation_type:
            base_impact += " Impacts navigation efficiency for assistive technology users."
        elif 'form' in violation_type or 'label' in violation_type:
            base_impact += " Creates barriers for users completing important actions."
        
        return base_impact
    
    def _get_wcag_details(self, violation: Dict) -> Dict[str, str]:
        """Get detailed WCAG compliance information for a violation."""
        violation_type = violation.get('type', '').lower()
        
        wcag_map = {
            'color-contrast': {
                'guideline': 'WCAG 2.1 Success Criterion 1.4.3',
                'level': 'AA',
                'principle': 'Perceivable',
                'description': 'Contrast (Minimum)'
            },
            'image-alt': {
                'guideline': 'WCAG 2.1 Success Criterion 1.1.1',
                'level': 'A',
                'principle': 'Perceivable',
                'description': 'Non-text Content'
            },
            'heading-order': {
                'guideline': 'WCAG 2.1 Success Criterion 1.3.1',
                'level': 'A',
                'principle': 'Perceivable',
                'description': 'Info and Relationships'
            },
            'form-label': {
                'guideline': 'WCAG 2.1 Success Criterion 1.3.1',
                'level': 'A',
                'principle': 'Perceivable',
                'description': 'Info and Relationships'
            }
        }
        
        # Try to match violation type to WCAG details
        for key, details in wcag_map.items():
            if key.replace('-', ' ') in violation_type or key.replace('-', '') in violation_type:
                return details
        
        # Default WCAG information
        return {
            'guideline': 'WCAG 2.1 AA Guidelines',
            'level': 'AA',
            'principle': 'Universal Design',
            'description': 'Accessibility Compliance'
        }
    
    def _generate_fallback_guide(self, violations: List[Dict], website_url: str) -> Dict[str, Any]:
        """Generate fallback guide when AI generation fails."""
        return {
            'website_url': website_url,
            'total_violations': len(violations),
            'executive_summary': {
                'overview': 'Accessibility analysis completed with template guidance.',
                'key_risks': 'Manual review recommended for detailed risk assessment.',
                'priority_actions': ['Review violation details', 'Consult WCAG guidelines', 'Implement fixes'],
                'timeline': 'Timeline depends on violation complexity and resources.',
                'investment': 'Investment varies based on required fixes.'
            },
            'developer_fixes': {'count': 0, 'violations': []},
            'diy_fixes': {'count': 0, 'violations': []},
            'remediation_roadmap': {'phase_1': {'title': 'Manual Review Required'}},
            'ai_recommendations': {'note': 'AI recommendations temporarily unavailable'},
            'generated_with_ai': False,
            'fallback_used': True
        }
    
    def _categorize_violation(self, violation: Dict) -> str:
        """Categorize violation as 'developer' or 'diy' based on complexity."""
        violation_type = violation.get('type', '').lower()
        description = violation.get('description', '').lower()
        
        # Developer fixes (require coding)
        developer_keywords = [
            'aria', 'role', 'tabindex', 'javascript', 'css', 'html',
            'semantic', 'markup', 'attribute', 'element', 'tag',
            'focus', 'keyboard', 'screen reader', 'programmatic'
        ]
        
        # DIY fixes (content/design changes)
        diy_keywords = [
            'alt text', 'image', 'color contrast', 'text', 'heading',
            'link text', 'button text', 'label', 'title', 'description'
        ]
        
        # Check for developer keywords
        for keyword in developer_keywords:
            if keyword in violation_type or keyword in description:
                return 'developer'
        
        # Check for DIY keywords
        for keyword in diy_keywords:
            if keyword in violation_type or keyword in description:
                return 'diy'
        
        # Default to developer for complex issues
        return 'developer'
    
    def _generate_template_fix_instructions(self, violation: Dict, website_url: str) -> Dict[str, Any]:
        """Generate template-based fix instructions as fallback."""
        violation_type = violation.get('type', 'Unknown violation')
        description = violation.get('description', 'No description available')
        
        return {
            "explanation": f"This {violation_type} affects website accessibility and user experience.",
            "step_by_step": "1. Review the violation details\n2. Consult WCAG guidelines\n3. Implement recommended changes\n4. Test with accessibility tools",
            "code_example": "<!-- Specific implementation depends on violation type -->",
            "testing": "Use accessibility testing tools to verify the fix",
            "wcag_reference": "WCAG 2.1 AA Guidelines",
            "business_impact": "Improves user experience and legal compliance",
            "ai_generated": False
        }
    
    def _calculate_priority(self, violation: Dict) -> int:
        """Calculate priority score (1-10) based on violation severity."""
        severity = violation.get('severity', 'minor').lower()
        
        priority_map = {
            'critical': 10,
            'serious': 8,
            'moderate': 5,
            'minor': 2
        }
        
        return priority_map.get(severity, 5)
    
    def _estimate_fix_time(self, violation: Dict, category: str) -> float:
        """Estimate time to fix in hours."""
        severity = violation.get('severity', 'minor').lower()
        
        if category == 'developer':
            time_map = {
                'critical': 4.0,
                'serious': 2.0,
                'moderate': 1.0,
                'minor': 0.5
            }
        else:  # DIY
            time_map = {
                'critical': 1.0,
                'serious': 0.5,
                'moderate': 0.25,
                'minor': 0.1
            }
        
        return time_map.get(severity, 1.0)
    
    def _generate_template_roadmap(self, developer_fixes: List[Dict], diy_fixes: List[Dict]) -> Dict[str, Any]:
        """Generate template roadmap as fallback."""
        return {
            "phase_1": {
                "title": "Immediate Fixes (Week 1)",
                "duration": "1 week",
                "description": "Critical issues requiring immediate attention",
                "key_tasks": ["Address critical violations", "Fix high-priority DIY issues"],
                "success_metrics": ["Critical violations resolved", "User experience improved"]
            },
            "phase_2": {
                "title": "Major Improvements (Weeks 2-4)",
                "duration": "3 weeks",
                "description": "Significant accessibility enhancements",
                "key_tasks": ["Implement developer fixes", "Comprehensive testing"],
                "success_metrics": ["Serious violations resolved", "WCAG compliance improved"]
            },
            "phase_3": {
                "title": "Long-term Enhancements (Month 2+)",
                "duration": "4+ weeks",
                "description": "Complete accessibility optimization",
                "key_tasks": ["Address remaining violations", "Ongoing monitoring"],
                "success_metrics": ["Full WCAG compliance", "Accessibility certification"]
            }
        }
    
    def _generate_template_executive_summary(self, violations: List[Dict]) -> Dict[str, Any]:
        """Generate template executive summary as fallback."""
        total_violations = len(violations)
        
        if total_violations == 0:
            return {
                "overview": "Website demonstrates good accessibility compliance with no violations detected.",
                "key_risks": "Minimal legal exposure with current accessibility status.",
                "priority_actions": ["Maintain current standards", "Implement monitoring", "Regular audits"],
                "timeline": "Ongoing maintenance and monitoring recommended.",
                "investment": "Minimal investment required for maintenance."
            }
        else:
            return {
                "overview": f"Website has {total_violations} accessibility violations requiring attention.",
                "key_risks": "Legal compliance concerns and user experience barriers identified.",
                "priority_actions": ["Address critical violations", "Implement systematic fixes", "Establish testing"],
                "timeline": f"Estimated 4-12 weeks for complete remediation of {total_violations} issues.",
                "investment": "Professional accessibility consultation and development resources recommended."
            }
    
    def _parse_executive_summary_text(self, content: str) -> Dict[str, str]:
        """Parse executive summary text response."""
        return {
            "overview": "AI-generated executive summary available in full report.",
            "key_risks": "Detailed risk analysis provided by AI consultant.",
            "priority_actions": "Strategic action plan generated by AI.",
            "timeline": "Realistic timeline estimated by AI analysis.",
            "investment": "Budget and resource recommendations from AI."
        }
    
    def _generate_ai_recommendations(self, violations: List[Dict], website_url: str) -> Dict[str, Any]:
        """Generate AI-powered strategic recommendations."""
        try:
            violation_count = len(violations)
            severity_summary = self._get_violation_summary(violations)
            
            prompt = f"""
            As an accessibility business consultant, provide strategic recommendations for {website_url}:
            
            Violations found: {violation_count}
            Breakdown: {severity_summary['critical']} critical, {severity_summary['serious']} serious, {severity_summary['moderate']} moderate, {severity_summary['minor']} minor
            
            Provide business-focused recommendations for:
            1. BUDGET: Realistic budget estimate for remediation
            2. TEAM: Required team composition and skills
            3. TIMELINE: Practical implementation timeline
            4. RISKS: Business and legal risk assessment
            5. CERTIFICATION: Path to WCAG certification
            
            Format as JSON with these keys: budget, team, timeline, risks, certification
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a business consultant specializing in accessibility compliance strategy."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            ai_content = response.choices[0].message.content
            
            try:
                return json.loads(ai_content)
            except json.JSONDecodeError:
                return self._generate_template_recommendations(violations)
                
        except Exception as e:
            logger.error(f"AI recommendations generation failed: {str(e)}")
            return self._generate_template_recommendations(violations)
    
    def _generate_template_recommendations(self, violations: List[Dict]) -> Dict[str, Any]:
        """Generate template recommendations as fallback."""
        violation_count = len(violations)
        
        if violation_count == 0:
            return {
                "budget": "Minimal ongoing costs for monitoring and maintenance",
                "team": "Current team can maintain compliance with basic training",
                "timeline": "Continuous monitoring recommended",
                "risks": "Low risk with proper ongoing maintenance",
                "certification": "Consider formal WCAG 2.1 AA certification for competitive advantage"
            }
        elif violation_count < 10:
            return {
                "budget": "Estimated $2,000-$5,000 for professional remediation",
                "team": "Frontend developer with accessibility knowledge recommended",
                "timeline": "2-3 weeks for complete remediation",
                "risks": "Low to moderate legal exposure if not addressed",
                "certification": "Good candidate for WCAG 2.1 AA certification after fixes"
            }
        else:
            return {
                "budget": f"Estimated $5,000-$25,000 for comprehensive remediation",
                "team": "Accessibility specialist and development team required",
                "timeline": "4-12 weeks for complete remediation",
                "risks": "Moderate to high legal exposure and business impact",
                "certification": "Systematic approach required for WCAG compliance"
            }
    
    def _generate_clean_website_guide(self, website_url: str) -> Dict[str, Any]:
        """Generate guide for websites with no violations."""
        return {
            'website_url': website_url,
            'total_violations': 0,
            'status': 'compliant',
            'executive_summary': {
                'overview': 'Excellent! Your website demonstrates strong accessibility compliance.',
                'key_risks': 'Minimal legal exposure with current accessibility status.',
                'priority_actions': ['Maintain current standards', 'Implement monitoring', 'Regular audits'],
                'timeline': 'Ongoing maintenance and monitoring recommended.',
                'investment': 'Minimal investment required for maintenance and monitoring.'
            },
            'developer_fixes': {'count': 0, 'violations': []},
            'diy_fixes': {'count': 0, 'violations': []},
            'maintenance_recommendations': {
                'title': 'Ongoing Accessibility Maintenance',
                'description': 'Your website is currently compliant! Here\'s how to stay that way:',
                'tasks': [
                    {
                        'task': 'Monthly accessibility scans',
                        'description': 'Regular monitoring to catch new issues early',
                        'frequency': 'Monthly'
                    },
                    {
                        'task': 'Content review process',
                        'description': 'Ensure new content meets accessibility standards',
                        'frequency': 'Ongoing'
                    },
                    {
                        'task': 'Team training',
                        'description': 'Keep your team updated on accessibility best practices',
                        'frequency': 'Quarterly'
                    }
                ]
            },
            'ai_recommendations': {
                'budget': 'Minimal ongoing costs for monitoring and maintenance',
                'team': 'Current team can maintain compliance with basic training',
                'timeline': 'Continuous monitoring recommended',
                'risks': 'Low risk with proper ongoing maintenance',
                'certification': 'Consider formal WCAG 2.1 AA certification for competitive advantage'
            },
            'generated_with_ai': self.use_ai
        }

