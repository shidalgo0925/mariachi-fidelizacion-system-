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
                       nullable=False, description="Tipo de modelo de Odoo")
    record_id = Column(Integer, nullable=False, description="ID del registro local")
    odoo_id = Column(Integer, nullable=True, description="ID en Odoo")
    
    # Operación y estado
    operation = Column(Enum('create', 'update', 'delete', 'read', name='sync_operation'), 
                      nullable=False, description="Operación realizada")
    status = Column(Enum('pending', 'syncing', 'completed', 'failed', 'retry', name='sync_status'), 
                   default='pending', nullable=False, description="Estado de la sincronización")
    
    # Detalles de la operación
    error_message = Column(Text, nullable=True, description="Mensaje de error si falló")
    retry_count = Column(Integer, default=0, nullable=False, description="Número de reintentos")
    max_retries = Column(Integer, default=3, nullable=False, description="Máximo de reintentos")
    
    # Metadatos
    sync_data = Column(Text, nullable=True, description="Datos sincronizados (JSON)")
    response_data = Column(Text, nullable=True, description="Respuesta de Odoo (JSON)")
    
    # Timestamps
    sync_timestamp = Column(DateTime(timezone=True), server_default=func.now(), description="Timestamp de la sincronización")
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
    odoo_url = Column(String(500), nullable=False, description="URL del servidor Odoo")
    odoo_database = Column(String(100), nullable=False, description="Nombre de la base de datos")
    odoo_username = Column(String(100), nullable=False, description="Usuario de Odoo")
    odoo_password = Column(String(255), nullable=False, description="Contraseña de Odoo")
    
    # Configuración de sincronización
    auto_sync = Column(Boolean, default=True, nullable=False, description="Sincronización automática habilitada")
    sync_interval = Column(Integer, default=30, nullable=False, description="Intervalo de sincronización en minutos")
    max_retries = Column(Integer, default=3, nullable=False, description="Máximo de reintentos")
    
    # Estado de conexión
    connection_status = Column(Enum('connected', 'disconnected', 'error', 'testing', name='connection_status'), 
                              default='disconnected', nullable=False, description="Estado de la conexión")
    last_sync = Column(DateTime(timezone=True), nullable=True, description="Última sincronización")
    last_error = Column(Text, nullable=True, description="Último error de conexión")
    
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
    event_type = Column(String(100), nullable=False, description="Tipo de evento")
    model = Column(String(100), nullable=False, description="Modelo de Odoo")
    record_id = Column(Integer, nullable=False, description="ID del registro")
    
    # Datos del webhook
    webhook_data = Column(Text, nullable=False, description="Datos del webhook (JSON)")
    processed = Column(Boolean, default=False, nullable=False, description="Si fue procesado")
    processing_error = Column(Text, nullable=True, description="Error de procesamiento")
    
    # Timestamps
    received_at = Column(DateTime(timezone=True), server_default=func.now(), description="Timestamp de recepción")
    processed_at = Column(DateTime(timezone=True), nullable=True, description="Timestamp de procesamiento")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<OdooWebhook(id={self.id}, event='{self.event_type}', model='{self.model}', processed={self.processed})>"

class OdooReport(Base):
    """Modelo para reportes de Odoo"""
    __tablename__ = "odoo_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(50), nullable=False, index=True)
    
    # Información del reporte
    report_type = Column(String(100), nullable=False, description="Tipo de reporte")
    report_name = Column(String(200), nullable=False, description="Nombre del reporte")
    report_format = Column(Enum('json', 'csv', 'pdf', 'xlsx', name='report_format'), 
                          default='json', nullable=False, description="Formato del reporte")
    
    # Filtros y parámetros
    date_from = Column(DateTime(timezone=True), nullable=True, description="Fecha desde")
    date_to = Column(DateTime(timezone=True), nullable=True, description="Fecha hasta")
    filters = Column(Text, nullable=True, description="Filtros adicionales (JSON)")
    
    # Resultados
    report_data = Column(Text, nullable=True, description="Datos del reporte (JSON)")
    file_path = Column(String(500), nullable=True, description="Ruta del archivo generado")
    file_size = Column(Integer, nullable=True, description="Tamaño del archivo en bytes")
    
    # Estado
    status = Column(Enum('pending', 'generating', 'completed', 'failed', name='report_status'), 
                   default='pending', nullable=False, description="Estado del reporte")
    error_message = Column(Text, nullable=True, description="Mensaje de error si falló")
    
    # Timestamps
    generated_at = Column(DateTime(timezone=True), nullable=True, description="Timestamp de generación")
    expires_at = Column(DateTime(timezone=True), nullable=True, description="Timestamp de expiración")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<OdooReport(id={self.id}, type='{self.report_type}', status='{self.status}')>"
