import tkinter as tk
from tkinter import ttk, messagebox
from face_recognition.initializers import face_database, save_face_database

class StatsPanel(ttk.LabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="Performance", **kwargs)
        self.fps_label = ttk.Label(self, text="FPS: 0")
        self.fps_label.pack(padx=5, pady=2)

        self.detection_time_label = ttk.Label(self, text="Detection: 0ms")
        self.detection_time_label.pack(padx=5, pady=2)

        self.recognition_label = ttk.Label(self, text="Recognition: 0ms")
        self.recognition_label.pack(padx=5, pady=2)

class StatusPanel(ttk.LabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="Status", **kwargs)
        self.status_label = ttk.Label(self, text="Initializing...")
        self.status_label.pack(padx=5, pady=2)

        self.face_count_label = ttk.Label(self, text="Faces: 0")
        self.face_count_label.pack(padx=5, pady=2)

        self.presence_label = ttk.Label(self, text="Present: None")
        self.presence_label.pack(padx=5, pady=2)
        
        self.away_label = ttk.Label(self, text="Away: None")
        self.away_label.pack(padx=5, pady=2)

class FaceListPanel(ttk.LabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="Saved Faces", **kwargs)
        self.face_listbox = tk.Listbox(self)
        self.face_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Button(self, text="Delete Selected Face",
                   command=self.delete_face).pack(fill=tk.X, padx=5, pady=2)

        self.update_face_list()

    def update_face_list(self):
        self.face_listbox.delete(0, tk.END)
        for name in face_database.keys():
            self.face_listbox.insert(tk.END, name)

    def delete_face(self):
        selected = self.face_listbox.curselection()
        if not selected:
            messagebox.showerror("Error", "No face selected")
            return

        name = self.face_listbox.get(selected[0])
        if messagebox.askyesno("Confirm", f"Delete face data for {name}?"):
            if name in face_database:
                del face_database[name]
                save_face_database(face_database)
                self.update_face_list()
                messagebox.showinfo("Success", f"Face data for {name} deleted")

class ControlPanel(ttk.Frame):
    def __init__(self, parent, command_callbacks, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Feature detection options
        self.detect_eyes_var = tk.BooleanVar(value=True)
        self.detect_mouth_var = tk.BooleanVar(value=True)
        self.color_var = tk.StringVar(value="green")

        # Stats frame
        self.stats_panel = StatsPanel(self)
        self.stats_panel.pack(fill=tk.X, padx=5, pady=5)

        # Status frame
        self.status_panel = StatusPanel(self)
        self.status_panel.pack(fill=tk.X, padx=5, pady=5)

        # Buttons frame
        buttons_frame = ttk.LabelFrame(self, text="Actions")
        buttons_frame.pack(fill=tk.X, padx=5, pady=5)

        # Camera management button
        ttk.Button(buttons_frame, text="Add Camera",
                  command=command_callbacks['add_camera']).pack(fill=tk.X, padx=5, pady=2)

        # Face management buttons
        ttk.Button(buttons_frame, text="Register New Face",
                  command=command_callbacks['register']).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(buttons_frame, text="View Saved Faces",
                  command=command_callbacks['view_faces']).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(buttons_frame, text="View Attendance Logs",
                  command=command_callbacks['view_logs']).pack(fill=tk.X, padx=5, pady=2)

        # Face list
        self.face_list = FaceListPanel(self)
        self.face_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def update_stats(self, fps, detection_time, recognition_time):
        self.stats_panel.fps_label.config(text=f"FPS: {fps:.1f}")
        self.stats_panel.detection_time_label.config(text=f"Detection: {detection_time:.1f}ms")
        self.stats_panel.recognition_label.config(text=f"Recognition: {recognition_time:.1f}ms")

    def update_status(self, status_text, face_count, present_text, away_text):
        self.status_panel.status_label.config(text=status_text)
        self.status_panel.face_count_label.config(text=f"Faces: {face_count}")
        self.status_panel.presence_label.config(text=f"At Desk: {present_text}")
        self.status_panel.away_label.config(text=f"Away: {away_text}")

    def get_feature_detection_options(self):
        return {
            'detect_eyes': self.detect_eyes_var.get(),
            'detect_mouth': self.detect_mouth_var.get(),
            'color': self.color_var.get()
        }
