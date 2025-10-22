#!/usr/bin/env python3
"""
Setup script for Notes Summarizer

Simple setup and dependency installation
"""

import sys
import subprocess
from pathlib import Path

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_environment():
    """Check if the environment is properly set up"""
    print("🔍 Checking environment...")
    
    # Check if .env file exists
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("⚠️  No .env file found. Creating from template...")
        try:
            env_content = env_example.read_text()
            env_file.write_text(env_content)
            print("✅ .env file created from template")
            print("💡 Edit .env file to add your OpenAI API key (only needed for diagram processing)")
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
    
    # Check backend structure
    backend_main = Path("backend/main.py")
    if backend_main.exists():
        print("✅ Backend structure is correct")
        return True
    else:
        print("❌ Backend structure is missing")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Notes Summarizer...")
    print()
    
    # Check environment
    if not check_environment():
        print("❌ Environment check failed")
        return 1
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Dependency installation failed")
        return 1
    
    print()
    print("🎉 Setup complete!")
    print()
    print("🔧 Quick Start:")
    print("  python process_pdf.py your_document.pdf")
    print("  python process_pdf.py your_document.pdf -f rag")
    print()
    print("📚 For more options, see README.md")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())