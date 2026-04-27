#!/bin/bash
# Quick Start Script for Document Intelligence System

echo "======================================"
echo "Document Intelligence System - Setup"
echo "======================================"
echo ""

# Check Python version
echo "Checking Python version..."
python --version

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install PyTorch with CUDA support
echo ""
echo "Installing PyTorch with CUDA support..."
echo "Choose your CUDA version:"
echo "1) CUDA 11.8"
echo "2) CUDA 12.1"
echo "3) CPU only (slow)"
read -p "Enter choice (1-3): " cuda_choice

case $cuda_choice in
    1)
        pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
        ;;
    2)
        pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
        ;;
    3)
        pip install torch torchvision
        ;;
    *)
        echo "Invalid choice. Installing with default."
        pip install torch torchvision
        ;;
esac

# Setup frontend
echo ""
echo "Setting up frontend..."
cd frontend
npm install
cd ..

# Create .env file
echo ""
echo "Creating .env file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo ".env file created. Please edit if needed."
else
    echo ".env file already exists."
fi

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "To start the system:"
echo "1. Terminal 1 - Backend:"
echo "   cd backend"
echo "   python app.py"
echo ""
echo "2. Terminal 2 - Frontend:"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "Frontend will open at http://localhost:3000"
echo "API available at http://localhost:8000"
