"""
Face Recognition System with CustomTkinter UI
"""
from ui.app import FaceRecognitionApp

def launch_ui():
    """Launch the face recognition UI application"""
    app = FaceRecognitionApp()
    app.mainloop()

if __name__ == "__main__":
    launch_ui()