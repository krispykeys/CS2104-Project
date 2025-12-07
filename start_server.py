#!/usr/bin/env python3
"""
Startup script for CS2104 Home Value Estimator Server
Automatically sets up Python paths and starts the FastAPI server
"""

import sys
import os
from pathlib import Path

# Get project paths
project_root = Path(__file__).parent
code_dir = project_root / "code"

# Add code directory to Python path
sys.path.insert(0, str(code_dir))

# Change to code directory for proper imports
os.chdir(code_dir)

# Import and run uvicorn
import uvicorn

if __name__ == "__main__":
    print(f"Starting Home Value Estimator Server...")
    print(f"Project root: {project_root}")
    print(f"Code directory: {code_dir}")
    print(f"Server will be available at: http://localhost:8000")
    print(f"Frontend will be available at: http://localhost:8000")
    print()
    
    # Run the server
    uvicorn.run(
        "customer_agent_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
