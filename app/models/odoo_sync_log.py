from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class OdooSyncLog(Base):
    """Modelo para logs de sincronización con Odoo"""
    __tablename__ = "odoo_sync_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(50), nullable=False, index=True)
    
    # Información del modelo y registro
    model_type = Column(Enum('res.partner', 'product.product', 'sale.order', 'account.move', 'project.project', 'project.task', name='odoo_model_type'), 
                       nullable=False)
    record_id = Column(Integer, nullable=False)
    odoo_id = Column(Integer, nullable=True)
    
    # Operación y estado
    operation = Column(Enum('create', 'update', 'delete', 'read', name='sync_operation'), 
                      nullable=False)
    status = Column(Enum('pending', 'syncing', 'completed', 'failed', 'retry', name='sync_status'), 
                   default='pending', nullable=False)
    
    # Detalles de la operación
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    # Metadatos
    sync_data = Column(Text, nullable=True)
    response_data = Column(Text, nullable=True)
    
    # Timestamps
    sync_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<OdooSyncLog(id={self.id}, model='{self.model_type}', record_id={self.record_id}, status='{self.status}')>"

class OdooConfig(Base):
    """Modelo para configuración de Odoo por sitio"""
    __tablename__ = "odoo_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Configuración de conexión
    odoo_url = Column(String(500), nullable=False)
    odoo_database = Column(String(100), nullable=False)
    odoo_username = Column(String(100), nullable=False)
    odoo_password = Column(String(255), nullable=False)
    
    # Configuración de sincronización
    auto_sync = Column(Boolean, default=True, nullable=False)
    sync_interval = Column(Integer, default=30, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    # Estado de conexión
    connection_status = Column(Enum('connected', 'disconnected', 'error', 'testing', name='connection_status'), 
                              default='disconnected', nullable=False)
    last_sync = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<OdooConfig(site_id='{self.site_id}', status='{self.connection_status}')>"

class OdooWebhook(Base):
    """Modelo para webhooks de Odoo"""
    __tablename__ = "odoo_webhooks"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(50), nullable=False, index=True)
    
    # Información del webhook
    event_type = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    record_id = Column(Integer, nullable=False)
    
    # Datos del webhook
    webhook_data = Column(Text, nullable=False)
    processed = Column(Boolean, default=False, nullable=False)
    processing_error = Column(Text, nullable=True)
    
    # Timestamps
    received_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<OdooWebhook(id={self.id}, event='{self.event_type}', model='{self.model}', processed={self.processed})>"

class OdooReport(Base):
    """Modelo para reportes de Odoo"""
    __tablename__ = "odoo_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(50), nullable=False, index=True)
    
    # Información del reporte
    report_type = Column(String(100), nullable=False)
    report_name = Column(String(200), nullable=False)
    report_format = Column(Enum('json', 'csv', 'pdf', 'xlsx', name='report_format'), 
                          default='json', nullable=False)
    
    # Filtros y parámetros
    date_from = Column(DateTime(timezone=True), nullable=True)
    date_to = Column(DateTime(timezone=True), nullable=True)
    filters = Column(Text, nullable=True)
    
    # Resultados
    report_data = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    
    # Estado
    status = Column(Enum('pending', 'generating', 'completed', 'failed', name='report_status'), 
                   default='pending', nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    generated_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<OdooReport(id={self.id}, type='{self.report_type}', status='{self.status}')>"
