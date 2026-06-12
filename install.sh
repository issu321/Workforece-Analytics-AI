#!/bin/bash
echo "========================================"
echo "  WorkforceAI Installation (Linux/macOS)"
echo "========================================"
echo ""
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    exit 1
fi
echo "Creating virtual environment..."
python3 -m venv venv
echo "Activating virtual environment..."
source venv/bin/activate
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo ""
echo "Creating directories..."
mkdir -p data uploads reports models
echo ""
echo "========================================"
echo "  Installation Complete!"
echo "========================================"
echo ""
echo "To start the application:"
echo "  source venv/bin/activate"
echo "  python app.py"
echo ""
echo "Then open http://localhost:5000 in your browser."
echo ""
echo "Default login: admin / admin123"
echo ""
