import cv2
import mediapipe as mp
import pyautogui
import os
import time
import numpy as np
from tkinter import Tk
from tkinter.filedialog import askopenfilename

# Configure PyAutoGUI
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.1

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

# Constants for gesture detection
GESTURE_TIMEOUT = 1.0
PINCH_THRESHOLD = 0.06
VERTICAL_THRESHOLD = 0.04      
VERTICAL_THRESHOLD_OUT = 0.06  
END_GESTURE_HOLD_TIME = 1.0    

def start_slideshow(file_path):
    """Open PowerPoint and start slideshow immediately in full screen."""
    try:
        os.startfile(file_path)
        print("Opening PowerPoint file...")
        time.sleep(3)  # Wait for PowerPoint to open
        pyautogui.press('f5')  # Start from beginning
        print("Starting slideshow in full screen")
        time.sleep(1)
        return True
    except Exception as e:
        print(f"Error starting presentation: {e}")
        return False

def next_slide():
    pyautogui.press("right")
    print("Next slide")

def previous_slide():
    pyautogui.press("left")
    print("Previous slide")

def zoom_in():
    try:
        pyautogui.hotkey('ctrl', '+')
        print("Zoom in")
    except Exception as e:
        print(f"Zoom in failed: {e}")

def zoom_out():
    try:
        pyautogui.hotkey('ctrl', '-')
        print("Zoom out")
    except Exception as e:
        print(f"Zoom out failed: {e}")

def end_slideshow():
    pyautogui.press("esc")
    print("End slideshow")

def main(file_path=None):
    """Main function that runs the gesture control system."""
    if not file_path:
        print("No file path provided. Exiting...")
        return

    print(f"Opening file: {file_path}")
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera")
        return

    # Start PowerPoint in full-screen slideshow mode
    if not start_slideshow(file_path):
        cap.release()
        return

    last_gesture_time = 0
    last_y_position = None
    is_pinching = False
    end_gesture_start_time = None

    with mp_hands.Hands(
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
        max_num_hands=1
    ) as hands:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)

            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Get finger landmarks
                thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
                ring_tip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP]
                pinky_tip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]
                
                # Get finger base positions
                index_base = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP]
                middle_base = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
                ring_base = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_MCP]

                current_time = time.time()

                # Calculate pinch distance
                pinch_distance = np.sqrt(
                    (thumb_tip.x - index_tip.x)**2 + 
                    (thumb_tip.y - index_tip.y)**2
                )

                # Handle slide navigation
                if current_time - last_gesture_time > GESTURE_TIMEOUT:
                    if index_tip.x < 0.3 and not is_pinching:
                        previous_slide()
                        last_gesture_time = current_time
                        cv2.putText(frame, "Previous Slide", (10, 30), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    elif index_tip.x > 0.7 and not is_pinching:
                        next_slide()
                        last_gesture_time = current_time
                        cv2.putText(frame, "Next Slide", (10, 30), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                # Handle zoom gestures
                if pinch_distance < PINCH_THRESHOLD:
                    if not is_pinching:
                        is_pinching = True
                        last_y_position = index_tip.y
                    else:
                        if last_y_position is not None:
                            y_movement = index_tip.y - last_y_position
                            if y_movement < -VERTICAL_THRESHOLD:
                                zoom_in()
                                cv2.putText(frame, "Zoom In", (10, 60), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                                last_y_position = index_tip.y
                            elif y_movement > VERTICAL_THRESHOLD_OUT:
                                zoom_out()
                                cv2.putText(frame, "Zoom Out", (10, 60), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                                last_y_position = index_tip.y
                else:
                    is_pinching = False
                    last_y_position = None

                # Detect three fingers up gesture
                three_fingers_up = (
                    index_tip.y < index_base.y - 0.1 and
                    middle_tip.y < middle_base.y - 0.1 and
                    ring_tip.y < ring_base.y - 0.1 and
                    thumb_tip.y > index_base.y and
                    pinky_tip.y > ring_base.y
                )

                # Handle end slideshow gesture
                if three_fingers_up:
                    if end_gesture_start_time is None:
                        end_gesture_start_time = current_time
                    elif current_time - end_gesture_start_time > END_GESTURE_HOLD_TIME:
                        cv2.putText(frame, "Ending Slideshow...", (10, 90), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                        time.sleep(0.5)
                        end_slideshow()
                        break
                else:
                    if end_gesture_start_time is not None:
                        print("Gesture cancelled")
                    end_gesture_start_time = None

                # Show end gesture progress
                if end_gesture_start_time is not None:
                    hold_progress = min(1.0, (current_time - end_gesture_start_time) / END_GESTURE_HOLD_TIME)
                    progress_text = f"Hold three fingers: {int(hold_progress * 100)}%"
                    color = (0, 255, 0) if hold_progress < 0.7 else (0, 0, 255)
                    cv2.putText(frame, progress_text, (10, 90),
                              cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

            # Display the frame
            cv2.imshow("Gesture Control", frame)
            
            if cv2.waitKey(5) & 0xFF == 27:  # Press ESC to exit
                break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()