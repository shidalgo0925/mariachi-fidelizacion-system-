#!/usr/bin/env python3
"""
Script de monitoreo para el sistema de fidelización multi-tenant
"""

import os
import sys
import time
import requests
import psutil
import structlog
from datetime import datetime, timedelta
from pathlib import Path

logger = structlog.get_logger()

class SystemMonitor:
    """Monitor del sistema"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.log_file = Path("logs/monitor.log")
        self.log_file.parent.mkdir(exist_ok=True)
    
    def check_health(self):
        """Verificar salud del sistema"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                logger.info("Health check passed", 
                           status=health_data.get("status"),
                           timestamp=health_data.get("timestamp"))
                return True
            else:
                logger.error("Health check failed", 
                            status_code=response.status_code)
                return False
                
        except Exception as e:
            logger.error("Health check error", error=str(e))
            return False
    
    def check_database(self):
        """Verificar conexión a la base de datos"""
        try:
            response = requests.get(f"{self.base_url}/health/database", timeout=10)
            
            if response.status_code == 200:
                db_data = response.json()
                logger.info("Database check passed", 
                           status=db_data.get("status"),
                           connection_time=db_data.get("connection_time"))
                return True
            else:
                logger.error("Database check failed", 
                            status_code=response.status_code)
                return False
                
        except Exception as e:
            logger.error("Database check error", error=str(e))
            return False
    
    def check_redis(self):
        """Verificar conexión a Redis"""
        try:
            response = requests.get(f"{self.base_url}/health/redis", timeout=10)
            
            if response.status_code == 200:
                redis_data = response.json()
                logger.info("Redis check passed", 
                           status=redis_data.get("status"),
                           connection_time=redis_data.get("connection_time"))
                return True
            else:
                logger.error("Redis check failed", 
                            status_code=response.status_code)
                return False
                
        except Exception as e:
            logger.error("Redis check error", error=str(e))
            return False
    
    def check_system_resources(self):
        """Verificar recursos del sistema"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memoria
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disco
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Verificar umbrales
            warnings = []
            if cpu_percent > 80:
                warnings.append(f"High CPU usage: {cpu_percent}%")
            if memory_percent > 80:
                warnings.append(f"High memory usage: {memory_percent}%")
            if disk_percent > 80:
                warnings.append(f"High disk usage: {disk_percent}%")
            
            if warnings:
                logger.warning("System resource warnings", warnings=warnings)
            else:
                logger.info("System resources OK", 
                           cpu_percent=cpu_percent,
                           memory_percent=memory_percent,
                           disk_percent=disk_percent)
            
            return len(warnings) == 0
            
        except Exception as e:
            logger.error("System resources check error", error=str(e))
            return False
    
    def check_log_files(self):
        """Verificar archivos de log"""
        try:
            log_dir = Path("logs")
            if not log_dir.exists():
                logger.warning("Log directory not found")
                return False
            
            # Verificar tamaño de logs
            total_size = 0
            for log_file in log_dir.glob("*.log"):
                total_size += log_file.stat().st_size
            
            # Convertir a MB
            total_size_mb = total_size / (1024 * 1024)
            
            if total_size_mb > 100:  # 100MB
                logger.warning("Large log files detected", 
                              total_size_mb=total_size_mb)
                return False
            else:
                logger.info("Log files OK", total_size_mb=total_size_mb)
                return True
                
        except Exception as e:
            logger.error("Log files check error", error=str(e))
            return False
    
    def check_application_metrics(self):
        """Verificar métricas de la aplicación"""
        try:
            response = requests.get(f"{self.base_url}/metrics", timeout=10)
            
            if response.status_code == 200:
                metrics = response.json()
                logger.info("Application metrics retrieved", 
                           total_users=metrics.get("total_users"),
                           active_users=metrics.get("active_users"),
                           total_interactions=metrics.get("total_interactions"))
                return True
            else:
                logger.error("Application metrics check failed", 
                            status_code=response.status_code)
                return False
                
        except Exception as e:
            logger.error("Application metrics check error", error=str(e))
            return False
    
    def run_monitoring_cycle(self):
        """Ejecutar ciclo de monitoreo"""
        try:
            logger.info("Starting monitoring cycle")
            
            # Verificaciones
            health_ok = self.check_health()
            db_ok = self.check_database()
            redis_ok = self.check_redis()
            resources_ok = self.check_system_resources()
            logs_ok = self.check_log_files()
            metrics_ok = self.check_application_metrics()
            
            # Resumen
            all_ok = all([health_ok, db_ok, redis_ok, resources_ok, logs_ok, metrics_ok])
            
            if all_ok:
                logger.info("All monitoring checks passed")
            else:
                logger.error("Some monitoring checks failed", 
                            health_ok=health_ok,
                            db_ok=db_ok,
                            redis_ok=redis_ok,
                            resources_ok=resources_ok,
                            logs_ok=logs_ok,
                            metrics_ok=metrics_ok)
            
            return all_ok
            
        except Exception as e:
            logger.error("Monitoring cycle error", error=str(e))
            return False
    
    def run_continuous_monitoring(self, interval=60):
        """Ejecutar monitoreo continuo"""
        try:
            logger.info("Starting continuous monitoring", interval=interval)
            
            while True:
                self.run_monitoring_cycle()
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error("Continuous monitoring error", error=str(e))

def main():
    """Función principal"""
    try:
        import argparse
        
        parser = argparse.ArgumentParser(description="System Monitor")
        parser.add_argument("--url", default="http://localhost:8000", 
                          help="Base URL of the application")
        parser.add_argument("--interval", type=int, default=60, 
                          help="Monitoring interval in seconds")
        parser.add_argument("--once", action="store_true", 
                          help="Run monitoring once instead of continuously")
        
        args = parser.parse_args()
        
        monitor = SystemMonitor(args.url)
        
        if args.once:
            success = monitor.run_monitoring_cycle()
            sys.exit(0 if success else 1)
        else:
            monitor.run_continuous_monitoring(args.interval)
            
    except Exception as e:
        logger.error("Monitor error", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
