import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from face_recognition.initializers import face_database, save_face_database
import os
from PIL import Image, ImageTk
from config import ATTENDANCE_LOG

def create_registration_dialog(parent, current_frame, face_app):
    """Create a dialog for registering new faces"""
    if current_frame is None:
        messagebox.showerror("Error", "No video frame available")
        return

    # Ask for person's name
    name = simpledialog.askstring("Register Face", "Enter person's name:")
    if not name:
        return

    # Create a registration window
    reg_window = tk.Toplevel(parent)
    reg_window.title("Face Registration")
    reg_window.geometry("400x200")

    # Instructions label
    ttk.Label(reg_window, 
             text="Please move your head slightly:\n1. Look straight\n2. Tilt slightly left/right\n3. Move closer/further",
             justify=tk.CENTER).pack(pady=20)

    # Progress variables
    registration_samples = []
    samples_needed = 5  # Multiple samples for better recognition

    def capture_sample():
        frame = current_frame.copy()
        faces = face_app.get(frame)

        if not faces:
            status_label.config(text="No face detected. Please try again.")
            return False

        best_face = max(faces, key=lambda x: x.det_score)
        if not hasattr(best_face, 'embedding') or best_face.embedding is None:
            status_label.config(text="Could not extract features. Please try again.")
            return False

        registration_samples.append(best_face.embedding)
        samples_left = samples_needed - len(registration_samples)
        status_label.config(text=f"Captured! {samples_left} samples remaining...")

        if len(registration_samples) >= samples_needed:
            # Add all samples to database
            if name in face_database:
                face_database[name].extend(registration_samples)
            else:
                face_database[name] = registration_samples

            # Save database
            save_face_database(face_database)
            messagebox.showinfo("Success", 
                f"Successfully registered {len(registration_samples)} samples for {name}")
            reg_window.destroy()
            return True

        return False

    # Status label
    status_label = ttk.Label(reg_window, text="Press Capture when ready")
    status_label.pack(pady=10)

    # Capture button
    ttk.Button(reg_window, text="Capture Sample", 
              command=capture_sample).pack(pady=10)

    # Cancel button
    ttk.Button(reg_window, text="Cancel", 
              command=reg_window.destroy).pack(pady=10)

def show_attendance_logs(parent):
    """Create a dialog for viewing attendance logs"""
    if not os.path.exists(ATTENDANCE_LOG):
        messagebox.showinfo("Info", "No attendance records found")
        return

    # Create popup window
    log_window = tk.Toplevel(parent)
    log_window.title("Attendance Logs")
    log_window.geometry("600x400")

    # Create text widget
    text_widget = tk.Text(log_window, wrap=tk.NONE)
    text_widget.pack(fill=tk.BOTH, expand=True)

    # Add scrollbars
    y_scrollbar = ttk.Scrollbar(
        log_window, orient=tk.VERTICAL, command=text_widget.yview)
    y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    x_scrollbar = ttk.Scrollbar(
        log_window, orient=tk.HORIZONTAL, command=text_widget.xview)
    x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    text_widget.configure(yscrollcommand=y_scrollbar.set,
                          xscrollcommand=x_scrollbar.set)

    # Load and display logs
    with open(ATTENDANCE_LOG, 'r') as f:
        text_widget.insert(tk.END, f.read())

    text_widget.configure(state='disabled')  # Make read-only

def show_saved_faces(parent):
    """Create a dialog for viewing saved faces"""
    if not face_database:
        messagebox.showinfo("Info", "No faces saved in database")
        return

    names = "\n".join(face_database.keys())
    messagebox.showinfo("Saved Faces", f"Saved faces:\n{names}")

def select_facial_features(parent, control_panel):
    """Create a dialog for selecting facial features to detect"""
    selection_window = tk.Toplevel(parent)
    selection_window.title("Select Facial Features")
    selection_window.geometry("300x200")

    # Get variables from control panel
    detect_eyes_var = control_panel.detect_eyes_var
    detect_mouth_var = control_panel.detect_mouth_var
    color_var = control_panel.color_var

    ttk.Checkbutton(selection_window, text="Detect Eyes",
                    variable=detect_eyes_var).pack(padx=20, pady=10)
    ttk.Checkbutton(selection_window, text="Detect Mouth",
                    variable=detect_mouth_var).pack(padx=20, pady=10)

    # Color selection
    ttk.Label(selection_window, text="Highlight Color:").pack(padx=20, pady=5)
    color_frame = ttk.Frame(selection_window)
    color_frame.pack(padx=20, pady=5)

    colors = [("Green", "green"), ("Red", "red"),
              ("Blue", "blue"), ("Yellow", "yellow")]
    for text, color in colors:
        ttk.Radiobutton(color_frame, text=text, value=color,
                        variable=color_var).pack(side=tk.LEFT, padx=5)

    ttk.Button(selection_window, text="Apply",
               command=selection_window.destroy).pack(pady=20)

class AddCameraDialog(tk.Toplevel):
   def __init__(self, parent, app):
       super().__init__(parent)
       self.app = app
       
       self.title("Add Camera")
       self.geometry("400x450")
       self.resizable(False, False)
       
       # Make dialog modal
       self.transient(parent)
       self.grab_set()
       
       self.setup_ui()
       
   def setup_ui(self):
       """Setup the dialog UI"""
       # Camera type selection
       type_frame = ttk.LabelFrame(self, text="Camera Type")
       type_frame.pack(fill=tk.X, padx=10, pady=5)
       
       self.camera_type = tk.StringVar(value="local")
       ttk.Radiobutton(type_frame, text="Local Camera",
                      variable=self.camera_type, value="local",
                      command=self.update_fields).pack(padx=5, pady=5)
       ttk.Radiobutton(type_frame, text="IP Camera",
                      variable=self.camera_type, value="ip",
                      command=self.update_fields).pack(padx=5, pady=5)
       
       # Settings frame
       self.settings_frame = ttk.LabelFrame(self, text="Camera Settings")
       self.settings_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
       
       # Local camera settings
       self.local_frame = ttk.Frame(self.settings_frame)
       ttk.Label(self.local_frame, text="Device ID:").pack(padx=5, pady=5)
       self.device_id = tk.StringVar(value="0")
       ttk.Entry(self.local_frame, textvariable=self.device_id).pack(padx=5, pady=5)
       
       # IP camera settings
       self.ip_frame = ttk.Frame(self.settings_frame)
       
       ttk.Label(self.ip_frame, text="URL:").pack(padx=5, pady=5)
       self.url = tk.StringVar()
       ttk.Entry(self.ip_frame, textvariable=self.url).pack(fill=tk.X, padx=5, pady=5)
       
       ttk.Label(self.ip_frame, text="Protocol:").pack(padx=5, pady=5)
       self.protocol = tk.StringVar(value="http")
       protocol_frame = ttk.Frame(self.ip_frame)
       protocol_frame.pack(fill=tk.X, padx=5, pady=5)
       ttk.Radiobutton(protocol_frame, text="HTTP",
                      variable=self.protocol, value="http").pack(side=tk.LEFT, padx=5)
       ttk.Radiobutton(protocol_frame, text="RTSP",
                      variable=self.protocol, value="rtsp").pack(side=tk.LEFT, padx=5)
       
       # Authentication frame
       auth_frame = ttk.LabelFrame(self.ip_frame, text="Authentication (Optional)")
       auth_frame.pack(fill=tk.X, padx=5, pady=5)
       
       ttk.Label(auth_frame, text="Username:").pack(padx=5, pady=5)
       self.username = tk.StringVar()
       ttk.Entry(auth_frame, textvariable=self.username).pack(fill=tk.X, padx=5, pady=5)
       
       ttk.Label(auth_frame, text="Password:").pack(padx=5, pady=5)
       self.password = tk.StringVar()
       ttk.Entry(auth_frame, textvariable=self.password, show="*").pack(fill=tk.X, padx=5, pady=5)
       
       # Show initial frame
       self.update_fields()
       
       # Buttons
       button_frame = ttk.Frame(self)
       button_frame.pack(fill=tk.X, padx=10, pady=10)
       
       ttk.Button(button_frame, text="Add", command=self.add_camera).pack(side=tk.LEFT, padx=5)
       ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=5)
       
   def update_fields(self):
       """Update visible fields based on camera type"""
       # Hide all frames
       self.local_frame.pack_forget()
       self.ip_frame.pack_forget()
       
       # Show appropriate frame
       if self.camera_type.get() == "local":
           self.local_frame.pack(fill=tk.BOTH, expand=True)
       else:
           self.ip_frame.pack(fill=tk.BOTH, expand=True)
           
   def add_camera(self):
       """Add the camera based on current settings"""
       try:
           if self.camera_type.get() == "local":
               # Validate device ID
               device_id = int(self.device_id.get())
               success = self.app.add_camera("local", device_id=device_id)
           else:
               # Validate URL
               url = self.url.get().strip()
               if not url:
                   raise ValueError("URL is required")
               
               # Build kwargs
               kwargs = {
                   "url": url,
                   "protocol": self.protocol.get()
               }
               
               # Add authentication if provided
               if self.username.get().strip():
                   kwargs.update({
                       "username": self.username.get().strip(),
                       "password": self.password.get()
                   })
               
               success = self.app.add_camera("ip", **kwargs)
               
           if success:
               self.destroy()
               
       except ValueError as e:
           tk.messagebox.showerror("Error", str(e))
       except Exception as e:
           tk.messagebox.showerror("Error", f"Failed to add camera: {str(e)}")
