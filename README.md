# Face Recognition Attendance System

## Project Structure

```
.
├── src/                    # Source code
│   ├── attendance/        # Attendance tracking
│   ├── config/           # Configuration files
│   ├── database/         # Database operations
│   ├── face_recognition/ # Face recognition logic
│   ├── tracking/         # Face tracking
│   ├── ui/              # User interface
│   └── utils/           # Utility functions
├── data/                # Data files
├── documentation/       # Project documentation
├── tests/              # Test files
├── tools/              # Helper tools and scripts
└── scripts/            # Maintenance scripts
```

## Setup

1. Install dependencies:
```bash
pip install -e .
```

2. Run the application:
```bash
python src/main.py
```

## Development

The project uses a modular architecture with clear separation of concerns:

- Face recognition and tracking in dedicated modules
- Database operations isolated
- UI components separated
- Utility functions organized by purpose

## Documentation

See the `documentation/` directory for detailed technical documentation.