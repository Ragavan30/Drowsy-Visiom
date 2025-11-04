"""
Core Drowsiness Detection System using OpenCV and dlib
Implements real-time eye aspect ratio (EAR) calculation for drowsiness detection
"""

import cv2
import dlib
import numpy as np
import time
import threading
from scipy.spatial import distance as dist
from email_notifier import EmailNotifier
from audio_alert import AudioAlert
import config
import utils

class DrowsinessDetector:
    def __init__(self):
        self.cap = None
        self.detector = None
        self.predictor = None
        self.email_notifier = EmailNotifier()
        self.audio_alert = AudioAlert()
        
        # Detection state variables
        self.is_drowsy = False
        self.eye_closed_frames = 0
        self.last_alert_time = 0
        self.last_email_time = 0
        self.running = False
        
        # Statistics
        self.total_frames = 0
        self.drowsy_detections = 0
        self.session_start_time = time.time()
        
        # Initialize detection models
        self.initialize_models()
        
    def initialize_models(self):
        """Initialize dlib face detector and predictor"""
        try:
            print("Initializing face detection models...")
            self.detector = dlib.get_frontal_face_detector()
            
            # Try to load the predictor model
            predictor_path = config.DLIB_PREDICTOR_PATH
            if not predictor_path or not utils.download_dlib_model():
                raise Exception("Could not load dlib predictor model")
                
            self.predictor = dlib.shape_predictor(predictor_path)
            print("Models initialized successfully")
            
        except Exception as e:
            print(f"Error initializing models: {e}")
            raise
    
    def initialize_camera(self):
        """Initialize webcam"""
        try:
            print("Initializing camera...")
            self.cap = cv2.VideoCapture(0)
            
            if not self.cap.isOpened():
                # Try alternative camera indices
                for i in range(1, 4):
                    self.cap = cv2.VideoCapture(i)
                    if self.cap.isOpened():
                        break
                else:
                    raise Exception("Could not access webcam")
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)
            
            print("Camera initialized successfully")
            return True
            
        except Exception as e:
            print(f"Error initializing camera: {e}")
            return False
    
    def calculate_ear(self, eye_landmarks):
        """Calculate Eye Aspect Ratio (EAR) for given eye landmarks"""
        # Compute distances between eye landmarks
        A = dist.euclidean(eye_landmarks[1], eye_landmarks[5])
        B = dist.euclidean(eye_landmarks[2], eye_landmarks[4])
        C = dist.euclidean(eye_landmarks[0], eye_landmarks[3])
        
        # Calculate EAR
        ear = (A + B) / (2.0 * C)
        return ear
    
    def extract_eye_landmarks(self, landmarks):
        """Extract left and right eye landmarks from facial landmarks"""
        # dlib's 68-point facial landmark indices for eyes
        left_eye_indices = list(range(36, 42))
        right_eye_indices = list(range(42, 48))
        
        left_eye = []
        right_eye = []
        
        for i in left_eye_indices:
            left_eye.append([landmarks.part(i).x, landmarks.part(i).y])
            
        for i in right_eye_indices:
            right_eye.append([landmarks.part(i).x, landmarks.part(i).y])
        
        return np.array(left_eye), np.array(right_eye)
    
    def draw_eye_landmarks(self, frame, eye_landmarks):
        """Draw eye landmarks on the frame"""
        for (x, y) in eye_landmarks:
            cv2.circle(frame, (int(x), int(y)), 2, (0, 255, 0), -1)
    
    def process_frame(self, frame):
        """Process a single frame for drowsiness detection"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detector(gray)
        
        current_ear = 0
        face_detected = False
        
        for face in faces:
            face_detected = True
            landmarks = self.predictor(gray, face)
            
            # Extract eye landmarks
            left_eye, right_eye = self.extract_eye_landmarks(landmarks)
            
            # Calculate EAR for both eyes
            left_ear = self.calculate_ear(left_eye)
            right_ear = self.calculate_ear(right_eye)
            current_ear = (left_ear + right_ear) / 2.0
            
            # Draw face rectangle
            x, y, w, h = face.left(), face.top(), face.width(), face.height()
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            
            # Draw eye landmarks
            self.draw_eye_landmarks(frame, left_eye)
            self.draw_eye_landmarks(frame, right_eye)
            
            # Check for drowsiness
            if current_ear < config.EAR_THRESHOLD:
                self.eye_closed_frames += 1
                
                if self.eye_closed_frames >= config.DROWSINESS_FRAMES_THRESHOLD:
                    if not self.is_drowsy:
                        self.is_drowsy = True
                        self.drowsy_detections += 1
                        self.handle_drowsiness_detection(frame)
                    
                    # Draw drowsiness alert
                    cv2.putText(frame, "DROWSINESS DETECTED!", (10, 30),
                              cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                else:
                    cv2.putText(frame, f"Eyes closed: {self.eye_closed_frames}", (10, 60),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            else:
                self.eye_closed_frames = 0
                self.is_drowsy = False
        
        # Display information on frame
        if face_detected:
            cv2.putText(frame, f"EAR: {current_ear:.3f}", (10, frame.shape[0] - 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, f"Threshold: {config.EAR_THRESHOLD:.3f}", (10, frame.shape[0] - 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        else:
            cv2.putText(frame, "No face detected", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        
        # Display session statistics
        session_time = int(time.time() - self.session_start_time)
        cv2.putText(frame, f"Session: {session_time}s | Detections: {self.drowsy_detections}", 
                   (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def handle_drowsiness_detection(self, frame):
        """Handle drowsiness detection - play alert and send email"""
        current_time = time.time()
        
        # Play audio alert (with cooldown)
        if current_time - self.last_alert_time > config.AUDIO_ALERT_COOLDOWN:
            threading.Thread(target=self.audio_alert.play_alert, daemon=True).start()
            self.last_alert_time = current_time
        
        # Send email notification (with cooldown)
        if current_time - self.last_email_time > config.EMAIL_ALERT_COOLDOWN:
            snapshot_path = f"snapshots/drowsy_{int(current_time)}.jpg"
            utils.ensure_directory("snapshots")
            cv2.imwrite(snapshot_path, frame)
            
            threading.Thread(
                target=self.email_notifier.send_alert,
                args=(snapshot_path, current_time),
                daemon=True
            ).start()
            self.last_email_time = current_time
    
    def start_detection(self):
        """Start the drowsiness detection process"""
        if not self.initialize_camera():
            return False
        
        self.running = True
        print("Drowsiness detection started. Press 'q' to quit.")
        
        try:
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    print("Error reading from camera")
                    break
                
                self.total_frames += 1
                
                # Process frame for drowsiness detection
                processed_frame = self.process_frame(frame)
                
                # Display the frame
                cv2.imshow('Drowsiness Detection System', processed_frame)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    # Save screenshot
                    screenshot_path = f"screenshots/screenshot_{int(time.time())}.jpg"
                    utils.ensure_directory("screenshots")
                    cv2.imwrite(screenshot_path, processed_frame)
                    print(f"Screenshot saved: {screenshot_path}")
                
        except Exception as e:
            print(f"Error during detection: {e}")
        finally:
            self.cleanup()
    
    def stop_detection(self):
        """Stop the detection process"""
        self.running = False
    
    def cleanup(self):
        """Clean up resources"""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("Cleanup completed")
    
    def get_statistics(self):
        """Get current detection statistics"""
        session_time = time.time() - self.session_start_time
        return {
            'session_time': session_time,
            'total_frames': self.total_frames,
            'drowsy_detections': self.drowsy_detections,
            'current_status': 'Drowsy' if self.is_drowsy else 'Alert',
            'fps': self.total_frames / max(session_time, 1)
        }
