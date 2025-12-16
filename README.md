# Gesture Mouse Control

Gesture Mouse Control is a computer-vision-based mouse control system built with Python, MediaPipe, and Tkinter.  
It allows users to control the mouse cursor, click, drag, and scroll using natural hand gestures captured by a webcam, with a graphical user interface for real-time parameter tuning.

This project focuses on stability, usability, and touchpad-like interaction rather than experimental gesture switching.

---

## Features

- Real-time hand tracking using MediaPipe
- Cursor tracking based on thumb tip for reduced jitter
- Pinch gesture for click and drag
- Two-finger gesture for scrolling (similar to macOS touchpad)
- Graphical UI for live parameter adjustment
- Start / Stop control to safely release camera and mouse
- Designed for experimentation and human–computer interaction learning

---

## Requirements

- Python 3.10
- Webcam
- macOS / Windows / Linux (tested mainly on macOS)

All required Python packages are listed in `requirements.txt`.

---

## Installation and Setup

Clone the repository, create a virtual environment, install dependencies, and run the program as follows:

```bash
git clone https://github.com/cccming1/GestureMouseControl.git
cd GestureMouseControl
python3.10 -m venv .venv
source .venv/bin/activate    # macOS / Linux
pip install -r requirements.txt
python ui.py 
```

After launching the UI:
	•	Adjust parameters such as cursor smoothness and click sensitivity
	•	Click Start to activate gesture-based mouse control
	•	Click Stop at any time to immediately release the camera and mouse

On first run, the system may request camera and accessibility permissions.

---

## Project Structure

GestureMouseControl/
├── gesture_engine.py          # Core gesture recognition logic
├── gesture_mouse_control.py   # Mouse action implementation
├── ui.py                      # Graphical user interface
├── requirements.txt           # Python dependencies
├── README.md                  # Project documentation

---

## Notes
	•	The virtual environment directory (.venv) is intentionally excluded from version control.
	•	Gesture parameters can be tuned live via the UI without restarting the program.
	•	This project is intended for educational use, experimentation, and prototyping gesture-based interfaces.

---

## License

This project is provided for educational and experimental purposes.
