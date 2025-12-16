import cv2
import mediapipe as mp
import pyautogui
import math
import time
import sys
import signal

# =============================
# System settings
# =============================
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0
SCREEN_W, SCREEN_H = pyautogui.size()

CAM_INDEX = 0

# Cursor movement
SMOOTH_ALPHA = 0.35
OFFSET_X = -20
OFFSET_Y = 0

# =============================
# Intent-gating parameters
# =============================
# Pinch hysteresis
PINCH_ON = 0.045
PINCH_OFF = 0.055

# "Arming" requires stable frames
ARM_FRAMES = 4

# Pinch click/drag split
CLICK_TIME = 0.4
DRAG_MOVE_PX = 15

# Two-finger scroll/zoom
SCROLL_SCALE = 450
SCROLL_DEADZONE = 0.004
ZOOM_GAP_STEP = 0.015
ZOOM_COOLDOWN = 0.18

# Critical fix: ignore middle/two-finger for a moment after leaving TWO
MIDDLE_IGNORE_TIME = 0.28  # seconds (0.2~0.35 feels good)

# Preview
SHOW_PREVIEW = True
FLIP = True  # mirror like selfie

# =============================
# Helpers
# =============================
def dist(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def finger_extended_y(lm, tip, pip, mcp):
    # Simple "extended" test: tip above pip above mcp (y smaller = higher)
    return (lm[tip].y < lm[pip].y) and (lm[pip].y < lm[mcp].y)

def two_finger_pose(lm):
    # Index and middle both extended
    idx_ok = finger_extended_y(lm, 8, 6, 5)
    mid_ok = finger_extended_y(lm, 12, 10, 9)
    return idx_ok and mid_ok

# =============================
# MediaPipe
# =============================
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

cap = cv2.VideoCapture(CAM_INDEX)
if not cap.isOpened():
    print("❌ Camera error")
    sys.exit(1)

# =============================
# State
# =============================
armed = "NONE"  # NONE / PINCH / TWO

pinch_arm_cnt = 0
two_arm_cnt = 0

pinch_start_time = None
pinch_start_xy = None
dragging = False

prev_two_y = None
prev_two_gap = None
zoom_cd_until = 0.0

smooth_x = None
smooth_y = None

# after leaving TWO, ignore middle / two-finger detection until this time
ignore_middle_until = 0.0

# =============================
# Exit handling
# =============================
running = True
def handle_exit(sig, frame):
    global running
    running = False
signal.signal(signal.SIGINT, handle_exit)

print("✅ Gesture input system ready (Intent-Gated v2)")

# =============================
# Main loop
# =============================
while running:
    ok, frame = cap.read()
    if not ok:
        break

    if FLIP:
        frame = cv2.flip(frame, 1)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = hands.process(rgb)

    now = time.time()

    if res.multi_hand_landmarks:
        lm = res.multi_hand_landmarks[0].landmark

        thumb = lm[4]
        index = lm[8]
        middle = lm[12]

        # Always compute pinch distance (pinch is based on thumb-index)
        pinch_d = dist(thumb, index)

        # Two-finger pose is "masked" for a short time after leaving TWO
        if now < ignore_middle_until:
            two_pose = False
        else:
            two_pose = two_finger_pose(lm)

        # -----------------------------
        # Cursor movement (always allowed)
        # -----------------------------
        x = clamp(thumb.x, 0, 1)
        y = clamp(thumb.y, 0, 1)

        if smooth_x is None:
            smooth_x, smooth_y = x, y
        else:
            smooth_x = smooth_x * (1 - SMOOTH_ALPHA) + x * SMOOTH_ALPHA
            smooth_y = smooth_y * (1 - SMOOTH_ALPHA) + y * SMOOTH_ALPHA

        pyautogui.moveTo(
            smooth_x * SCREEN_W + OFFSET_X,
            smooth_y * SCREEN_H + OFFSET_Y
        )

        # =============================
        # ARM STAGE (only when NONE)
        # =============================
        if armed == "NONE":
            # PINCH arm: thumb-index pinch stable frames
            if pinch_d < PINCH_ON:
                pinch_arm_cnt += 1
            else:
                pinch_arm_cnt = 0

            # TWO arm: needs explicit two-finger pose stable frames
            if two_pose:
                two_arm_cnt += 1
            else:
                two_arm_cnt = 0

            if pinch_arm_cnt >= ARM_FRAMES:
                armed = "PINCH"
                pinch_arm_cnt = 0
                two_arm_cnt = 0

                pinch_start_time = now
                pinch_start_xy = pyautogui.position()
                dragging = False

            elif two_arm_cnt >= ARM_FRAMES:
                armed = "TWO"
                pinch_arm_cnt = 0
                two_arm_cnt = 0

                prev_two_y = None
                prev_two_gap = None

        # =============================
        # PINCH MODE (left click world)
        # =============================
        elif armed == "PINCH":
            # In PINCH mode, we intentionally ignore two_pose completely.
            # (Even if the middle finger moves, it cannot steal control.)
            cur_x, cur_y = pyautogui.position()
            moved = math.hypot(
                cur_x - pinch_start_xy[0],
                cur_y - pinch_start_xy[1]
            )

            # Decide drag
            if (not dragging) and (moved > DRAG_MOVE_PX or (now - pinch_start_time) > CLICK_TIME):
                pyautogui.mouseDown()
                dragging = True

            # Release pinch
            if pinch_d > PINCH_OFF:
                if dragging:
                    pyautogui.mouseUp()
                else:
                    pyautogui.click()

                # Disarm to NONE (require re-arm for any action)
                armed = "NONE"
                pinch_start_time = None
                pinch_start_xy = None
                dragging = False

                # small safety: avoid accidental instant TWO after pinch release
                ignore_middle_until = max(ignore_middle_until, now + 0.10)

        # =============================
        # TWO MODE (scroll / zoom)
        # =============================
        elif armed == "TWO":
            # TWO mode should only work while the explicit pose holds.
            # If the pose breaks, we disarm and start middle-ignore cooldown.
            if not two_pose:
                armed = "NONE"
                prev_two_y = None
                prev_two_gap = None

                # KEY FIX: after leaving TWO, ignore middle briefly
                ignore_middle_until = now + MIDDLE_IGNORE_TIME

            else:
                # Scroll (two fingers up/down)
                avg_y = (index.y + middle.y) / 2.0
                if prev_two_y is not None:
                    dy = avg_y - prev_two_y
                    if abs(dy) > SCROLL_DEADZONE:
                        pyautogui.scroll(int(-dy * SCROLL_SCALE))
                prev_two_y = avg_y


        # =============================
        # Preview
        # =============================
        if SHOW_PREVIEW:
            mp_draw.draw_landmarks(frame, res.multi_hand_landmarks[0], mp_hands.HAND_CONNECTIONS)

            info1 = f"MODE: {armed} | pinch_d={pinch_d:.3f} | two_pose={two_pose}"
            info2 = f"ignore_middle={(ignore_middle_until-now):.2f}s" if now < ignore_middle_until else "ignore_middle=0.00s"
            cv2.putText(frame, info1, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
            cv2.putText(frame, info2, (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
            cv2.putText(frame, "NONE: no action | PINCH: click/drag | TWO: scroll/zoom | q to quit",
                        (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0,255,0), 2)

    if SHOW_PREVIEW:
        cv2.imshow("Gesture Input System (Intent-Gated v2)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# =============================
# Cleanup
# =============================
try:
    pyautogui.mouseUp()
except Exception:
    pass

cap.release()
cv2.destroyAllWindows()
hands.close()
print("🛑 Exit")