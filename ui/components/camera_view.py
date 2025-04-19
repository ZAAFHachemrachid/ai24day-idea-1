import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
from ..theme import get_color, get_font, get_padding

class CameraFrame(ctk.CTkFrame):
    def __init__(self, parent, width=640, height=480):
        super().__init__(
            parent,
            width=width,
            height=height,
            fg_color=get_color("surface")
        )
        
        # Ensure the frame maintains its size
        self.grid_propagate(False)
        
        # Create canvas for displaying camera feed
        self.canvas = ctk.CTkCanvas(
            self,
            width=width,
            height=height,
            bg=get_color("background")
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.current_image = None
    
    def update_frame(self, frame=None):
        """Update the camera frame with new image"""
        if frame is not None:
            # Convert frame to PIL Image
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(frame)
            
            # Resize image to fit frame while maintaining aspect ratio
            target_width = self.winfo_width()
            target_height = self.winfo_height()
            
            # Calculate scaling factor
            scale_w = target_width / image.width
            scale_h = target_height / image.height
            scale = min(scale_w, scale_h)
            
            # Calculate new dimensions
            new_width = int(image.width * scale)
            new_height = int(image.height * scale)
            
            # Resize image
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.current_image = ImageTk.PhotoImage(image)
            
            # Clear canvas and draw new image
            self.canvas.delete("all")
            
            # Calculate position to center image
            x = (target_width - new_width) // 2
            y = (target_height - new_height) // 2
            
            self.canvas.create_image(
                x, y,
                anchor="nw",
                image=self.current_image
            )
        else:
            # Clear canvas if no frame provided
            self.canvas.delete("all")
            self.current_image = None

class CameraGridView(ctk.CTkFrame):
    def __init__(self, parent, camera_manager):
        super().__init__(
            parent,
            fg_color="transparent"
        )
        
        self.camera_manager = camera_manager
        self.camera_frames = {}
        
        # Initialize grid
        self.setup_grid()
    
    def setup_grid(self):
        """Setup the camera grid layout"""
        # Calculate grid dimensions based on number of cameras
        num_cameras = len(self.camera_manager.cameras)
        if num_cameras <= 1:
            rows, cols = 1, 1
        elif num_cameras <= 4:
            rows, cols = 2, 2
        else:
            rows = (num_cameras + 2) // 3
            cols = 3
        
        # Configure grid
        for i in range(rows):
            self.grid_rowconfigure(i, weight=1)
        for i in range(cols):
            self.grid_columnconfigure(i, weight=1)
        
        # Create camera frames
        for i, (camera_id, camera) in enumerate(self.camera_manager.cameras.items()):
            row = i // cols
            col = i % cols
            
            frame = CameraFrame(self)
            frame.grid(
                row=row,
                column=col,
                padx=get_padding("small"),
                pady=get_padding("small"),
                sticky="nsew"
            )
            
            self.camera_frames[camera_id] = frame
    
    def update_frame(self, frame=None):
        """Update all camera frames"""
        if frame is not None:
            # Single frame provided - update first camera
            first_frame = next(iter(self.camera_frames.values()), None)
            if first_frame:
                first_frame.update_frame(frame)
        else:
            # Update all cameras
            frames = self.camera_manager.get_all_frames()
            for camera_id, frame in frames.items():
                if camera_id in self.camera_frames:
                    self.camera_frames[camera_id].update_frame(frame)

class SingleCameraView(ctk.CTkFrame):
    def __init__(self, parent, camera_manager, camera_id):
        super().__init__(
            parent,
            fg_color="transparent"
        )
        
        self.camera_manager = camera_manager
        self.camera_id = camera_id
        
        # Create camera frame
        self.camera_frame = CameraFrame(self)
        self.camera_frame.pack(
            fill="both",
            expand=True,
            padx=get_padding("small"),
            pady=get_padding("small")
        )
    
    def update_frame(self, frame=None):
        """Update camera frame"""
        if frame is not None:
            self.camera_frame.update_frame(frame)
        else:
            frame = self.camera_manager.get_frame(self.camera_id)
            if frame is not None:
                self.camera_frame.update_frame(frame)