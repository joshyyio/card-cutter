#!/bin/bash

echo "🎯 Starting LD Debate Card Cutter..."
echo ""

# Check if .env file exists in backend
if [ ! -f backend/.env ]; then
    echo "⚠️  No .env file found in backend directory!"
    echo "Please create backend/.env with your OpenAI API key:"
    echo "OPENAI_API_KEY=your_openai_api_key_here"
    echo ""
    exit 1
fi

# Start backend
echo "🚀 Starting backend server..."
cd backend
source venv/bin/activate 2>/dev/null || python -m venv venv && source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1
python app.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend
echo "🚀 Starting frontend server..."
cd frontend
npm install > /dev/null 2>&1
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Application started!"
echo "   Backend:  http://localhost:5000"
echo "   Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for Ctrl+C
trap "echo ''; echo '🛑 Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait 