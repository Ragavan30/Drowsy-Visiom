#!/usr/bin/env python3
"""
Main entry point for the Drowsiness Detection System
Handles command-line execution and web interface launching
"""

import threading
import argparse
import sys
import os
from drowsiness_detector import DrowsinessDetector
from web_interface import app
import config

def run_detection_only():
    """Run drowsiness detection in command-line mode"""
    print("Starting Drowsiness Detection System...")
    print("Press 'q' to quit, 's' to take screenshot")
    
    detector = DrowsinessDetector()
    
    try:
        detector.start_detection()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        detector.cleanup()

def run_web_interface():
    """Run the web interface"""
    print("Starting Drowsiness Detection Web Interface...")
    print(f"Access the interface at: http://localhost:5000")
    
    # Start detection in a separate thread
    detector = DrowsinessDetector()
    detection_thread = threading.Thread(target=detector.start_detection, daemon=True)
    detection_thread.start()
    
    # Start web server
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error starting web interface: {e}")
    finally:
        detector.cleanup()

def main():
    parser = argparse.ArgumentParser(description='Drowsiness Detection System')
    parser.add_argument('--mode', choices=['cli', 'web'], default='web',
                       help='Run in CLI mode or web interface mode (default: web)')
    parser.add_argument('--config', help='Path to configuration file')
    
    args = parser.parse_args()
    
    # Load custom config if provided
    if args.config and os.path.exists(args.config):
        print(f"Loading configuration from: {args.config}")
        # Load custom configuration logic here
    
    if args.mode == 'cli':
        run_detection_only()
    else:
        run_web_interface()

if __name__ == "__main__":
    main()
