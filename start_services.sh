#!/bin/bash

# Start Both Backend and Frontend Services
# This script starts both the backend and frontend servers for development

set -e  # Exit on any error

echo "🚀 Starting AI Team Development Services"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "crewai_app/main.py" ]; then
    echo "❌ Error: Not in the correct directory. Please run from the project root."
    exit 1
fi

# Function to kill processes on specific ports
kill_port() {
    local port=$1
    local service_name=$2
    
    echo "🔍 Checking for processes on port $port..."
    
    # Find processes using the port
    local pids=$(lsof -ti:$port 2>/dev/null || true)
    
    if [ -n "$pids" ]; then
        echo "⚠️  Found processes on port $port: $pids"
        echo "🔄 Killing processes on port $port..."
        
        # Try graceful kill first
        echo $pids | xargs kill -TERM 2>/dev/null || true
        sleep 3
        
        # Check if still running
        local remaining_pids=$(lsof -ti:$port 2>/dev/null || true)
        if [ -n "$remaining_pids" ]; then
            echo "⚠️  Processes still running on port $port, forcing kill..."
            echo $remaining_pids | xargs kill -9 2>/dev/null || true
            sleep 2
            
            # Final check
            local final_pids=$(lsof -ti:$port 2>/dev/null || true)
            if [ -n "$final_pids" ]; then
                echo "❌ Failed to kill processes on port $port: $final_pids"
                return 1
            fi
        fi
        echo "✅ Port $port cleared"
    else
        echo "✅ Port $port is free"
    fi
    return 0
}

# Function to check if port is free
check_port() {
    local port=$1
    local max_attempts=5
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if ! lsof -ti:$port >/dev/null 2>&1; then
            return 0
        fi
        echo "⏳ Port $port still in use, attempt $attempt/$max_attempts..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ Port $port is still in use after $max_attempts attempts"
    return 1
}

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f uvicorn 2>/dev/null || true
pkill -f "ng serve" 2>/dev/null || true

# Clear ports
kill_port 8000 "backend"
kill_port 4200 "frontend"

# Function to fix database schema
fix_database_schema() {
    echo "🔧 Checking database schema..."
    
    # Check if the new columns exist
    local missing_columns=$(sqlite3 ai_team.db "PRAGMA table_info(workflows);" | grep -E "(started_at|finished_at|error|last_heartbeat_at)" | wc -l)
    
    if [ "$missing_columns" -lt 4 ]; then
        echo "⚠️  Database schema is outdated, adding missing columns..."
        
        # Add missing columns if they don't exist
        sqlite3 ai_team.db "ALTER TABLE workflows ADD COLUMN started_at DATETIME;" 2>/dev/null || true
        sqlite3 ai_team.db "ALTER TABLE workflows ADD COLUMN finished_at DATETIME;" 2>/dev/null || true
        sqlite3 ai_team.db "ALTER TABLE workflows ADD COLUMN error TEXT;" 2>/dev/null || true
        sqlite3 ai_team.db "ALTER TABLE workflows ADD COLUMN last_heartbeat_at DATETIME;" 2>/dev/null || true
        
        echo "✅ Database schema updated"
    else
        echo "✅ Database schema is up to date"
    fi
}

# Fix database schema before starting backend
fix_database_schema

# Function to start backend with retry logic
start_backend() {
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "🔧 Starting backend server (attempt $attempt/$max_attempts)..."
        
        # Check if port is free before starting
        if ! check_port 8000; then
            echo "❌ Port 8000 is still in use, cannot start backend"
            return 1
        fi
        
        # Start backend in background
        source venv/bin/activate
        uvicorn crewai_app.main:app --reload --host 127.0.0.1 --port 8000 > backend.log 2>&1 &
        BACKEND_PID=$!
        
        # Wait for backend to start
        echo "⏳ Waiting for backend to start..."
        sleep 8
        
        # Test backend health
        echo "🧪 Testing backend health..."
        if curl -f -s http://127.0.0.1:8000/health >/dev/null 2>&1; then
            echo "✅ Backend is healthy"
            return 0
        else
            echo "⚠️  Backend health check failed (attempt $attempt/$max_attempts)"
            
            # Check if backend process is still running
            if ! kill -0 $BACKEND_PID 2>/dev/null; then
                echo "❌ Backend process died, checking logs..."
                tail -20 backend.log 2>/dev/null || echo "No backend logs available"
            fi
            
            # Kill the failed backend process
            kill $BACKEND_PID 2>/dev/null || true
            sleep 2
            
            attempt=$((attempt + 1))
        fi
    done
    
    echo "❌ Failed to start backend after $max_attempts attempts"
    return 1
}

# Start backend with retry logic
if ! start_backend; then
    echo "❌ Backend startup failed. Check backend.log for details."
    exit 1
fi

# Function to start frontend with retry logic
start_frontend() {
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "🎨 Starting frontend server (attempt $attempt/$max_attempts)..."
        
        # Check if port is free before starting
        if ! check_port 4200; then
            echo "❌ Port 4200 is still in use, cannot start frontend"
            return 1
        fi
        
        # Start frontend in background
        cd frontend
        npm run start -- --host minions.localhost --port 4200 > ../frontend.log 2>&1 &
        FRONTEND_PID=$!
        cd ..
        
        # Wait for frontend to start
        echo "⏳ Waiting for frontend to start..."
        sleep 15
        
        # Test frontend
        echo "🧪 Testing frontend..."
        if curl -f -s http://minions.localhost:4200 >/dev/null 2>&1; then
            echo "✅ Frontend is healthy"
            return 0
        else
            echo "⚠️  Frontend health check failed (attempt $attempt/$max_attempts)"
            
            # Check if frontend process is still running
            if ! kill -0 $FRONTEND_PID 2>/dev/null; then
                echo "❌ Frontend process died, checking logs..."
                tail -20 frontend.log 2>/dev/null || echo "No frontend logs available"
            fi
            
            # Kill the failed frontend process
            kill $FRONTEND_PID 2>/dev/null || true
            sleep 2
            
            attempt=$((attempt + 1))
        fi
    done
    
    echo "❌ Failed to start frontend after $max_attempts attempts"
    return 1
}

# Start frontend with retry logic
if ! start_frontend; then
    echo "❌ Frontend startup failed. Check frontend.log for details."
    exit 1
fi

echo ""
echo "✅ Both services are starting!"
echo "=============================="
echo "🔧 Backend: http://127.0.0.1:8000"
echo "🎨 Frontend: http://minions.localhost:4200"
echo "📊 API Docs: http://127.0.0.1:8000/docs"
echo ""
echo "Press Ctrl+C to stop both services"

# Wait for user to stop
trap 'echo "🛑 Stopping services..."; kill $BACKEND_PID 2>/dev/null || true; kill $FRONTEND_PID 2>/dev/null || true; echo "✅ Services stopped"; exit 0' INT

# Keep script running and show status
echo "📊 Services are running. Press Ctrl+C to stop."
echo "📝 Logs: backend.log, frontend.log"
echo ""

# Monitor services
while true; do
    sleep 30
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "⚠️  Backend process died unexpectedly"
        break
    fi
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "⚠️  Frontend process died unexpectedly"
        break
    fi
done
