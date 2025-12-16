import tkinter as tk
import threading
from threading import Event

from gesture_engine import run_gesture

gesture_thread = None
stop_event = Event()

# ===== Colors =====
BG = "#0b1220"
PANEL = "#101a2f"
TEXT = "#f4f6fb"
MUTED = "#BAB8B8"
ACCENT = "#4da3ff"
GOOD = "#2bd576"
TRACK = "#2a3552"
LOWHIGH = "#1c2540"
BORDER = "#1b2a4a"
BTN_START_BG = "#1f6feb"    # 深蓝（GitHub 风格）
BTN_STOP_BG  = "#c93c3c"    # 深红
BTN_DISABLED_BG = "#1b2338" # 深灰（禁用态）
BTN_TEXT = "#51a51d"


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def band_name(v, rec_low, rec_high):
    if v < rec_low:
        return "Low"
    if v > rec_high:
        return "High"
    return "Recommended"


class SmartSlider(tk.Canvas):
    """
    A single-track slider drawn on Canvas:
    - Low zone / Recommended zone / High zone in one track
    - Draggable knob
    - Calls on_change(value) when updated
    """
    def __init__(self, parent, *,
                 min_v, max_v, value,
                 rec_low, rec_high,
                 height=28, on_change=None,
                 fmt=None,
                 **kw):
        super().__init__(parent, height=height, bg=PANEL, highlightthickness=0, **kw)
        self.min_v = float(min_v)
        self.max_v = float(max_v)
        self.rec_low = float(rec_low)
        self.rec_high = float(rec_high)
        self.value = float(value)
        self.on_change = on_change
        self.fmt = fmt or (lambda x: f"{x:.2f}")

        self.pad = 10
        self.track_h = 10
        self.knob_r = 7

        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<Button-1>", self._on_mouse)
        self.bind("<B1-Motion>", self._on_mouse)

    def set_value(self, v, notify=True):
        self.value = clamp(float(v), self.min_v, self.max_v)
        self.redraw()
        if notify and self.on_change:
            self.on_change(self.value)

    def _x_to_value(self, x):
        w = self.winfo_width()
        x0 = self.pad
        x1 = max(self.pad + 1, w - self.pad)
        t = (x - x0) / (x1 - x0)
        t = clamp(t, 0.0, 1.0)
        return self.min_v + t * (self.max_v - self.min_v)

    def _value_to_x(self, v):
        w = self.winfo_width()
        x0 = self.pad
        x1 = max(self.pad + 1, w - self.pad)
        t = (v - self.min_v) / (self.max_v - self.min_v)
        t = clamp(t, 0.0, 1.0)
        return int(x0 + t * (x1 - x0))

    def _on_mouse(self, e):
        self.set_value(self._x_to_value(e.x), notify=True)

    def redraw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 30:
            return

        y = h // 2
        x0 = self.pad
        x1 = w - self.pad

        # map rec range
        rx1 = self._value_to_x(self.rec_low)
        rx2 = self._value_to_x(self.rec_high)

        # base track
        self.create_round_rect(x0, y - self.track_h//2, x1, y + self.track_h//2, r=6, fill=TRACK, outline="")

        # low zone
        self.create_round_rect(x0, y - self.track_h//2, rx1, y + self.track_h//2, r=6, fill=LOWHIGH, outline="")
        # recommended zone
        self.create_round_rect(rx1, y - self.track_h//2, rx2, y + self.track_h//2, r=6, fill=GOOD, outline="")
        # high zone
        self.create_round_rect(rx2, y - self.track_h//2, x1, y + self.track_h//2, r=6, fill=LOWHIGH, outline="")

        # border
        self.create_round_rect(x0, y - self.track_h//2, x1, y + self.track_h//2, r=6, fill="", outline="#2f3f6a", width=1)

        # knob
        kx = self._value_to_x(self.value)
        self.create_oval(kx - self.knob_r, y - self.knob_r, kx + self.knob_r, y + self.knob_r,
                         fill=ACCENT, outline="")

        # tiny tick marks at ends (optional)
        self.create_line(x0, y + 10, x0, y + 16, fill="#2f3f6a")
        self.create_line(x1, y + 10, x1, y + 16, fill="#2f3f6a")

    # helper: rounded rectangle for canvas
    def create_round_rect(self, x1, y1, x2, y2, r=8, **kwargs):
        r = min(r, abs(x2-x1)//2, abs(y2-y1)//2)
        points = [
            x1+r, y1, x2-r, y1,
            x2, y1, x2, y1+r,
            x2, y2-r, x2, y2,
            x2-r, y2, x1+r, y2,
            x1, y2, x1, y2-r,
            x1, y1+r, x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)


def make_block(root, title, desc, unit,
               min_v, max_v, init_v,
               rec_low, rec_high, rec_text,
               fmt_value):
    frame = tk.Frame(root, bg=PANEL, bd=0, highlightthickness=1, highlightbackground=BORDER)
    frame.pack(fill="x", padx=18, pady=10)

    tk.Label(frame, text=title, bg=PANEL, fg=TEXT,
             font=("Helvetica", 12, "bold")).pack(anchor="w", padx=12, pady=(10, 2))

    tk.Label(frame, text=desc, bg=PANEL, fg=MUTED,
             font=("Helvetica", 9)).pack(anchor="w", padx=12, pady=(0, 8))

    row = tk.Frame(frame, bg=PANEL)
    row.pack(fill="x", padx=12, pady=(0, 6))

    # right side readout
    readout = tk.Frame(row, bg=PANEL)
    readout.pack(side="right", padx=(12, 0))

    value_lbl = tk.Label(readout, text="", bg=PANEL, fg=TEXT, font=("Menlo", 12, "bold"))
    value_lbl.pack(anchor="e")

    level_lbl = tk.Label(readout, text="", bg=PANEL, fg=GOOD, font=("Helvetica", 11, "bold"))
    level_lbl.pack(anchor="e")

    # slider
    current = {"v": float(init_v)}

    def on_change(v):
        current["v"] = v
        value_lbl.config(text=fmt_value(v))
        lvl = band_name(v, rec_low, rec_high)
        if lvl == "Recommended":
            level_lbl.config(text="Recommended", fg=GOOD)
        else:
            level_lbl.config(text=lvl, fg=MUTED)

    slider = SmartSlider(
        row,
        min_v=min_v, max_v=max_v, value=init_v,
        rec_low=rec_low, rec_high=rec_high,
        on_change=on_change
    )
    slider.pack(side="left", fill="x", expand=True)

    # recommended text
    tk.Label(frame, text=f"Recommended range: {rec_text}",
             bg=PANEL, fg=GOOD, font=("Helvetica", 9, "bold")).pack(anchor="w", padx=12, pady=(0, 10))

    # initial update
    on_change(init_v)

    return current, slider


def main():
    global gesture_thread, stop_event

    root = tk.Tk()
    root.title("Gesture Mouse Control")
    root.geometry("560x700")
    root.resizable(False, False)
    root.configure(bg=BG)

    # header
    header = tk.Frame(root, bg=BG)
    header.pack(fill="x", padx=18, pady=(16, 10))

    tk.Label(header, text="Gesture Mouse Control", bg=BG, fg=TEXT,
             font=("Helvetica", 20, "bold")).pack(anchor="w")
    tk.Label(header,
             text="Adjust parameters first, then press Start. Stop releases camera & mouse immediately.",
             bg=BG, fg=MUTED, font=("Helvetica", 10)).pack(anchor="w", pady=(6, 0))

    # status + buttons
    topbar = tk.Frame(root, bg=BG)
    topbar.pack(fill="x", padx=18, pady=(0, 10))

    status_var = tk.StringVar(value="Stopped")
    status_pill = tk.Label(topbar, textvariable=status_var,
                           bg="#142044", fg=TEXT,
                           font=("Helvetica", 10, "bold"),
                           padx=12, pady=8)
    status_pill.pack(side="left")

    def worker(params):
        run_gesture(stop_event, params, show_preview=False)

    def on_start():
        nonlocal start_btn, stop_btn
        global gesture_thread, stop_event

        if gesture_thread and gesture_thread.is_alive():
            return

        status_var.set("Running (camera active)")
        status_pill.config(bg="#123a2a")
        start_btn.config(state="disabled", bg=BTN_DISABLED_BG)
        stop_btn.config(state="normal", bg=BTN_STOP_BG)

        stop_event = Event()

        params = {
            "smooth": float(smooth_state["v"]),
            "click_sens": float(click_state["v"]),
            "drag_delay_ms": int(drag_state["v"]),
            "scroll_speed": int(scroll_state["v"]),
        }

        gesture_thread = threading.Thread(target=worker, args=(params,), daemon=True)
        gesture_thread.start()

    def on_stop():
        nonlocal start_btn, stop_btn
        global stop_event

        stop_event.set()
        status_var.set("Stopped")
        status_pill.config(bg="#142044")
        start_btn.config(state="normal", bg=BTN_START_BG)
        stop_btn.config(state="disabled", bg=BTN_DISABLED_BG)

    start_btn = tk.Button(
    topbar,
    text="▶ Start",
    command=on_start,
    bg=BTN_START_BG,
    fg=BTN_TEXT,
    bd=0,
    activebackground="#2b7fff",
    activeforeground=BTN_TEXT,
    padx=20,
    pady=12,
    font=("Helvetica", 11, "bold")
    )
    start_btn.pack(side="right", padx=(10, 0))

    stop_btn = tk.Button(
    topbar,
    text="■ Stop",
    command=on_stop,
    bg=BTN_DISABLED_BG,
    fg=BTN_TEXT,
    bd=0,
    activebackground=BTN_STOP_BG,
    activeforeground=BTN_TEXT,
    padx=20,
    pady=12,
    font=("Helvetica", 11, "bold"),
    state="disabled"
    )
    stop_btn.pack(side="right")

    # blocks
    smooth_state, _ = make_block(
        root,
        "Cursor Smoothness",
        "Higher = smoother but slightly slower. Lower = more responsive.",
        unit="",
        min_v=0.10, max_v=0.90, init_v=0.35,
        rec_low=0.28, rec_high=0.45, rec_text="0.28 ~ 0.45 (Balanced)",
        fmt_value=lambda v: f"{v:.2f}"
    )

    click_state, _ = make_block(
        root,
        "Click Sensitivity",
        "Higher = easier pinch click. If accidental clicks happen, lower it.",
        unit="",
        min_v=0.30, max_v=1.00, init_v=0.65,
        rec_low=0.55, rec_high=0.72, rec_text="0.55 ~ 0.72 (Reliable)",
        fmt_value=lambda v: f"{v:.2f}"
    )

    drag_state, _ = make_block(
        root,
        "Drag Delay (ms)",
        "Lower = click more often. Higher = drag more often.",
        unit="ms",
        min_v=80, max_v=400, init_v=160,
        rec_low=140, rec_high=220, rec_text="140 ~ 220 ms (Natural)",
        fmt_value=lambda v: f"{int(v)}ms"
    )

    scroll_state, _ = make_block(
        root,
        "Scroll Speed",
        "Two fingers extended → scroll. Higher = faster scrolling.",
        unit="",
        min_v=200, max_v=1000, init_v=500,
        rec_low=380, rec_high=700, rec_text="380 ~ 700 (Comfort)",
        fmt_value=lambda v: f"{int(v)}"
    )

    def on_close():
        on_stop()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()