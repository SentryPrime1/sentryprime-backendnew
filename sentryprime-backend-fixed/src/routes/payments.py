import logging
import os
import stripe
from flask import Blueprint, request, jsonify

payments_bp = Blueprint('payments', __name__)
logger = logging.getLogger(__name__)

# Configure Stripe with your API keys
stripe.api_key = "sk_test_51RtvtHPmXqc2etr7kikaK3dTNx2jt55v5zsdk6FCpDheGyiVUeaBYsCYBaJI0WurH6ikxhg7xJKmnvSLvMm8jKZK000u1qrChx"

# Subscription plans with enhanced pricing
SUBSCRIPTION_PLANS = {
    'starter': {
        'name': 'Starter Plan',
        'price': 59,
        'price_id': 'price_1RtvuGPmXqc2etr7mHVJgKJL',
        'features': [
            'Up to 100 pages scanned monthly',
            'Basic accessibility reports',
            'Email support',
            'WCAG 2.1 compliance checking'
        ],
        'max_pages': 100
    },
    'pro': {
        'name': 'Pro Plan',
        'price': 149,
        'price_id': 'price_1RtvuGPmXqc2etr7mHVJgKJL',
        'features': [
            'Up to 1,000 pages scanned monthly',
            'AI-powered remediation guides',
            'Priority support',
            'Advanced reporting',
            'API access',
            'Custom integrations'
        ],
        'max_pages': 1000
    },
    'agency': {
        'name': 'Agency Plan',
        'price': 349,
        'price_id': 'price_1RtvuGPmXqc2etr7mHVJgKJL',
        'features': [
            'Up to 5,000 pages scanned monthly',
            'White-label reporting',
            'Dedicated account manager',
            'Custom compliance workflows',
            'Advanced API access',
            'Multi-client management'
        ],
        'max_pages': 5000
    }
}

@payments_bp.route('/plans', methods=['GET'])
def get_plans():
    """Get available subscription plans"""
    try:
        return jsonify({
            'status': 'success',
            'plans': SUBSCRIPTION_PLANS
        })
    except Exception as e:
        logger.error(f'Error fetching plans: {str(e)}')
        return jsonify({
            'status': 'error',
            'error': 'Unable to fetch plans'
        }), 500

@payments_bp.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    """Create Stripe checkout session for subscription"""
    try:
        data = request.get_json()
        plan_type = data.get('planType', '').lower()
        
        if plan_type not in SUBSCRIPTION_PLANS:
            return jsonify({
                'status': 'error',
                'error': 'Invalid plan type'
            }), 400
        
        plan = SUBSCRIPTION_PLANS[plan_type]
        
        # Create Stripe checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': plan['price_id'],
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.host_url + 'success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + 'cancel',
            metadata={
                'plan_type': plan_type,
                'plan_name': plan['name']
            }
        )
        
        logger.info(f'Created checkout session for {plan_type} plan: {session.id}')
        
        return jsonify({
            'status': 'success',
            'checkout_url': session.url,
            'session_id': session.id
        })
        
    except stripe.error.StripeError as e:
        logger.error(f'Stripe error: {str(e)}')
        return jsonify({
            'status': 'error',
            'error': 'Payment processing error'
        }), 500
    except Exception as e:
        logger.error(f'Checkout session error: {str(e)}')
        return jsonify({
            'status': 'error',
            'error': 'Unable to create checkout session'
        }), 500

@payments_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        # Verify webhook signature (in production, use your webhook secret)
        # event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        
        # For now, just log the webhook
        logger.info('Received Stripe webhook')
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        logger.error(f'Webhook error: {str(e)}')
        return jsonify({'status': 'error'}), 400

@payments_bp.route('/subscription/status', methods=['GET'])
def subscription_status():
    """Get subscription status for authenticated user"""
    # TODO: Implement user authentication and subscription lookup
    return jsonify({
        'status': 'authentication_required',
        'message': 'Please sign in to view subscription status'
    })

@payments_bp.route('/subscription/cancel', methods=['POST'])
def cancel_subscription():
    """Cancel user subscription"""
    # TODO: Implement user authentication and subscription cancellation
    return jsonify({
        'status': 'authentication_required',
        'message': 'Please sign in to manage subscription'
    })

@payments_bp.errorhandler(Exception)
def handle_payment_error(e):
    """Handle payment-specific errors gracefully"""
    logger.error(f'Payment error: {str(e)}')
    return jsonify({
        'status': 'error',
        'error': 'Payment service temporarily unavailable'
    }), 500

