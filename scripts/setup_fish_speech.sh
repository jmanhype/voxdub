#!/bin/bash

###############################################################################
# Fish Speech (OpenAudio S1) Installation and Setup Script
#
# This script installs and configures Fish Speech TTS for VoxDub
#
# Requirements:
# - CUDA-compatible GPU with 12GB+ VRAM (recommended)
# - Python 3.10+
# - Git
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
FISH_SPEECH_DIR="$HOME/fish-speech"
MODEL_DIR="$FISH_SPEECH_DIR/checkpoints"
MODEL_NAME="s1-mini"  # Options: s1, s1-mini
API_PORT=8080

# Helper functions
print_header() {
    echo -e "\n${BLUE}===================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check system requirements
check_requirements() {
    print_header "Checking System Requirements"

    # Check Python version
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_success "Python 3 found: $PYTHON_VERSION"
    else
        print_error "Python 3 not found. Please install Python 3.10+"
        exit 1
    fi

    # Check Git
    if command -v git &> /dev/null; then
        print_success "Git found"
    else
        print_error "Git not found. Please install Git"
        exit 1
    fi

    # Check CUDA
    if command -v nvidia-smi &> /dev/null; then
        GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | head -n 1)
        print_success "NVIDIA GPU detected: $GPU_INFO"
    else
        print_warning "NVIDIA GPU not detected. CPU mode will be used (slower)"
    fi
}

# Clone Fish Speech repository
clone_repository() {
    print_header "Cloning Fish Speech Repository"

    if [ -d "$FISH_SPEECH_DIR" ]; then
        print_warning "Fish Speech directory already exists"
        read -p "Remove and re-clone? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$FISH_SPEECH_DIR"
        else
            print_success "Using existing directory"
            return
        fi
    fi

    git clone https://github.com/fishaudio/fish-speech.git "$FISH_SPEECH_DIR"
    cd "$FISH_SPEECH_DIR"
    print_success "Repository cloned to $FISH_SPEECH_DIR"
}

# Install Fish Speech dependencies
install_dependencies() {
    print_header "Installing Fish Speech Dependencies"

    cd "$FISH_SPEECH_DIR"

    # Create virtual environment
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Upgrade pip
    pip install --upgrade pip

    # Install PyTorch with CUDA support
    if command -v nvidia-smi &> /dev/null; then
        print_success "Installing PyTorch with CUDA support..."
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    else
        print_warning "Installing PyTorch with CPU support..."
        pip install torch torchvision torchaudio
    fi

    # Install Fish Speech
    pip install -e .

    # Install additional dependencies
    pip install fish-speech-core

    print_success "Dependencies installed"
}

# Download model weights
download_models() {
    print_header "Downloading Model Weights"

    cd "$FISH_SPEECH_DIR"
    mkdir -p "$MODEL_DIR"

    # Activate virtual environment
    source venv/bin/activate

    print_success "Downloading $MODEL_NAME model weights..."

    # Download using Hugging Face CLI
    pip install -U "huggingface_hub[cli]"

    if [ "$MODEL_NAME" = "s1-mini" ]; then
        huggingface-cli download fishaudio/fish-speech-1.4 \
            --local-dir "$MODEL_DIR/fish-speech-1.4" \
            --include "model.pth" "config.json"
    else
        huggingface-cli download fishaudio/fish-speech-1.4-full \
            --local-dir "$MODEL_DIR/fish-speech-1.4-full" \
            --include "model.pth" "config.json"
    fi

    print_success "Model weights downloaded to $MODEL_DIR"
}

# Create API server configuration
create_api_config() {
    print_header "Creating API Server Configuration"

    cat > "$FISH_SPEECH_DIR/api_config.yaml" <<EOF
# Fish Speech API Server Configuration

server:
  host: 0.0.0.0
  port: $API_PORT
  workers: 1

model:
  name: $MODEL_NAME
  checkpoint: checkpoints/fish-speech-1.4/model.pth
  config: checkpoints/fish-speech-1.4/config.json
  device: cuda  # or cpu
  compile: false  # Enable for faster inference (requires more VRAM)

inference:
  max_new_tokens: 1024
  top_p: 0.7
  temperature: 0.7
  repetition_penalty: 1.2

reference_audio:
  cache_dir: ./references
  max_duration: 30  # seconds
EOF

    print_success "API configuration created at $FISH_SPEECH_DIR/api_config.yaml"
}

# Create systemd service (optional)
create_service() {
    print_header "Creating Systemd Service (Optional)"

    read -p "Create systemd service for auto-start? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Skipping systemd service creation"
        return
    fi

    SERVICE_FILE="/etc/systemd/system/fish-speech.service"

    sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Fish Speech TTS API Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$FISH_SPEECH_DIR
Environment="PATH=$FISH_SPEECH_DIR/venv/bin"
ExecStart=$FISH_SPEECH_DIR/venv/bin/python -m fish_speech.webui.launch_api --config api_config.yaml
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable fish-speech

    print_success "Systemd service created"
    print_success "Start with: sudo systemctl start fish-speech"
    print_success "Check status: sudo systemctl status fish-speech"
}

# Create startup script
create_startup_script() {
    print_header "Creating Startup Script"

    cat > "$FISH_SPEECH_DIR/start_api.sh" <<'EOF'
#!/bin/bash

# Fish Speech API Server Startup Script

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate

# Start API server
echo "Starting Fish Speech API Server..."
python -m fish_speech.webui.launch_api --config api_config.yaml

# Alternative: Use uvicorn directly
# uvicorn fish_speech.webui.api:app --host 0.0.0.0 --port 8080 --workers 1
EOF

    chmod +x "$FISH_SPEECH_DIR/start_api.sh"

    print_success "Startup script created at $FISH_SPEECH_DIR/start_api.sh"
}

# Test installation
test_installation() {
    print_header "Testing Installation"

    cd "$FISH_SPEECH_DIR"
    source venv/bin/activate

    # Test import
    python3 -c "import fish_speech; print('Fish Speech imported successfully')" && \
        print_success "Fish Speech installation verified" || \
        print_error "Fish Speech import failed"

    # Check model files
    if [ -f "$MODEL_DIR/fish-speech-1.4/model.pth" ]; then
        print_success "Model weights verified"
    else
        print_error "Model weights not found"
    fi
}

# Print usage instructions
print_usage() {
    print_header "Installation Complete!"

    echo -e "${GREEN}Fish Speech has been successfully installed!${NC}\n"

    echo "Quick Start:"
    echo "1. Start the API server:"
    echo -e "   ${YELLOW}cd $FISH_SPEECH_DIR${NC}"
    echo -e "   ${YELLOW}./start_api.sh${NC}"
    echo ""
    echo "2. Test the API (in another terminal):"
    echo -e "   ${YELLOW}curl http://localhost:$API_PORT/health${NC}"
    echo ""
    echo "3. Configure VoxDub to use Fish Speech:"
    echo -e "   ${YELLOW}Edit .env file:${NC}"
    echo "   TTS_PROVIDER=fish_speech"
    echo "   FISH_SPEECH_API_URL=http://localhost:$API_PORT"
    echo "   FISH_SPEECH_MODEL=$MODEL_NAME"
    echo ""
    echo "Documentation:"
    echo "   - Fish Speech: https://github.com/fishaudio/fish-speech"
    echo "   - API Docs: http://localhost:$API_PORT/docs (after starting server)"
    echo ""
    echo -e "${BLUE}Enjoy state-of-the-art TTS with VoxDub!${NC}\n"
}

# Main installation flow
main() {
    print_header "Fish Speech Installation for VoxDub"

    echo "This script will install Fish Speech TTS"
    echo "Model: $MODEL_NAME"
    echo "Installation directory: $FISH_SPEECH_DIR"
    echo ""

    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Installation cancelled"
        exit 0
    fi

    check_requirements
    clone_repository
    install_dependencies
    download_models
    create_api_config
    create_startup_script
    create_service
    test_installation
    print_usage
}

# Run main installation
main
