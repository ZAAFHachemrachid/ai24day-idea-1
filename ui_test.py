import customtkinter as ctk

class TestApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("CustomTkinter Test")
        self.geometry("800x600")
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create a frame
        self.frame = ctk.CTkFrame(self)
        self.frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add some test widgets
        self.label = ctk.CTkLabel(
            self.frame, 
            text="CustomTkinter Test",
            font=("Helvetica", 24)
        )
        self.label.pack(pady=20)
        
        self.button = ctk.CTkButton(
            self.frame,
            text="Test Button",
            command=self.button_callback
        )
        self.button.pack(pady=10)
        
    def button_callback(self):
        print("Button clicked!")

if __name__ == "__main__":
    app = TestApp()
    app.mainloop()