import shutil
import os
import zipfile
import sqlite3
from datetime import datetime
from fastapi import HTTPException

DB_PATH = "./ecommerce.db"
BACKUP_DIR = "./backups"

def ensure_backup_dir():
    """Create backup directory if it doesn't exist"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        print(f"Created backup directory: {BACKUP_DIR}")

async def backup_database():
    """Create a backup of the database"""
    try:
        ensure_backup_dir()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"ecommerce_backup_{timestamp}.db"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        # Close any existing connections
        # Create backup by copying file
        shutil.copy2(DB_PATH, backup_path)
        
        # Also create a compressed version
        zip_filename = f"ecommerce_backup_{timestamp}.zip"
        zip_path = os.path.join(BACKUP_DIR, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(backup_path, os.path.basename(backup_path))
        
        # Delete the uncompressed backup to save space
        os.remove(backup_path)
        
        print(f"✅ Backup created: {zip_filename}")
        
        return {
            "success": True,
            "filename": zip_filename,
            "path": zip_path,
            "size": os.path.getsize(zip_path),
            "timestamp": timestamp
        }
    except Exception as e:
        print(f"❌ Backup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")

async def restore_database(backup_file_path: str):
    """Restore database from backup"""
    try:
        # Check if backup file exists
        if not os.path.exists(backup_file_path):
            raise HTTPException(status_code=404, detail=f"Backup file not found: {backup_file_path}")
        
        # If it's a zip file, extract first
        temp_db_path = None
        if backup_file_path.endswith('.zip'):
            temp_db_path = backup_file_path.replace('.zip', '_temp.db')
            with zipfile.ZipFile(backup_file_path, 'r') as zipf:
                # Extract the .db file
                for file in zipf.namelist():
                    if file.endswith('.db'):
                        with open(temp_db_path, 'wb') as f:
                            f.write(zipf.read(file))
                        break
            backup_file_path = temp_db_path
        
        # Validate the backup file is a valid SQLite database
        try:
            conn = sqlite3.connect(backup_file_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"Backup contains {len(tables)} tables")
            conn.close()
        except Exception as e:
            if temp_db_path and os.path.exists(temp_db_path):
                os.remove(temp_db_path)
            raise HTTPException(status_code=400, detail=f"Invalid backup file: {str(e)}")
        
        # Backup current database before restore
        current_backup = await backup_database()
        
        # Restore the backup
        shutil.copy2(backup_file_path, DB_PATH)
        
        # Clean up temp file if created
        if temp_db_path and os.path.exists(temp_db_path):
            os.remove(temp_db_path)
        
        print(f"✅ Database restored successfully from {backup_file_path}")
        
        return {
            "success": True,
            "message": "Database restored successfully",
            "backup_created_before_restore": current_backup
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Restore failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")

async def list_backups():
    """List all available backups"""
    try:
        ensure_backup_dir()
        backups = []
        
        for filename in os.listdir(BACKUP_DIR):
            if filename.endswith('.zip'):
                file_path = os.path.join(BACKUP_DIR, filename)
                stat = os.stat(file_path)
                backups.append({
                    "filename": filename,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat()
                })
        
        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        
        return backups
    except Exception as e:
        print(f"❌ Failed to list backups: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list backups: {str(e)}")