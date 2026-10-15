from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
import os
from database import get_db
from auth import get_current_admin
import backup

router = APIRouter(prefix="/api/backup", tags=["Backup"])

@router.post("/create")
async def create_backup(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Create database backup (admin only)"""
    try:
        result = await backup.backup_database()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_backups(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """List all backups (admin only)"""
    try:
        backups = await backup.list_backups()
        return backups
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/restore")
async def restore_backup(
    backup_file: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Restore database from backup (admin only)"""
    try:
        # Construct full backup path
        backup_path = os.path.join(backup.BACKUP_DIR, backup_file)
        
        # Validate file exists
        if not os.path.exists(backup_path):
            raise HTTPException(status_code=404, detail=f"Backup file not found: {backup_file}")
        
        result = await backup.restore_database(backup_path)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import")
async def import_database(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Import database from .db file (admin only)"""
    try:
        if not file.filename.endswith('.db'):
            raise HTTPException(status_code=400, detail="Only .db files are allowed")
        
        # Save uploaded file
        import shutil
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Restore from the uploaded file
        result = await backup.restore_database(temp_path)
        
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{backup_file}")
async def download_backup(
    backup_file: str,
    current_user = Depends(get_current_admin)
):
    """Download backup file (admin only)"""
    try:
        backup_path = os.path.join(backup.BACKUP_DIR, backup_file)
        if not os.path.exists(backup_path):
            raise HTTPException(status_code=404, detail="Backup file not found")
        
        return FileResponse(
            backup_path,
            media_type='application/zip',
            filename=backup_file
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))