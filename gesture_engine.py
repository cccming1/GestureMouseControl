import cv2
import mediapipe as mp
import pyautogui
import math
import time


pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def dist(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def finger_extended_y(lm, tip, pip, mcp):
    return (lm[tip].y < lm[pip].y) and (lm[pip].y < lm[mcp].y)


def two_finger_pose(lm):
    idx_ok = finger_extended_y(lm, 8, 6, 5)
    mid_ok = finger_extended_y(lm, 12, 10, 9)
    return idx_ok and mid_ok


def run_gesture(stop_event, params, show_preview=False):
    """
    ✅ macOS 稳定版：默认不在子线程里开 OpenCV 预览窗口（imshow 会崩）
    show_preview=True 仅用于你将来改成主线程显示时
    """

    # ---------- map user params -> engine params ----------
    SMOOTH_ALPHA = float(params.get("smooth", 0.35))

    click_sens = float(params.get("click_sens", 0.6))
    # click_sens 越大 => 更容易判定 pinch
    PINCH_ON = 0.030 + (click_sens - 0.3) * (0.050 - 0.030) / (1.0 - 0.3)
    PINCH_ON = clamp(PINCH_ON, 0.028, 0.060)
    PINCH_OFF = PINCH_ON + 0.020

    CLICK_TIME = float(params.get("drag_delay_ms", 160)) / 1000.0

    ARM_FRAMES = int(round(6 - (click_sens - 0.3) * (6 - 3) / (1.0 - 0.3)))
    ARM_FRAMES = max(2, min(8, ARM_FRAMES))

    DRAG_MOVE_PX = 15

    SCROLL_SCALE = int(params.get("scroll_speed", 500))
    SCROLL_DEADZONE = 0.004

    MIDDLE_IGNORE_TIME = 0.28
    OFFSET_X = -20
    OFFSET_Y = 0
    FLIP = True

    screen_w, screen_h = pyautogui.size()

    # ---------- MediaPipe ----------
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6,
    )

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot open camera.")
        hands.close()
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_BRIGHTNESS, 150)  # 增加亮度

    print("📷 Warming up camera...")
    for _ in range(10):
        cap.read()
    print("✅ Camera ready")

    # ---------- state ----------
    armed = "NONE"  # NONE / PINCH / TWO
    pinch_arm_cnt = 0
    two_arm_cnt = 0

    pinch_start_time = None
    pinch_start_xy = None
    dragging = False

    prev_two_y = None
    smooth_x = None
    smooth_y = None

    ignore_middle_until = 0.0

    # FPS heartbeat（确认摄像头在跑）
    frame_cnt = 0
    t0 = time.time()

    print("✅ Gesture engine running (preview OFF for stability).")

    try:
        while not stop_event.is_set():
            ok, frame = cap.read()
            if not ok:
                break

            if FLIP:
                frame = cv2.flip(frame, 1)

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = hands.process(rgb)
            now = time.time()

            # heartbeat
            frame_cnt += 1
            if now - t0 >= 1.0:
                # 你想安静就把这行注释掉
                # print(f"FPS: {frame_cnt}")
                frame_cnt = 0
                t0 = now

            if res.multi_hand_landmarks:
                lm = res.multi_hand_landmarks[0].landmark
                thumb = lm[4]
                index = lm[8]
                middle = lm[12]

                pinch_d = dist(thumb, index)

                # TWO pose masked right after leaving TWO
                if now < ignore_middle_until:
                    two_pose = False
                else:
                    two_pose = two_finger_pose(lm)

                # Cursor follows thumb tip
                x = clamp(thumb.x, 0, 1)
                y = clamp(thumb.y, 0, 1)

                if smooth_x is None:
                    smooth_x, smooth_y = x, y
                else:
                    a = clamp(SMOOTH_ALPHA, 0.05, 0.95)
                    smooth_x = smooth_x * (1 - a) + x * a
                    smooth_y = smooth_y * (1 - a) + y * a

                pyautogui.moveTo(
                    smooth_x * screen_w + OFFSET_X,
                    smooth_y * screen_h + OFFSET_Y,
                    duration=0
                )

                # =========== ARM stage ===========
                if armed == "NONE":
                    pinch_arm_cnt = pinch_arm_cnt + 1 if pinch_d < PINCH_ON else 0
                    two_arm_cnt = two_arm_cnt + 1 if two_pose else 0

                    if pinch_arm_cnt >= ARM_FRAMES:
                        armed = "PINCH"
                        pinch_arm_cnt = two_arm_cnt = 0
                        pinch_start_time = now
                        pinch_start_xy = pyautogui.position()
                        dragging = False

                    elif two_arm_cnt >= ARM_FRAMES:
                        armed = "TWO"
                        pinch_arm_cnt = two_arm_cnt = 0
                        prev_two_y = None

                # =========== PINCH ===========
                elif armed == "PINCH":
                    cur_x, cur_y = pyautogui.position()
                    moved = math.hypot(cur_x - pinch_start_xy[0], cur_y - pinch_start_xy[1])

                    if (not dragging) and (moved > DRAG_MOVE_PX or (now - pinch_start_time) > CLICK_TIME):
                        pyautogui.mouseDown()
                        dragging = True

                    if pinch_d > PINCH_OFF:
                        if dragging:
                            pyautogui.mouseUp()
                        else:
                            pyautogui.click()

                        armed = "NONE"
                        pinch_start_time = None
                        pinch_start_xy = None
                        dragging = False
                        ignore_middle_until = max(ignore_middle_until, now + 0.10)

                # =========== TWO (scroll only) ===========
                elif armed == "TWO":
                    if not two_pose:
                        armed = "NONE"
                        prev_two_y = None
                        ignore_middle_until = now + MIDDLE_IGNORE_TIME
                    else:
                        avg_y = (index.y + middle.y) / 2.0
                        if prev_two_y is not None:
                            dy = avg_y - prev_two_y
                            if abs(dy) > SCROLL_DEADZONE:
                                pyautogui.scroll(int(-dy * SCROLL_SCALE))
                        prev_two_y = avg_y

            # ❌ 不在子线程里 imshow / waitKey（macOS 会崩）
            if show_preview:
                # 预留：后面我们做“主线程预览”时再用
                pass

    finally:
        try:
            pyautogui.mouseUp()
        except Exception:
            pass
        cap.release()
        hands.close()
        print("🛑 Gesture engine stopped.")