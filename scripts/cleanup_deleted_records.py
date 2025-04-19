#!/usr/bin/env python3

import os
import sys
import argparse
from datetime import datetime
from src.database.db_operations import DatabaseOperations
from src.utils.delete_manager import DeleteManager

def cleanup_expired_records(retention_days: int, dry_run: bool = False):
    """
    Clean up expired deleted records
    
    Args:
        retention_days: Number of days to keep deleted records
        dry_run: If True, only show what would be deleted without actually deleting
    """
    db = DatabaseOperations()
    delete_manager = DeleteManager(db.session)
    
    print(f"\nChecking for records deleted more than {retention_days} days ago...")
    
    # Get expired records info
    deleted_users = db.get_deleted_users()
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
    expired_users = [u for u in deleted_users if u.deleted_at < cutoff_date]
    
    if not expired_users:
        print("No expired records found")
        return
    
    print(f"\nFound {len(expired_users)} expired users:")
    for user in expired_users:
        days_deleted = (datetime.utcnow() - user.deleted_at).days
        stats = db.get_user_stats(user.id)
        print(f"\n- {user.name}:")
        print(f"  * Deleted: {user.deleted_at.strftime('%Y-%m-%d')} ({days_deleted} days ago)")
        print(f"  * Face samples: {stats['face_samples']}")
        print(f"  * Recognition events: {stats['recognition_events']}")
    
    if dry_run:
        print("\nDRY RUN - No records will be deleted")
        return
    
    # Confirm deletion
    response = input("\nPermanently delete these records? (yes/no): ")
    if response.lower() != 'yes':
        print("Cleanup cancelled")
        return
    
    # Perform cleanup
    print("\nPerforming cleanup...")
    
    # Clean up files first
    file_results = delete_manager.cleanup_expired(retention_days)
    print(f"Removed {file_results['files_deleted']} archived directories")
    
    # Then clean up database records
    db_results = db.cleanup_deleted_records(retention_days)
    print(f"Removed {db_results['users_removed']} users")
    print(f"Removed {db_results['samples_removed']} face samples")
    print(f"Removed {db_results['events_removed']} recognition events")
    
    print("\nCleanup completed successfully")

def main():
    parser = argparse.ArgumentParser(
        description="Clean up expired deleted records from the face recognition system"
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days to keep deleted records (default: 30)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )
    
    args = parser.parse_args()
    
    try:
        cleanup_expired_records(args.days, args.dry_run)
    except KeyboardInterrupt:
        print("\nCleanup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during cleanup: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()