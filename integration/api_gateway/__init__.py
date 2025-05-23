"""
Flask-based API Gateway Module

This module provides a Flask-based API gateway for the Elite Manus AI system.
"""

# Flask imports for routing
from flask import Blueprint, jsonify

# Create Flask Blueprint for API routes
api_blueprint = Blueprint('api', __name__)

# Define routes
@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})

# Import is done here to avoid circular imports
def register_blueprints(app):
    """Register all blueprints with the Flask app"""
    app.register_blueprint(api_blueprint, url_prefix='/api')
    return app
