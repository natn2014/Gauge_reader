#!/bin/bash

################################################################################
# Jetson Orin Nano Setup Script for Vacuum Bag Gauge Reader
# 
# This script sets up the complete environment including:
# - System dependencies
# - Python virtual environment
# - Required Python packages (with CUDA support)
# - Systemd service for auto-start on boot
# - Auto-detects JetPack version (5.x, 6.0, 6.1, 6.2)
#
# Usage: bash setup_jetson.sh
################################################################################

set -e

echo "=========================================="
echo "Jetson Orin Nano - Gauge Reader Setup"
echo "=========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get current user
CURRENT_USER=$(whoami)
WORK_DIR=$(pwd)

# Detect JetPack version
echo -e "${BLUE}Detecting JetPack version...${NC}"
JETPACK_VERSION=$(cat /etc/nv_tegra_release | grep "R[0-9]" | grep -oE "R[0-9]+" | grep -oE "[0-9]+")

if [ "$JETPACK_VERSION" = "35" ]; then
    JETPACK_MAJOR="5"
    PYTORCH_WHEEL_URL="https://download.pytorch.org/whl/cu118"
    TORCH_VERSION="torch torchvision torchaudio"
    echo -e "${GREEN}✓ Detected: JetPack 5.x (R35) - Using CUDA 11.8${NC}"
elif [ "$JETPACK_VERSION" = "36" ]; then
    JETPACK_MAJOR="6"
    PYTORCH_WHEEL_URL="https://download.pytorch.org/whl/cu121"
    TORCH_VERSION="torch torchvision torchaudio"
    echo -e "${GREEN}✓ Detected: JetPack 6.x (R36) - Using CUDA 12.1${NC}"
else
    echo -e "${YELLOW}⚠ Unknown JetPack version detected (R$JETPACK_VERSION)${NC}"
    echo -e "${YELLOW}Assuming JetPack 6.x with CUDA 12.1${NC}"
    JETPACK_MAJOR="6"
    PYTORCH_WHEEL_URL="https://download.pytorch.org/whl/cu121"
    TORCH_VERSION="torch torchvision torchaudio"
fi

echo ""

echo -e "${YELLOW}[1/7]${NC} Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y > /dev/null 2>&1
echo -e "${GREEN}✓ System packages updated${NC}"

echo ""
echo -e "${YELLOW}[2/7]${NC} Installing Python development tools..."
sudo apt-get install -y \
    python3-pip \
    python3-dev \
    python3-venv \
    build-essential \
    libatlas-base-dev \
    libjasper-dev \
    libtiff-dev \
    libjasper-dev \
    libhdf5-dev \
    libharfbuzz0b \
    libwebp6 > /dev/null 2>&1
echo -e "${GREEN}✓ Python tools installed${NC}"

echo ""
echo -e "${YELLOW}[3/7]${NC} Creating Python virtual environment..."
if [ -d "gauge_venv" ]; then
    echo "Virtual environment already exists, skipping..."
else
    python3 -m venv gauge_venv
fi
source gauge_venv/bin/activate
echo -e "${GREEN}✓ Virtual environment created${NC}"

echo ""
echo -e "${YELLOW}[4/7]${NC} Upgrading pip..."
python3 -m pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✓ pip upgraded${NC}"

echo ""
echo -e "${YELLOW}[5/7]${NC} Installing Python dependencies (this may take 10-15 minutes)..."
python3 -m pip install --upgrade \
    numpy \
    opencv-python \
    pandas \
    matplotlib \
    seaborn \
    easyocr \
    PySide6 \
    pyyaml \
    pillow > /dev/null 2>&1
echo -e "${GREEN}✓ Core packages installed${NC}"

echo ""
echo -e "${YELLOW}[6/7]${NC} Installing PyTorch with CUDA support..."
echo "    Using: $PYTORCH_WHEEL_URL"
echo "    This may take 20-30 minutes (large downloads)..."
python3 -m pip install $TORCH_VERSION --index-url $PYTORCH_WHEEL_URL > /dev/null 2>&1
echo -e "${GREEN}✓ PyTorch with CUDA installed${NC}"

echo ""
echo -e "${YELLOW}[6.5/7]${NC} Installing YOLOv8..."
python3 -m pip install ultralytics > /dev/null 2>&1
echo -e "${GREEN}✓ YOLOv8 installed${NC}"

echo ""
echo -e "${YELLOW}[7/7]${NC} Creating systemd service for auto-start..."

# Create systemd service file
sudo tee /etc/systemd/system/gauge-reader.service > /dev/null <<EOF
[Unit]
Description=Vacuum Bag Gauge Reader Application
After=network.target

[Service]
Type=simple
User=${CURRENT_USER}
WorkingDirectory=${WORK_DIR}
Environment="DISPLAY=:0"
Environment="XAUTHORITY=/home/${CURRENT_USER}/.Xauthority"
ExecStart=${WORK_DIR}/gauge_venv/bin/python3 main_jetson.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable gauge-reader.service
echo -e "${GREEN}✓ Systemd service created and enabled${NC}"

echo ""
echo "=========================================="
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo "=========================================="
echo ""
echo -e "${BLUE}System Information:${NC}"
echo "  JetPack Version: ${JETPACK_MAJOR}.x (R${JETPACK_VERSION})"
echo "  CUDA Configuration: $PYTORCH_WHEEL_URL"
echo "  Work Directory: ${WORK_DIR}"
echo "  Current User: ${CURRENT_USER}"
echo ""
echo "📋 Next steps:"
echo "   1. Copy gauge_epoch-100.pt to: ${WORK_DIR}/"
echo "   2. Copy ui_mainwindow.py to: ${WORK_DIR}/"
echo "   3. Copy styles.qss to: ${WORK_DIR}/"
echo "   4. Connect USB camera to Jetson (will appear as /dev/video0)"
echo ""
echo "🚀 To run the application:"
echo ""
echo "   Start now:    sudo systemctl start gauge-reader"
echo "   Stop:         sudo systemctl stop gauge-reader"
echo "   Check status: sudo systemctl status gauge-reader"
echo "   View logs:    journalctl -u gauge-reader -f"
echo ""
echo "💡 Auto-start on boot is already enabled!"
echo "   The application will start automatically when the Jetson boots."
echo ""
echo "✅ Verify installation:"
echo "   python3 -c \"import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')\""
echo ""
