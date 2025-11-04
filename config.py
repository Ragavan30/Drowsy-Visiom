"""
Configuration settings for the Drowsiness Detection System
All configurable parameters are defined here
"""

import os

# ==================================================
# DETECTION PARAMETERS
# ==================================================

# Eye Aspect Ratio threshold for drowsiness detection
# Lower values = more sensitive (detect drowsiness earlier)
# Higher values = less sensitive (reduce false positives)
EAR_THRESHOLD = 0.25

# Number of consecutive frames with closed eyes to trigger alert
# Higher values = more stable detection but slower response
DROWSINESS_FRAMES_THRESHOLD = 20

# ==================================================
# CAMERA SETTINGS
# ==================================================

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# ==================================================
# AUDIO ALERT SETTINGS
# ==================================================

# Paths to try for audio alert files (in order of preference)
AUDIO_ALERT_PATHS = [
    r"C:\Users\RAGAVI\Downloads\beep-warning-6387.mp3",  # User-specified path
    "assets/alert.mp3",
    "assets/alert.wav",
    "sounds/beep.mp3",
    "sounds/beep.wav"
]

# Number of times to repeat the audio alert
AUDIO_ALERT_REPEATS = 3

# Cooldown between audio alerts (seconds)
AUDIO_ALERT_COOLDOWN = 5

# ==================================================
# EMAIL NOTIFICATION SETTINGS
# ==================================================

# SMTP Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

# Email credentials (use environment variables for security)
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")  # Use app password for Gmail
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", "")

# Email alert cooldown (seconds) - prevents spam
EMAIL_ALERT_COOLDOWN = 60  # 1 minute

# ==================================================
# DLIB MODEL SETTINGS
# ==================================================

# Path to dlib's facial landmark predictor model
DLIB_PREDICTOR_PATH = "models/shape_predictor_68_face_landmarks.dat"

# URL to download the model if not found locally
DLIB_MODEL_URL = "https://github.com/italojs/facial-landmarks-recognition/raw/master/shape_predictor_68_face_landmarks.dat"

# ==================================================
# WEB INTERFACE SETTINGS
# ==================================================

WEB_HOST = "0.0.0.0"
WEB_PORT = 5000
WEB_DEBUG = False

# ==================================================
# LOGGING AND DEBUGGING
# ==================================================

# Enable debug mode for additional console output
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

# Log detection events to file
LOG_DETECTIONS = True
LOG_FILE = "logs/drowsiness_log.txt"

# ==================================================
# PERFORMANCE SETTINGS
# ==================================================

# Frame skip factor for performance (process every Nth frame)
# 1 = process every frame, 2 = process every other frame, etc.
FRAME_SKIP = 1

# Maximum processing time per frame (seconds) before skipping
MAX_FRAME_PROCESSING_TIME = 0.1

# ==================================================
# VALIDATION AND HELPER FUNCTIONS
# ==================================================

def validate_config():
    """Validate configuration settings"""
    issues = []
    
    if EAR_THRESHOLD <= 0 or EAR_THRESHOLD >= 1:
        issues.append("EAR_THRESHOLD must be between 0 and 1")
    
    if DROWSINESS_FRAMES_THRESHOLD < 1:
        issues.append("DROWSINESS_FRAMES_THRESHOLD must be at least 1")
    
    if not SENDER_EMAIL or not RECEIVER_EMAIL:
        issues.append("Email configuration incomplete - email alerts will be disabled")
    
    return issues

def get_email_config_status():
    """Check if email configuration is complete"""
    return bool(SENDER_EMAIL and SENDER_PASSWORD and RECEIVER_EMAIL)

def get_audio_config_status():
    """Check if any audio file paths exist"""
    for path in AUDIO_ALERT_PATHS:
        if path and os.path.exists(path):
            return True, path
    return False, None

# Validate configuration on import
if __name__ == "__main__":
    issues = validate_config()
    if issues:
        print("Configuration issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("Configuration is valid")
    
    # Display configuration status
    email_status = get_email_config_status()
    audio_status, audio_path = get_audio_config_status()
    
    print(f"\nEmail alerts: {'Enabled' if email_status else 'Disabled'}")
    print(f"Audio alerts: {'Enabled' if audio_status else 'Using fallback'}")
    if audio_status:
        print(f"Audio file: {audio_path}")
