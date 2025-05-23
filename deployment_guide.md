# Elite Manus AI Deployment Guide

## Overview

This guide provides instructions for deploying the Elite Manus AI system, a powerful multimodal AI platform capable of text, image, and video generation using Ollama.

## System Requirements

- **Digital Ocean Droplet**: Basic Droplet with at least 4GB RAM (8GB+ recommended for video generation)
- **Storage**: Minimum 25GB (50GB+ recommended for multiple models)
- **Operating System**: Ubuntu 22.04 LTS

## Prerequisites

1. **Install Docker**:
   ```bash
   sudo apt update
   sudo apt install -y docker.io docker-compose
   sudo systemctl enable docker
   sudo systemctl start docker
   ```

2. **Install Ollama**:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

3. **Start Ollama Service**:
   ```bash
   ollama serve
   ```

## Deployment Steps

### 1. Clone the Repository

```bash
git clone https://github.com/SpartanPlumbingJosh/The_Juggernaut_Backend.git
cd The_Juggernaut_Backend
```

### 2. Set Up Environment Variables

Create a `.env` file in the root directory:

```bash
FLASK_ENV=production
PORT=5000
DEBUG=False
OLLAMA_API_URL=http://localhost:11434
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Pull Required Models

```bash
# Text models
ollama pull mistral:7b-instruct-v0.3
ollama pull mixtral:8x7b-instruct-v0.1
ollama pull codellama:7b-instruct

# Image models
ollama pull stable-diffusion-xl
ollama pull playground-v2

# Video models
ollama pull stable-video-diffusion
ollama pull animatediff
```

### 5. Start the Backend Service

```bash
gunicorn app:app --bind 0.0.0.0:5000 --workers 4
```

### 6. Configure Frontend

Update the frontend environment variables to point to your backend:

```
REACT_APP_API_URL=https://your-backend-url.ondigitalocean.app
```

## API Endpoints

### Text Generation
- **Endpoint**: `/api/chat`
- **Method**: POST
- **Payload**:
  ```json
  {
    "message": "Your text prompt here",
    "session_id": "optional-session-id"
  }
  ```

### Image Generation
- **Endpoint**: `/api/generate/image`
- **Method**: POST
- **Payload**:
  ```json
  {
    "prompt": "Your image description here",
    "model": "optional-model-name"
  }
  ```

### Video Generation
- **Endpoint**: `/api/generate/video`
- **Method**: POST
- **Payload**:
  ```json
  {
    "prompt": "Your video description here",
    "model": "optional-model-name"
  }
  ```

### List Available Models
- **Endpoint**: `/api/models`
- **Method**: GET

### List Plugins
- **Endpoint**: `/api/plugins`
- **Method**: GET

## Troubleshooting

### Common Issues

1. **Ollama Not Running**:
   - Check if Ollama is running: `ps aux | grep ollama`
   - Restart Ollama: `ollama serve`

2. **Model Download Failures**:
   - Check disk space: `df -h`
   - Check Ollama logs: `journalctl -u ollama`

3. **Memory Issues**:
   - Reduce the number of models loaded simultaneously
   - Upgrade to a larger Droplet size

## Resource Management

The system is designed to use multiple models for different tasks. To optimize resource usage:

1. **For Low-Resource Environments (4GB RAM)**:
   - Use only Mistral 7B for text generation
   - Disable video generation

2. **For Medium-Resource Environments (8GB RAM)**:
   - Use Mistral 7B for text and Stable Diffusion for images
   - Limit video generation to short clips

3. **For High-Resource Environments (16GB+ RAM)**:
   - Enable all models and features

## Monitoring

Monitor system resource usage:
```bash
htop
nvidia-smi  # If using GPU
```

## Updating

To update the system:
```bash
cd The_Juggernaut_Backend
git pull
pip install -r requirements.txt
sudo systemctl restart your-service-name
```

## Support

For issues or questions, please open an issue on the GitHub repository.
