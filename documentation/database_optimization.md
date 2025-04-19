# Database Optimization Guide

## Overview

This guide details the optimization strategies for the SQLite database used in the face recognition attendance system.

## Database Schema Optimization

### Indexing Strategy

```sql
-- User Indexes
CREATE INDEX idx_users_name ON users(name);
CREATE INDEX idx_users_created_at ON users(created_at);

-- Face Samples Indexes
CREATE INDEX idx_face_samples_user_id ON face_samples(user_id);

-- Attendance Indexes
CREATE INDEX idx_attendance_user_date ON attendance(user_id, date);
CREATE INDEX idx_attendance_date ON attendance(date);
```

### Query Optimization

#### Common Queries
```sql
-- Efficient user lookup
SELECT id, name 
FROM users 
WHERE name LIKE ? 
LIMIT 1;

-- Optimized attendance check
SELECT a.* 
FROM attendance a 
WHERE a.user_id = ? 
  AND a.date = CURRENT_DATE;

-- Efficient face sample retrieval
SELECT fs.image_path 
FROM face_samples fs 
WHERE fs.user_id = ?;
```

## Connection Management

### Connection Pool Configuration
```python
def setup_database_pool():
    """Configure database connection pool"""
    engine = create_engine(
        'sqlite:///database.sqlite',
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800
    )
    return engine
```

### Session Management
```python
def get_session():
    """Get database session with retry mechanism"""
    retry_count = 3
    while retry_count > 0:
        try:
            session = Session()
            return session
        except Exception as e:
            retry_count -= 1
            time.sleep(1)
    raise DatabaseConnectionError("Failed to establish database connection")
```

## Performance Optimization

### Batch Operations
```python
def batch_insert_attendance(records):
    """Efficient batch insertion of attendance records"""
    session = get_session()
    try:
        session.bulk_save_objects(records)
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()
```

### Query Optimization Techniques

1. **Use EXISTS Instead of IN**
```python
# Instead of
SELECT * FROM users 
WHERE id IN (SELECT user_id FROM attendance WHERE date = CURRENT_DATE);

# Use
SELECT * FROM users u 
WHERE EXISTS (
    SELECT 1 
    FROM attendance a 
    WHERE a.user_id = u.id 
      AND a.date = CURRENT_DATE
);
```

2. **Efficient Pagination**
```python
def get_paginated_attendance(page=1, per_page=50):
    """Efficient pagination using keyset pagination"""
    query = (
        select(Attendance)
        .order_by(Attendance.id)
        .limit(per_page)
        .offset((page - 1) * per_page)
    )
    return session.execute(query).scalars().all()
```

## Maintenance Procedures

### Regular Optimization
```sql
-- Database optimization script
VACUUM;
ANALYZE;
REINDEX;
```

### Database Cleanup
```python
def cleanup_old_records():
    """Remove old attendance records"""
    cutoff_date = datetime.now() - timedelta(days=365)
    
    session = get_session()
    try:
        session.query(Attendance)\
            .filter(Attendance.date < cutoff_date)\
            .delete()
        session.commit()
    finally:
        session.close()
```

## Monitoring and Diagnostics

### Query Performance Monitoring
```python
def monitor_query_performance(query):
    """Monitor query execution time"""
    start_time = time.time()
    result = session.execute(query)
    execution_time = time.time() - start_time
    
    if execution_time > 1.0:  # Slow query threshold
        log_slow_query(query, execution_time)
    
    return result
```

### Database Health Checks
```python
def check_database_health():
    """Perform database health check"""
    checks = [
        check_connection_pool(),
        verify_indexes(),
        check_table_sizes(),
        analyze_query_performance()
    ]
    return all(checks)
```

## Backup Strategy

### Automated Backup
```python
def backup_database():
    """Create database backup"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'backups/database_{timestamp}.sqlite'
    
    # Create backup
    connection = sqlite3.connect('database.sqlite')
    backup = sqlite3.connect(backup_path)
    connection.backup(backup)
    
    # Compress backup
    with open(backup_path, 'rb') as f_in:
        with gzip.open(f'{backup_path}.gz', 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
```

### Backup Rotation
```python
def rotate_backups():
    """Maintain backup rotation policy"""
    backup_dir = 'backups'
    max_backups = 10
    
    backups = sorted(
        Path(backup_dir).glob('*.sqlite.gz'),
        key=lambda x: x.stat().st_mtime
    )
    
    # Remove old backups
    while len(backups) > max_backups:
        oldest = backups.pop(0)
        oldest.unlink()
```

## Error Handling

### Transaction Management
```python
@contextmanager
def transaction_scope():
    """Provide transaction scope with error handling"""
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()
```

### Recovery Procedures
```python
def recover_database():
    """Database recovery procedure"""
    steps = [
        verify_database_integrity(),
        repair_corrupted_tables(),
        rebuild_indexes(),
        validate_foreign_keys()
    ]
    
    for step in steps:
        try:
            step()
        except Exception as e:
            log_recovery_error(e)
            raise
```

## Best Practices

1. **Use Transactions Appropriately**
   - Wrap related operations in transactions
   - Keep transactions short
   - Handle deadlocks properly

2. **Index Management**
   - Create indexes for frequently queried columns
   - Remove unused indexes
   - Monitor index usage

3. **Regular Maintenance**
   - Schedule regular VACUUM operations
   - Monitor database size
   - Analyze query performance

4. **Error Handling**
   - Implement proper error recovery
   - Log database errors
   - Monitor connection pool health