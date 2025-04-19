import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from PIL import Image, ImageTk
import cv2
import numpy as np
from ..theme import get_color, get_font, get_padding
from face_recognition.initializers import (
    face_database,
    save_face_database,
    FaceEntry
)
import os

class BaseDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, width=400, height=300):
        super().__init__(parent)
        
        # Configure window
        self.title(title)
        self.geometry(f"{width}x{height}")
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - width) // 2
        y = parent.winfo_y() + (parent.winfo_height() - height) // 2
        self.geometry(f"+{x}+{y}")
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Setup UI
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI - override in subclasses"""
        pass

class EnhancedRegistrationDialog(BaseDialog):
    def __init__(self, parent, camera_manager, face_app):
        self.camera_manager = camera_manager
        self.face_app = face_app
        self.poses = {
            'front': {
                'count': 0,
                'max': 5,
                'instruction': "Look directly at camera",
                'directions': [
                    "1. Straight ahead - neutral expression",
                    "2. Straight ahead - slight smile",
                    "3. Straight ahead - raise eyebrows",
                    "4. Straight ahead - open mouth slightly",
                    "5. Straight ahead - neutral expression"
                ],
                'frames': []
            },
            'side': {
                'count': 0,
                'max': 2,
                'instruction': "Profile shots",
                'directions': [
                    "1. Turn head 90° to left side",
                    "2. Turn head 90° to right side"
                ],
                'frames': []
            },
            'tilt': {
                'count': 0,
                'max': 4,
                'instruction': "Tilted poses",
                'directions': [
                    "1. Tilt head slightly left",
                    "2. Tilt head slightly right",
                    "3. Tilt head slightly up",
                    "4. Tilt head slightly down"
                ],
                'frames': []
            },
            'back': {
                'count': 0,
                'max': 5,
                'instruction': "Back angles",
                'directions': [
                    "1. Tilt head back halfway",
                    "2. Turn head back + left",
                    "3. Turn head back + right",
                    "4. Look up at 45°",
                    "5. Look up fully"
                ],
                'frames': []
            }
        }
        self.current_pose = 'front'
        self.face_entry = None
        self.running = True
        self.thumbnail_size = (100, 100)  # Size for captured image thumbnails
        super().__init__(parent, "Enhanced Face Registration", 1000, 700)
    
    def setup_ui(self):
        # Main container with 3 columns
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Left side - Camera Preview and Controls
        left_frame = ctk.CTkFrame(container)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Camera preview
        self.preview_frame = ctk.CTkFrame(left_frame)
        self.preview_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.preview_label = ctk.CTkLabel(self.preview_frame, text="")
        self.preview_label.pack(expand=True)
        
        # Name input
        input_frame = ctk.CTkFrame(left_frame)
        input_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            input_frame,
            text="Name:",
            font=get_font()
        ).pack(side="left", padx=(20, 10))
        
        self.name_entry = ctk.CTkEntry(
            input_frame,
            font=get_font()
        )
        self.name_entry.pack(side="left", fill="x", expand=True, padx=(0, 20))
        
        # Control buttons
        button_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        self.capture_btn = ctk.CTkButton(
            button_frame,
            text="Capture",
            command=self.capture_pose,
            font=get_font()
        )
        self.capture_btn.pack(side="right", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.on_closing,
            font=get_font()
        ).pack(side="right", padx=5)
        
        # Middle - Captured Images
        middle_frame = ctk.CTkFrame(container, width=300)
        middle_frame.pack(side="left", fill="both", padx=10)
        
        ctk.CTkLabel(
            middle_frame,
            text="Captured Images",
            font=get_font("title")
        ).pack(pady=(10, 5))
        
        # Scrollable frame for captured images
        self.captures_frame = ctk.CTkScrollableFrame(middle_frame)
        self.captures_frame.pack(fill="both", expand=True)
        
        # Right side - Instructions and Progress
        right_frame = ctk.CTkFrame(container, width=250)
        right_frame.pack(side="right", fill="both", padx=(10, 0))
        right_frame.pack_propagate(False)
        
        # Instructions
        ctk.CTkLabel(
            right_frame,
            text="Current Pose",
            font=get_font("title")
        ).pack(pady=(10, 5))
        
        self.instruction_label = ctk.CTkLabel(
            right_frame,
            text="",
            font=get_font(),
            wraplength=230
        )
        self.instruction_label.pack(pady=(0, 10))
        
        # Current direction
        self.direction_label = ctk.CTkLabel(
            right_frame,
            text="",
            font=get_font(),
            wraplength=230,
            fg_color=get_color("primary"),
            corner_radius=6
        )
        self.direction_label.pack(pady=(0, 20), padx=10, fill="x")
        
        # Progress section
        ctk.CTkLabel(
            right_frame,
            text="Progress",
            font=get_font("title")
        ).pack(pady=(0, 10))
        
        # Progress indicators for each pose
        self.progress_labels = {}
        for pose, info in self.poses.items():
            frame = ctk.CTkFrame(right_frame, fg_color="transparent")
            frame.pack(fill="x", pady=2, padx=10)
            
            ctk.CTkLabel(
                frame,
                text=pose.title(),
                font=get_font()
            ).pack(side="left")
            
            label = ctk.CTkLabel(
                frame,
                text=f"0/{info['max']}",
                font=get_font()
            )
            label.pack(side="right")
            self.progress_labels[pose] = label
        
        # Start camera update
        self.update_preview()
    
    def update_preview(self):
        """Update camera preview"""
        if self.running:
            # Get frame from camera
            frame = self.camera_manager.get_frame("main_camera")
            if frame is not None:
                # Convert to RGB for display
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame_rgb)
                
                # Scale image to fit
                width = min(600, image.width)
                height = int(width * image.height / image.width)
                image = image.resize((width, height), Image.Resampling.LANCZOS)
                
                # Update preview
                photo = ImageTk.PhotoImage(image)
                self.preview_label.configure(image=photo)
                self.preview_label.image = photo
            
            # Update instructions
            pose_info = self.poses[self.current_pose]
            self.instruction_label.configure(
                text=f"{pose_info['instruction']}\n"
                     f"({pose_info['count'] + 1}/{pose_info['max']})"
            )
            
            # Update current direction
            if pose_info['count'] < pose_info['max']:
                self.direction_label.configure(
                    text=pose_info['directions'][pose_info['count']]
                )
            
            # Schedule next update
            self.after(33, self.update_preview)
    
    def add_capture_thumbnail(self, frame, pose_type):
        """Add thumbnail of captured frame"""
        # Create thumbnail
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame_rgb)
        image.thumbnail(self.thumbnail_size)
        photo = ImageTk.PhotoImage(image)
        
        # Create container for thumbnails of this pose if not exists
        container_name = f"{pose_type}_container"
        if not hasattr(self, container_name):
            pose_frame = ctk.CTkFrame(self.captures_frame)
            pose_frame.pack(fill="x", pady=5, padx=5)
            
            ctk.CTkLabel(
                pose_frame,
                text=pose_type.title(),
                font=get_font("title"),
                fg_color=get_color("primary"),
                corner_radius=6
            ).pack(pady=5, padx=5, fill="x")
            
            images_frame = ctk.CTkFrame(pose_frame, fg_color="transparent")
            images_frame.pack(fill="x", pady=5)
            setattr(self, container_name, images_frame)
        
        # Add thumbnail with count label
        count = self.poses[pose_type]['count']
        thumbnail_frame = ctk.CTkFrame(getattr(self, container_name))
        thumbnail_frame.pack(side="left", padx=2)
        
        # Add image
        thumbnail_label = ctk.CTkLabel(
            thumbnail_frame,
            image=photo,
            text="",
        )
        thumbnail_label.image = photo
        thumbnail_label.pack()
        
        # Add count label
        ctk.CTkLabel(
            thumbnail_frame,
            text=str(count + 1),
            font=get_font("medium")
        ).pack()

    def capture_pose(self):
        """Capture current pose"""
        # Get name on first capture
        if not self.face_entry:
            name = self.name_entry.get().strip()
            if not name:
                self.show_error("Please enter a name")
                return
            
            if name in face_database:
                self.show_error("Name already exists")
                return
            
            # Initialize face entry
            self.face_entry = FaceEntry()
            self.name = name
        
        try:
            # Get current frame and detect face
            frame = self.camera_manager.get_frame("main_camera")
            if frame is None:
                self.show_error("No camera frame available")
                return
            
            faces = self.face_app.get(frame)
            if not faces:
                self.show_error("No face detected")
                return
            
            # Add embedding to current pose
            face = faces[0]
            if self.face_entry.add_embedding(self.current_pose, face.embedding):
                # Store frame and add thumbnail
                self.poses[self.current_pose]['frames'].append(frame.copy())
                self.add_capture_thumbnail(frame, self.current_pose)
                
                # Update progress
                self.poses[self.current_pose]['count'] += 1
                self.progress_labels[self.current_pose].configure(
                    text=f"{self.poses[self.current_pose]['count']}/{self.poses[self.current_pose]['max']}"
                )
                
                # Check if current pose is complete
                if self.poses[self.current_pose]['count'] >= self.poses[self.current_pose]['max']:
                    # Move to next pose
                    pose_order = ['front', 'side', 'tilt', 'back']
                    current_idx = pose_order.index(self.current_pose)
                    
                    if current_idx < len(pose_order) - 1:
                        self.current_pose = pose_order[current_idx + 1]
                        self.show_info(f"Great! Now let's capture {self.current_pose} poses")
                    else:
                        # All poses captured
                        self.complete_registration()
            
        except Exception as e:
            self.show_error(f"Error capturing pose: {str(e)}")
    
    def complete_registration(self):
        """Complete the registration process"""
        try:
            # Validate that all poses are complete
            for pose_type, info in self.poses.items():
                if info['count'] < info['max']:
                    self.show_error(f"Incomplete poses: {pose_type} ({info['count']}/{info['max']})")
                    return
            
            # Validate face entry
            if not self.face_entry or not self.name:
                self.show_error("Invalid registration state")
                return
            
            if not self.face_entry.is_complete():
                poses = [p for p, emb in self.face_entry.embeddings.items()
                        if len(emb) < self.poses[p]['max']]
                self.show_error(f"Missing embeddings for poses: {', '.join(poses)}")
                return

            print(f"Saving registration for {self.name}...")
            for pose, embeddings in self.face_entry.embeddings.items():
                print(f"{pose}: {len(embeddings)}/{self.poses[pose]['max']} embeddings")
            
            # Save to database with confirmation
            face_database[self.name] = self.face_entry
            if not save_face_database(face_database):
                raise Exception("Failed to save face database")
            
            self.show_info(
                "Registration successful!\n\n"
                f"Captured {sum(len(emb) for emb in self.face_entry.embeddings.values())} "
                "poses for enhanced recognition."
            )
            self.running = False
            self.destroy()
            
        except Exception as e:
            import traceback
            print(f"Registration error: {str(e)}")
            print(traceback.format_exc())
            self.show_error(
                "Error saving registration:\n"
                f"{str(e)}\n\n"
                "Please try again or check logs for details."
            )
    
    def on_closing(self):
        """Handle window closing"""
        if any(info['count'] > 0 for info in self.poses.values()):
            confirm = CTkMessagebox(
                self,
                title="Confirm Close",
                message="Registration in progress. Are you sure you want to close?",
                icon="warning",
                option_1="Cancel",
                option_2="Close"
            )
            if confirm.get() != "Close":
                return
                
        self.running = False
        self.destroy()
    
    def show_error(self, message):
        """Show error dialog"""
        ctk.CTkMessagebox(
            self,
            title="Error",
            message=message,
            icon="cancel"
        )
    
    def show_info(self, message):
        """Show info dialog"""
        ctk.CTkMessagebox(
            self,
            title="Success",
            message=message,
            icon="check"
        )

class AddCameraDialog(BaseDialog):
    def __init__(self, parent):
        super().__init__(parent, "Add Camera", 400, 300)
    
    def setup_ui(self):
        # Create main container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Camera type selection
        type_frame = ctk.CTkFrame(container)
        type_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            type_frame,
            text="Camera Type:",
            font=get_font()
        ).pack(side="left", padx=20)
        
        self.camera_type = ctk.StringVar(value="local")
        
        ctk.CTkRadioButton(
            type_frame,
            text="Local Camera",
            variable=self.camera_type,
            value="local",
            command=self.update_fields,
            font=get_font()
        ).pack(side="left", padx=20)
        
        ctk.CTkRadioButton(
            type_frame,
            text="IP Camera",
            variable=self.camera_type,
            value="ip",
            command=self.update_fields,
            font=get_font()
        ).pack(side="left", padx=20)
        
        # Input fields frame
        self.fields_frame = ctk.CTkFrame(container)
        self.fields_frame.pack(fill="x", pady=(0, 20))
        
        # Initialize with local camera fields
        self.update_fields()
        
        # Buttons
        button_frame = ctk.CTkFrame(container, fg_color="transparent")
        button_frame.pack(fill="x")
        
        ctk.CTkButton(
            button_frame,
            text="Add",
            command=self.add_camera,
            font=get_font()
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            font=get_font()
        ).pack(side="right", padx=5)
    
    def update_fields(self):
        """Update input fields based on camera type"""
        # Clear existing fields
        for widget in self.fields_frame.winfo_children():
            widget.destroy()
        
        if self.camera_type.get() == "local":
            # Device ID field
            ctk.CTkLabel(
                self.fields_frame,
                text="Device ID:",
                font=get_font()
            ).pack(side="left", padx=(20, 10))
            
            self.device_id = ctk.CTkEntry(
                self.fields_frame,
                font=get_font()
            )
            self.device_id.pack(side="left", fill="x", expand=True, padx=(0, 20))
            self.device_id.insert(0, "0")
            
        else:  # IP camera
            # URL field
            url_frame = ctk.CTkFrame(self.fields_frame, fg_color="transparent")
            url_frame.pack(fill="x", pady=5)
            
            ctk.CTkLabel(
                url_frame,
                text="URL:",
                font=get_font()
            ).pack(side="left", padx=(20, 10))
            
            self.url = ctk.CTkEntry(
                url_frame,
                font=get_font()
            )
            self.url.pack(side="left", fill="x", expand=True, padx=(0, 20))
            
            # Credentials frame
            cred_frame = ctk.CTkFrame(self.fields_frame, fg_color="transparent")
            cred_frame.pack(fill="x", pady=5)
            
            # Username
            ctk.CTkLabel(
                cred_frame,
                text="Username:",
                font=get_font()
            ).pack(side="left", padx=(20, 10))
            
            self.username = ctk.CTkEntry(
                cred_frame,
                font=get_font()
            )
            self.username.pack(side="left", fill="x", expand=True, padx=(0, 20))
            
            # Password frame
            pass_frame = ctk.CTkFrame(self.fields_frame, fg_color="transparent")
            pass_frame.pack(fill="x", pady=5)
            
            ctk.CTkLabel(
                pass_frame,
                text="Password:",
                font=get_font()
            ).pack(side="left", padx=(20, 10))
            
            self.password = ctk.CTkEntry(
                pass_frame,
                font=get_font(),
                show="*"
            )
            self.password.pack(side="left", fill="x", expand=True, padx=(0, 20))
    
    def add_camera(self):
        """Add new camera"""
        try:
            if self.camera_type.get() == "local":
                device_id = int(self.device_id.get())
                self.master.add_camera("local", device_id=device_id)
            else:
                url = self.url.get().strip()
                if not url:
                    self.show_error("URL is required")
                    return
                
                username = self.username.get().strip()
                password = self.password.get()
                
                self.master.add_camera(
                    "ip",
                    url=url,
                    username=username if username else None,
                    password=password if password else None
                )
            
            self.destroy()
            
        except Exception as e:
            self.show_error(f"Error adding camera: {str(e)}")
    
    def show_error(self, message):
        """Show error dialog"""
        CTkMessagebox(
            self,
            title="Error",
            message=message,
            icon="cancel"
        )

def create_registration_dialog(parent, camera_manager, face_app):
    """Create and show enhanced registration dialog"""
    try:
        dialog = EnhancedRegistrationDialog(parent, camera_manager, face_app)
        parent.wait_window(dialog)
    except Exception as e:
        CTkMessagebox(
            parent,
            title="Error",
            message=f"Error creating registration dialog: {str(e)}",
            icon="cancel"
        )

class SavedFacesDialog(BaseDialog):
    """Dialog for viewing and managing saved faces"""
    def __init__(self, parent):
        self.face_entries = {}  # Store checkbox widgets
        super().__init__(parent, "Saved Faces", 400, 500)
    
    def setup_ui(self):
        # Create main container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create scrollable frame
        self.scroll_frame = ctk.CTkScrollableFrame(
            container,
            fg_color=get_color("surface")
        )
        self.scroll_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Add face entries
        self.create_face_entries()
        
        # Create buttons
        self.create_buttons(container)
    
    def create_face_entries(self):
        """Create checkbox entries for each face"""
        for name in face_database.keys():
            # Create frame for entry
            frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            frame.pack(fill="x", pady=2)
            
            # Create checkbox
            checkbox = ctk.CTkCheckBox(
                frame,
                text=name,
                font=get_font(),
                fg_color=get_color("primary")
            )
            checkbox.pack(side="left", padx=10)
            
            self.face_entries[name] = checkbox
    
    def create_buttons(self, container):
        """Create action buttons"""
        button_frame = ctk.CTkFrame(container, fg_color="transparent")
        button_frame.pack(fill="x")
        
        delete_button = ctk.CTkButton(
            button_frame,
            text="Delete Selected",
            command=self.delete_selected,
            font=get_font(),
            fg_color=get_color("error")
        )
        delete_button.pack(side="right", padx=5)
        
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Close",
            command=self.destroy,
            font=get_font()
        )
        cancel_button.pack(side="right", padx=5)
    
    def delete_selected(self):
        """Delete selected faces"""
        selected = [name for name, cb in self.face_entries.items()
                   if cb.get()]
        
        if not selected:
            CTkMessagebox(
                self,
                title="Info",
                message="No faces selected",
                icon="info"
            )
            return
        
        # Confirm deletion
        names = "\n".join(selected)
        confirm = CTkMessagebox(
            self,
            title="Confirm Delete",
            message=f"Are you sure you want to delete these faces?\n\n{names}",
            icon="warning",
            option_1="Cancel",
            option_2="Delete"
        )
        
        if confirm.get() == "Delete":
            try:
                # Remove from database
                for name in selected:
                    del face_database[name]
                    # Remove from UI
                    self.face_entries[name].pack_forget()
                    del self.face_entries[name]
                
                # Save changes
                save_face_database(face_database)
                
                CTkMessagebox(
                    self,
                    title="Success",
                    message="Selected faces deleted successfully",
                    icon="check"
                )
                
            except Exception as e:
                CTkMessagebox(
                    self,
                    title="Error",
                    message=f"Error deleting faces: {str(e)}",
                    icon="cancel"
                )

def show_saved_faces(parent):
    """Show saved faces dialog"""
    dialog = SavedFacesDialog(parent)
    parent.wait_window(dialog)

def show_attendance_logs(parent):
    """Show attendance logs dialog"""
    dialog = BaseDialog(parent, "Attendance Logs", 600, 400)
    
    # Create text widget
    text = ctk.CTkTextbox(
        dialog,
        font=get_font()
    )
    text.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Load and display logs
    log_path = "attendance_records"
    if os.path.exists(log_path):
        for file in sorted(os.listdir(log_path), reverse=True):
            if file.endswith(".csv"):
                text.insert("end", f"=== {file} ===\n")
                with open(os.path.join(log_path, file), 'r') as f:
                    text.insert("end", f.read() + "\n")
    
    dialog.wait_window()