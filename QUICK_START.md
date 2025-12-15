# Quick Start Guide - Fix "Disconnected" Dashboard

## 🎯 Problem: Dashboard Shows "Disconnected"

Your dashboard at `http://localhost:3001/` shows "Disconnected" because the backend API server is not running.

## ✅ Solution: Start Both Frontend and Backend

### **Step 1: Start Backend API Server**

Open a **new terminal** and run:

```bash
# Option A: Using the startup script
./start-backend.sh

# Option B: Direct command
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Option C: Using the API server script
python3 api/server.py --reload --debug
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### **Step 2: Verify Backend is Running**

Test the API health endpoint:
```bash
curl http://localhost:8000/api/v1/health
```

**Expected response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "uptime": 123
  }
}
```

### **Step 3: Frontend Should Connect**

Your dashboard at `http://localhost:3001/` should now show:
- ✅ **Connected** status (instead of "Disconnected")
- 📊 **Real system metrics**
- 📈 **Live charts and data**
- 🔄 **Real-time updates**

## 🔧 Architecture Overview

```
┌─────────────────────┐    ┌─────────────────────┐
│   Frontend (Vite)   │    │   Backend (FastAPI) │
│   Port: 3001        │◄──►│   Port: 8000        │
│   React Dashboard   │    │   REST API + WS     │
└─────────────────────┘    └─────────────────────┘
```

## 🚀 Complete Startup Commands

**Terminal 1 - Backend API:**
```bash
cd /path/to/agentic-kernel-testing
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend Dashboard:**
```bash
cd /path/to/agentic-kernel-testing/dashboard
npm run dev -- --port 3001
```

## 🌐 Access Points

Once both are running:

- **📱 Dashboard:** http://localhost:3001/
- **🔧 API Health:** http://localhost:8000/api/v1/health
- **📚 API Docs:** http://localhost:8000/docs
- **📋 OpenAPI:** http://localhost:8000/openapi.json

## 🔍 Troubleshooting

### Backend Won't Start
```bash
# Check if port 8000 is in use
netstat -tulpn | grep :8000

# Kill existing process
pkill -f "uvicorn.*8000"

# Try again
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Still Shows "Disconnected"
1. **Check browser console** (F12) for errors
2. **Verify API is responding:** `curl http://localhost:8000/api/v1/health`
3. **Check network tab** in browser dev tools
4. **Refresh the page** after backend starts

### Port Conflicts
```bash
# Use different ports if needed
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
npm run dev -- --port 3002

# Update Vite proxy in dashboard/vite.config.ts if using different API port
```

## 🎉 Success Indicators

✅ **Backend running:** API responds to health checks  
✅ **Frontend connected:** Dashboard shows "Connected" status  
✅ **Data flowing:** Charts and metrics display real data  
✅ **Real-time updates:** Status changes reflect immediately  

Your Agentic AI Testing System should now be fully operational! 🚀