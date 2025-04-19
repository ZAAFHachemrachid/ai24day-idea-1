import customtkinter as ctk

# Color scheme
COLORS = {
    "primary": {"light": "#007BFF", "dark": "#0056B3"},
    "secondary": {"light": "#6C757D", "dark": "#495057"},
    "success": {"light": "#28A745", "dark": "#1E7E34"},
    "warning": {"light": "#FFC107", "dark": "#D39E00"},
    "danger": {"light": "#DC3545", "dark": "#BD2130"},
    "background": {"light": "#F8F9FA", "dark": "#212529"},
    "surface": {"light": "#FFFFFF", "dark": "#343A40"}
}

# Theme configuration
THEME = {
    "font": {
        "family": "Helvetica",
        "size": {
            "small": 12,
            "medium": 14,
            "large": 16,
            "title": 24
        }
    },
    "corner_radius": 8,
    "button_height": 35,
    "padding": {
        "small": 5,
        "medium": 10,
        "large": 20
    }
}

def setup_theme():
    """Configure the CustomTkinter theme settings"""
    # Set appearance mode (dark/light)
    ctk.set_appearance_mode("dark")
    
    # Set default color theme
    ctk.set_default_color_theme("blue")
    
    # Configure widget defaults
    ctk.set_widget_scaling(1.0)  # Adjust for high DPI displays
    ctk.set_window_scaling(1.0)  # Adjust window scaling

def get_color(name: str, mode: str = None) -> str:
    """Get a color from the theme color scheme
    
    Args:
        name: Color name (primary, secondary, etc.)
        mode: Light or dark mode (default: current appearance mode)
    
    Returns:
        str: Color hex code
    """
    if mode is None:
        mode = "dark" if ctk.get_appearance_mode() == "Dark" else "light"
    return COLORS.get(name, COLORS["primary"])[mode]

def get_font(size: str = "medium") -> tuple:
    """Get a font configuration tuple
    
    Args:
        size: Font size name (small, medium, large, title)
    
    Returns:
        tuple: Font family and size
    """
    return (THEME["font"]["family"], THEME["font"]["size"][size])

def get_corner_radius() -> int:
    """Get the default corner radius for widgets"""
    return THEME["corner_radius"]

def get_padding(size: str = "medium") -> int:
    """Get padding value
    
    Args:
        size: Padding size name (small, medium, large)
    
    Returns:
        int: Padding value in pixels
    """
    return THEME["padding"][size]