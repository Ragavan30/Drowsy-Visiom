"""
Web interface for the Drowsiness Detection System
Provides real-time monitoring and configuration
"""

from flask import Flask, render_template, jsonify, request, Response
import json
import threading
import time
import cv2
import base64
from drowsiness_detector import DrowsinessDetector
from email_notifier import EmailNotifier
from audio_alert import AudioAlert
import config
import utils

app = Flask(__name__)

# Global detector instance
detector = None
detector_thread = None

def get_detector():
    """Get or create detector instance"""
    global detector
    if detector is None:
        detector = DrowsinessDetector()
    return detector

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get current detection status"""
    det = get_detector()
    
    # Get detection statistics
    stats = det.get_statistics()
    
    # Check system status
    email_status = config.get_email_config_status()
    audio_status, audio_path = config.get_audio_config_status()
    
    return jsonify({
        'running': det.running,
        'current_status': stats.get('current_status', 'Unknown'),
        'session_time': int(stats.get('session_time', 0)),
        'total_frames': stats.get('total_frames', 0),
        'drowsy_detections': stats.get('drowsy_detections', 0),
        'fps': round(stats.get('fps', 0), 1),
        'email_configured': email_status,
        'audio_configured': audio_status,
        'audio_file': audio_path if audio_status else None,
        'ear_threshold': config.EAR_THRESHOLD,
        'frames_threshold': config.DROWSINESS_FRAMES_THRESHOLD
    })

@app.route('/api/start', methods=['POST'])
def start_detection():
    """Start drowsiness detection"""
    global detector_thread
    
    try:
        det = get_detector()
        
        if not det.running:
            detector_thread = threading.Thread(target=det.start_detection, daemon=True)
            detector_thread.start()
            return jsonify({'success': True, 'message': 'Detection started'})
        else:
            return jsonify({'success': False, 'message': 'Detection already running'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error starting detection: {e}'})

@app.route('/api/stop', methods=['POST'])
def stop_detection():
    """Stop drowsiness detection"""
    try:
        det = get_detector()
        det.stop_detection()
        return jsonify({'success': True, 'message': 'Detection stopped'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error stopping detection: {e}'})

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    return jsonify({
        'ear_threshold': config.EAR_THRESHOLD,
        'frames_threshold': config.DROWSINESS_FRAMES_THRESHOLD,
        'audio_alert_cooldown': config.AUDIO_ALERT_COOLDOWN,
        'email_alert_cooldown': config.EMAIL_ALERT_COOLDOWN,
        'camera_width': config.CAMERA_WIDTH,
        'camera_height': config.CAMERA_HEIGHT,
        'sender_email': config.SENDER_EMAIL,
        'receiver_email': config.RECEIVER_EMAIL,
        'smtp_server': config.SMTP_SERVER,
        'smtp_port': config.SMTP_PORT
    })

@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration settings"""
    try:
        data = request.get_json()
        
        # Update configuration values
        if 'ear_threshold' in data:
            config.EAR_THRESHOLD = float(data['ear_threshold'])
        if 'frames_threshold' in data:
            config.DROWSINESS_FRAMES_THRESHOLD = int(data['frames_threshold'])
        if 'audio_alert_cooldown' in data:
            config.AUDIO_ALERT_COOLDOWN = int(data['audio_alert_cooldown'])
        if 'email_alert_cooldown' in data:
            config.EMAIL_ALERT_COOLDOWN = int(data['email_alert_cooldown'])
        
        return jsonify({'success': True, 'message': 'Configuration updated'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating configuration: {e}'})

@app.route('/api/test-email', methods=['POST'])
def test_email():
    """Test email configuration"""
    try:
        email_notifier = EmailNotifier()
        success, message = email_notifier.send_test_email()
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error testing email: {e}'})

@app.route('/api/test-audio', methods=['POST'])
def test_audio():
    """Test audio alert"""
    try:
        audio_alert = AudioAlert()
        threading.Thread(target=audio_alert.test_audio, daemon=True).start()
        return jsonify({'success': True, 'message': 'Audio test triggered'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error testing audio: {e}'})

@app.route('/api/screenshot', methods=['POST'])
def take_screenshot():
    """Take a screenshot"""
    try:
        det = get_detector()
        if det.cap and det.cap.isOpened():
            ret, frame = det.cap.read()
            if ret:
                screenshot_path = f"screenshots/manual_screenshot_{int(time.time())}.jpg"
                utils.ensure_directory("screenshots")
                cv2.imwrite(screenshot_path, frame)
                return jsonify({'success': True, 'message': f'Screenshot saved: {screenshot_path}'})
            else:
                return jsonify({'success': False, 'message': 'Could not capture frame'})
        else:
            return jsonify({'success': False, 'message': 'Camera not available'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error taking screenshot: {e}'})

def generate_frames():
    """Generate frames for video streaming"""
    det = get_detector()
    
    while True:
        try:
            if det.cap and det.cap.isOpened():
                ret, frame = det.cap.read()
                if ret:
                    # Process frame for detection
                    processed_frame = det.process_frame(frame.copy())
                    
                    # Encode frame as JPEG
                    _, buffer = cv2.imencode('.jpg', processed_frame)
                    frame_bytes = buffer.tobytes()
                    
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                else:
                    time.sleep(0.1)
            else:
                time.sleep(0.1)
        except Exception as e:
            print(f"Error in frame generation: {e}")
            time.sleep(1)

@app.route('/api/video-feed')
def video_feed():
    """Video streaming endpoint"""
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/system-info')
def get_system_info():
    """Get system information"""
    try:
        import platform
        import psutil
        
        # Get system info
        system_info = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total // (1024**3),  # GB
            'memory_available': psutil.virtual_memory().available // (1024**3),  # GB
        }
        
        # Get OpenCV info
        opencv_info = {
            'version': cv2.__version__,
            'build_info': cv2.getBuildInformation()
        }
        
        return jsonify({
            'success': True,
            'system': system_info,
            'opencv': opencv_info
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting system info: {e}'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
