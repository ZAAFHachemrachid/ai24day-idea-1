# Saved Faces Dialog Enhancement Plan

## Overview
Enhance the saved faces dialog with checkboxes for selection and delete functionality for managing stored face data.

## Components

### SavedFacesDialog Class
```python
class SavedFacesDialog(BaseDialog):
    def __init__(self, parent):
        super().__init__(parent, "Saved Faces", 400, 500)
        self.face_entries = {}  # Store checkbox widgets
```

### UI Layout
1. Scrollable Frame Container
   - Uses `CTkScrollableFrame` for scrollable list
   - Fixed width, expandable height

2. Face Entry Components
   - Checkbox for selection
   - Name label
   - Horizontal layout per entry

3. Control Buttons
   - Delete button (bottom of dialog)
   - Cancel button

## Implementation Steps

1. Create SavedFacesDialog Class:
   ```python
   def setup_ui(self):
       # Create scrollable container
       self.scroll_frame = ctk.CTkScrollableFrame(self)
       self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(20,10))
       
       # Add face entries
       self.create_face_entries()
       
       # Add buttons
       self.create_buttons()
   ```

2. Face Entry Creation:
   ```python
   def create_face_entry(self, name):
       frame = ctk.CTkFrame(self.scroll_frame)
       checkbox = ctk.CTkCheckBox(frame, text=name)
       self.face_entries[name] = checkbox
   ```

3. Delete Functionality:
   ```python
   def delete_selected(self):
       selected = [name for name, cb in self.face_entries.items() 
                  if cb.get()]
       if selected:
           self.confirm_delete(selected)
   ```

4. Database Integration:
   - Load faces from face_database
   - Remove selected entries
   - Save updated database

## User Flow
1. User opens Saved Faces dialog
2. List of faces displayed with checkboxes
3. User selects faces to delete
4. Clicks Delete button
5. Confirmation dialog shown
6. On confirm, faces removed and database updated

## Implementation Details
1. Face Database Management
   ```python
   def update_database(self, to_delete):
       for name in to_delete:
           del face_database[name]
       save_face_database(face_database)
   ```

2. Confirmation Dialog
   ```python
   def confirm_delete(self, selected):
       names = "\n".join(selected)
       message = f"Delete selected faces?\n\n{names}"
       if CTkMessagebox(...).get():
           self.update_database(selected)
   ```

## Next Steps
1. Switch to Code mode
2. Implement SavedFacesDialog class
3. Update show_saved_faces function
4. Test deletion functionality
5. Add error handling

## Migration Plan
1. Create new dialog implementation
2. Test in isolation
3. Replace existing show_saved_faces
4. Verify database updates
5. Add user feedback for actions