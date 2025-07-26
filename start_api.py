#!/usr/bin/env python3
"""
Start the Notes Summarizer API Server

Provides a web interface and API for searching processed notes
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Start the API server"""
    api_server = Path(__file__).parent / "backend" / "services" / "api_server.py"
    
    print("🚀 Starting Notes Summarizer API Server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("🔍 Web interface: http://localhost:8000")
    print("📚 API docs: http://localhost:8000/docs")
    print("\n⏹️  Press Ctrl+C to stop the server\n")
    
    try:
        # Run the API server
        subprocess.run([sys.executable, str(api_server)], check=True)
    except KeyboardInterrupt:
        print("\n✅ Server stopped")
    except FileNotFoundError:
        print(f"❌ Error: API server not found at {api_server}")
        return 1
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())