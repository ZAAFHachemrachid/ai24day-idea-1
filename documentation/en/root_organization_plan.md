# Root Directory Organization Plan

## Current Root Structure Analysis

### Source Code Files
- `main.py` - Main application entry point
- `config.py` - Configuration file
- `ui.py`, `ui_test.py`, `ui_old.py` - UI-related files
- `utils.py` - Utility functions
- `test_custom_ui.py` - UI tests

### Documentation Files
- Various `.md` files for documentation
- Documentation in different languages (e.g. `documentation_ar.md`)

### Build Files
- `main.spec` - PyInstaller spec file
- `build/` directory

### Data Files
- `database.sqlite`
- `re.txt`
- `requirements.txt`

## Reorganization Recommendations

### 1. Move Source Code Files
Move all source code files to `src/` directory:
- `main.py` → `src/main.py`
- `config.py` → `src/config/config.py`
- `utils.py` → `src/utils/utils.py`
- UI files into `src/ui/`

### 2. Consolidate Documentation
Move all documentation files to `documentation/` directory:
- All `.md` files except README.md
- Create subdirectories for different languages (en/, ar/)

### 3. Organize Tests
Move all test files to `tests/` directory:
- `test_custom_ui.py` → `tests/ui/`
- `ui_test.py` → `tests/ui/`

### 4. Clean Build Artifacts
- Remove or ignore `build/` directory
- Keep `main.spec` in root (needed for builds)

### 5. Data Management
- Move database file to `data/` directory
- Create separate directories for different types of data

### 6. Root Level Should Contain Only
1. `src/` - All source code
2. `tests/` - All tests
3. `documentation/` - All documentation
4. `data/` - All data files
5. Essential root files:
   - `requirements.txt`
   - `README.md`
   - `.gitignore`
   - `main.spec`

## Implementation Steps
1. Create new directories if needed
2. Move files to their new locations
3. Update import statements and file references
4. Update .gitignore with new paths
5. Test application after reorganization

## Benefits
- Cleaner root directory
- Better organized codebase
- Easier maintenance
- Clear separation of concerns
- Improved project navigation

## Next Steps
After approval:
1. Switch to Code mode
2. Create necessary directories
3. Move files to new locations
4. Update file references
5. Test the application