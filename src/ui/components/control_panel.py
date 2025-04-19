import customtkinter as ctk
from datetime import datetime
from typing import List, Optional, Callable
from ..theme import get_color, get_font, get_padding
from ...face_recognition.initializers import face_database, save_face_database
from ...utils.delete_manager import DeleteManager
from ...database.db_operations import DatabaseOperations
from ...utils.presence_verifier import PresenceVerifier

class StatsPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(
            parent,
            fg_color=get_color("surface")
        )
        
        # Configure title
        self.title = ctk.CTkLabel(
            self,
            text="Performance",
            font=get_font("large")
        )
        self.title.pack(padx=get_padding(), pady=get_padding("small"))
        
        # Stats labels
        self.fps_label = ctk.CTkLabel(
            self,
            text="FPS: 0",
            font=get_font()
        )
        self.fps_label.pack(padx=get_padding(), pady=get_padding("small"))
        
        self.detection_label = ctk.CTkLabel(
            self,
            text="Detection: 0ms",
            font=get_font()
        )
        self.detection_label.pack(padx=get_padding(), pady=get_padding("small"))
        
        self.recognition_label = ctk.CTkLabel(
            self,
            text="Recognition: 0ms",
            font=get_font()
        )
        self.recognition_label.pack(padx=get_padding(), pady=get_padding("small"))

class StatusPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(
            parent,
            fg_color=get_color("surface")
        )
        
        # Configure title
        self.title = ctk.CTkLabel(
            self,
            text="Status",
            font=get_font("large")
        )
        self.title.pack(padx=get_padding(), pady=get_padding("small"))
        
        # Status labels
        self.status_label = ctk.CTkLabel(
            self,
            text="Initializing...",
            font=get_font()
        )
        self.status_label.pack(padx=get_padding(), pady=get_padding("small"))
        
        self.face_count_label = ctk.CTkLabel(
            self,
            text="Faces: 0",
            font=get_font()
        )
        self.face_count_label.pack(padx=get_padding(), pady=get_padding("small"))
        
        self.presence_label = ctk.CTkLabel(
            self,
            text="Present: None",
            font=get_font()
        )
        self.presence_label.pack(padx=get_padding(), pady=get_padding("small"))
        
        self.away_label = ctk.CTkLabel(
            self,
            text="Away: None",
            font=get_font()
        )
        self.away_label.pack(padx=get_padding(), pady=get_padding("small"))

class DeleteConfirmDialog(ctk.CTkToplevel):
    def __init__(self, parent, users: List[dict], on_confirm: Callable):
        super().__init__(parent)
        
        self.title("Confirm Deletion")
        self.geometry("400x500")
        
        # Header
        header = ctk.CTkLabel(
            self,
            text="Delete Selected Users",
            font=get_font("large")
        )
        header.pack(padx=get_padding(), pady=get_padding())
        
        # User list
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(fill="both", expand=True, padx=get_padding(), pady=get_padding("small"))
        
        for user in users:
            user_frame = ctk.CTkFrame(list_frame)
            user_frame.pack(fill="x", padx=get_padding("small"), pady=get_padding("small"))
            
            ctk.CTkLabel(
                user_frame,
                text=f"Name: {user['name']}",
                font=get_font()
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                user_frame,
                text=f"Registered: {user['created_at'].strftime('%Y-%m-%d')}",
                font=get_font("small")
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                user_frame,
                text=f"Face Samples: {user['sample_count']}",
                font=get_font("small")
            ).pack(anchor="w")
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=get_padding(), pady=get_padding())
        
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            font=get_font()
        ).pack(side="left", padx=get_padding("small"))
        
        ctk.CTkButton(
            button_frame,
            text="Confirm Delete",
            command=lambda: [on_confirm(), self.destroy()],
            font=get_font(),
            fg_color=get_color("error")
        ).pack(side="right", padx=get_padding("small"))

class FaceListPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(
            parent,
            fg_color=get_color("surface")
        )
        
        self.db = DatabaseOperations()
        self.delete_manager = DeleteManager(self.db.session)
        self.presence_verifier = PresenceVerifier()
        self.selected_users = set()
        self.undetected_faces = set()  # Keep track of faces not detected
        
        # Configure title
        self.title = ctk.CTkLabel(
            self,
            text="Saved Faces",
            font=get_font("large")
        )
        self.title.pack(padx=get_padding(), pady=get_padding("small"))
        
        # Face listbox with selection
        self.face_list = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )
        self.face_list.pack(
            fill="both",
            expand=True,
            padx=get_padding(),
            pady=get_padding("small")
        )
        
        # Action buttons
        self.button_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        self.button_frame.pack(
            fill="x",
            padx=get_padding(),
            pady=get_padding("small")
        )
        
        self.delete_button = ctk.CTkButton(
            self.button_frame,
            text="Delete Selected",
            command=self.delete_faces,
            font=get_font(),
            state="disabled"
        )
        self.delete_button.pack(
            side="left",
            padx=(0, get_padding("small"))
        )
        
        self.restore_button = ctk.CTkButton(
            self.button_frame,
            text="Restore",
            command=self.restore_faces,
            font=get_font(),
            state="disabled"
        )
        self.restore_button.pack(side="left")
        
        # Status message
        self.status_label = ctk.CTkLabel(
            self,
            text="",
            font=get_font("small"),
            text_color=get_color("error")
        )
        self.status_label.pack(
            padx=get_padding(),
            pady=(0, get_padding("small"))
        )
        
        self.update_face_list()
    
    def toggle_selection(self, user_id: int, checkbox: ctk.CTkCheckBox):
        """Handle user selection toggle"""
        if checkbox.get():
            self.selected_users.add(user_id)
        else:
            self.selected_users.remove(user_id)
            
        # Update button states
        has_selection = len(self.selected_users) > 0
        self.delete_button.configure(state="normal" if has_selection else "disabled")
        self.restore_button.configure(state="normal" if has_selection else "disabled")
    
    def update_face_list(self, detected_faces: set = None):
        """
        Update the face list with current database entries
        
        Args:
            detected_faces: Set of user IDs currently detected in the camera feed
        """
        # Update detected faces list
        if detected_faces is not None:
            self.undetected_faces = {
                user_id for user_id in face_database.keys()
                if user_id not in detected_faces
            }
            
        # Clear existing list
        for widget in self.face_list.winfo_children():
            widget.destroy()
        
        # Add users to list
        users = self.db.get_all_users()
        active_users = [u for u in users if not u.deleted_at]
        deleted_users = [u for u in users if u.deleted_at]
        
        if active_users:
            ctk.CTkLabel(
                self.face_list,
                text="Active Users",
                font=get_font("medium")
            ).pack(anchor="w", pady=(0, get_padding("small")))
            
            for user in active_users:
                is_detected = str(user.id) not in self.undetected_faces
                self.add_user_item(user, is_deleted=False, is_detected=is_detected)
        
        if deleted_users:
            ctk.CTkLabel(
                self.face_list,
                text="Recently Deleted",
                font=get_font("medium")
            ).pack(anchor="w", pady=get_padding("small"))
            
            for user in deleted_users:
                self.add_user_item(user, is_deleted=True)
    
    def add_user_item(self, user, is_deleted: bool = False, is_detected: bool = True):
        """Add a user item to the list"""
        frame = ctk.CTkFrame(self.face_list, fg_color="transparent")
        frame.pack(fill="x", pady=1)
        
        checkbox = ctk.CTkCheckBox(
            frame,
            text="",
            command=lambda: self.toggle_selection(user.id, checkbox),
            font=get_font()
        )
        checkbox.pack(side="left")
        
        # Determine text color based on status
        if is_deleted:
            name_color = get_color("text_disabled")
        elif not is_detected:
            name_color = get_color("error")
        else:
            name_color = get_color("text")
            
        # Create name label with status indicator
        name_frame = ctk.CTkFrame(frame, fg_color="transparent")
        name_frame.pack(side="left", fill="x", expand=True, padx=get_padding("small"))
        
        name_label = ctk.CTkLabel(
            name_frame,
            text=user.name,
            font=get_font(),
            text_color=name_color
        )
        name_label.pack(side="left")
        
        # Add status indicators
        if is_deleted:
            deleted_days = (datetime.utcnow() - user.deleted_at).days
            ctk.CTkLabel(
                name_frame,
                text=f"(deleted {deleted_days}d ago)",
                font=get_font("small"),
                text_color=get_color("text_disabled")
            ).pack(side="right")
        elif not is_detected:
            ctk.CTkLabel(
                name_frame,
                text="(not detected)",
                font=get_font("small"),
                text_color=get_color("error")
            ).pack(side="right")
    
    def show_status(self, message: str, is_error: bool = False):
        """Show status message"""
        color = get_color("error") if is_error else get_color("success")
        self.status_label.configure(text=message, text_color=color)
        
        # Clear message after 5 seconds
        self.after(5000, lambda: self.status_label.configure(text=""))
    
    def delete_faces(self):
        """Delete selected faces"""
        if not self.selected_users:
            return
            
        # Get user details for confirmation
        users_to_delete = []
        for user_id in self.selected_users:
            user = self.db.get_user(user_id)
            if user:
                users_to_delete.append({
                    'id': user.id,
                    'name': user.name,
                    'created_at': user.created_at,
                    'sample_count': len(user.face_samples)
                })
        
        # Show confirmation dialog
        def confirm_delete():
            results = self.delete_manager.delete_users(
                [u['id'] for u in users_to_delete]
            )
            
            if results['success_count'] > 0:
                self.show_status(
                    f"Successfully deleted {results['success_count']} users"
                )
                self.selected_users.clear()
                self.update_face_list()
            
            if results['error_count'] > 0:
                self.show_status(
                    f"Failed to delete {results['error_count']} users",
                    is_error=True
                )
        
        DeleteConfirmDialog(self, users_to_delete, confirm_delete)
    
    def restore_faces(self):
        """Restore selected faces"""
        if not self.selected_users:
            return
            
        results = self.delete_manager.restore_users(list(self.selected_users))
        
        if results['success_count'] > 0:
            self.show_status(
                f"Successfully restored {results['success_count']} users"
            )
            self.selected_users.clear()
            self.update_face_list()
        
        if results['error_count'] > 0:
            self.show_status(
                f"Failed to restore {results['error_count']} users",
                is_error=True
            )

class ControlPanel(ctk.CTkFrame):
    def __init__(self, parent, callbacks):
        super().__init__(
            parent,
            width=300,
            fg_color="transparent"
        )
        
        # Initialize control variables
        self.detect_eyes_var = ctk.BooleanVar(value=True)
        self.detect_mouth_var = ctk.BooleanVar(value=True)
        self.color_var = ctk.StringVar(value="green")
        
        # Create components
        self.setup_stats_panel()
        self.setup_status_panel()
        self.setup_action_buttons(callbacks)
        self.setup_face_list()
    
    def setup_stats_panel(self):
        """Setup performance statistics panel"""
        self.stats_panel = StatsPanel(self)
        self.stats_panel.pack(
            fill="x",
            padx=get_padding("small"),
            pady=get_padding("small")
        )
    
    def setup_status_panel(self):
        """Setup status information panel"""
        self.status_panel = StatusPanel(self)
        self.status_panel.pack(
            fill="x",
            padx=get_padding("small"),
            pady=get_padding("small")
        )
    
    def setup_action_buttons(self, callbacks):
        """Setup action buttons"""
        # Create frame for buttons
        buttons = ctk.CTkFrame(
            self,
            fg_color=get_color("surface")
        )
        buttons.pack(
            fill="x",
            padx=get_padding("small"),
            pady=get_padding("small")
        )
        
        # Add title
        title = ctk.CTkLabel(
            buttons,
            text="Actions",
            font=get_font("large")
        )
        title.pack(padx=get_padding(), pady=get_padding("small"))
        
        # Add buttons
        for text, callback in [
            ("Add Camera", callbacks['add_camera']),
            ("Register New Face", callbacks['register']),
            ("View Saved Faces", callbacks['view_faces']),
            ("View Attendance Logs", callbacks['view_logs'])
        ]:
            ctk.CTkButton(
                buttons,
                text=text,
                command=callback,
                font=get_font()
            ).pack(
                fill="x",
                padx=get_padding(),
                pady=get_padding("small")
            )
    
    def setup_face_list(self):
        """Setup face list panel"""
        self.face_list = FaceListPanel(self)
        self.face_list.pack(
            fill="both",
            expand=True,
            padx=get_padding("small"),
            pady=get_padding("small")
        )
    
    def update_stats(self, fps, detection_time, recognition_time):
        """Update performance statistics"""
        self.stats_panel.fps_label.configure(text=f"FPS: {fps:.1f}")
        self.stats_panel.detection_label.configure(text=f"Detection: {detection_time:.1f}ms")
        self.stats_panel.recognition_label.configure(text=f"Recognition: {recognition_time:.1f}ms")
    
    def update_status(self, status_text, face_count, present_text, away_text):
        """Update status information"""
        self.status_panel.status_label.configure(text=status_text)
        self.status_panel.face_count_label.configure(text=f"Faces: {face_count}")
        self.status_panel.presence_label.configure(text=f"At Desk: {present_text}")
        self.status_panel.away_label.configure(text=f"Away: {away_text}")
    
    def get_feature_detection_options(self):
        """Get current feature detection options"""
        return {
            'detect_eyes': self.detect_eyes_var.get(),
            'detect_mouth': self.detect_mouth_var.get(),
            'color': self.color_var.get()
        }