import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import threading
import time
import math
import sys
import subprocess

import pyautogui

# ============== Configuration / Tuning ============
SERIAL_BAUD = 115200
READ_INTERVAL = 0.15  # seconds
STEP_PERCENT = 10.0
DEFAULT_USER_SCALE = 1.2
# ==================================================

class EyeZoomApp:
    def __init__(self, root):
        self.root = root
        root.title("EyeZoom — Arduino Distance to OS Zoom")
        self.serial = None
        self.running = False
        self.current_distance_cm = None
        self.target_magnification = 1.0

        frame = ttk.Frame(root, padding=12)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="Serial port:").grid(row=0, column=0, sticky="w")
        self.port_cb = ttk.Combobox(frame, values=self.list_serial_ports(), width=20)
        self.port_cb.grid(row=0, column=1, sticky="w")
        ttk.Button(frame, text="Refresh", command=self.refresh_ports).grid(row=0, column=2)
        ttk.Button(frame, text="Connect", command=self.connect_serial).grid(row=0, column=3)

        ttk.Label(frame, text="Eye power (diopters):").grid(row=1, column=0, sticky="w")
        self.diopter_var = tk.DoubleVar(value=2.0)
        ttk.Entry(frame, textvariable=self.diopter_var, width=10).grid(row=1, column=1, sticky="w")

        ttk.Label(frame, text="User scale (tune):").grid(row=1, column=2, sticky="w")
        self.scale_var = tk.DoubleVar(value=DEFAULT_USER_SCALE)
        ttk.Entry(frame, textvariable=self.scale_var, width=8).grid(row=1, column=3, sticky="w")

        ttk.Label(frame, text="Mode:").grid(row=2, column=0, sticky="w")
        self.mode_var = tk.StringVar(value="windows_magnifier")
        ttk.Radiobutton(frame, text="Windows Magnifier (Win + + / -)", variable=self.mode_var, value="windows_magnifier").grid(row=2, column=1, sticky="w")
        ttk.Radiobutton(frame, text="App/Browser zoom (Ctrl + + / -)", variable=self.mode_var, value="ctrl_zoom").grid(row=2, column=2, sticky="w")

        self.status_lbl = ttk.Label(frame, text="Not connected", foreground="red")
        self.status_lbl.grid(row=3, column=0, columnspan=4, sticky="w", pady=(8,0))

        ttk.Label(frame, text="Distance (cm):").grid(row=4, column=0, sticky="w")
        self.dist_lbl = ttk.Label(frame, text="—")
        self.dist_lbl.grid(row=4, column=1, sticky="w")

        ttk.Label(frame, text="Suggested Zoom (%):").grid(row=5, column=0, sticky="w")
        self.zoom_lbl = ttk.Label(frame, text="—")
        self.zoom_lbl.grid(row=5, column=1, sticky="w")

        ttk.Button(frame, text="Apply Zoom Now", command=self.apply_zoom_now).grid(row=6, column=0, pady=(8,0))
        ttk.Button(frame, text="Stop", command=self.stop).grid(row=6, column=1, pady=(8,0))

        for i in range(4):
            frame.columnconfigure(i, weight=1)

        self.reader_thread = None

    def list_serial_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        return ports

    def refresh_ports(self):
        self.port_cb['values'] = self.list_serial_ports()

    def connect_serial(self):
        if self.serial:
            self.stop()
            time.sleep(0.2)
        port = self.port_cb.get()
        if not port:
            messagebox.showerror("Error", "Choose a serial COM port first.")
            return
        try:
            self.serial = serial.Serial(port, SERIAL_BAUD, timeout=1)
            self.running = True
            self.status_lbl.config(text=f"Connected {port}", foreground="green")
            self.reader_thread = threading.Thread(target=self.read_loop, daemon=True)
            self.reader_thread.start()
        except Exception as e:
            messagebox.showerror("Serial error", str(e))
            self.status_lbl.config(text="Not connected", foreground="red")
            self.serial = None

    def stop(self):
        self.running = False
        if self.serial:
            try:
                self.serial.close()
            except:
                pass
            self.serial = None
        self.status_lbl.config(text="Stopped", foreground="orange")

    def read_loop(self):
        while self.running and self.serial:
            try:
                line = self.serial.readline().decode(errors='ignore').strip()
                if line and line.startswith("D,"):
                    try:
                        cm = float(line.split(",")[1])
                        if cm > 0:
                            self.current_distance_cm = cm
                            self.root.after(0, self.update_ui)
                    except:
                        pass
                time.sleep(READ_INTERVAL)
            except Exception as e:
                print("Serial read error:", e, file=sys.stderr)
                self.running = False
                self.root.after(0, lambda: self.status_lbl.config(text="Serial error", foreground="red"))
                break

    def update_ui(self):
        if self.current_distance_cm:
            self.dist_lbl.config(text=f"{self.current_distance_cm:.1f}")
            self.target_magnification = self.compute_magnification(self.current_distance_cm, self.diopter_var.get(), self.scale_var.get())
            percent = self.target_magnification * 100.0
            self.zoom_lbl.config(text=f"{percent:.0f}%")
        else:
            self.dist_lbl.config(text="—")
            self.zoom_lbl.config(text="—")

    def compute_magnification(self, distance_cm, diopters, user_scale):
        d = max(distance_cm, 1.0) / 100.0
        if diopters <= 0:
            diopters = 1.0
        f = 1.0 / float(diopters)
        M = d / f
        M = max(0.3, min(M, 6.0))
        M = M * float(user_scale)
        M = max(0.3, min(M, 8.0))
        return M

    def apply_zoom_now(self):
        if not self.current_distance_cm:
            messagebox.showwarning("No distance", "No distance reading yet.")
            return
        mag = self.target_magnification
        percent = mag * 100.0
        mode = self.mode_var.get()
        steps = int(round((percent - 100.0) / STEP_PERCENT))
        if mode == "windows_magnifier":
            self.apply_windows_magnifier_steps(steps)
        else:
            self.apply_ctrl_zoom_steps(steps)

    def apply_windows_magnifier_steps(self, steps):
        try:
            pyautogui.hotkey('alt', 'tab')
            time.sleep(0.1)

            pyautogui.hotkey('winleft', 'esc')
            time.sleep(0.2)
            pyautogui.hotkey('winleft', '+')
            time.sleep(0.3)

            if steps > 0:
                for i in range(steps):
                    pyautogui.hotkey('winleft', '+')
                    time.sleep(0.08)
            elif steps < 0:
                for i in range(abs(steps)):
                    pyautogui.hotkey('winleft', '-')
                    time.sleep(0.08)

            self.status_lbl.config(text=f"Applied {steps} Win steps.", foreground="green")
        except Exception as e:
            messagebox.showerror("Error applying magnifier keys", str(e))

    def apply_ctrl_zoom_steps(self, steps):
        try:
            pyautogui.hotkey('alt', 'tab')
            time.sleep(0.1)

            if steps > 0:
                for i in range(steps):
                    pyautogui.hotkey('ctrl', '+')
                    time.sleep(0.06)
            elif steps < 0:
                for i in range(abs(steps)):
                    pyautogui.hotkey('ctrl', '-')
                    time.sleep(0.06)

            self.status_lbl.config(text=f"Applied {steps} Ctrl steps.", foreground="green")
        except Exception as e:
            messagebox.showerror("Error applying ctrl zoom", str(e))

def main():
    root = tk.Tk()
    app = EyeZoomApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
