"""
Database backup and restore utilities
"""
import os
import subprocess
import datetime
import logging
import shutil
import gzip
from pathlib import Path
from typing import Optional, List
from app.config import settings
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class BackupManager:
    """Database backup and restore manager"""
    
    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        self.max_local_backups = 7  # Keep 7 days of local backups
        
    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """Create a database backup"""
        if not backup_name:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"dreambig_backup_{timestamp}"
        
        backup_file = self.backup_dir / f"{backup_name}.sql"
        
        try:
            if settings.SQLALCHEMY_DATABASE_URI.startswith("postgresql"):
                self._create_postgres_backup(backup_file)
            elif settings.SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
                self._create_sqlite_backup(backup_file)
            else:
                raise ValueError("Unsupported database type for backup")
            
            # Compress the backup
            compressed_file = self._compress_backup(backup_file)
            
            # Clean up old backups
            self._cleanup_old_backups()
            
            logger.info(f"Backup created successfully: {compressed_file}")
            return str(compressed_file)
            
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            raise
    
    def _create_postgres_backup(self, backup_file: Path):
        """Create PostgreSQL backup using pg_dump"""
        db_url = settings.SQLALCHEMY_DATABASE_URI
        
        # Parse database URL
        # postgresql://user:password@host:port/database
        parts = db_url.replace("postgresql://", "").split("/")
        db_name = parts[1]
        user_host = parts[0].split("@")
        user_pass = user_host[0].split(":")
        host_port = user_host[1].split(":")
        
        user = user_pass[0]
        password = user_pass[1] if len(user_pass) > 1 else ""
        host = host_port[0]
        port = host_port[1] if len(host_port) > 1 else "5432"
        
        env = os.environ.copy()
        if password:
            env["PGPASSWORD"] = password
        
        cmd = [
            "pg_dump",
            "-h", host,
            "-p", port,
            "-U", user,
            "-d", db_name,
            "--no-password",
            "--verbose",
            "--clean",
            "--no-acl",
            "--no-owner",
            "-f", str(backup_file)
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"pg_dump failed: {result.stderr}")
    
    def _create_sqlite_backup(self, backup_file: Path):
        """Create SQLite backup by copying the database file"""
        db_path = settings.SQLALCHEMY_DATABASE_URI.replace("sqlite:///", "")
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_file)
        else:
            raise FileNotFoundError(f"SQLite database file not found: {db_path}")
    
    def _compress_backup(self, backup_file: Path) -> Path:
        """Compress backup file using gzip"""
        compressed_file = backup_file.with_suffix(backup_file.suffix + ".gz")
        
        with open(backup_file, 'rb') as f_in:
            with gzip.open(compressed_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove uncompressed file
        backup_file.unlink()
        
        return compressed_file
    
    def _cleanup_old_backups(self):
        """Remove old backup files"""
        backup_files = sorted(
            [f for f in self.backup_dir.glob("*.sql.gz")],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        # Keep only the most recent backups
        for old_backup in backup_files[self.max_local_backups:]:
            old_backup.unlink()
            logger.info(f"Removed old backup: {old_backup}")
    
    def restore_backup(self, backup_file: str):
        """Restore database from backup"""
        backup_path = Path(backup_file)
        
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        try:
            # Decompress if needed
            if backup_path.suffix == ".gz":
                decompressed_file = backup_path.with_suffix("")
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(decompressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                backup_path = decompressed_file
            
            if settings.SQLALCHEMY_DATABASE_URI.startswith("postgresql"):
                self._restore_postgres_backup(backup_path)
            elif settings.SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
                self._restore_sqlite_backup(backup_path)
            else:
                raise ValueError("Unsupported database type for restore")
            
            logger.info(f"Database restored successfully from: {backup_file}")
            
        except Exception as e:
            logger.error(f"Restore failed: {str(e)}")
            raise
        finally:
            # Clean up decompressed file if it was created
            if backup_path.suffix == "" and backup_path.exists():
                backup_path.unlink()
    
    def _restore_postgres_backup(self, backup_file: Path):
        """Restore PostgreSQL backup using psql"""
        db_url = settings.SQLALCHEMY_DATABASE_URI
        
        # Parse database URL (same as backup)
        parts = db_url.replace("postgresql://", "").split("/")
        db_name = parts[1]
        user_host = parts[0].split("@")
        user_pass = user_host[0].split(":")
        host_port = user_host[1].split(":")
        
        user = user_pass[0]
        password = user_pass[1] if len(user_pass) > 1 else ""
        host = host_port[0]
        port = host_port[1] if len(host_port) > 1 else "5432"
        
        env = os.environ.copy()
        if password:
            env["PGPASSWORD"] = password
        
        cmd = [
            "psql",
            "-h", host,
            "-p", port,
            "-U", user,
            "-d", db_name,
            "--no-password",
            "-f", str(backup_file)
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"psql restore failed: {result.stderr}")
    
    def _restore_sqlite_backup(self, backup_file: Path):
        """Restore SQLite backup by copying the file"""
        db_path = settings.SQLALCHEMY_DATABASE_URI.replace("sqlite:///", "")
        
        # Create backup of current database
        if os.path.exists(db_path):
            backup_current = f"{db_path}.backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(db_path, backup_current)
        
        # Restore from backup
        shutil.copy2(backup_file, db_path)
    
    def list_backups(self) -> List[dict]:
        """List available backups"""
        backups = []
        
        for backup_file in sorted(self.backup_dir.glob("*.sql.gz"), key=lambda x: x.stat().st_mtime, reverse=True):
            stat = backup_file.stat()
            backups.append({
                "filename": backup_file.name,
                "path": str(backup_file),
                "size": stat.st_size,
                "created_at": datetime.datetime.fromtimestamp(stat.st_mtime),
                "size_mb": round(stat.st_size / (1024 * 1024), 2)
            })
        
        return backups

class CloudBackupManager:
    """Cloud backup manager for AWS S3"""
    
    def __init__(self, bucket_name: str, aws_access_key: str = None, aws_secret_key: str = None):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key or os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=aws_secret_key or os.getenv('AWS_SECRET_ACCESS_KEY')
        )
    
    def upload_backup(self, local_backup_path: str, s3_key: str = None) -> str:
        """Upload backup to S3"""
        if not s3_key:
            filename = Path(local_backup_path).name
            s3_key = f"database-backups/{filename}"
        
        try:
            self.s3_client.upload_file(local_backup_path, self.bucket_name, s3_key)
            logger.info(f"Backup uploaded to S3: s3://{self.bucket_name}/{s3_key}")
            return s3_key
        except ClientError as e:
            logger.error(f"Failed to upload backup to S3: {str(e)}")
            raise
    
    def download_backup(self, s3_key: str, local_path: str):
        """Download backup from S3"""
        try:
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)
            logger.info(f"Backup downloaded from S3: {s3_key} -> {local_path}")
        except ClientError as e:
            logger.error(f"Failed to download backup from S3: {str(e)}")
            raise
    
    def list_cloud_backups(self) -> List[dict]:
        """List backups in S3"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix="database-backups/"
            )
            
            backups = []
            for obj in response.get('Contents', []):
                backups.append({
                    "key": obj['Key'],
                    "size": obj['Size'],
                    "last_modified": obj['LastModified'],
                    "size_mb": round(obj['Size'] / (1024 * 1024), 2)
                })
            
            return sorted(backups, key=lambda x: x['last_modified'], reverse=True)
            
        except ClientError as e:
            logger.error(f"Failed to list S3 backups: {str(e)}")
            raise

# Convenience functions
def create_backup(backup_name: Optional[str] = None) -> str:
    """Create a database backup"""
    manager = BackupManager()
    return manager.create_backup(backup_name)

def restore_backup(backup_file: str):
    """Restore database from backup"""
    manager = BackupManager()
    manager.restore_backup(backup_file)

def list_backups() -> List[dict]:
    """List available backups"""
    manager = BackupManager()
    return manager.list_backups()
