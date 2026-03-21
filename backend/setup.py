"""
Setup Helper Script for Adaptive Learning Platform Backend

Run this script to help set up the project quickly.
"""
import os
import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def print_success(text):
    """Print success message"""
    print(f"✅ {text}")


def print_warning(text):
    """Print warning message"""
    print(f"⚠️  {text}")


def print_error(text):
    """Print error message"""
    print(f"❌ {text}")


def print_info(text):
    """Print info message"""
    print(f"ℹ️  {text}")


def check_python_version():
    """Check Python version"""
    print_header("Checking Python Version")
    
    version = sys.version_info
    version_string = f"{version.major}.{version.minor}.{version.micro}"
    
    print(f"Python version: {version_string}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python 3.8+ required (you have {version_string})")
        return False
    
    print_success(f"Python {version_string} is compatible")
    return True


def check_pip():
    """Check if pip is available"""
    print_header("Checking pip")
    
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                                capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout.strip())
            print_success("pip is available")
            return True
    except Exception as e:
        print_error(f"pip check failed: {e}")
    
    return False


def check_if_venv_exists():
    """Check if virtual environment exists"""
    venv_path = Path("venv")
    return venv_path.exists() and (venv_path / "pyvenv.cfg").exists()


def create_venv():
    """Create virtual environment"""
    print_header("Creating Virtual Environment")
    
    if check_if_venv_exists():
        print_warning("Virtual environment already exists at ./venv")
        return True
    
    try:
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print_success("Virtual environment created")
        
        if sys.platform == "win32":
            print_info("On Windows, activate with: venv\\Scripts\\activate")
        else:
            print_info("On macOS/Linux, activate with: source venv/bin/activate")
        
        return True
    except Exception as e:
        print_error(f"Failed to create venv: {e}")
        return False


def get_pip_executable():
    """Get the pip executable path"""
    if sys.platform == "win32":
        return Path("venv") / "Scripts" / "pip.exe"
    else:
        return Path("venv") / "bin" / "pip"


def install_requirements():
    """Install requirements"""
    print_header("Installing Requirements")
    
    pip_exe = get_pip_executable()
    requirements_file = "requirements.txt"
    
    if not Path(requirements_file).exists():
        print_error(f"{requirements_file} not found!")
        return False
    
    try:
        print(f"Installing packages from {requirements_file}...")
        subprocess.run([str(pip_exe), "install", "-r", requirements_file], check=True)
        print_success("All requirements installed")
        return True
    except Exception as e:
        print_error(f"Failed to install requirements: {e}")
        return False


def setup_env_file():
    """Setup .env file"""
    print_header("Setting Up .env File")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print_info(".env file already exists")
        print_info("Current API key status:")
        
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                if "your_gemini_api_key_here" in content or content.strip() == "":
                    print_warning("  GEMINI_API_KEY not set in .env")
                else:
                    print_success("  GEMINI_API_KEY appears to be set")
        except:
            pass
        
        return True
    
    if env_example.exists():
        print("Copying .env.example to .env...")
        try:
            with open(env_example, 'r') as f:
                example_content = f.read()
            with open(env_file, 'w') as f:
                f.write(example_content)
            print_success(".env file created from .env.example")
            print_warning("⚠️  Remember to add your GEMINI_API_KEY to .env!")
            return True
        except Exception as e:
            print_error(f"Failed to create .env: {e}")
            return False
    else:
        print_warning(".env.example not found, creating .env template...")
        template = """\
# Google Gemini API Key
# Get your key from: https://aistudio.google.com/app/apikeys
GEMINI_API_KEY=your_gemini_api_key_here

# Server Configuration
SERVER_HOST=127.0.0.1
SERVER_PORT=8000
DEBUG=True
"""
        try:
            with open(env_file, 'w') as f:
                f.write(template)
            print_success(".env template created")
            print_warning("⚠️  Add your GEMINI_API_KEY to .env!")
            return True
        except Exception as e:
            print_error(f"Failed to create .env: {e}")
            return False


def check_gemini_api_key():
    """Check if Gemini API key is configured"""
    print_header("Checking Gemini API Key")
    
    # Check .env file
    env_file = Path(".env")
    if env_file.exists():
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        value = line.split("=", 1)[1].strip()
                        if value and value != "your_gemini_api_key_here":
                            print_success("GEMINI_API_KEY is set in .env")
                            return True
        except:
            pass
    
    # Check environment variable
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        print_success("GEMINI_API_KEY is set in environment")
        return True
    
    print_warning("GEMINI_API_KEY not configured")
    print_info("To use Gemini features:")
    print_info("1. Get API key: https://aistudio.google.com/app/apikeys")
    print_info("2. Add to .env: GEMINI_API_KEY=your_key_here")
    print_info("(Backend works without it, returns demo questions)")
    
    return False


def verify_installation():
    """Verify installation by checking imports"""
    print_header("Verifying Installation")
    
    try:
        import fastapi
        print_success("FastAPI is installed")
    except ImportError:
        print_error("FastAPI not installed")
        return False
    
    try:
        import pydantic
        print_success("Pydantic is installed")
    except ImportError:
        print_error("Pydantic not installed")
        return False
    
    try:
        import google.generativeai
        print_success("google-generativeai is installed")
    except ImportError:
        print_warning("google-generativeai not installed (optional for demo mode)")
    
    return True


def main():
    """Main setup flow"""
    print("\n" + "="*70)
    print("  🎓 Adaptive Learning Platform - Backend Setup")
    print("="*70)
    
    # Check Python
    if not check_python_version():
        return 1
    
    # Check pip
    if not check_pip():
        return 1
    
    # Create venv
    if not create_venv():
        return 1
    
    # Install requirements
    if not install_requirements():
        print_warning("Installation had issues, but continuing...")
    
    # Setup .env
    setup_env_file()
    
    # Check API key
    check_gemini_api_key()
    
    # Verify
    if not verify_installation():
        print_error("Installation verification failed!")
        return 1
    
    # Success!
    print_header("✅ Setup Complete!")
    
    print(f"""
Next steps:

1. Activate virtual environment:
   {"venv\\Scripts\\activate" if sys.platform == "win32" else "source venv/bin/activate"}

2. Add your Gemini API key to .env:
   - Get key from: https://aistudio.google.com/app/apikeys
   - Edit .env and set: GEMINI_API_KEY=your_key_here

3. Start the server:
   python main.py

4. Access API documentation:
   http://127.0.0.1:8000/docs

5. Test with example client:
   python example_client.py

Good luck with your hackathon! 🚀
""")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
