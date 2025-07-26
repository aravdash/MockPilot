#!/usr/bin/env python3
"""
Wrapper script for Pinecone Notes Integration
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Run the backend Pinecone integration with all arguments passed through"""
    backend_pinecone = Path(__file__).parent / "backend" / "services" / "pinecone_integration.py"
    
    # Pass all command line arguments to the backend script
    cmd = [sys.executable, str(backend_pinecone)] + sys.argv[1:]
    
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        return e.returncode
    except FileNotFoundError:
        print(f"Error: Backend Pinecone script not found at {backend_pinecone}")
        return 1

if __name__ == "__main__":
    sys.exit(main())