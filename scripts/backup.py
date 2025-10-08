#!/usr/bin/env python3
"""
Script de backup para el sistema de fidelización multi-tenant
"""

import os
import sys
import subprocess
import datetime
from pathlib import Path
import structlog

logger = structlog.get_logger()

def run_command(command, description):
    """Ejecutar comando y registrar resultado"""
    try:
        logger.info(f"Starting {description}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"{description} completed successfully")
            return True
        else:
            logger.error(f"{description} failed", 
                        error=result.stderr, 
                        returncode=result.returncode)
            return False
            
    except Exception as e:
        logger.error(f"Error during {description}", error=str(e))
        return False

def backup_database():
    """Hacer backup de la base de datos"""
    try:
        # Obtener variables de entorno
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            logger.error("DATABASE_URL not found in environment")
            return False
        
        # Parsear URL de la base de datos
        # postgresql://user:password@host:port/database
        parts = db_url.replace("postgresql://", "").split("/")
        if len(parts) != 2:
            logger.error("Invalid DATABASE_URL format")
            return False
        
        auth_host = parts[0]
        database = parts[1]
        
        if "@" in auth_host:
            auth, host = auth_host.split("@")
            if ":" in auth:
                user, password = auth.split(":")
            else:
                user = auth
                password = ""
        else:
            user = "postgres"
            password = ""
            host = auth_host
        
        # Crear directorio de backups
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        
        # Generar nombre de archivo con timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"mariachi_fidelizacion_{timestamp}.sql"
        
        # Comando de backup
        if password:
            command = f"PGPASSWORD={password} pg_dump -h {host} -U {user} -d {database} -f {backup_file}"
        else:
            command = f"pg_dump -h {host} -U {user} -d {database} -f {backup_file}"
        
        success = run_command(command, "Database backup")
        
        if success:
            # Comprimir backup
            compress_command = f"gzip {backup_file}"
            run_command(compress_command, "Backup compression")
            
            # Limpiar backups antiguos (mantener solo 7 días)
            cleanup_command = f"find {backup_dir} -name '*.sql.gz' -mtime +7 -delete"
            run_command(cleanup_command, "Old backups cleanup")
            
            logger.info("Database backup completed", backup_file=f"{backup_file}.gz")
            return True
        
        return False
        
    except Exception as e:
        logger.error("Error during database backup", error=str(e))
        return False

def backup_files():
    """Hacer backup de archivos importantes"""
    try:
        # Crear directorio de backups
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        
        # Generar nombre de archivo con timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"files_{timestamp}.tar.gz"
        
        # Archivos y directorios a respaldar
        files_to_backup = [
            "reports/",
            "exports/",
            "logs/",
            "uploads/",
            ".env",
            "alembic.ini",
            "alembic/versions/"
        ]
        
        # Crear comando tar
        command = f"tar -czf {backup_file} {' '.join(files_to_backup)}"
        
        success = run_command(command, "Files backup")
        
        if success:
            # Limpiar backups antiguos (mantener solo 7 días)
            cleanup_command = f"find {backup_dir} -name 'files_*.tar.gz' -mtime +7 -delete"
            run_command(cleanup_command, "Old files cleanup")
            
            logger.info("Files backup completed", backup_file=backup_file)
            return True
        
        return False
        
    except Exception as e:
        logger.error("Error during files backup", error=str(e))
        return False

def backup_redis():
    """Hacer backup de Redis"""
    try:
        # Obtener URL de Redis
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            logger.error("REDIS_URL not found in environment")
            return False
        
        # Parsear URL de Redis
        # redis://host:port/db
        parts = redis_url.replace("redis://", "").split("/")
        if len(parts) != 2:
            logger.error("Invalid REDIS_URL format")
            return False
        
        host_port = parts[0]
        db = parts[1]
        
        if ":" in host_port:
            host, port = host_port.split(":")
        else:
            host = host_port
            port = "6379"
        
        # Crear directorio de backups
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        
        # Generar nombre de archivo con timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"redis_{timestamp}.rdb"
        
        # Comando de backup de Redis
        command = f"redis-cli -h {host} -p {port} -n {db} --rdb {backup_file}"
        
        success = run_command(command, "Redis backup")
        
        if success:
            # Comprimir backup
            compress_command = f"gzip {backup_file}"
            run_command(compress_command, "Redis backup compression")
            
            # Limpiar backups antiguos (mantener solo 7 días)
            cleanup_command = f"find {backup_dir} -name 'redis_*.rdb.gz' -mtime +7 -delete"
            run_command(cleanup_command, "Old Redis backups cleanup")
            
            logger.info("Redis backup completed", backup_file=f"{backup_file}.gz")
            return True
        
        return False
        
    except Exception as e:
        logger.error("Error during Redis backup", error=str(e))
        return False

def main():
    """Función principal de backup"""
    try:
        logger.info("Starting backup process")
        
        # Backup de base de datos
        db_success = backup_database()
        
        # Backup de archivos
        files_success = backup_files()
        
        # Backup de Redis
        redis_success = backup_redis()
        
        # Resumen
        if db_success and files_success and redis_success:
            logger.info("All backups completed successfully")
            sys.exit(0)
        else:
            logger.error("Some backups failed", 
                        db_success=db_success, 
                        files_success=files_success, 
                        redis_success=redis_success)
            sys.exit(1)
            
    except Exception as e:
        logger.error("Error during backup process", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
