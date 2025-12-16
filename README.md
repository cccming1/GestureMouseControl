# Gesture Mouse Control

A computer-vision–based gesture mouse control system built with Python and MediaPipe.

This project allows users to control the mouse cursor, perform clicks, drag actions,
and scroll using natural hand gestures captured by a camera.  
A clean graphical UI is provided for real-time parameter tuning.


## Features

- Real-time hand tracking using **MediaPipe**
- **Thumb-based cursor tracking** for improved stability
- **Pinch gesture** for click and drag
- **Two-finger gesture** for scrolling
- Intuitive **graphical UI** for parameter adjustment
- Adjustable sensitivity, smoothing, and timing parameters


## Gesture Controls

- **Move Cursor**  
  Move your **thumb tip** to control cursor position

- **Click**  
  Short pinch gesture (thumb + index finger)

- **Drag**  
  Long pinch gesture and move

- **Scroll**  
  Extend index + middle fingers and move vertically


## Requirements

- Python **3.10** (recommended)
- Webcam or built-in camera

### Python Dependencies

The required Python libraries are:

- `opencv-python`
- `mediapipe`
- `pyautogui`
- `numpy`

All dependencies are listed in `requirements.txt`.


## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/gesture-mouse-control.git
cd gesture-mouse-control

2. (Recommended) Create a virtual environment

python3.10 -m venv .venv
source .venv/bin/activate

3. Install dependencies

pip install -r requirements.txt


Run the Program:

Start the graphical control panel:

python ui.py

Then click Start in the UI to activate gesture-based mouse control.
Click Stop at any time to release the camera and mouse.


Project Structure:

.
├── gesture_engine.py        # Core gesture recognition and logic
├── gesture_mouse_control.py # Mouse control implementation
├── ui.py                    # Graphical user interface
├── requirements.txt         # Python dependencies
└── README.md




Notes:
This project is intended for educational and experimental use
On macOS, camera and accessibility permissions may be required
Windows and Linux are supported when running from source


License:
This project is released for learning, experimentation, and personal use.

