import uvicorn
import subprocess
import sys
import os

def run_migrations():
    """Initialize database"""
    subprocess.run([sys.executable, "initialize_db.py"])
    subprocess.run([sys.executable, "create_admin.py"])

if __name__ == "__main__":
    print("Starting E-Commerce Backend Server...")
    
    # Initialize database if needed
    if not os.path.exists("ecommerce.db"):
        print("Initializing database...")
        run_migrations()
    
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )