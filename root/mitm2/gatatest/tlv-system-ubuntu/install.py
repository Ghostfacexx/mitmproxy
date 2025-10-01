"""
Installation script for the NFC proxy system.
"""
import subprocess
import sys
import os


def install_dependencies():
    """Install required Python packages."""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def create_directories():
    """Create necessary directories."""
    print("📁 Creating directories...")
    
    directories = ['keys', 'logs']
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created directory: {directory}")
    
    return True


def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print(f"❌ Python 3.7+ required, found {version.major}.{version.minor}")
        return False
    
    print(f"✓ Python version check passed: {version.major}.{version.minor}.{version.micro}")
    return True


def main():
    """Run the installation process."""
    print("🚀 NFC Proxy System Installation")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Create directories
    if not create_directories():
        return 1
    
    # Install dependencies
    if not install_dependencies():
        print("\n⚠️  Installation completed with warnings.")
        print("You can install dependencies manually:")
        print("pip install pycryptodome protobuf")
        return 0
    
    print("\n🎉 Installation completed successfully!")
    print("\nNext steps:")
    print("1. Review and modify configuration files in config/")
    print("2. Run the system: python main.py")
    print("3. Check logs in logs/ directory")
    
    return 0


if __name__ == "__main__":
    exit(main())
