"""
Utility functions for the Drowsiness Detection System
Common helper functions used across modules
"""

import os
import urllib.request
import hashlib
import shutil
from pathlib import Path
import config

def ensure_directory(path):
    """Ensure directory exists, create if it doesn't"""
    Path(path).mkdir(parents=True, exist_ok=True)
    return path

def download_file(url, destination, chunk_size=8192):
    """Download a file from URL to destination with progress"""
    try:
        print(f"Downloading {url}...")
        
        # Create destination directory if it doesn't exist
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        
        with urllib.request.urlopen(url) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            
            with open(destination, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        print(f"\rProgress: {progress:.1f}%", end='', flush=True)
        
        print(f"\nDownload completed: {destination}")
        return True
        
    except Exception as e:
        print(f"Error downloading file: {e}")
        return False

def verify_file_hash(filepath, expected_hash, algorithm='sha256'):
    """Verify file integrity using hash"""
    try:
        hash_func = hashlib.new(algorithm)
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        
        actual_hash = hash_func.hexdigest()
        return actual_hash.lower() == expected_hash.lower()
        
    except Exception as e:
        print(f"Error verifying file hash: {e}")
        return False

def download_dlib_model():
    """Download dlib's facial landmark predictor model if not present"""
    model_path = config.DLIB_PREDICTOR_PATH
    model_url = config.DLIB_MODEL_URL
    
    # Check if model already exists
    if os.path.exists(model_path):
        print(f"dlib model found: {model_path}")
        return True
    
    print("dlib facial landmark model not found, downloading...")
    
    # Create models directory
    models_dir = os.path.dirname(model_path)
    ensure_directory(models_dir)
    
    # Download the model
    try:
        if download_file(model_url, model_path):
            # Verify the file exists and has reasonable size
            if os.path.exists(model_path) and os.path.getsize(model_path) > 1000000:  # > 1MB
                print("dlib model downloaded successfully")
                return True
            else:
                print("Downloaded file appears to be invalid")
                if os.path.exists(model_path):
                    os.remove(model_path)
                return False
        else:
            return False
            
    except Exception as e:
        print(f"Error downloading dlib model: {e}")
        return False

def get_file_size_mb(filepath):
    """Get file size in MB"""
    try:
        size_bytes = os.path.getsize(filepath)
        size_mb = size_bytes / (1024 * 1024)
        return round(size_mb, 2)
    except:
        return 0

def cleanup_old_files(directory, max_files=50, pattern="*.jpg"):
    """Clean up old files in directory, keeping only the most recent ones"""
    try:
        if not os.path.exists(directory):
            return
        
        import glob
        files = glob.glob(os.path.join(directory, pattern))
        
        if len(files) <= max_files:
            return
        
        # Sort by modification time (oldest first)
        files.sort(key=os.path.getmtime)
        
        # Remove oldest files
        files_to_remove = files[:-max_files]
        for file_path in files_to_remove:
            try:
                os.remove(file_path)
                print(f"Removed old file: {file_path}")
            except Exception as e:
                print(f"Could not remove {file_path}: {e}")
                
        print(f"Cleaned up {len(files_to_remove)} old files from {directory}")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")

def get_system_info():
    """Get basic system information"""
    try:
        import platform
        import psutil
        import cv2
        
        info = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'python_version': platform.python_version(),
            'opencv_version': cv2.__version__,
            'cpu_count': os.cpu_count(),
            'memory_gb': round(psutil.virtual_memory().total / (1024**3), 1),
            'disk_space_gb': round(shutil.disk_usage('.').free / (1024**3), 1)
        }
        
        return info
        
    except Exception as e:
        print(f"Error getting system info: {e}")
        return {}

def format_duration(seconds):
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

def log_detection_event(event_type, details=None):
    """Log detection events to file"""
    if not config.LOG_DETECTIONS:
        return
    
    try:
        import datetime
        
        log_dir = os.path.dirname(config.LOG_FILE)
        ensure_directory(log_dir)
        
        timestamp = datetime.datetime.now().isoformat()
        log_entry = f"[{timestamp}] {event_type}"
        
        if details:
            log_entry += f" - {details}"
        
        with open(config.LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
            
    except Exception as e:
        print(f"Error logging event: {e}")

def check_dependencies():
    """Check if all required dependencies are available"""
    dependencies = {
        'opencv': 'cv2',
        'dlib': 'dlib',
        'numpy': 'numpy',
        'pygame': 'pygame',
        'flask': 'flask',
        'scipy': 'scipy'
    }
    
    missing = []
    available = []
    
    for name, module in dependencies.items():
        try:
            __import__(module)
            available.append(name)
        except ImportError:
            missing.append(name)
    
    return available, missing

def test_camera_access():
    """Test if camera is accessible"""
    try:
        import cv2
        
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            return ret and frame is not None
        else:
            return False
            
    except Exception as e:
        print(f"Error testing camera: {e}")
        return False

if __name__ == "__main__":
    print("Running utility diagnostics...")
    
    # Check dependencies
    available, missing = check_dependencies()
    print(f"Available dependencies: {', '.join(available)}")
    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
    
    # Test camera
    camera_ok = test_camera_access()
    print(f"Camera access: {'OK' if camera_ok else 'Failed'}")
    
    # Check dlib model
    model_ok = download_dlib_model()
    print(f"dlib model: {'OK' if model_ok else 'Failed'}")
    
    # System info
    info = get_system_info()
    if info:
        print(f"System: {info.get('platform')} {info.get('platform_version')}")
        print(f"Python: {info.get('python_version')}")
        print(f"OpenCV: {info.get('opencv_version')}")
        print(f"CPU cores: {info.get('cpu_count')}")
        print(f"Memory: {info.get('memory_gb')} GB")
