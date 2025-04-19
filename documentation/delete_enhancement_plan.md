# Face Delete Enhancement Plan

## Current Issues
1. Basic confirmation dialog using generic input
2. No visual feedback after deletion
3. Fragile selection mechanism
4. Poor error handling
5. No multi-select capability
6. No undo functionality
7. Incomplete database cleanup

## Proposed Enhancements

### 1. UI Improvements
- Create custom confirmation dialog showing:
  * User name
  * Registration date
  * Number of recognition events
  * Recent attendance records
- Implement proper selection mechanism using ListView
- Add multi-select support with shift/ctrl clicking
- Show loading indicator during deletion
- Display success/error messages using toast notifications
- Add undo button in success notification

### 2. Database Integration
- Create unified delete operation that handles:
  * Face database entries
  * SQL database records
  * Face image files
- Implement soft delete mechanism:
  * Add deleted_at timestamp to User table
  * Move face images to archive directory
  * Preserve historical attendance records
- Add transaction support for atomic operations
- Implement cascading archives for related data

### 3. New Features
- Recycle Bin
  * 30-day retention period
  * Bulk restore capability
  * Automatic cleanup of expired items
- Bulk Operations
  * Select multiple faces
  * Show batch deletion progress
  * All-or-nothing transaction
- Audit Logging
  * Track all delete/restore operations
  * Include timestamp and operator
  * Exportable audit trail

## Implementation Steps

1. Database Updates
```sql
-- Add soft delete support
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP;
ALTER TABLE face_samples ADD COLUMN deleted_at TIMESTAMP;
CREATE TABLE delete_audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(50),
    details JSONB,
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

2. File System Organization
```
faces/
  active/       # Current face images
  archived/     # Soft deleted images
    {user_id}/  # Organized by user
      {timestamp}/  # Archive timestamp
logs/
  audit/        # Delete audit logs
```

3. Code Structure
```python
class DeleteManager:
    def delete_users(self, user_ids: List[int], archive: bool = True)
    def restore_users(self, user_ids: List[int])
    def cleanup_expired()

class DeleteUI:
    def show_delete_dialog(self, selected_users: List[User])
    def show_delete_progress(self, total: int)
    def show_success_toast(self, count: int, allow_undo: bool)
```

## Migration Plan

1. Create new database columns and tables
2. Set up archive directory structure
3. Update face database to support soft deletes
4. Implement new UI components
5. Add delete manager logic
6. Update existing delete calls
7. Add undo/restore functionality
8. Implement cleanup job

## Security Considerations

1. Add user permission checks for delete operations
2. Validate all user input
3. Ensure atomic transactions
4. Maintain audit trail
5. Implement proper error handling

## Testing Plan

1. Unit Tests
   - DeleteManager operations
   - Database transactions
   - File system operations

2. Integration Tests
   - End-to-end delete flow
   - Restore operations
   - Cleanup job

3. UI Tests
   - Selection mechanism
   - Progress indicators
   - Error handling
   - Undo functionality

## Future Improvements

1. Add batch operation scheduling
2. Implement deletion policies
3. Add custom retention periods
4. Create detailed audit reports
5. Add recovery from backups