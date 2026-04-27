#!/bin/bash
# Simple one-command startup for Linux/Mac
# Runs both backend and frontend

echo ""
echo "========================================"
echo "Document Intelligence System"
echo "Starting Backend + Frontend..."
echo "========================================"
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found!"
    echo "Run setup.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Start backend in background
echo "Starting Backend (Port 8000)..."
cd backend
python app.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend
cd ../frontend
echo ""
echo "Starting Frontend (Port 3000)..."
echo "Opening http://localhost:3000 in browser..."
echo ""

npm run dev

# Cleanup on exit
trap "kill $BACKEND_PID" EXIT
