import customtkinter as ctk
from ui.theme import setup_theme
from ui.components.control_panel import ControlPanel
from ui.components.camera_view import CameraFrame, CameraGridView
from ui.components.dialogs import create_registration_dialog, show_saved_faces, show_attendance_logs

class TestWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Setup theme
        setup_theme()
        
        # Configure window
        self.title("CustomTkinter UI Test")
        self.geometry("1200x700")
        
        # Main container
        container = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add camera view
        self.camera_frame = CameraFrame(container)
        self.camera_frame.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 10)
        )
        
        # Add control panel with test callbacks
        callbacks = {
            'register': lambda: print("Register clicked"),
            'view_faces': lambda: print("View faces clicked"), 
            'view_logs': lambda: print("View logs clicked"),
            'add_camera': lambda: print("Add camera clicked")
        }
        
        self.control_panel = ControlPanel(container, callbacks)
        self.control_panel.pack(
            side="right",
            fill="y"
        )
        
        # Add test buttons
        self.add_test_controls()
        
        # Start update loop
        self.update_stats()
    
    def add_test_controls(self):
        """Add buttons to test various functionality"""
        test_frame = ctk.CTkFrame(self)
        test_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        
        # Test stats update
        ctk.CTkButton(
            test_frame,
            text="Update Stats",
            command=self.test_stats_update
        ).pack(side="left", padx=5)
        
        # Test status update
        ctk.CTkButton(
            test_frame,
            text="Update Status",
            command=self.test_status_update
        ).pack(side="left", padx=5)
        
        # Test dialogs
        ctk.CTkButton(
            test_frame,
            text="Show Registration",
            command=self.test_registration
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            test_frame,
            text="Show Faces",
            command=lambda: show_saved_faces(self)
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            test_frame,
            text="Show Logs",
            command=lambda: show_attendance_logs(self)
        ).pack(side="left", padx=5)
    
    def test_stats_update(self):
        """Test updating performance stats"""
        self.control_panel.update_stats(30.5, 25.3, 15.8)
    
    def test_status_update(self):
        """Test updating status information"""
        self.control_panel.update_status(
            "Testing status",
            2,
            "John, Jane",
            "Bob"
        )
    
    def test_registration(self):
        """Test registration dialog"""
        import numpy as np
        # Create dummy frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        create_registration_dialog(self, frame, None)
    
    def update_stats(self):
        """Simulate periodic stats updates"""
        import random
        
        # Update with random values
        fps = random.uniform(25, 35)
        det_time = random.uniform(20, 30)
        rec_time = random.uniform(10, 20)
        
        self.control_panel.update_stats(fps, det_time, rec_time)
        
        # Schedule next update
        self.after(1000, self.update_stats)

if __name__ == "__main__":
    app = TestWindow()
    app.mainloop()