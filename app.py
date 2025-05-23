"""
Updated Flask Application with Multimodal Support

This module provides the main Flask application with endpoints for text, image, and video generation.
"""

from flask import Flask, request, jsonify, send_file
import os
import sys
import logging
import tempfile
import base64
from io import BytesIO
from dotenv import load_dotenv

# Add the core engine and integration modules to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core-engine/src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'integration/api_gateway'))

# Import core components
from core_engine.src.main import initialize_engine
from integration.api_gateway.main import setup_api_gateway

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize core engine
engine = initialize_engine()

# Setup API gateway
api_gateway = setup_api_gateway(engine)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "version": "1.0.0"})

@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat endpoint that processes user messages"""
    try:
        data = request.json
        user_message = data.get('message', '')
        session_id = data.get('session_id', '')
        
        if not user_message:
            return jsonify({"error": "No message provided"}), 400
            
        response = api_gateway.process_message(user_message, session_id)
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/generate/image', methods=['POST'])
def generate_image():
    """Image generation endpoint"""
    try:
        data = request.json
        prompt = data.get('prompt', '')
        model = data.get('model', None)
        
        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400
            
        response = api_gateway.generate_image(prompt, model)
        
        # Check if the response contains an error
        if "error" in response:
            return jsonify(response), 500
            
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/generate/video', methods=['POST'])
def generate_video():
    """Video generation endpoint"""
    try:
        data = request.json
        prompt = data.get('prompt', '')
        model = data.get('model', None)
        
        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400
            
        response = api_gateway.generate_video(prompt, model)
        
        # Check if the response contains an error
        if "error" in response:
            return jsonify(response), 500
            
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error generating video: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/models', methods=['GET'])
def list_models():
    """List available models endpoint"""
    try:
        response = api_gateway.list_models()
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/plugins', methods=['GET'])
def list_plugins():
    """List available plugins"""
    try:
        plugins = api_gateway.list_plugins()
        return jsonify({"plugins": plugins})
    except Exception as e:
        logger.error(f"Error listing plugins: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
