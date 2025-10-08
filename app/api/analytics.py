from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.site_config import SiteConfig
from app.schemas.analytics import (
    AnalyticsQuery, AnalyticsResponse, DashboardMetrics, RealTimeMetrics,
    ReportRequest, ReportResponse, ExportRequest, ExportResponse,
    AnalyticsPeriod, ReportType, ReportFormat
)
from app.services.analytics_service import AnalyticsService
from app.services.report_service import ReportService
from app.api.dependencies import (
    get_current_user, get_site_config, require_site_access, 
    require_user_ownership, require_active_user
)
from typing import Optional, List
import structlog
from datetime import datetime, timedelta

logger = structlog.get_logger()

router = APIRouter()

@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    period: str = Query("30d", description="Período de análisis"),
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Obtener métricas del dashboard"""
    try:
        analytics_service = AnalyticsService(db)
        
        dashboard = await analytics_service.get_dashboard_metrics(
            site_id=site_config.site_id,
            period=period
        )
        
        logger.info("Dashboard metrics retrieved", 
                   site_id=site_config.site_id, 
                   period=period)
        
        return dashboard
        
    except Exception as e:
        logger.error("Error getting dashboard metrics", 
                    site_id=site_config.site_id, 
                    period=period, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving dashboard metrics"
        )

@router.post("/query", response_model=AnalyticsResponse)
async def query_analytics(
    query: AnalyticsQuery,
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Consultar analytics personalizados"""
    try:
        # Verificar que el query es para el sitio correcto
        if query.site_id != site_config.site_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this site's analytics"
            )
        
        analytics_service = AnalyticsService(db)
        
        response = await analytics_service.get_custom_analytics(query)
        
        logger.info("Custom analytics queried", 
                   site_id=site_config.site_id, 
                   period=query.period,
                   metrics_count=len(query.metrics))
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error querying analytics", 
                    site_id=site_config.site_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error querying analytics"
        )

@router.get("/realtime", response_model=RealTimeMetrics)
async def get_realtime_metrics(
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Obtener métricas en tiempo real"""
    try:
        analytics_service = AnalyticsService(db)
        
        # Obtener métricas en tiempo real
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Usuarios activos ahora (última hora)
        from app.models.interaction import Interaction
        active_users = db.query(User).join(Interaction).filter(
            User.site_id == site_config.site_id,
            User.activo == True,
            Interaction.site_id == site_config.site_id,
            Interaction.fecha_interaccion >= one_hour_ago
        ).distinct().count()
        
        # Interacciones en la última hora
        interactions_last_hour = db.query(Interaction).filter(
            Interaction.site_id == site_config.site_id,
            Interaction.fecha_interaccion >= one_hour_ago
        ).count()
        
        # Notificaciones enviadas hoy
        from app.models.notification import Notification
        notifications_sent_today = db.query(Notification).filter(
            Notification.site_id == site_config.site_id,
            Notification.created_at >= today_start,
            Notification.status == 'sent'
        ).count()
        
        # Stickers generados hoy
        from app.models.sticker import Sticker
        stickers_generated_today = db.query(Sticker).filter(
            Sticker.site_id == site_config.site_id,
            Sticker.fecha_generacion >= today_start
        ).count()
        
        # Videos vistos hoy
        from app.models.video import VideoWatchSession
        videos_watched_today = db.query(VideoWatchSession).join(Video).filter(
            Video.site_id == site_config.site_id,
            VideoWatchSession.start_time >= today_start
        ).count()
        
        realtime_metrics = RealTimeMetrics(
            site_id=site_config.site_id,
            active_users=active_users,
            total_sessions=0,  # TODO: Implementar
            interactions_last_hour=interactions_last_hour,
            notifications_sent_today=notifications_sent_today,
            stickers_generated_today=stickers_generated_today,
            videos_watched_today=videos_watched_today,
            system_health={
                "database": "healthy",
                "redis": "healthy",
                "external_apis": "healthy"
            }
        )
        
        logger.info("Realtime metrics retrieved", 
                   site_id=site_config.site_id)
        
        return realtime_metrics
        
    except Exception as e:
        logger.error("Error getting realtime metrics", 
                    site_id=site_config.site_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving realtime metrics"
        )

@router.post("/reports", response_model=ReportResponse)
async def generate_report(
    report_request: ReportRequest,
    background_tasks: BackgroundTasks,
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Generar reporte"""
    try:
        # Verificar que el reporte es para el sitio correcto
        if report_request.site_id != site_config.site_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this site's reports"
            )
        
        report_service = ReportService(db)
        
        # Generar reporte en background
        result = await report_service.generate_report(report_request)
        
        logger.info("Report generated", 
                   report_id=result.report_id, 
                   report_type=report_request.report_type.value,
                   format=report_request.format.value)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating report", 
                    site_id=site_config.site_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating report"
        )

@router.get("/reports/{report_id}")
async def download_report(
    report_id: str,
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Descargar reporte generado"""
    try:
        from fastapi.responses import FileResponse
        from pathlib import Path
        
        # Verificar que el archivo existe
        reports_dir = Path("reports")
        report_files = list(reports_dir.glob(f"{report_id}.*"))
        
        if not report_files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        report_file = report_files[0]
        
        # Verificar que el archivo no ha expirado (7 días)
        file_age = datetime.utcnow() - datetime.fromtimestamp(report_file.stat().st_mtime)
        if file_age.days > 7:
            # Eliminar archivo expirado
            report_file.unlink()
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Report has expired"
            )
        
        # Determinar tipo de contenido
        content_type = "application/octet-stream"
        if report_file.suffix == ".pdf":
            content_type = "application/pdf"
        elif report_file.suffix == ".csv":
            content_type = "text/csv"
        elif report_file.suffix == ".xlsx":
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif report_file.suffix == ".json":
            content_type = "application/json"
        elif report_file.suffix == ".html":
            content_type = "text/html"
        
        logger.info("Report downloaded", 
                   report_id=report_id, 
                   site_id=site_config.site_id)
        
        return FileResponse(
            path=report_file,
            media_type=content_type,
            filename=report_file.name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error downloading report", 
                    report_id=report_id, 
                    site_id=site_config.site_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error downloading report"
        )

@router.post("/export", response_model=ExportResponse)
async def export_data(
    export_request: ExportRequest,
    background_tasks: BackgroundTasks,
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Exportar datos"""
    try:
        # Verificar que la exportación es para el sitio correcto
        if export_request.site_id != site_config.site_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this site's data"
            )
        
        report_service = ReportService(db)
        
        # Exportar datos en background
        result = await report_service.export_data(export_request)
        
        logger.info("Data exported", 
                   export_id=result.export_id, 
                   data_type=export_request.data_type,
                   format=export_request.format.value)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error exporting data", 
                    site_id=site_config.site_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error exporting data"
        )

@router.get("/export/{export_id}")
async def download_export(
    export_id: str,
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Descargar exportación generada"""
    try:
        from fastapi.responses import FileResponse
        from pathlib import Path
        
        # Verificar que el archivo existe
        exports_dir = Path("exports")
        export_files = list(exports_dir.glob(f"{export_id}.*"))
        
        if not export_files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export not found"
            )
        
        export_file = export_files[0]
        
        # Verificar que el archivo no ha expirado (7 días)
        file_age = datetime.utcnow() - datetime.fromtimestamp(export_file.stat().st_mtime)
        if file_age.days > 7:
            # Eliminar archivo expirado
            export_file.unlink()
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Export has expired"
            )
        
        # Determinar tipo de contenido
        content_type = "application/octet-stream"
        if export_file.suffix == ".csv":
            content_type = "text/csv"
        elif export_file.suffix == ".xlsx":
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif export_file.suffix == ".json":
            content_type = "application/json"
        
        logger.info("Export downloaded", 
                   export_id=export_id, 
                   site_id=site_config.site_id)
        
        return FileResponse(
            path=export_file,
            media_type=content_type,
            filename=export_file.name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error downloading export", 
                    export_id=export_id, 
                    site_id=site_config.site_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error downloading export"
        )

@router.get("/metrics/available")
async def get_available_metrics(
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Obtener métricas disponibles"""
    try:
        available_metrics = {
            "user_metrics": [
                "total_users",
                "active_users",
                "new_users",
                "returning_users",
                "user_retention_rate"
            ],
            "engagement_metrics": [
                "total_interactions",
                "interactions_per_user",
                "engagement_rate",
                "interactions_by_type"
            ],
            "sticker_metrics": [
                "total_stickers_generated",
                "total_stickers_used",
                "sticker_usage_rate",
                "average_discount_percentage"
            ],
            "video_metrics": [
                "total_videos",
                "total_views",
                "total_completions",
                "completion_rate",
                "average_watch_time"
            ],
            "notification_metrics": [
                "total_notifications_sent",
                "total_notifications_delivered",
                "total_notifications_read",
                "delivery_rate",
                "read_rate"
            ]
        }
        
        available_dimensions = [
            "interactions_by_type",
            "stickers_by_type",
            "notifications_by_type",
            "users_by_source",
            "users_by_device"
        ]
        
        available_periods = [
            "1h", "1d", "7d", "30d", "90d", "1y", "custom"
        ]
        
        available_formats = [
            "json", "csv", "pdf", "xlsx", "html"
        ]
        
        logger.info("Available metrics retrieved", 
                   site_id=site_config.site_id)
        
        return {
            "metrics": available_metrics,
            "dimensions": available_dimensions,
            "periods": available_periods,
            "formats": available_formats
        }
        
    except Exception as e:
        logger.error("Error getting available metrics", 
                    site_id=site_config.site_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving available metrics"
        )

@router.get("/insights")
async def get_analytics_insights(
    period: str = Query("30d", description="Período de análisis"),
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Obtener insights de analytics"""
    try:
        analytics_service = AnalyticsService(db)
        
        # Obtener métricas del dashboard
        dashboard = await analytics_service.get_dashboard_metrics(
            site_id=site_config.site_id,
            period=period
        )
        
        insights = []
        
        # Insight 1: Retención de usuarios
        if dashboard.user_activity.user_retention_rate < 50:
            insights.append({
                "type": "warning",
                "title": "Baja retención de usuarios",
                "description": f"La tasa de retención es del {dashboard.user_activity.user_retention_rate}%, considera implementar estrategias de engagement.",
                "recommendation": "Implementar notificaciones de re-engagement y contenido personalizado.",
                "impact": "medium"
            })
        
        # Insight 2: Uso de stickers
        if dashboard.stickers.sticker_usage_rate < 30:
            insights.append({
                "type": "info",
                "title": "Bajo uso de stickers",
                "description": f"Solo el {dashboard.stickers.sticker_usage_rate}% de los stickers generados son utilizados.",
                "recommendation": "Mejorar la comunicación sobre los beneficios de los stickers y simplificar el proceso de uso.",
                "impact": "low"
            })
        
        # Insight 3: Engagement
        if dashboard.engagement.engagement_rate > 70:
            insights.append({
                "type": "success",
                "title": "Excelente engagement",
                "description": f"El engagement del {dashboard.engagement.engagement_rate}% es muy bueno.",
                "recommendation": "Mantener las estrategias actuales y considerar expandir el contenido.",
                "impact": "high"
            })
        
        # Insight 4: Completación de videos
        if dashboard.videos.completion_rate < 40:
            insights.append({
                "type": "warning",
                "title": "Baja completación de videos",
                "description": f"Solo el {dashboard.videos.completion_rate}% de los videos son completados.",
                "recommendation": "Optimizar la duración de los videos y mejorar la calidad del contenido.",
                "impact": "medium"
            })
        
        # Insight 5: Notificaciones
        if dashboard.notifications.read_rate < 60:
            insights.append({
                "type": "info",
                "title": "Baja tasa de lectura de notificaciones",
                "description": f"Solo el {dashboard.notifications.read_rate}% de las notificaciones son leídas.",
                "recommendation": "Optimizar el timing y contenido de las notificaciones.",
                "impact": "low"
            })
        
        logger.info("Analytics insights retrieved", 
                   site_id=site_config.site_id, 
                   period=period,
                   insights_count=len(insights))
        
        return {
            "insights": insights,
            "period": period,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Error getting analytics insights", 
                    site_id=site_config.site_id, 
                    period=period, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving analytics insights"
        )
