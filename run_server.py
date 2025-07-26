#!/usr/bin/env python3
"""
Simple server runner for DreamBig application
"""
import uvicorn
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

if __name__ == "__main__":
    print("🚀 Starting DreamBig Real Estate Server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📍 Login page: http://localhost:8000/login")
    print("📍 API docs: http://localhost:8000/api/docs")
    print("-" * 50)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
