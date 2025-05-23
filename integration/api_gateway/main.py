"""
Flask-based API Gateway Main Module

This module provides the main Flask application setup for the Elite Manus AI system.
"""

from flask import Flask, jsonify, request
from .api_gateway import APIGateway

def setup_api_gateway(engine):
    """
    Set up the API Gateway with Flask.
    
    Args:
        engine: Core engine components and configuration
        
    Returns:
        APIGateway: Initialized API Gateway
    """
    # Create API Gateway instance
    api_gateway = APIGateway(engine)
    
    # Import here to avoid circular imports
    from integration.api_gateway import register_blueprints
    
    return api_gateway
