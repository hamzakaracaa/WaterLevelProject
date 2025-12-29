import serial
import time
import tkinter as tk
from tkinter import font, messagebox
import threading
import math
from collections import deque
import csv
from datetime import datetime
import os
import sys

# Default settings
SERIAL_PORT = 'COM3'
BAUD_RATE = 115200

class ProWaterMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Dryer Monitor v2.0")
        self.root.geometry("600x800")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(True, True)
        self.root.minsize(600, 800)
        # Set a relatable icon (replace 'water_icon.ico' with your icon file path)
        try:
            # Get script directory and find icon in project root
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            icon_path = os.path.join(project_root, 'water_icon.ico')
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass  # Use default if icon not found

        # Variables
        self.running = True
        self.serial_connected = False
        self.ser = None  # Initialize serial object
        
        # Filtering buffer (holds last 20 values)
        self.data_buffer = deque(maxlen=20) 
        
        # Calibration values (default)
        self.calib_min = 100   # Empty value
        self.calib_max = 2500  # Full value
        self.raw_val = 0       # Current raw data
        
        # Data logging
        self.logging_active = False
        # Get script directory for log files
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        self.log_filename = os.path.join(project_root, f"sensor_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

        # Setup UI
        self.setup_ui()
        
        # Start
        self.start_serial_thread()
        self.animate_water()

    def setup_ui(self):
        # Fonts
        self.font_title = font.Font(family="Segoe UI", size=20, weight="bold")
        self.font_val = font.Font(family="Consolas", size=40, weight="bold")
        self.font_small = font.Font(family="Segoe UI", size=10)

        # Main panel
        main_frame = tk.Frame(self.root, bg="#1e1e2e")
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # Title
        tk.Label(main_frame, text="WATER TANK STATUS", font=self.font_title, bg="#1e1e2e", fg="#cdd6f4").pack()
        self.lbl_status = tk.Label(main_frame, text="Waiting for connection...", font=self.font_small, bg="#1e1e2e", fg="#fab387")
        self.lbl_status.pack(pady=(0, 10))

        # Canvas (water tank)
        self.canvas = tk.Canvas(main_frame, bg="#181825", highlightthickness=0)
        self.canvas.pack(pady=10, expand=True, fill="both")
        self.cw, self.ch = 250, 350  # initial sizes
        self.canvas.bind('<Configure>', self.on_resize)
        self.redraw_tank()

        # Info panel
        self.lbl_percent = tk.Label(main_frame, text="%0", font=self.font_val, bg="#1e1e2e", fg="#89b4fa")
        self.lbl_percent.pack()
        self.lbl_raw = tk.Label(main_frame, text="Raw Data: 0", font=self.font_small, bg="#1e1e2e", fg="#6c757d")
        self.lbl_raw.pack()

        # Control panel (calibration and logging)
        control_frame = tk.LabelFrame(main_frame, text=" Control Panel ", bg="#2a2d3a", fg="#ffffff", font=self.font_small, bd=3, relief="ridge")
        control_frame.pack(fill="x", pady=20, ipadx=10, ipady=10)

        # Calibration buttons
        btn_style = {"bg": "#4a90e2", "fg": "white", "font": ("Segoe UI", 10, "bold"), "relief": "raised", "bd": 2, "width": 12, "height": 2}
        
        tk.Button(control_frame, text="Set Min Level", command=self.set_min_calib, **btn_style).pack(side="left", padx=15, pady=5)
        tk.Button(control_frame, text="Set Max Level", command=self.set_max_calib, **btn_style).pack(side="left", padx=15, pady=5)
        
        # Data logging checkbox
        self.check_var = tk.IntVar()
        self.chk_log = tk.Checkbutton(control_frame, text="📊 Save Data (.csv)", variable=self.check_var, 
                                      command=self.toggle_logging, bg="#2a2d3a", fg="#a6e3a1", selectcolor="#4a90e2", activebackground="#2a2d3a", font=("Segoe UI", 9))
        self.chk_log.pack(side="right", padx=15, pady=5)

        # Animation variables
        self.current_percent = 0.0
        self.target_percent = 0.0
        self.wave_phase = 0.0

    def on_resize(self, event):
        self.cw = self.canvas.winfo_width()
        self.ch = self.canvas.winfo_height()
        self.redraw_tank()

    def redraw_tank(self):
        self.canvas.delete("all")
        # Tank lines
        for i in range(1, 10):
            y = i * (self.ch / 10)
            color = "#313244" if i % 5 != 0 else "#45475a"
            self.canvas.create_line(10, y, self.cw - 10, y, fill=color, dash=(5, 2))
            if i % 5 == 0:
                self.canvas.create_text(self.cw / 2, y, text=f"{100 - i*10}%", fill="#585b70", font=("Arial", 8))
        # Water polygon
        self.water_poly = self.canvas.create_polygon(0, self.ch, self.cw, self.ch, self.cw, self.ch, 0, self.ch, fill="#3498db")
        self.foam_line = self.canvas.create_line(0, self.ch, self.cw, self.ch, fill="#89cff0", width=3)

    # Serial communication and filtering
    def start_serial_thread(self):
        t = threading.Thread(target=self.read_serial, daemon=True)
        t.start()

    def read_serial(self):
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            self.serial_connected = True
            self.update_ui_status(f"CONNECTED: {SERIAL_PORT}", "#a6e3a1")
        except Exception as e:
            self.update_ui_status(f"No Connection!", "#f38ba8")
            return

        while self.running:
            try:
                if self.ser and self.ser.is_open and self.ser.in_waiting:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if "Su Seviyesi:" in line:
                        try:
                            # Get raw data
                            val = int(line.split(":")[1])
                            self.raw_val = val
                            
                            # Add to buffer (for filtering)
                            self.data_buffer.append(val)
                            
                            # Calculate moving average (reduces noise)
                            if len(self.data_buffer) > 0:
                                filtered_val = sum(self.data_buffer) / len(self.data_buffer)
                            else:
                                filtered_val = val  # Fallback if buffer is empty
                            
                            # Convert to percentage (based on calibration)
                            # Clamp value between min and max
                            if self.calib_max != self.calib_min:  # Prevent division by zero
                                clamped_val = max(self.calib_min, min(filtered_val, self.calib_max))
                                percentage = ((clamped_val - self.calib_min) / (self.calib_max - self.calib_min)) * 100
                            else:
                                percentage = 0
                            self.target_percent = percentage

                            # Logging (if active)
                            if self.logging_active:
                                self.log_data(val, filtered_val, percentage)

                        except ValueError:
                            pass
            except (serial.SerialException, AttributeError, OSError) as e:
                self.update_ui_status("Connection Lost!", "#f38ba8")
                self.serial_connected = False
                if self.ser and self.ser.is_open:
                    try:
                        self.ser.close()
                    except:
                        pass
                break
            
            time.sleep(0.01) # Small delay to reduce CPU load

    # Logging (Excel/CSV)
    def toggle_logging(self):
        if self.check_var.get() == 1:
            self.logging_active = True
            # Write file headers
            try:
                if not os.path.exists(self.log_filename):
                    with open(self.log_filename, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(["Zaman", "Ham Veri", "Filtreli Veri", "Yüzde"])
                messagebox.showinfo("Recording Started", f"Data is being saved to:\n{self.log_filename}")
            except (IOError, OSError, PermissionError) as e:
                messagebox.showerror("Error", f"Cannot create log file:\n{str(e)}")
                self.logging_active = False
                self.check_var.set(0)
        else:
            self.logging_active = False

    def log_data(self, raw, filtered, percent):
        # Log every reading (high resolution)
        try:
            with open(self.log_filename, 'a', newline='') as f:
                writer = csv.writer(f)
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                writer.writerow([timestamp, raw, f"{filtered:.2f}", f"{percent:.2f}"])
        except (IOError, OSError, PermissionError) as e:
            # Silently fail logging if file can't be written
            pass

    # Calibration functions
    def set_min_calib(self):
        # Set current value as empty (min)
        self.calib_min = self.raw_val
        messagebox.showinfo("Calibration", f"New EMPTY value set: {self.calib_min}")

    def set_max_calib(self):
        # Set current value as full (max)
        self.calib_max = self.raw_val
        messagebox.showinfo("Calibration", f"New FULL value set: {self.calib_max}")

    # Visual update
    def update_ui_status(self, text, color):
        self.root.after(0, lambda: self.lbl_status.config(text=text, fg=color))

    def animate_water(self):
        if not self.running: return

        # Smooth transition (lerp)
        self.current_percent += (self.target_percent - self.current_percent) * 0.1
        
        # Graphical calculations
        water_h_px = (self.current_percent / 100) * self.ch
        surface_y = self.ch - water_h_px

        # Wave animation
        self.wave_phase += 0.2
        wave_points = []
        
        # Create wave points
        for x in range(0, self.cw + 1, 5):
            amp = 5 
            y = surface_y + math.sin((x * 0.05) + self.wave_phase) * amp
            wave_points.extend([x, y])

        # Draw polygon (bottom left -> wave -> bottom right)
        poly_coords = [0, self.ch] + wave_points + [self.cw, self.ch]
        self.canvas.coords(self.water_poly, *poly_coords)
        
        # Draw foam line on top
        self.canvas.coords(self.foam_line, *wave_points)

        # Update text labels
        self.lbl_percent.config(text=f"%{int(self.current_percent)}")
        self.lbl_raw.config(text=f"Sensor Value: {self.raw_val}")

        # Color change
        color = "#3498db"
        if self.current_percent < 10: color = "#e74c3c" # Red
        elif self.current_percent > 90: color = "#f1c40f" # Yellow
        
        if self.serial_connected:
            self.canvas.itemconfig(self.water_poly, fill=color)
        else:
            self.canvas.itemconfig(self.water_poly, fill="#444") # Gray

        self.root.after(30, self.animate_water)

    def on_closing(self):
        self.running = False
        # Properly close serial connection
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except:
                pass
        self.root.destroy()

if __name__ == "__main__":
    app = tk.Tk()
    monitor = ProWaterMonitor(app)
    app.protocol("WM_DELETE_WINDOW", monitor.on_closing)
    app.mainloop()