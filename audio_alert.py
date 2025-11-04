"""
Audio alert system for drowsiness detection
Handles audio file playback for immediate alerts
"""

import pygame
import os
import threading
import time
import config

class AudioAlert:
    def __init__(self):
        self.initialized = False
        self.current_sound = None
        self.playing = False
        self.initialize_audio()
    
    def initialize_audio(self):
        """Initialize pygame mixer for audio playback"""
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.initialized = True
            print("Audio system initialized successfully")
        except Exception as e:
            print(f"Warning: Could not initialize audio system: {e}")
            self.initialized = False
    
    def load_sound(self, sound_path):
        """Load sound file for playback"""
        try:
            if not self.initialized:
                return None
                
            if os.path.exists(sound_path):
                sound = pygame.mixer.Sound(sound_path)
                print(f"Loaded sound file: {sound_path}")
                return sound
            else:
                print(f"Sound file not found: {sound_path}")
                return None
                
        except Exception as e:
            print(f"Error loading sound file {sound_path}: {e}")
            return None
    
    def generate_beep_sound(self):
        """Generate a default beep sound using pygame"""
        try:
            if not self.initialized:
                return None
            
            # Generate a simple beep tone
            sample_rate = 22050
            duration = 0.5  # seconds
            frequency = 800  # Hz
            
            import numpy as np
            frames = int(duration * sample_rate)
            arr = np.zeros((frames, 2))
            
            for i in range(frames):
                wave = 4096 * np.sin(2 * np.pi * frequency * i / sample_rate)
                # Apply fade in/out to avoid clicks
                fade_frames = int(0.01 * sample_rate)
                if i < fade_frames:
                    wave *= i / fade_frames
                elif i > frames - fade_frames:
                    wave *= (frames - i) / fade_frames
                arr[i] = [wave, wave]
            
            # Convert to the format pygame expects
            arr = arr.astype(np.int16)
            sound = pygame.sndarray.make_sound(arr)
            return sound
            
        except Exception as e:
            print(f"Error generating beep sound: {e}")
            return None
    
    def play_alert(self):
        """Play drowsiness alert sound"""
        if self.playing:
            return  # Avoid overlapping sounds
        
        self.playing = True
        
        try:
            # Try to load custom sound first
            sound = None
            
            # Check for user-specified sound file
            for sound_path in config.AUDIO_ALERT_PATHS:
                if sound_path and os.path.exists(sound_path):
                    sound = self.load_sound(sound_path)
                    if sound:
                        break
            
            # If no custom sound found, try default sound
            if not sound:
                default_sound_path = "assets/default_beep.wav"
                if os.path.exists(default_sound_path):
                    sound = self.load_sound(default_sound_path)
            
            # If still no sound, generate a beep
            if not sound:
                sound = self.generate_beep_sound()
            
            if sound and self.initialized:
                # Play the alert sound multiple times
                for _ in range(config.AUDIO_ALERT_REPEATS):
                    if pygame.mixer.get_init():
                        sound.play()
                        # Wait for sound to finish
                        while pygame.mixer.get_busy():
                            time.sleep(0.1)
                        time.sleep(0.2)  # Brief pause between repeats
                    else:
                        break
            else:
                # Fallback: system beep
                self.system_beep()
                
        except Exception as e:
            print(f"Error playing audio alert: {e}")
            self.system_beep()
        finally:
            self.playing = False
    
    def system_beep(self):
        """Fallback system beep for when audio files aren't available"""
        try:
            import sys
            if sys.platform.startswith('win'):
                import winsound
                for _ in range(3):
                    winsound.Beep(800, 500)
                    time.sleep(0.2)
            elif sys.platform.startswith('darwin'):  # macOS
                for _ in range(3):
                    os.system('say "Alert! Drowsiness detected!"')
            else:  # Linux and others
                for _ in range(3):
                    os.system('echo -e "\a"')
                    time.sleep(0.5)
        except Exception as e:
            print(f"Could not play system beep: {e}")
    
    def test_audio(self):
        """Test audio playback functionality"""
        print("Testing audio alert...")
        self.play_alert()
    
    def stop_audio(self):
        """Stop current audio playback"""
        try:
            if self.initialized and pygame.mixer.get_init():
                pygame.mixer.stop()
            self.playing = False
        except Exception as e:
            print(f"Error stopping audio: {e}")
    
    def cleanup(self):
        """Cleanup audio resources"""
        try:
            self.stop_audio()
            if self.initialized:
                pygame.mixer.quit()
        except Exception as e:
            print(f"Error cleaning up audio: {e}")
