import tkinter as tk
from tkinter import ttk
from typing import Optional
from datetime import datetime

class UIFeedback:
    def __init__(self, parent: tk.Widget):
        self.parent = parent
        self.status_var = tk.StringVar()
        self.progress_var = tk.DoubleVar()
        self.setup_ui()

    def setup_ui(self):
        """Set up the UI feedback components"""
        # Create frame for feedback elements
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill='x', padx=10, pady=5)

        # Status label
        self.status_label = ttk.Label(
            self.frame, 
            textvariable=self.status_var,
            font=('Arial', 10)
        )
        self.status_label.pack(fill='x')

        # Progress bar
        self.progress_bar = ttk.Progressbar(
            self.frame,
            variable=self.progress_var,
            mode='determinate'
        )
        self.progress_bar.pack(fill='x', pady=(5, 0))

        # Keyboard shortcuts frame
        self.shortcuts_frame = ttk.LabelFrame(self.frame, text='Keyboard Shortcuts')
        self.shortcuts_frame.pack(fill='x', pady=(10, 0))

        shortcuts = [
            ('Space', 'Capture Photo'),
            ('R', 'Retake Photo'),
            ('Esc', 'Exit Camera')
        ]

        for key, action in shortcuts:
            shortcut_label = ttk.Label(
                self.shortcuts_frame,
                text=f'{key}: {action}',
                font=('Arial', 9)
            )
            shortcut_label.pack(anchor='w', padx=5, pady=2)

    def update_status(self, status: str):
        """Update the status text with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_var.set(f"[{timestamp}] {status}")

    def update_progress(self, value: float):
        """Update the progress bar (0-100)"""
        self.progress_var.set(value)

    def show_capture_feedback(self):
        """Show visual feedback when photo is captured"""
        original_bg = self.frame.cget('background')
        self.frame.configure(background='green')
        self.parent.after(200, lambda: self.frame.configure(background=original_bg))

    def show_error(self, message: str):
        """Show error message with red highlight"""
        self.update_status(f"Error: {message}")
        original_bg = self.status_label.cget('background')
        self.status_label.configure(background='#ffcccc')
        self.parent.after(2000, lambda: self.status_label.configure(background=original_bg))

    def show_countdown(self, seconds: int, callback: Optional[callable] = None):
        """Show countdown before photo capture"""
        if seconds > 0:
            self.update_status(f"Taking photo in {seconds}...")
            self.parent.after(1000, lambda: self.show_countdown(seconds - 1, callback))
        else:
            self.update_status("Capturing photo...")
            if callback:
                callback()

    def start_capture_session(self, total_photos: int):
        """Initialize a new capture session"""
        self.update_status(f"Starting capture session ({total_photos} photos)")
        self.progress_var.set(0)
        self.total_photos = total_photos

    def update_capture_progress(self, current_photo: int):
        """Update progress for current capture session"""
        progress = (current_photo / self.total_photos) * 100
        self.update_progress(progress)
        self.update_status(f"Captured photo {current_photo}/{self.total_photos}")

    def end_capture_session(self):
        """End the current capture session"""
        self.update_status("Capture session completed")
        self.progress_var.set(100)