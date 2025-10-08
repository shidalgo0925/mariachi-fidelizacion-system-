from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
from app.models.user import User
from app.models.sticker import Sticker
from app.models.video import Video, VideoCompletion, VideoWatchSession
from app.models.interaction import Interaction, Like, Comment, Review
from app.models.notification import Notification
from app.models.site_config import SiteConfig
from app.schemas.analytics import (
    AnalyticsQuery, AnalyticsResponse, UserActivityAnalytics, EngagementAnalytics,
    StickerAnalytics, VideoAnalytics, NotificationAnalytics, DashboardMetrics,
    AnalyticsMetric, AnalyticsDimension, TimeSeriesData, MetricType
)
from typing import Optional, List, Dict, Any
import structlog
from datetime import datetime, timedelta, date
import json

logger = structlog.get_logger()

class AnalyticsService:
    """Servicio para analytics y reportes multi-tenant"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_dashboard_metrics(
        self, 
        site_id: str, 
        period: str = "30d"
    ) -> DashboardMetrics:
        """Obtener métricas del dashboard"""
        try:
            # Calcular fechas
            end_date = datetime.utcnow()
            if period.endswith('d'):
                days = int(period[:-1])
                start_date = end_date - timedelta(days=days)
            elif period.endswith('w'):
                weeks = int(period[:-1])
                start_date = end_date - timedelta(weeks=weeks)
            elif period.endswith('m'):
                months = int(period[:-1])
                start_date = end_date - timedelta(days=months * 30)
            else:
                start_date = end_date - timedelta(days=30)
            
            # Obtener métricas de cada módulo
            user_activity = await self._get_user_activity_analytics(site_id, start_date, end_date)
            engagement = await self._get_engagement_analytics(site_id, start_date, end_date)
            stickers = await self._get_sticker_analytics(site_id, start_date, end_date)
            videos = await self._get_video_analytics(site_id, start_date, end_date)
            notifications = await self._get_notification_analytics(site_id, start_date, end_date)
            
            dashboard = DashboardMetrics(
                site_id=site_id,
                period=period,
                user_activity=user_activity,
                engagement=engagement,
                stickers=stickers,
                videos=videos,
                notifications=notifications
            )
            
            logger.info("Dashboard metrics retrieved", 
                       site_id=site_id, 
                       period=period)
            
            return dashboard
            
        except Exception as e:
            logger.error("Error getting dashboard metrics", 
                        site_id=site_id, 
                        period=period, 
                        error=str(e))
            raise
    
    async def _get_user_activity_analytics(
        self, 
        site_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> UserActivityAnalytics:
        """Obtener analytics de actividad de usuarios"""
        try:
            # Total de usuarios
            total_users = self.db.query(User).filter(
                and_(
                    User.site_id == site_id,
                    User.activo == True
                )
            ).count()
            
            # Usuarios activos (con interacciones en el período)
            active_users = self.db.query(User).join(Interaction).filter(
                and_(
                    User.site_id == site_id,
                    User.activo == True,
                    Interaction.site_id == site_id,
                    Interaction.fecha_interaccion >= start_date,
                    Interaction.fecha_interaccion <= end_date
                )
            ).distinct().count()
            
            # Usuarios nuevos en el período
            new_users = self.db.query(User).filter(
                and_(
                    User.site_id == site_id,
                    User.activo == True,
                    User.fecha_registro >= start_date,
                    User.fecha_registro <= end_date
                )
            ).count()
            
            # Usuarios que regresan (activos en período anterior)
            previous_start = start_date - (end_date - start_date)
            returning_users = self.db.query(User).join(Interaction).filter(
                and_(
                    User.site_id == site_id,
                    User.activo == True,
                    Interaction.site_id == site_id,
                    Interaction.fecha_interaccion >= start_date,
                    Interaction.fecha_interaccion <= end_date
                )
            ).join(Interaction, and_(
                Interaction.usuario_id == User.id,
                Interaction.site_id == site_id,
                Interaction.fecha_interaccion >= previous_start,
                Interaction.fecha_interaccion < start_date
            )).distinct().count()
            
            # Tasa de retención
            retention_rate = (returning_users / active_users * 100) if active_users > 0 else 0
            
            # Usuarios activos diarios (simplificado)
            daily_active_users = []
            current_date = start_date.date()
            end_date_only = end_date.date()
            
            while current_date <= end_date_only:
                day_start = datetime.combine(current_date, datetime.min.time())
                day_end = datetime.combine(current_date, datetime.max.time())
                
                dau = self.db.query(User).join(Interaction).filter(
                    and_(
                        User.site_id == site_id,
                        User.activo == True,
                        Interaction.site_id == site_id,
                        Interaction.fecha_interaccion >= day_start,
                        Interaction.fecha_interaccion <= day_end
                    )
                ).distinct().count()
                
                daily_active_users.append(TimeSeriesData(
                    timestamp=day_start,
                    value=float(dau)
                ))
                
                current_date += timedelta(days=1)
            
            return UserActivityAnalytics(
                total_users=total_users,
                active_users=active_users,
                new_users=new_users,
                returning_users=returning_users,
                user_retention_rate=round(retention_rate, 2),
                average_session_duration=0.0,  # TODO: Implementar
                users_by_source=[],  # TODO: Implementar
                users_by_device=[],  # TODO: Implementar
                daily_active_users=daily_active_users
            )
            
        except Exception as e:
            logger.error("Error getting user activity analytics", 
                        site_id=site_id, 
                        error=str(e))
            return UserActivityAnalytics()
    
    async def _get_engagement_analytics(
        self, 
        site_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> EngagementAnalytics:
        """Obtener analytics de engagement"""
        try:
            # Total de interacciones
            total_interactions = self.db.query(Interaction).filter(
                and_(
                    Interaction.site_id == site_id,
                    Interaction.fecha_interaccion >= start_date,
                    Interaction.fecha_interaccion <= end_date
                )
            ).count()
            
            # Usuarios activos
            active_users = self.db.query(User).join(Interaction).filter(
                and_(
                    User.site_id == site_id,
                    User.activo == True,
                    Interaction.site_id == site_id,
                    Interaction.fecha_interaccion >= start_date,
                    Interaction.fecha_interaccion <= end_date
                )
            ).distinct().count()
            
            # Interacciones por usuario
            interactions_per_user = (total_interactions / active_users) if active_users > 0 else 0
            
            # Tasa de engagement (simplificada)
            total_users = self.db.query(User).filter(
                and_(
                    User.site_id == site_id,
                    User.activo == True
                )
            ).count()
            engagement_rate = (active_users / total_users * 100) if total_users > 0 else 0
            
            # Interacciones por tipo
            interactions_by_type = []
            interaction_types = ['like', 'comment', 'review', 'share', 'view']
            
            for interaction_type in interaction_types:
                count = self.db.query(Interaction).filter(
                    and_(
                        Interaction.site_id == site_id,
                        Interaction.tipo_interaccion == interaction_type,
                        Interaction.fecha_interaccion >= start_date,
                        Interaction.fecha_interaccion <= end_date
                    )
                ).count()
                
                if count > 0:
                    percentage = (count / total_interactions * 100) if total_interactions > 0 else 0
                    interactions_by_type.append(AnalyticsDimension(
                        name=interaction_type,
                        value=interaction_type,
                        count=count,
                        percentage=round(percentage, 2)
                    ))
            
            # Tendencia de engagement (diaria)
            engagement_trend = []
            current_date = start_date.date()
            end_date_only = end_date.date()
            
            while current_date <= end_date_only:
                day_start = datetime.combine(current_date, datetime.min.time())
                day_end = datetime.combine(current_date, datetime.max.time())
                
                daily_interactions = self.db.query(Interaction).filter(
                    and_(
                        Interaction.site_id == site_id,
                        Interaction.fecha_interaccion >= day_start,
                        Interaction.fecha_interaccion <= day_end
                    )
                ).count()
                
                engagement_trend.append(TimeSeriesData(
                    timestamp=day_start,
                    value=float(daily_interactions)
                ))
                
                current_date += timedelta(days=1)
            
            return EngagementAnalytics(
                total_interactions=total_interactions,
                interactions_per_user=round(interactions_per_user, 2),
                engagement_rate=round(engagement_rate, 2),
                most_engaged_content=[],  # TODO: Implementar
                interactions_by_type=interactions_by_type,
                engagement_trend=engagement_trend,
                top_users=[]  # TODO: Implementar
            )
            
        except Exception as e:
            logger.error("Error getting engagement analytics", 
                        site_id=site_id, 
                        error=str(e))
            return EngagementAnalytics()
    
    async def _get_sticker_analytics(
        self, 
        site_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> StickerAnalytics:
        """Obtener analytics de stickers"""
        try:
            # Total de stickers generados
            total_stickers_generated = self.db.query(Sticker).filter(
                and_(
                    Sticker.site_id == site_id,
                    Sticker.fecha_generacion >= start_date,
                    Sticker.fecha_generacion <= end_date
                )
            ).count()
            
            # Total de stickers usados
            total_stickers_used = self.db.query(Sticker).filter(
                and_(
                    Sticker.site_id == site_id,
                    Sticker.usado == True,
                    Sticker.fecha_uso >= start_date,
                    Sticker.fecha_uso <= end_date
                )
            ).count()
            
            # Tasa de uso de stickers
            usage_rate = (total_stickers_used / total_stickers_generated * 100) if total_stickers_generated > 0 else 0
            
            # Descuento promedio
            avg_discount = self.db.query(func.avg(Sticker.porcentaje_descuento)).filter(
                and_(
                    Sticker.site_id == site_id,
                    Sticker.fecha_generacion >= start_date,
                    Sticker.fecha_generacion <= end_date
                )
            ).scalar() or 0
            
            # Stickers por tipo
            stickers_by_type = []
            sticker_types = ['registro', 'instagram', 'reseña', 'video_completado']
            
            for sticker_type in sticker_types:
                count = self.db.query(Sticker).filter(
                    and_(
                        Sticker.site_id == site_id,
                        Sticker.tipo_sticker == sticker_type,
                        Sticker.fecha_generacion >= start_date,
                        Sticker.fecha_generacion <= end_date
                    )
                ).count()
                
                if count > 0:
                    percentage = (count / total_stickers_generated * 100) if total_stickers_generated > 0 else 0
                    stickers_by_type.append(AnalyticsDimension(
                        name=sticker_type,
                        value=sticker_type,
                        count=count,
                        percentage=round(percentage, 2)
                    ))
            
            # Tendencia de generación de stickers
            sticker_generation_trend = []
            current_date = start_date.date()
            end_date_only = end_date.date()
            
            while current_date <= end_date_only:
                day_start = datetime.combine(current_date, datetime.min.time())
                day_end = datetime.combine(current_date, datetime.max.time())
                
                daily_stickers = self.db.query(Sticker).filter(
                    and_(
                        Sticker.site_id == site_id,
                        Sticker.fecha_generacion >= day_start,
                        Sticker.fecha_generacion <= day_end
                    )
                ).count()
                
                sticker_generation_trend.append(TimeSeriesData(
                    timestamp=day_start,
                    value=float(daily_stickers)
                ))
                
                current_date += timedelta(days=1)
            
            return StickerAnalytics(
                total_stickers_generated=total_stickers_generated,
                total_stickers_used=total_stickers_used,
                sticker_usage_rate=round(usage_rate, 2),
                average_discount_percentage=round(avg_discount, 2),
                total_discount_value=0.0,  # TODO: Implementar
                stickers_by_type=stickers_by_type,
                sticker_generation_trend=sticker_generation_trend,
                top_discount_codes=[]  # TODO: Implementar
            )
            
        except Exception as e:
            logger.error("Error getting sticker analytics", 
                        site_id=site_id, 
                        error=str(e))
            return StickerAnalytics()
    
    async def _get_video_analytics(
        self, 
        site_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> VideoAnalytics:
        """Obtener analytics de videos"""
        try:
            # Total de videos
            total_videos = self.db.query(Video).filter(
                and_(
                    Video.site_id == site_id,
                    Video.activo == True
                )
            ).count()
            
            # Total de visualizaciones
            total_views = self.db.query(VideoWatchSession).join(Video).filter(
                and_(
                    Video.site_id == site_id,
                    VideoWatchSession.start_time >= start_date,
                    VideoWatchSession.start_time <= end_date
                )
            ).count()
            
            # Total de completaciones
            total_completions = self.db.query(VideoCompletion).join(Video).filter(
                and_(
                    Video.site_id == site_id,
                    VideoCompletion.completed_at >= start_date,
                    VideoCompletion.completed_at <= end_date
                )
            ).count()
            
            # Tasa de completación
            completion_rate = (total_completions / total_views * 100) if total_views > 0 else 0
            
            # Tiempo promedio de visualización
            avg_watch_time = self.db.query(func.avg(VideoWatchSession.total_watched_seconds)).join(Video).filter(
                and_(
                    Video.site_id == site_id,
                    VideoWatchSession.start_time >= start_date,
                    VideoWatchSession.start_time <= end_date
                )
            ).scalar() or 0
            
            # Videos más vistos
            most_watched_videos = []
            video_stats = self.db.query(
                Video.id,
                Video.titulo,
                func.count(VideoWatchSession.id).label('view_count')
            ).join(VideoWatchSession).filter(
                and_(
                    Video.site_id == site_id,
                    VideoWatchSession.start_time >= start_date,
                    VideoWatchSession.start_time <= end_date
                )
            ).group_by(Video.id, Video.titulo).order_by(desc('view_count')).limit(10).all()
            
            for video_stat in video_stats:
                percentage = (video_stat.view_count / total_views * 100) if total_views > 0 else 0
                most_watched_videos.append(AnalyticsDimension(
                    name=video_stat.titulo,
                    value=str(video_stat.id),
                    count=video_stat.view_count,
                    percentage=round(percentage, 2)
                ))
            
            # Tendencia de rendimiento de videos
            video_performance_trend = []
            current_date = start_date.date()
            end_date_only = end_date.date()
            
            while current_date <= end_date_only:
                day_start = datetime.combine(current_date, datetime.min.time())
                day_end = datetime.combine(current_date, datetime.max.time())
                
                daily_views = self.db.query(VideoWatchSession).join(Video).filter(
                    and_(
                        Video.site_id == site_id,
                        VideoWatchSession.start_time >= day_start,
                        VideoWatchSession.start_time <= day_end
                    )
                ).count()
                
                video_performance_trend.append(TimeSeriesData(
                    timestamp=day_start,
                    value=float(daily_views)
                ))
                
                current_date += timedelta(days=1)
            
            return VideoAnalytics(
                total_videos=total_videos,
                total_views=total_views,
                total_completions=total_completions,
                completion_rate=round(completion_rate, 2),
                average_watch_time=round(avg_watch_time, 2),
                most_watched_videos=most_watched_videos,
                video_performance_trend=video_performance_trend,
                user_engagement_by_video=[]  # TODO: Implementar
            )
            
        except Exception as e:
            logger.error("Error getting video analytics", 
                        site_id=site_id, 
                        error=str(e))
            return VideoAnalytics()
    
    async def _get_notification_analytics(
        self, 
        site_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> NotificationAnalytics:
        """Obtener analytics de notificaciones"""
        try:
            # Total de notificaciones enviadas
            total_sent = self.db.query(Notification).filter(
                and_(
                    Notification.site_id == site_id,
                    Notification.created_at >= start_date,
                    Notification.created_at <= end_date,
                    Notification.status == 'sent'
                )
            ).count()
            
            # Total de notificaciones entregadas
            total_delivered = self.db.query(Notification).filter(
                and_(
                    Notification.site_id == site_id,
                    Notification.created_at >= start_date,
                    Notification.created_at <= end_date,
                    Notification.delivered_at.isnot(None)
                )
            ).count()
            
            # Total de notificaciones leídas
            total_read = self.db.query(Notification).filter(
                and_(
                    Notification.site_id == site_id,
                    Notification.created_at >= start_date,
                    Notification.created_at <= end_date,
                    Notification.read_at.isnot(None)
                )
            ).count()
            
            # Tasas
            delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0
            read_rate = (total_read / total_delivered * 100) if total_delivered > 0 else 0
            
            # Notificaciones por tipo
            notifications_by_type = []
            notification_types = ['sticker', 'instagram', 'points', 'level_up', 'system', 'video_completed']
            
            for notification_type in notification_types:
                count = self.db.query(Notification).filter(
                    and_(
                        Notification.site_id == site_id,
                        Notification.type == notification_type,
                        Notification.created_at >= start_date,
                        Notification.created_at <= end_date
                    )
                ).count()
                
                if count > 0:
                    percentage = (count / total_sent * 100) if total_sent > 0 else 0
                    notifications_by_type.append(AnalyticsDimension(
                        name=notification_type,
                        value=notification_type,
                        count=count,
                        percentage=round(percentage, 2)
                    ))
            
            # Tendencia de rendimiento de notificaciones
            notification_performance_trend = []
            current_date = start_date.date()
            end_date_only = end_date.date()
            
            while current_date <= end_date_only:
                day_start = datetime.combine(current_date, datetime.min.time())
                day_end = datetime.combine(current_date, datetime.max.time())
                
                daily_sent = self.db.query(Notification).filter(
                    and_(
                        Notification.site_id == site_id,
                        Notification.created_at >= day_start,
                        Notification.created_at <= day_end,
                        Notification.status == 'sent'
                    )
                ).count()
                
                notification_performance_trend.append(TimeSeriesData(
                    timestamp=day_start,
                    value=float(daily_sent)
                ))
                
                current_date += timedelta(days=1)
            
            return NotificationAnalytics(
                total_notifications_sent=total_sent,
                total_notifications_delivered=total_delivered,
                total_notifications_read=total_read,
                delivery_rate=round(delivery_rate, 2),
                read_rate=round(read_rate, 2),
                notifications_by_type=notifications_by_type,
                notifications_by_channel=[],  # TODO: Implementar
                notification_performance_trend=notification_performance_trend
            )
            
        except Exception as e:
            logger.error("Error getting notification analytics", 
                        site_id=site_id, 
                        error=str(e))
            return NotificationAnalytics()
    
    async def get_custom_analytics(
        self, 
        query: AnalyticsQuery
    ) -> AnalyticsResponse:
        """Obtener analytics personalizados"""
        try:
            # Calcular fechas
            end_date = datetime.utcnow()
            if query.period == "custom" and query.start_date and query.end_date:
                start_date = query.start_date
                end_date = query.end_date
            else:
                if query.period.endswith('d'):
                    days = int(query.period[:-1])
                    start_date = end_date - timedelta(days=days)
                elif query.period.endswith('w'):
                    weeks = int(query.period[:-1])
                    start_date = end_date - timedelta(weeks=weeks)
                elif query.period.endswith('m'):
                    months = int(query.period[:-1])
                    start_date = end_date - timedelta(days=months * 30)
                else:
                    start_date = end_date - timedelta(days=30)
            
            # Calcular métricas solicitadas
            metrics = []
            for metric_name in query.metrics:
                metric = await self._calculate_metric(
                    metric_name, 
                    query.site_id, 
                    start_date, 
                    end_date, 
                    query.filters
                )
                if metric:
                    metrics.append(metric)
            
            # Calcular dimensiones si se solicitan
            dimensions = []
            if query.dimensions:
                for dimension_name in query.dimensions:
                    dimension_data = await self._calculate_dimension(
                        dimension_name, 
                        query.site_id, 
                        start_date, 
                        end_date, 
                        query.filters
                    )
                    dimensions.extend(dimension_data)
            
            # Calcular series temporales si se solicita agrupación
            time_series = []
            if query.group_by:
                time_series = await self._calculate_time_series(
                    query.metrics, 
                    query.site_id, 
                    start_date, 
                    end_date, 
                    query.group_by, 
                    query.filters
                )
            
            response = AnalyticsResponse(
                site_id=query.site_id,
                period=query.period,
                start_date=start_date,
                end_date=end_date,
                metrics=metrics,
                dimensions=dimensions if dimensions else None,
                time_series=time_series if time_series else None
            )
            
            logger.info("Custom analytics retrieved", 
                       site_id=query.site_id, 
                       period=query.period,
                       metrics_count=len(metrics))
            
            return response
            
        except Exception as e:
            logger.error("Error getting custom analytics", 
                        site_id=query.site_id, 
                        error=str(e))
            raise
    
    async def _calculate_metric(
        self, 
        metric_name: str, 
        site_id: str, 
        start_date: datetime, 
        end_date: datetime, 
        filters: Optional[Dict[str, Any]] = None
    ) -> Optional[AnalyticsMetric]:
        """Calcular una métrica específica"""
        try:
            # Implementar cálculos de métricas específicas
            # Por ahora retornar métricas básicas
            
            if metric_name == "total_users":
                count = self.db.query(User).filter(
                    and_(
                        User.site_id == site_id,
                        User.activo == True
                    )
                ).count()
                return AnalyticsMetric(
                    name=metric_name,
                    value=float(count),
                    type=MetricType.COUNT,
                    unit="users"
                )
            
            elif metric_name == "total_interactions":
                count = self.db.query(Interaction).filter(
                    and_(
                        Interaction.site_id == site_id,
                        Interaction.fecha_interaccion >= start_date,
                        Interaction.fecha_interaccion <= end_date
                    )
                ).count()
                return AnalyticsMetric(
                    name=metric_name,
                    value=float(count),
                    type=MetricType.COUNT,
                    unit="interactions"
                )
            
            elif metric_name == "total_stickers":
                count = self.db.query(Sticker).filter(
                    and_(
                        Sticker.site_id == site_id,
                        Sticker.fecha_generacion >= start_date,
                        Sticker.fecha_generacion <= end_date
                    )
                ).count()
                return AnalyticsMetric(
                    name=metric_name,
                    value=float(count),
                    type=MetricType.COUNT,
                    unit="stickers"
                )
            
            # Agregar más métricas según sea necesario
            
            return None
            
        except Exception as e:
            logger.error("Error calculating metric", 
                        metric_name=metric_name, 
                        site_id=site_id, 
                        error=str(e))
            return None
    
    async def _calculate_dimension(
        self, 
        dimension_name: str, 
        site_id: str, 
        start_date: datetime, 
        end_date: datetime, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[AnalyticsDimension]:
        """Calcular dimensiones específicas"""
        try:
            dimensions = []
            
            if dimension_name == "interactions_by_type":
                interaction_types = ['like', 'comment', 'review', 'share', 'view']
                
                for interaction_type in interaction_types:
                    count = self.db.query(Interaction).filter(
                        and_(
                            Interaction.site_id == site_id,
                            Interaction.tipo_interaccion == interaction_type,
                            Interaction.fecha_interaccion >= start_date,
                            Interaction.fecha_interaccion <= end_date
                        )
                    ).count()
                    
                    if count > 0:
                        dimensions.append(AnalyticsDimension(
                            name=interaction_type,
                            value=interaction_type,
                            count=count,
                            percentage=0.0  # Se calculará después
                        ))
            
            # Calcular porcentajes
            total = sum(d.count for d in dimensions)
            for dimension in dimensions:
                dimension.percentage = (dimension.count / total * 100) if total > 0 else 0
            
            return dimensions
            
        except Exception as e:
            logger.error("Error calculating dimension", 
                        dimension_name=dimension_name, 
                        site_id=site_id, 
                        error=str(e))
            return []
    
    async def _calculate_time_series(
        self, 
        metrics: List[str], 
        site_id: str, 
        start_date: datetime, 
        end_date: datetime, 
        group_by: str, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[TimeSeriesData]:
        """Calcular series temporales"""
        try:
            time_series = []
            
            # Determinar intervalo
            if group_by == "hour":
                interval = timedelta(hours=1)
            elif group_by == "day":
                interval = timedelta(days=1)
            elif group_by == "week":
                interval = timedelta(weeks=1)
            elif group_by == "month":
                interval = timedelta(days=30)
            else:
                interval = timedelta(days=1)
            
            current_date = start_date
            while current_date <= end_date:
                next_date = current_date + interval
                
                # Calcular valor para el período
                value = 0.0
                if "total_interactions" in metrics:
                    count = self.db.query(Interaction).filter(
                        and_(
                            Interaction.site_id == site_id,
                            Interaction.fecha_interaccion >= current_date,
                            Interaction.fecha_interaccion < next_date
                        )
                    ).count()
                    value += count
                
                time_series.append(TimeSeriesData(
                    timestamp=current_date,
                    value=value
                ))
                
                current_date = next_date
            
            return time_series
            
        except Exception as e:
            logger.error("Error calculating time series", 
                        site_id=site_id, 
                        error=str(e))
            return []
